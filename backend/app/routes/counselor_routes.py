# backend/app/routes/counselor_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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

# --- 소견서 저장 ---
@counselor_bp.route('/report/save', methods=['POST'])
@jwt_required()
def save_report():
    counselor_id = get_jwt_identity()
    data = request.get_json()
    
    client_call_id = data.get('client_call_id')
    client_name = data.get('client_name')
    client_age = data.get('client_age')
    client_gender = data.get('client_gender')
    memo_text = data.get('memo_text')

    if not all([client_call_id, memo_text]): # 필수 필드 확인
        return jsonify({'message': 'Client Call ID, and Memo are required'}), 400

    client_call = ClientCall.query.get(client_call_id)
    if not client_call:
        return jsonify({'message': 'Client call not found'}), 404
    if client_call.assigned_counselor_id != counselor_id: # 권한 확인 (해당 상담사의 통화인지)
         return jsonify({'message': 'Unauthorized to report on this call. Not assigned to you.'}), 403


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
@jwt_required()
def get_my_reports():
    counselor_id = get_jwt_identity()

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