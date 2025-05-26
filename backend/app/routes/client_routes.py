# backend/app/routes/client_routes.py
from flask import Blueprint, request, jsonify
import os
import random
from werkzeug.utils import secure_filename
from .. import db
from ..models import ClientCall, User
from ..config import Config
from ..services import ai_service

client_bp = Blueprint('client', __name__)

# 파일 업로드 설정 (선택 사항: Config 클래스에서 관리 가능)
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'} # 허용할 오디오 확장자

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@client_bp.route('/submit', methods=['POST'])
def submit_client_data():
    # 프론트엔드에서 form-data로 음성 파일과 전화번호를 보낸다고 가정
    if 'audio' not in request.files:
        return jsonify({'message': 'No audio file part'}), 400
    audio_file = request.files['audio']
    phone_number = request.form.get('phoneNumber') # 폼 데이터에서 전화번호 추출

    if not phone_number:
        return jsonify({'message': 'Phone number is required'}), 400
    if audio_file.filename == '':
        return jsonify({'message': 'No selected audio file'}), 400

    if audio_file and allowed_file(audio_file.filename):
        filename = secure_filename(audio_file.filename) # 안전한 파일 이름 사용
        # 파일명 중복 방지를 위해 타임스탬프나 UUID 추가 권장
        import uuid; filename = str(uuid.uuid4()) + "_" + filename
        audio_file_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(audio_file_path)

        # --- AI 모델을 사용하여 위험도 분석 ---
        risk_level = ai_service.analyze_audio_risk(audio_file_path)

        if risk_level is None:
            # AI 분석 실패 시, 임시로 기본 위험도를 할당하거나 오류를 반환할 수 있음
            # 여기서는 기본 위험도 0을 할당하고, 로그를 남기는 것을 고려
            print(f"AI risk analysis failed for {audio_file_path}. Assigning default risk level 0.")
            risk_level = 0 # 또는 오류 반환: return jsonify({'message': 'AI analysis failed'}), 500
                           # 파일을 저장했으므로, 분석 실패 시에도 일단 DB에 기록할지 결정 필요

        # 상담사 배정 로직
        available_counselors = User.query.filter_by(status='available').all()
        assigned_counselor = None
        if not available_counselors:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path) # 상담사 없으면 파일도 삭제
            return jsonify({'message': 'No available counselors at the moment. Please try again later.'}), 503

        # TODO: 가장 대기열이 적은 상담사에게 배정하는 로직 고도화 필요
        assigned_counselor = available_counselors[0] if available_counselors else None


        new_call = ClientCall(
            phone_number=phone_number,
            audio_file_path=audio_file_path, # DB에는 상대경로나 전체경로 저장
            risk_level=risk_level, # <<< AI가 분석한 위험도
            status='pending',
            assigned_counselor_id=assigned_counselor.id if assigned_counselor else None
        )
        try:
            db.session.add(new_call)
            db.session.commit()
            # AI 분석 실패 시 파일은 이미 저장되었고, DB에도 기록됨 (기본 위험도로)
            # 성공/실패 여부에 따라 프론트에 다른 메시지를 줄 수도 있음
            return jsonify({
                'message': 'Call data submitted successfully.',
                'call_id': new_call.id,
                'risk_level': risk_level, # 분석된 (또는 기본) 위험도
                'assigned_counselor_id': assigned_counselor.id if assigned_counselor else None
            }), 201
        except Exception as e:
            db.session.rollback()
            if os.path.exists(audio_file_path): # DB 저장 실패 시 파일 삭제
                os.remove(audio_file_path)
            return jsonify({'message': 'Failed to submit call data after analysis', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'File type not allowed or no file'}), 400