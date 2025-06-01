from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from io import BytesIO
import logging
from ..services.file_service import FileService
from ..models import User
from .. import db

logger = logging.getLogger(__name__)
file_bp = Blueprint('files', __name__)
file_service = FileService()

@file_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """파일 업로드 엔드포인트"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '선택된 파일이 없습니다.'}), 400

        # 파일 타입 확인
        file_type = request.form.get('file_type')
        if not file_type or file_type not in ['audio', 'report']:
            return jsonify({'error': '유효하지 않은 파일 타입입니다.'}), 400

        # 현재 사용자 조회
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        # 파일 저장
        file_data = file.read()
        encrypted_file = file_service.save_file(file_data, file_type, user)
        db.session.commit()

        return jsonify({
            'message': '파일이 성공적으로 업로드되었습니다.',
            'file_id': encrypted_file.id
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"파일 업로드 실패: {e}")
        return jsonify({'error': str(e)}), 500

@file_bp.route('/download/<int:file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """파일 다운로드 엔드포인트"""
    try:
        # 현재 사용자 조회
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        # 파일 조회 및 복호화
        file_data, file_type = file_service.get_file(file_id, user)

        # 파일 스트림 생성
        file_stream = BytesIO(file_data)
        file_stream.seek(0)

        return send_file(
            file_stream,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=f'file_{file_id}.{file_type}'
        )

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"파일 다운로드 실패: {e}")
        return jsonify({'error': str(e)}), 500

@file_bp.route('/permissions/<int:file_id>', methods=['POST'])
@jwt_required()
def grant_permission(file_id):
    """파일 접근 권한 부여 엔드포인트"""
    try:
        data = request.get_json()
        if not data or 'target_user_id' not in data:
            return jsonify({'error': '대상 사용자 ID가 필요합니다.'}), 400

        # 현재 사용자와 대상 사용자 조회
        current_user_id = get_jwt_identity()
        creator = User.query.get_or_404(current_user_id)
        target_user = User.query.get_or_404(data['target_user_id'])

        # 권한 부여
        file_service.grant_permission(file_id, creator, target_user)
        db.session.commit()

        return jsonify({
            'message': f'사용자 {target_user.id}에게 파일 {file_id}에 대한 접근 권한이 부여되었습니다.'
        }), 200

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        logger.error(f"권한 부여 실패: {e}")
        return jsonify({'error': str(e)}), 500

@file_bp.route('/permissions/<int:file_id>', methods=['DELETE'])
@jwt_required()
def revoke_permission(file_id):
    """파일 접근 권한 취소 엔드포인트"""
    try:
        data = request.get_json()
        if not data or 'target_user_id' not in data:
            return jsonify({'error': '대상 사용자 ID가 필요합니다.'}), 400

        # 현재 사용자와 대상 사용자 조회
        current_user_id = get_jwt_identity()
        creator = User.query.get_or_404(current_user_id)
        target_user = User.query.get_or_404(data['target_user_id'])

        # 권한 취소
        file_service.revoke_permission(file_id, creator, target_user)
        db.session.commit()

        return jsonify({
            'message': f'사용자 {target_user.id}의 파일 {file_id}에 대한 접근 권한이 취소되었습니다.'
        }), 200

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        logger.error(f"권한 취소 실패: {e}")
        return jsonify({'error': str(e)}), 500

@file_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """파일 삭제 엔드포인트"""
    try:
        # 현재 사용자 조회
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        # 파일 삭제
        file_service.delete_file(file_id, user)
        db.session.commit()

        return jsonify({
            'message': f'파일 {file_id}가 성공적으로 삭제되었습니다.'
        }), 200

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        logger.error(f"파일 삭제 실패: {e}")
        return jsonify({'error': str(e)}), 500 