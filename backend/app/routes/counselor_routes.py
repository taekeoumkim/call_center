# backend/app/routes/counselor_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from ..models import User, ClientCall, ConsultationReport

counselor_bp = Blueprint('counselor', __name__)

# --- 상담사 상태 조회 및 변경 ---
@counselor_bp.route('/status', methods=['GET', 'POST'])
@jwt_required()
def manage_counselor_status():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "Counselor not found"}), 404

    if request.method == 'POST':
        data = request.get_json()
        is_active_from_frontend = data.get('is_active') # 프론트에서 0 또는 1로 전달

        if is_active_from_frontend is None or is_active_from_frontend not in [0, 1]:
            return jsonify({"message": "'is_active' field (0 or 1) is required in request body"}), 400

        if is_active_from_frontend == 1:
            user.status = 'available' # 상담 시작 시 'available'
        else:
            user.status = 'offline'   # 상담 종료 시 'offline'
            # 추가 로직: 만약 이 상담사가 현재 진행 중인 ClientCall이 있다면 처리 (예: 대기열로 복귀)
            # assigned_calls = ClientCall.query.filter_by(assigned_counselor_id=user.id, status='assigned').all()
            # for call in assigned_calls:
            #     call.status = 'pending' # 또는 다른 적절한 상태
            #     call.assigned_counselor_id = None

        try:
            db.session.commit()
            return jsonify({'message': 'Counselor status updated successfully', 'new_db_status': user.status}), 200
        except Exception as e:
            db.session.rollback()
            # current_app.logger.error(...) # 로깅
            return jsonify({'message': 'Failed to update counselor status', 'error': str(e)}), 500
    
    # GET 요청 처리
    is_active_flag = 1 if user.status in ['available', 'busy'] else 0
    return jsonify({'is_active': is_active_flag, 'current_db_status': user.status}), 200

# --- 상담사 마이페이지 - 프로필 정보 조회 ---
@counselor_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_counselor_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "Counselor not found"}), 404

    profile_data = {
        "username": user.username,  # 로그인 ID
        "name": user.name,          # 이름
        "status": user.status       # 현재 상태 (참고용)
    }
    return jsonify(profile_data), 200

# --- 상담사 마이페이지 - 프로필 정보 수정 ---
@counselor_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_counselor_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "Counselor not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is empty"}), 400

    # 'name' 필드만 수정 허용
    if 'name' in data:
        new_name = data.get('name')
        if not new_name or not isinstance(new_name, str) or len(new_name.strip()) == 0:
            return jsonify({"message": "Name cannot be empty"}), 400
        user.name = new_name.strip()
    else:
        # 'name' 외 다른 필드 변경 시도가 있다면 무시하거나, 명시적으로 에러를 반환할 수 있습니다.
        # 여기서는 'name' 필드만 처리하고 나머지는 무시합니다.
        # 만약 'name' 필드가 요청에 없다면, 아무 작업도 하지 않고 성공 메시지를 반환하거나,
        # "No updatable fields provided" 같은 메시지를 반환할 수 있습니다.
        # 여기서는 'name'이 없으면 업데이트할 내용이 없는 것으로 간주하고 성공 처리합니다.
        if not 'name' in data:
             return jsonify({"message": "No 'name' field provided to update"}), 400


    try:
        db.session.commit()
        updated_profile = {
            "username": user.username,
            "name": user.name,
            "status": user.status
        }
        return jsonify({"message": "Profile updated successfully", "profile": updated_profile}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update profile", "error": str(e)}), 500

# --- 상담사 마이페이지 - 비밀번호 변경 ---
@counselor_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_counselor_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.user_type != 'counselor':
        return jsonify({"message": "Counselor not found or not authorized"}), 404

    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    confirm_new_password = data.get('confirmNewPassword')

    if not all([current_password, new_password, confirm_new_password]):
        return jsonify({"message": "Current password, new password, and confirmation are required"}), 400
    
    if not check_password_hash(user.password_hash, current_password): # User 모델에 password_hash 필드가 있고, 여기에 해시된 비밀번호가 저장되어 있다고 가정
        return jsonify({"message": "Invalid current password"}), 400
    
    if new_password != confirm_new_password:
        return jsonify({"message": "New passwords do not match"}), 400
    
    # 새 비밀번호 유효성 검사 (예: 길이, 복잡도 - 필요시 추가)
    if len(new_password) < 6: # 예시: 최소 6자
        return jsonify({"message": "New password is too short (minimum 6 characters)"}), 400

    user.password_hash = generate_password_hash(new_password) # 새 비밀번호를 해시하여 저장
    try:
        db.session.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
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

    # 필수 필드 검증 (프론트엔드 필드명 기준)
    # client_age, client_gender는 선택 사항일 수 있으므로, 정책에 맞게 조정
    if not all([client_call_id_from_frontend, client_name_from_frontend, memo_text_from_frontend]):
        missing_fields = []
        if not client_call_id_from_frontend: missing_fields.append('client_id')
        if not client_name_from_frontend: missing_fields.append('name')
        if not memo_text_from_frontend: missing_fields.append('memo')
        return jsonify({'message': f'Required fields are missing: {", ".join(missing_fields)}'}), 400
    
    # age는 숫자로 변환 시도 (프론트에서 parseInt 했지만, 여기서도 유효성 검사 가능)
    try:
        if client_age_from_frontend is not None: # age가 제공된 경우에만 변환
            client_age_from_frontend = int(client_age_from_frontend)
    except ValueError:
        return jsonify({'message': 'Age must be a valid number.'}), 400


    client_call = ClientCall.query.get(client_call_id_from_frontend)
    if not client_call:
        return jsonify({'message': f'Client call with ID {client_call_id_from_frontend} not found'}), 404
    
    if client_call.assigned_counselor_id != counselor_id:
         return jsonify({'message': 'Unauthorized to report on this call. Not assigned to you.'}), 403

    existing_report = ConsultationReport.query.filter_by(client_call_id=client_call_id_from_frontend).first()
    if existing_report:
        return jsonify({'message': f'Report for client call ID {client_call_id_from_frontend} already exists. (Report ID: {existing_report.id})'}), 409

    new_report = ConsultationReport(
        client_call_id=client_call_id_from_frontend, # DB 필드명은 client_call_id
        counselor_id=counselor_id,
        client_name=client_name_from_frontend,       # DB 필드명은 client_name
        client_age=client_age_from_frontend,         # DB 필드명은 client_age
        client_gender=client_gender_from_frontend,   # DB 필드명은 client_gender
        memo_text=memo_text_from_frontend,           # DB 필드명은 memo_text
        risk_level_recorded=client_call.risk_level 
    )
    try:
        db.session.add(new_report)
        client_call.status = 'completed' 
        db.session.commit()
        return jsonify({'message': 'Report saved successfully', 'report_id': new_report.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to save report', 'error': str(e)}), 500


# --- 상담사 마이페이지 - 상담 완료 리스트 및 소견서 조회 라우트 ---
@counselor_bp.route('/myreports', methods=['GET'])
@jwt_required()
def get_my_reports():
    counselor_id = get_jwt_identity()
    user = User.query.get(counselor_id)
    if not user:
        return jsonify({"message": "Counselor not found or not authorized"}), 404

    search_by = request.args.get('search_by') 
    search_term = request.args.get('search_term')

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) # 페이지당 항목 수

    query = ConsultationReport.query.filter_by(counselor_id=counselor_id)

    # 검색 로직 (ClientCall과 조인하여 검색)
    if search_term:
        if search_by == 'name':
            query = query.filter(ConsultationReport.client_name.ilike(f'%{search_term}%'))
        elif search_by == 'phone':
            # ClientCall 테이블과 조인하여 전화번호 검색
            # ConsultationReport 모델과 ClientCall 모델이 client_call_id로 관계가 맺어져 있어야 합니다.
            # (예: ConsultationReport.client_call -> backref='reports' in ClientCall)
            # 또는 명시적 join 사용
            query = query.join(ClientCall, ClientCall.id == ConsultationReport.client_call_id)\
                         .filter(ClientCall.phone_number.ilike(f'%{search_term}%'))


    pagination = query.order_by(ConsultationReport.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    reports = pagination.items
    
    reports_data = []
    for report in reports:
        client_call = ClientCall.query.get(report.client_call_id) # 전화번호 가져오기 위해 필요
        
        # 프론트엔드 Report 인터페이스에 맞게 필드 구성
        report_item = {
            'id': report.id,                            # Report.id
            'name': report.client_name,                 # Report.name
            'age': report.client_age,                   # Report.age
            'gender': report.client_gender,             # Report.gender
            'phone': client_call.phone_number if client_call else None, # Report.phone
            'risk': report.risk_level_recorded,         # Report.risk
            'memo': report.memo_text,                   # Report.memo
            'created_at': report.created_at.isoformat() # Report.created_at
            # 'client_call_id'는 프론트에서 현재 직접 사용하지 않으므로 제외하거나 필요시 추가
        }
        reports_data.append(report_item)
        
    return jsonify({
        'reports': reports_data,
        'total_pages': pagination.pages,
        'current_page': pagination.page,
        'total_items': pagination.total
    }), 200

@counselor_bp.route('/report/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    current_counselor_id = get_jwt_identity()
    report = ConsultationReport.query.get_or_404(report_id)

    if report.counselor_id != current_counselor_id: # 권한 확인
        return jsonify({'message': 'Unauthorized to view this report'}), 403

    # ClientCall 정보도 함께 반환하면 좋음
    client_call = ClientCall.query.get(report.client_call_id)

    report_data = {
        'report_id': report.id,
        'client_call_id': report.client_call_id,
        'counselor_id': report.counselor_id,
        'client_name': report.client_name,
        'client_age': report.client_age,
        'client_gender': report.client_gender,
        'memo_text': report.memo_text,
        'risk_level_recorded': report.risk_level_recorded,
        'created_at': report.created_at.isoformat(),
        'client_phone_number': client_call.phone_number if client_call else None,
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