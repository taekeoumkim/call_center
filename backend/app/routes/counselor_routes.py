# backend/app/routes/counselor_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from ..models import User, ClientCall, ConsultationReport
from ..utils.hybrid_encryption import HybridEncryption

counselor_bp = Blueprint('counselor', __name__)

def log_event(event: str, data: dict = None):
    if data and 'name' in data:
        data = {**data, 'user_name': data.pop('name')}
    current_app.logger.info(f"[Counselor] {event}", extra=data if data else {})

# --- 상담사 상태 조회 및 변경 ---
@counselor_bp.route('/status', methods=['GET', 'POST'])
@jwt_required()
def manage_counselor_status():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        log_event('상태 관리 실패 - 상담사 찾을 수 없음', {'user_id': current_user_id})
        return jsonify({"message": "Counselor not found"}), 404

    if request.method == 'POST':
        data = request.get_json()
        is_active_from_frontend = data.get('is_active') # 프론트에서 0 또는 1로 전달

        if is_active_from_frontend is None or is_active_from_frontend not in [0, 1]:
            log_event('상태 변경 실패 - 잘못된 is_active 값', {'user_id': current_user_id, 'is_active': is_active_from_frontend})
            return jsonify({"message": "'is_active' field (0 or 1) is required in request body"}), 400

        if is_active_from_frontend == 1:
            user.status = 'available' # 상담 시작 시 'available'
            log_event('상태 변경 - 상담 가능', {'user_id': current_user_id})
        else:
            user.status = 'offline'   # 상담 종료 시 'offline'
            # 추가 로직: 만약 이 상담사가 현재 진행 중인 ClientCall이 있다면 처리 (예: 대기열로 복귀)
            # assigned_calls = ClientCall.query.filter_by(assigned_counselor_id=user.id, status='assigned').all()
            # for call in assigned_calls:
            #     call.status = 'pending' # 또는 다른 적절한 상태
            #     call.assigned_counselor_id = None

        try:
            db.session.commit()
            log_event('상태 변경 성공', {'user_id': current_user_id, 'new_status': user.status})
            return jsonify({'message': 'Counselor status updated successfully', 'new_db_status': user.status}), 200
        except Exception as e:
            db.session.rollback()
            log_event('상태 변경 실패', {'user_id': current_user_id, 'error': str(e)})
            return jsonify({'message': 'Failed to update counselor status', 'error': str(e)}), 500
    
    # GET 요청 처리
    is_active_flag = 1 if user.status in ['available', 'busy'] else 0
    log_event('상태 조회 성공', {'user_id': current_user_id, 'status': user.status})
    return jsonify({'is_active': is_active_flag, 'current_db_status': user.status}), 200

# --- 상담사 마이페이지 - 프로필 정보 조회 ---
@counselor_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_counselor_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        log_event('프로필 조회 실패 - 상담사 찾을 수 없음', {'user_id': current_user_id})
        return jsonify({"message": "Counselor not found"}), 404

    profile_data = {
        "username": user.username,  # 로그인 ID
        "name": user.name,          # 이름
        "status": user.status       # 현재 상태 (참고용)
    }
    log_event('프로필 조회 성공', {'user_id': current_user_id})
    return jsonify(profile_data), 200

# --- 상담사 마이페이지 - 프로필 정보 수정 ---
@counselor_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_counselor_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        log_event('프로필 수정 실패 - 상담사 찾을 수 없음', {'user_id': current_user_id})
        return jsonify({"message": "Counselor not found"}), 404

    data = request.get_json()
    if not data:
        log_event('프로필 수정 실패 - 요청 데이터 없음', {'user_id': current_user_id})
        return jsonify({"message": "Request body is empty"}), 400

    # 'name' 필드만 수정 허용
    if 'name' in data:
        new_name = data.get('name')
        if not new_name or not isinstance(new_name, str) or len(new_name.strip()) == 0:
            log_event('프로필 수정 실패 - 잘못된 이름 형식', {'user_id': current_user_id})
            return jsonify({"message": "Name cannot be empty"}), 400
        user.name = new_name.strip()
        log_event('프로필 수정 시도', {'user_id': current_user_id, 'new_name': new_name})
    else:
        log_event('프로필 수정 실패 - 이름 필드 누락', {'user_id': current_user_id})
        return jsonify({"message": "No 'name' field provided to update"}), 400

    try:
        db.session.commit()
        updated_profile = {
            "username": user.username,
            "name": user.name,
            "status": user.status
        }
        log_event('프로필 수정 성공', {'user_id': current_user_id})
        return jsonify({"message": "Profile updated successfully", "profile": updated_profile}), 200
    except Exception as e:
        db.session.rollback()
        log_event('프로필 수정 실패', {'user_id': current_user_id, 'error': str(e)})
        return jsonify({"message": "Failed to update profile", "error": str(e)}), 500

# --- 상담사 마이페이지 - 비밀번호 변경 ---
@counselor_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_counselor_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.user_type != 'counselor':
        log_event('비밀번호 변경 실패 - 상담사 찾을 수 없음', {'user_id': current_user_id})
        return jsonify({"message": "Counselor not found or not authorized"}), 404

    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    confirm_new_password = data.get('confirmNewPassword')

    if not all([current_password, new_password, confirm_new_password]):
        log_event('비밀번호 변경 실패 - 필수 필드 누락', {'user_id': current_user_id})
        return jsonify({"message": "Current password, new password, and confirmation are required"}), 400
    
    if not check_password_hash(user.password_hash, current_password): # User 모델에 password_hash 필드가 있고, 여기에 해시된 비밀번호가 저장되어 있다고 가정
        log_event('비밀번호 변경 실패 - 현재 비밀번호 불일치', {'user_id': current_user_id})
        return jsonify({"message": "Invalid current password"}), 400
    
    if new_password != confirm_new_password:
        log_event('비밀번호 변경 실패 - 새 비밀번호 불일치', {'user_id': current_user_id})
        return jsonify({"message": "New passwords do not match"}), 400
    
    # 새 비밀번호 유효성 검사 (예: 길이, 복잡도 - 필요시 추가)
    if len(new_password) < 6: # 예시: 최소 6자
        log_event('비밀번호 변경 실패 - 비밀번호 너무 짧음', {'user_id': current_user_id})
        return jsonify({"message": "New password is too short (minimum 6 characters)"}), 400

    user.password_hash = generate_password_hash(new_password) # 새 비밀번호를 해시하여 저장
    try:
        db.session.commit()
        log_event('비밀번호 변경 성공', {'user_id': current_user_id})
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        log_event('비밀번호 변경 실패', {'user_id': current_user_id, 'error': str(e)})
        return jsonify({"message": "Failed to update password", "error": str(e)}), 500

# --- 소견서 저장 ---
@counselor_bp.route('/report/save', methods=['POST'])
@jwt_required()
def save_report():
    counselor_id = get_jwt_identity()
    data = request.get_json()
    
    # 프론트엔드에서 오는 필드명으로 수정
    client_call_id_from_frontend = data.get('client_id') # 'client_id'로 받음
    client_name_from_frontend = data.get('name')         # 'name'으로 받음
    client_age_from_frontend = data.get('age')           # 'age'로 받음
    client_gender_from_frontend = data.get('gender')     # 'gender'으로 받음
    memo_text_from_frontend = data.get('memo')           # 'memo'로 받음
    transcribed_text_from_frontend = data.get('transcribed_text') # Whisper로 인식된 텍스트

    # 필수 필드 검증 (프론트엔드 필드명 기준)
    # client_age, client_gender는 선택 사항일 수 있으므로, 정책에 맞게 조정
    if not all([client_call_id_from_frontend, memo_text_from_frontend]):
        missing_fields = []
        if not client_call_id_from_frontend: missing_fields.append('client_id')
        if not memo_text_from_frontend: missing_fields.append('memo')
        log_event('소견서 저장 실패 - 필수 필드 누락', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend,
            'missing_fields': missing_fields
        })
        return jsonify({'message': f'Required fields are missing: {", ".join(missing_fields)}'}), 400
    
    # age는 숫자로 변환 시도 (프론트에서 parseInt 했지만, 여기서도 유효성 검사 가능)
    try:
        if client_age_from_frontend is not None: # age가 제공된 경우에만 변환
            client_age_from_frontend = int(client_age_from_frontend)
    except ValueError:
        log_event('소견서 저장 실패 - 잘못된 나이 형식', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend,
            'age': client_age_from_frontend
        })
        return jsonify({'message': 'Age must be a valid number.'}), 400


    client_call = ClientCall.query.get(client_call_id_from_frontend)
    if not client_call:
        log_event('소견서 저장 실패 - 통화 찾을 수 없음', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend
        })
        return jsonify({'message': f'Client call with ID {client_call_id_from_frontend} not found'}), 404
    
    if client_call.assigned_counselor_id != counselor_id:
        log_event('소견서 저장 실패 - 권한 없음', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend,
            'assigned_counselor_id': client_call.assigned_counselor_id
        })
        return jsonify({'message': 'Unauthorized to report on this call. Not assigned to you.'}), 403

    existing_report = ConsultationReport.query.filter_by(client_call_id=client_call_id_from_frontend).first()
    if existing_report:
        log_event('소견서 저장 실패 - 이미 존재함', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend,
            'existing_report_id': existing_report.id
        })
        return jsonify({'message': f'Report for client call ID {client_call_id_from_frontend} already exists. (Report ID: {existing_report.id})'}), 409

    new_report = ConsultationReport(
        client_call_id=client_call_id_from_frontend,
        counselor_id=counselor_id,
        client_gender=client_gender_from_frontend,
        risk_level_recorded=client_call.risk_level
    )

    # 암호화할 필드들 설정
    if client_name_from_frontend:
        new_report.client_name = client_name_from_frontend
    else:
        new_report.client_name = '미상'  # 이름이 없을 경우 기본값 설정
    if client_age_from_frontend:
        new_report.client_age = client_age_from_frontend
    if memo_text_from_frontend:
        new_report.memo_text = memo_text_from_frontend
    if transcribed_text_from_frontend:
        new_report.transcribed_text = transcribed_text_from_frontend

    # 필드 암호화
    hybrid_encryption = HybridEncryption()
    new_report.encrypt_fields(hybrid_encryption)

    try:
        db.session.add(new_report)
        client_call.status = 'completed' 
        db.session.commit()
        log_event('소견서 저장 성공', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend,
            'report_id': new_report.id
        })
        return jsonify({'message': 'Report saved successfully', 'report_id': new_report.id}), 201
    except Exception as e:
        db.session.rollback()
        log_event('소견서 저장 실패', {
            'counselor_id': counselor_id,
            'client_call_id': client_call_id_from_frontend,
            'error': str(e)
        })
        return jsonify({'message': 'Failed to save report', 'error': str(e)}), 500


# --- 상담사 마이페이지 - 상담 완료 리스트 및 소견서 조회 라우트 ---
@counselor_bp.route('/myreports', methods=['GET'])
@jwt_required()
def get_my_reports():
    """상담사가 작성한 모든 소견서 목록을 반환합니다."""
    try:
        current_user_id = get_jwt_identity()
        reports = ConsultationReport.query.filter_by(counselor_id=current_user_id).all()
        
        if not reports:
            return jsonify({'reports': []}), 200
        
        hybrid_encryption = HybridEncryption()
        report_list = []
        decryption_failed = False
        
        for report in reports:
            try:
                # DEK 관련 필드 설정
                hybrid_encryption.encrypted_dek_trad = report.encrypted_dek_trad
                hybrid_encryption.pqc_kem_ciphertext = report.pqc_kem_ciphertext
                hybrid_encryption.pqc_secret_key = report.pqc_secret_key
                hybrid_encryption.nonce_for_dek_encryption = report.nonce_for_dek_encryption
                hybrid_encryption.encrypted_dek_by_pqc_shared_secret = report.encrypted_dek_by_pqc_shared_secret
                
                # 필드 복호화
                report.decrypt_fields(hybrid_encryption)
                
                # ClientCall 정보 가져오기
                client_call = ClientCall.query.get(report.client_call_id)
                
                # 복호화된 데이터 확인
                current_app.logger.debug(f"복호화된 데이터 - client_name: {report.client_name}, memo_text: {report.memo_text}, transcribed_text: {report.transcribed_text}")
                current_app.logger.debug(f"ClientCall 정보 - phone_number: {client_call.phone_number if client_call else None}, risk_level: {report.risk_level_recorded}")
                
                report_data = {
                    'id': report.id,
                    'client_call_id': report.client_call_id,
                    'name': report.client_name if report.client_name else '알 수 없음',
                    'age': report.client_age if report.client_age else '알 수 없음',
                    'gender': report.client_gender if report.client_gender else '알 수 없음',
                    'risk': report.risk_level_recorded,
                    'created_at': report.created_at.isoformat() if report.created_at else None,
                    'memo': report.memo_text if report.memo_text else '알 수 없음',
                    'transcribed_text': report.transcribed_text if report.transcribed_text else '알 수 없음',
                    'phone': client_call.phone_number if client_call else '알 수 없음'
                }
                report_list.append(report_data)
            except Exception as e:
                current_app.logger.error(f"소견서 {report.id} 복호화 실패: {str(e)}")
                decryption_failed = True
                continue
        
        if decryption_failed:
            return jsonify({
                'error': '일부 소견서의 복호화에 실패했습니다. 관리자에게 문의해주세요.',
                'reports': report_list
            }), 500
        
        return jsonify({'reports': report_list}), 200
        
    except Exception as e:
        current_app.logger.error(f"소견서 목록 조회 실패: {str(e)}")
        return jsonify({
            'error': '소견서 목록을 불러오는데 실패했습니다.',
            'reports': []
        }), 500

@counselor_bp.route('/report/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    current_counselor_id = get_jwt_identity()
    report = ConsultationReport.query.get_or_404(report_id)

    if report.counselor_id != current_counselor_id: # 권한 확인
        return jsonify({'message': 'Unauthorized to view this report'}), 403

    # ClientCall 정보도 함께 반환하면 좋음
    client_call = ClientCall.query.get(report.client_call_id)

    # 암호화된 필드 복호화
    hybrid_encryption = HybridEncryption()
    
    # DEK 관련 필드 설정
    hybrid_encryption.encrypted_dek_trad = report.encrypted_dek_trad
    hybrid_encryption.pqc_kem_ciphertext = report.pqc_kem_ciphertext
    hybrid_encryption.pqc_secret_key = report.pqc_secret_key
    hybrid_encryption.nonce_for_dek_encryption = report.nonce_for_dek_encryption
    hybrid_encryption.encrypted_dek_by_pqc_shared_secret = report.encrypted_dek_by_pqc_shared_secret
    
    # 필드 복호화
    report.decrypt_fields(hybrid_encryption)

    report_data = {
        'report_id': report.id,
        'client_call_id': report.client_call_id,
        'counselor_id': report.counselor_id,
        'client_name': report.client_name if report.client_name else '알 수 없음',
        'client_age': report.client_age if report.client_age else '알 수 없음',
        'client_gender': report.client_gender if report.client_gender else '알 수 없음',
        'memo_text': report.memo_text if report.memo_text else '알 수 없음',
        'transcribed_text': report.transcribed_text if report.transcribed_text else '알 수 없음',
        'risk_level_recorded': report.risk_level_recorded,
        'created_at': report.created_at.isoformat() if report.created_at else None,
        'client_phone_number': client_call.phone_number if client_call else '알 수 없음',
        'call_received_at': client_call.received_at.isoformat() if client_call else None
    }
    return jsonify(report_data), 200

@counselor_bp.route('/assign_client/<int:client_call_id>', methods=['POST'])
@jwt_required()
def assign_client_to_counselor(client_call_id):
    current_counselor_id = get_jwt_identity()
    
    client_call = ClientCall.query.get(client_call_id)
    if not client_call:
        return jsonify({"message": "Client call not found"}), 404

    # 이미 다른 상담사에게 배정되었는지, 또는 이미 완료된 콜인지 등 상태 체크 (선택적이지만 권장)
    if client_call.assigned_counselor_id and client_call.assigned_counselor_id != current_counselor_id:
        # 이미 다른 상담사에게 배정된 경우 (정책에 따라 다르게 처리 가능)
        other_counselor = User.query.get(client_call.assigned_counselor_id)
        return jsonify({"message": f"This call is already assigned to another counselor ({other_counselor.name if other_counselor else 'Unknown'})."}), 409 # Conflict
    
    if client_call.status not in ['pending', 'available_for_assignment']: # 'pending' 또는 배정 가능한 상태일 때만
        return jsonify({"message": f"This call is not in a state to be assigned (current status: {client_call.status})."}), 400

    client_call.assigned_counselor_id = current_counselor_id
    client_call.status = 'assigned' # 또는 'being_consulted' 등 상태 변경
    
    try:
        db.session.commit()
        # 프론트엔드에 배정된 내담자 정보를 다시 보내줄 수도 있음
        assigned_client_data = {
            "id": client_call.id,
            "phone": client_call.phone_number,
            "risk": client_call.risk_level,
            "status": client_call.status,
            "assigned_counselor_id": client_call.assigned_counselor_id
        }
        return jsonify({"message": "Client assigned successfully.", "client": assigned_client_data}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to assign client", "error": str(e)}), 500