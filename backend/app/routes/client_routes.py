# backend/app/routes/client_routes.py
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc, asc
from .. import db
from ..models import ClientCall, User, ConsultationReport
from ..services import ai_service
from ..config import Config

client_bp = Blueprint('client', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'webm'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@client_bp.route('/<int:client_call_id>', methods=['GET'])
@jwt_required() # 인증된 사용자만 접근 가능
def get_client_detail(client_call_id):
    """
    특정 ClientCall(내담자 통화)의 상세 정보를 반환합니다.
    프론트엔드의 ClientDetailPage에서 사용됩니다.
    """
    client_call = ClientCall.query.get(client_call_id)

    if not client_call:
        return jsonify({"message": "Client call not found"}), 404

    # 프론트엔드 Client 인터페이스에 맞게 데이터 구성
    # interface Client {
    #   id: number;
    #   phone: string;
    #   risk: 0 | 1 | 2;
    # }
    client_data = {
        "id": client_call.id,
        "phone": client_call.phone_number, # ClientCall.phone_number -> phone
        "risk": client_call.risk_level,    # ClientCall.risk_level -> risk
        "transcribed_text": client_call.transcribed_text  # 음성 인식 텍스트 추가
        # 필요에 따라 다른 ClientCall 필드도 추가 가능
        # "status": client_call.status,
        # "received_at": client_call.received_at.isoformat() if client_call.received_at else None,
    }

    return jsonify(client_data), 200

@client_bp.route('/queue', methods=['GET'])
@jwt_required()
def get_waiting_queue():
    try:
        current_app.logger.debug("Fetching waiting queue...")
        # status가 'pending' 또는 'available_for_assignment'인 ClientCall들을 risk_level 내림차순, received_at 오름차순으로 정렬
        waiting_calls = db.session.query(ClientCall)\
                                  .filter(ClientCall.status.in_(['pending', 'available_for_assignment']))\
                                  .order_by(db.desc(ClientCall.risk_level), db.asc(ClientCall.received_at))\
                                  .all()

        client_list_for_frontend = []
        if waiting_calls:
            for call in waiting_calls:
                client_list_for_frontend.append({
                    'id': call.id,
                    'phone': call.phone_number,
                    'risk': call.risk_level, # 위험도 값 그대로 사용 (0, 1, 2)
                })
            current_app.logger.debug(f"Found {len(client_list_for_frontend)} calls in queue.")
        else:
            current_app.logger.debug("No calls found in pending queue.")
        
        return jsonify(clients=client_list_for_frontend), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching waiting queue: {str(e)}")
        return jsonify({"message": "Failed to fetch waiting queue", "error": str(e)}), 500
    
@client_bp.route('/queue/reset', methods=['DELETE'])
@jwt_required()
def reset_client_queue():
    try:
        current_app.logger.info("Attempting to reset client queue...")

        # 'pending' 또는 'available_for_assignment' 상태인 모든 통화의 상태를 'cancelled' 또는 'archived'로 변경
        calls_to_reset = ClientCall.query.filter(ClientCall.status.in_(['pending', 'available_for_assignment'])).all()
        num_reset = len(calls_to_reset)
        for call in calls_to_reset:
            call.status = 'cancelled_by_reset' # 또는 'archived', 'aborted' 등 적절한 상태명
            # call.assigned_counselor_id = None # 배정 정보도 초기화할 수 있음
        
        if num_reset > 0:
            db.session.commit()
            current_app.logger.info(f"{num_reset} pending calls were marked as 'cancelled_by_reset'.")
        else:
            current_app.logger.info("No pending calls found to reset.")

        return jsonify({'message': f'Client queue reset successfully. {num_reset} calls affected.'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting client queue: {str(e)}")
        return jsonify({"message": "Failed to reset client queue", "error": str(e)}), 500
    
@client_bp.route('/queue/delete', methods=['POST'])
@jwt_required()
def delete_client_from_queue():
    data = request.get_json()
    client_id_to_delete = data.get('client_id')

    if client_id_to_delete is None: # client_id가 없는 경우
        return jsonify({"message": "client_id is required in the request body"}), 400

    try:
        client_call_id = int(client_id_to_delete)
    except ValueError:
        return jsonify({"message": "client_id must be an integer"}), 400

    call_to_modify = ClientCall.query.get(client_call_id)

    if not call_to_modify:
        current_app.logger.warn(f"Attempted to delete client_id {client_call_id} from queue, but it was not found.")
        return jsonify({"message": f"Client call with ID {client_call_id} not found."}), 404

    current_app.logger.info(f"Request to remove client_id {client_call_id} from queue. Current status: {call_to_modify.status}")

    # 이미 'completed' 상태라면 (소견서 저장 시 이미 변경됨), 특별한 추가 작업 없이 성공 응답
    if call_to_modify.status == 'completed':
        return jsonify({"message": f"Client call {client_call_id} is already completed. No further action needed for queue removal."}), 200
    
    # 만약 'pending', 'available_for_assignment' 또는 'assigned' 상태에서 이 API가 호출되었다면 (예상치 못한 상황),
    # 'completed' 또는 다른 적절한 상태로 변경할 수 있습니다.
    if call_to_modify.status in ['pending', 'available_for_assignment', 'assigned']:
        call_to_modify.status = 'completed_manual_dequeue'
        # call_to_modify.assigned_counselor_id = None # 배정 정보 초기화는 소견서 작성 상담사가 있으므로 불필요할 수 있음

    try:
        db.session.commit()
        current_app.logger.info(f"Client call {client_call_id} processed for queue removal (or was already completed).")
        return jsonify({"message": f"Client call {client_call_id} successfully processed for queue removal."}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing client call {client_call_id} for queue removal: {str(e)}")
        return jsonify({"message": "Failed to process client call for queue removal", "error": str(e)}), 500

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

        # 음성 인식 및 위험도 분석
        transcribed_text = ai_service.speech_to_text(audio_file_path)
        risk_level = ai_service.predict_suicide_risk(transcribed_text) if transcribed_text else 0

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
        subquery = db.session.query(
            ClientCall.assigned_counselor_id,
            func.count(ClientCall.id).label('active_calls')
        ).filter(
            ClientCall.status.in_(['pending', 'assigned'])
        ).group_by(
            ClientCall.assigned_counselor_id
        ).subquery()

        counselor_call_counts_query = db.session.query(
            User,
            subquery.c.active_calls
        ).outerjoin(
            subquery, User.id == subquery.c.assigned_counselor_id
        ).filter(
            User.status == 'available'
        )
        
        counselors_with_counts = []
        for user, count in counselor_call_counts_query.all():
            active_calls = count if count is not None else 0
            counselors_with_counts.append({'user': user, 'active_calls': active_calls})

        if not counselors_with_counts:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Failed to determine counselor availability for assignment.'}), 500

        counselors_with_counts.sort(key=lambda x: (x['active_calls'], x['user'].id))

        # 가장 적합한 상담사 선택
        if counselors_with_counts:
            assigned_counselor_id = counselors_with_counts[0]['user'].id
            current_app.logger.info(f"Assigned to counselor ID: {assigned_counselor_id} with {counselors_with_counts[0]['active_calls']} active calls.")
        else:
            current_app.logger.error("Could not assign to any available counselor after AI analysis.")
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Could not assign to any available counselor.'}), 500

        new_call = ClientCall(
            phone_number=phone_number,
            audio_file_path=audio_file_path,
            transcribed_text=transcribed_text, # 음성 인식 텍스트 저장
            risk_level=risk_level,
            status='available_for_assignment',  # 'pending' 대신 'available_for_assignment'로 변경
            assigned_counselor_id=None  # 상담사 배정은 나중에 하도록 변경
        )
        try:
            db.session.add(new_call)
            db.session.commit()
            current_app.logger.info(f"New call (ID: {new_call.id}) submitted and saved to DB.")
            return jsonify({
                'message': 'Call data submitted successfully.',
                'call_id': new_call.id,
                'risk_level': risk_level
            }), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving new call to DB for {audio_file_path}")
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Failed to submit call data after assignment', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'File type not allowed or no file'}), 400

@client_bp.route('/<int:client_call_id>/previous-reports', methods=['GET'])
@jwt_required()
def get_previous_reports(client_call_id):
    """
    특정 ClientCall과 같은 전화번호를 가진 이전 소견서들을 반환합니다.
    """
    client_call = ClientCall.query.get(client_call_id)
    if not client_call:
        return jsonify({"message": "Client call not found"}), 404

    # 같은 전화번호를 가진 다른 ClientCall들을 찾습니다
    previous_calls = ClientCall.query.filter(
        ClientCall.phone_number == client_call.phone_number,
        ClientCall.id != client_call.id  # 현재 통화는 제외
    ).all()

    previous_reports = []
    for call in previous_calls:
        report = ConsultationReport.query.filter_by(client_call_id=call.id).first()
        if report:
            previous_reports.append({
                'id': report.id,
                'name': report.client_name,
                'age': report.client_age,
                'gender': report.client_gender,
                'phone': call.phone_number,
                'risk': report.risk_level_recorded,
                'memo': report.memo_text,
                'transcribed_text': report.transcribed_text,
                'created_at': report.created_at.isoformat()
            })

    # 생성일 기준으로 정렬 (최신순)
    previous_reports.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify({
        'reports': previous_reports,
        'latest_report': previous_reports[0] if previous_reports else None
    }), 200