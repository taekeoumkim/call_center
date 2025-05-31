# backend/app/routes/auth_routes.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone
from .. import db
from ..models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__)

def log_event(event: str, data: dict = None):
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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')

    log_event('회원가입 시도', {'username': username, 'name': name})

    if not username or not password or not name:
        log_event('회원가입 실패 - 필수 입력 누락', {'username': username, 'name': name})
        return jsonify({'message': '아이디, 비밀번호, 이름은 필수 입력 항목입니다.'}), 400

    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        log_event('회원가입 실패 - 아이디 유효성 검사 실패', {'username': username, 'error': username_error})
        return jsonify({'message': username_error}), 400

    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        log_event('회원가입 실패 - 비밀번호 유효성 검사 실패', {'username': username, 'error': password_error})
        return jsonify({'message': password_error}), 400

    if User.query.filter_by(username=username).first():
        log_event('회원가입 실패 - 아이디 중복', {'username': username})
        return jsonify({'message': '이미 사용 중인 아이디입니다.'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password, name=name, status='offline')

    try:
        db.session.add(new_user)
        db.session.commit()
        log_event('회원가입 성공', {'username': username, 'name': name})
        return jsonify({'message': '회원가입이 완료되었습니다.'}), 201
    except Exception as e:
        db.session.rollback()
        log_event('회원가입 실패 - DB 오류', {'username': username, 'error': str(e)})
        return jsonify({'message': '회원가입 중 오류가 발생했습니다.', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    log_event('로그인 시도', {'username': username})

    if not username or not password:
        log_event('로그인 실패 - 필수 입력 누락', {'username': username})
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        log_event('로그인 실패 - 인증 실패', {'username': username})
        return jsonify({'message': 'Invalid username or password'}), 401

    access_token = create_access_token(identity=user.id, fresh=True)
    refresh_token = create_refresh_token(identity=user.id)
    user.status = 'available'

    try:
        db.session.commit()
        log_event('로그인 성공', {'username': username, 'user_id': user.id})
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user.id,
            'name': user.name,
            'username': user.username
        }), 200
    except Exception as e:
        db.session.rollback()
        log_event('로그인 실패 - 상태 업데이트 오류', {'username': username, 'error': str(e)})
        return jsonify({'message': 'Login successful, but failed to update user status', 'error': str(e)}), 500

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
        return jsonify({"message": f"Token already revoked ({token_type} token)"}), 200

    db_token = TokenBlocklist(jti=jti, created_at=datetime.now(timezone.utc))

    try:
        db.session.add(db_token)
        user = User.query.get(current_user_id)
        if user:
            user.status = 'offline'
        db.session.commit()
        log_event('로그아웃 성공', {'user_id': current_user_id, 'token_type': token_type})
        return jsonify({"message": f"Successfully logged out. {token_type.capitalize()} token revoked."}), 200
    except Exception as e:
        db.session.rollback()
        log_event('로그아웃 실패 - DB 오류', {'user_id': current_user_id, 'error': str(e)})
        return jsonify({"message": "Failed to logout", "error": str(e)}), 500

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
        return jsonify({"message": "Failed to refresh token", "error": str(e)}), 500