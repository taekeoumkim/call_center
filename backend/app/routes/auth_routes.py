# backend/app/routes/auth_routes.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone, timedelta
from .. import db
from ..models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__)

def log_event(event, data=None):
    """인증 관련 이벤트를 로깅합니다."""
    if data and 'name' in data:
        data['user_name'] = data.pop('name')
    current_app.logger.info(f"[Auth] {event}", extra=data if data else {})

def validate_password(password):
    """비밀번호 유효성 검사"""
    if len(password) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다."
    if not any(c.isalpha() for c in password):
        return False, "비밀번호는 영문자를 포함해야 합니다."
    if not any(c.isdigit() for c in password):
        return False, "비밀번호는 숫자를 포함해야 합니다."
    return True, ""

def validate_username(username):
    """아이디 유효성 검사"""
    if not (4 <= len(username) <= 12):
        return False, "아이디는 4~12자 사이여야 합니다."
    if not username.isalnum():
        return False, "아이디는 영문자와 숫자만 사용할 수 있습니다."
    return True, ""

@auth_bp.route('/register', methods=['POST'])
def signup():
    """회원가입 엔드포인트"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        
        if not all([username, password, name]):
            return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
            
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '이미 사용 중인 아이디입니다.'}), 400
            
        log_event('회원가입 시도', {'username': username, 'user_name': name})
        
        user = User(username=username, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_event('회원가입 성공', {'username': username, 'user_name': name})
        return jsonify({'message': '회원가입이 완료되었습니다.'}), 201
        
    except Exception as e:
        log_event('회원가입 실패', {'error': str(e)})
        return jsonify({'error': '회원가입 중 오류가 발생했습니다.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    log_event('로그인 시도', {'username': username})

    if not username or not password:
        log_event('로그인 실패 - 필수 입력 누락', {'username': username})
        return jsonify({'error': '아이디와 비밀번호를 입력해주세요.'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        log_event('로그인 실패 - 인증 실패', {'username': username})
        return jsonify({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401

    access_token = create_access_token(identity=user.id, fresh=True)
    refresh_token = create_refresh_token(identity=user.id)
    user.status = 'available'

    try:
        db.session.commit()
        log_event('로그인 성공', {'username': username, 'user_id': user.id})
        return jsonify({
            'message': '로그인 성공',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user.id,
            'name': user.name,
            'username': user.username
        }), 200
    except Exception as e:
        db.session.rollback()
        log_event('로그인 실패 - 상태 업데이트 오류', {'username': username, 'error': str(e)})
        return jsonify({'error': '로그인은 성공했으나 사용자 상태 업데이트에 실패했습니다.'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)
def logout():
    token = get_jwt()
    jti = token["jti"]
    token_type = token["type"]
    current_user_id = get_jwt_identity()

    log_event('로그아웃 시도', {'user_id': current_user_id, 'token_type': token_type})

    existing_token = TokenBlocklist.query.filter_by(jti=jti).one_or_none()
    if existing_token:
        log_event('로그아웃 실패 - 이미 만료된 토큰', {'user_id': current_user_id, 'token_type': token_type})
        return jsonify({"message": "이미 만료된 토큰입니다."}), 200

    db_token = TokenBlocklist(jti=jti, created_at=datetime.now(timezone.utc))

    try:
        db.session.add(db_token)
        user = User.query.get(current_user_id)
        if user:
            user.status = 'offline'
        db.session.commit()
        log_event('로그아웃 성공', {'user_id': current_user_id, 'token_type': token_type})
        return jsonify({"message": "로그아웃되었습니다."}), 200
    except Exception as e:
        db.session.rollback()
        log_event('로그아웃 실패 - DB 오류', {'user_id': current_user_id, 'error': str(e)})
        return jsonify({"error": "로그아웃 중 오류가 발생했습니다."}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    current_user_id = get_jwt_identity()
    log_event('토큰 갱신 시도', {'user_id': current_user_id})
    
    try:
        new_access_token = create_access_token(identity=current_user_id, fresh=False)
        log_event('토큰 갱신 성공', {'user_id': current_user_id})
        return jsonify(access_token=new_access_token), 200
    except Exception as e:
        log_event('토큰 갱신 실패', {'user_id': current_user_id, 'error': str(e)})
        return jsonify({"error": "토큰 갱신에 실패했습니다."}), 500