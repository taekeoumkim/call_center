# backend/app/routes/client_routes.py
from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import func
from .. import db
from ..models import ClientCall, User
from ..services import ai_service
from ..config import Config

client_bp = Blueprint('client', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@client_bp.route('/submit', methods=['POST'])
def submit_client_data():
    if 'audio' not in request.files:
        return jsonify({'message': 'No audio file part'}), 400
    audio_file = request.files['audio']
    phone_number = request.form.get('phoneNumber')

    if not phone_number:
        return jsonify({'message': 'Phone number is required'}), 400
    if audio_file.filename == '':
        return jsonify({'message': 'No selected audio file'}), 400

    if audio_file and allowed_file(audio_file.filename):
        original_filename = secure_filename(audio_file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + original_filename
        audio_file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        audio_file.save(audio_file_path)
        current_app.logger.info(f"Audio file saved to: {audio_file_path}")

        risk_level = ai_service.analyze_audio_risk(audio_file_path)

        if risk_level is None:
            current_app.logger.error(f"AI risk analysis failed for {audio_file_path}. Assigning default risk level 0.")
            risk_level = 0
        else:
            current_app.logger.info(f"AI risk analysis completed for {audio_file_path}. Risk level: {risk_level}")

        # --- 상담사 배정 로직 ---
        assigned_counselor_id = None

        # 1. 'available' 상태인 상담사 목록 가져오기
        available_counselors = User.query.filter_by(status='available').all()

        if not available_counselors:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'No available counselors at the moment. Please try again later.'}), 503

        # 2. 각 상담사별 현재 활성 대기열 수 계산
        # ClientCall 테이블에서 'pending' 또는 'assigned' 상태인 통화 수를 상담사별로 집계
        # 결과: [(counselor_id, count), (counselor_id, count), ...]
        # SQLAlchemy의 func.count와 group_by를 사용
        subquery = db.session.query(
            ClientCall.assigned_counselor_id,
            func.count(ClientCall.id).label('active_calls')
        ).filter(
            ClientCall.status.in_(['pending', 'assigned']) # 활성 상태로 간주할 상태들
        ).group_by(
            ClientCall.assigned_counselor_id
        ).subquery()

        # 상담사 정보와 그들의 활성 통화 수를 조인 (LEFT JOIN 사용)
        # 결과: [(User 객체, active_calls_count 또는 None), ...]
        counselor_call_counts_query = db.session.query(
            User,
            subquery.c.active_calls
        ).outerjoin(
            subquery, User.id == subquery.c.assigned_counselor_id
        ).filter(
            User.status == 'available' # 다시 한번 'available' 상태 필터링
        )
        
        counselors_with_counts = []
        for user, count in counselor_call_counts_query.all():
            active_calls = count if count is not None else 0 # 집계 결과가 없는 상담사는 0건
            counselors_with_counts.append({'user': user, 'active_calls': active_calls})

        if not counselors_with_counts:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Failed to determine counselor availability for assignment.'}), 500


        # 3 & 4. 대기열 수가 가장 적은 상담사 찾기 (같을 경우 ID가 낮은 순)
        # active_calls 기준으로 오름차순 정렬, 그 다음 user.id 기준으로 오름차순 정렬
        counselors_with_counts.sort(key=lambda x: (x['active_calls'], x['user'].id))

        # 가장 적합한 상담사 선택
        if counselors_with_counts: # 정렬된 리스트에서 첫 번째 상담사가 가장 적합
            assigned_counselor_id = counselors_with_counts[0]['user'].id
            current_app.logger.info(f"Assigned to counselor ID: {assigned_counselor_id} with {counselors_with_counts[0]['active_calls']} active calls.")
        else:
            # 이 경우는 available_counselors는 있었지만, 어떤 이유로 최종 배정할 상담사를 찾지 못한 경우
            # (이론상으로는 available_counselors가 있다면 이 분기에 도달하지 않아야 함)
            current_app.logger.error("Could not assign to any available counselor after AI analysis.")
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Could not assign to any available counselor.'}), 500


        new_call = ClientCall(
            phone_number=phone_number,
            audio_file_path=audio_file_path,
            risk_level=risk_level,
            status='pending', # 초기 상태는 'pending', 상담사가 수락하면 'assigned' 등으로 변경 가능
            assigned_counselor_id=assigned_counselor_id
        )
        try:
            db.session.add(new_call)
            db.session.commit()
            current_app.logger.info(f"New call (ID: {new_call.id}) submitted and saved to DB.")
            return jsonify({
                'message': 'Call data submitted successfully and assigned.',
                'call_id': new_call.id,
                'risk_level': risk_level,
                'assigned_counselor_id': assigned_counselor_id
            }), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving new call to DB for {audio_file_path}")
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Failed to submit call data after assignment', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'File type not allowed or no file'}), 400