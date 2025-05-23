# backend/app/routes/counselor_routes.py
from flask import Blueprint, request, jsonify
# from flask_jwt_extended import jwt_required, get_jwt_identity # JWT 사용 시
from .. import db
from ..models import User, ClientCall, ConsultationReport

counselor_bp = Blueprint('counselor', __name__)

# --- 상담사 상태 변경 ---
@counselor_bp.route('/status', methods=['POST'])
# @jwt_required() # JWT 인증 필요
def update_counselor_status():
    # user_id = get_jwt_identity() # JWT에서 사용자 ID 가져오기
    # 임시: 요청 바디에서 user_id를 받는다고 가정 (JWT 구현 전)
    data = request.get_json()
    user_id = data.get('user_id')
    new_status = data.get('status') # 'available', 'busy', 'offline' 등

    if not user_id or not new_status:
        return jsonify({'message': 'User ID and status are required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    allowed_statuses = ['available', 'busy', 'offline'] # 예시
    if new_status not in allowed_statuses:
        return jsonify({'message': f'Invalid status. Allowed: {", ".join(allowed_statuses)}'}), 400

    user.status = new_status
    try:
        db.session.commit()
        return jsonify({'message': f'Status updated to {new_status}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update status', 'error': str(e)}), 500

# --- 상담사 대기열 조회 ---
@counselor_bp.route('/queue', methods=['GET'])
# @jwt_required()
def get_counselor_queue():
    # user_id = get_jwt_identity()
    # 임시: 쿼리 파라미터에서 user_id를 받는다고 가정
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # 해당 상담사에게 배정된 'pending' 또는 'assigned' 상태의 통화 목록
    # 위험도 높은 순 -> 접수 시간 빠른 순 정렬
    calls = ClientCall.query.filter_by(assigned_counselor_id=user_id)\
                            .filter(ClientCall.status.in_(['pending', 'assigned']))\
                            .order_by(ClientCall.risk_level.desc(), ClientCall.received_at.asc())\
                            .all()

    queue_data = [{
        'call_id': call.id,
        'phone_number': call.phone_number,
        'risk_level': call.risk_level,
        'received_at': call.received_at.isoformat(), # ISO 형식으로 변환
        'status': call.status
    } for call in calls]
    return jsonify(queue_data), 200

# --- 소견서 저장 ---
@counselor_bp.route('/report/save', methods=['POST'])
# @jwt_required()
def save_report():
    # counselor_id = get_jwt_identity()
    data = request.get_json()
    # 임시: counselor_id를 요청 바디에서 받음
    counselor_id = data.get('counselor_id')
    client_call_id = data.get('client_call_id')
    client_name = data.get('client_name')
    client_age = data.get('client_age')
    client_gender = data.get('client_gender')
    memo_text = data.get('memo_text')
    # risk_level_recorded는 client_call에서 가져오거나, 프론트에서 다시 전달받을 수 있음
    # 여기서는 client_call에서 가져온다고 가정

    if not all([counselor_id, client_call_id, memo_text]): # 필수 필드 확인
        return jsonify({'message': 'Counselor ID, Client Call ID, and Memo are required'}), 400

    client_call = ClientCall.query.get(client_call_id)
    if not client_call:
        return jsonify({'message': 'Client call not found'}), 404
    if client_call.assigned_counselor_id != counselor_id: # 권한 확인 (해당 상담사의 통화인지)
         return jsonify({'message': 'Unauthorized to report on this call'}), 403


    new_report = ConsultationReport(
        client_call_id=client_call_id,
        counselor_id=counselor_id,
        client_name=client_name,
        client_age=client_age,
        client_gender=client_gender,
        memo_text=memo_text,
        risk_level_recorded=client_call.risk_level # 통화 당시의 위험도 기록
    )
    try:
        db.session.add(new_report)
        client_call.status = 'completed' # 상담 완료 처리
        db.session.commit()
        return jsonify({'message': 'Report saved successfully', 'report_id': new_report.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to save report', 'error': str(e)}), 500


# --- 상담사 마이페이지 - 상담 완료 리스트 및 소견서 조회 라우트 (구현 필요) ---
@counselor_bp.route('/myreports', methods=['GET'])
# @jwt_required()
def get_my_reports():
    # counselor_id = get_jwt_identity()
    # 임시
    counselor_id = request.args.get('counselor_id', type=int)
    if not counselor_id:
        return jsonify({'message': 'Counselor ID required'}), 400

    # 검색 기능 추가 (이름 또는 전화번호)
    search_by = request.args.get('search_by') # 'name' or 'phone'
    search_term = request.args.get('search_term')

    query = ConsultationReport.query.filter_by(counselor_id=counselor_id)

    # 여기에 검색 로직 추가
    # if search_term and search_by == 'name':
    #     query = query.filter(ConsultationReport.client_name.ilike(f'%{search_term}%'))
    # elif search_term and search_by == 'phone':
    #     # ClientCall 테이블과 조인하여 전화번호 검색 필요
    #     query = query.join(ClientCall).filter(ClientCall.phone_number.ilike(f'%{search_term}%'))


    reports = query.order_by(ConsultationReport.created_at.desc()).all()
    reports_data = [{
        'report_id': report.id,
        'client_call_id': report.client_call_id,
        'client_name': report.client_name,
        'created_at': report.created_at.isoformat(),
        # 'client_phone_number': ClientCall.query.get(report.client_call_id).phone_number # 필요시 추가
    } for report in reports]
    return jsonify(reports_data), 200

@counselor_bp.route('/report/<int:report_id>', methods=['GET'])
# @jwt_required()
def get_report_detail(report_id):
    # counselor_id = get_jwt_identity()
    # 임시
    # counselor_id_param = request.args.get('counselor_id', type=int) # 권한 확인용

    report = ConsultationReport.query.get_or_404(report_id)
    # if report.counselor_id != counselor_id_param: # 권한 확인
    #     return jsonify({'message': 'Unauthorized'}), 403

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