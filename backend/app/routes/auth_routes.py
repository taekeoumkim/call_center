# backend/app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone
from .. import db
from ..models import User, TokenBlocklist

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')

    if not username or not password or not name:
        return jsonify({'message': 'Username, password, and name are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password, name=name, status='offline')

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create user', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid username or password'}), 401

    # JWT 토큰 생성
    access_token = create_access_token(identity=user.id, fresh=True) # 로그인 시 fresh 토큰
    refresh_token = create_refresh_token(identity=user.id)
    print(f"--- DEBUG: Generated access_token in login: {access_token}") # <--- 생성된 토큰 출력
    print(f"--- DEBUG: Type of access_token: {type(access_token)}")

    user.status = 'available' # 로그인 시 상담 가능 상태로 변경 (예시)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Login successful, but failed to update user status', 'error': str(e)}), 500

    return jsonify({'message': 'Login successful',
                    'access_token': access_token, 'refresh_token': refresh_token,
                    'user_id': user.id, 'name': user.name, 'username': user.username}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required(verify_type=False) # 토큰 검증 비활성화
def logout():
    token = get_jwt() # 현재 요청의 JWT payload 전체를 가져옴
    jti = token["jti"]
    token_type = token["type"] # 'access' or 'refresh'

    # TokenBlocklist에 이미 있는지 확인 (선택 사항, 중복 저장 방지)
    existing_token = TokenBlocklist.query.filter_by(jti=jti).one_or_none()
    if existing_token:
        return jsonify({"message": f"Token already revoked ({token_type} token)"}), 200


    # created_at은 모델에서 default로 설정되지만, 명시적으로 지정할 수도 있음
    # token_expires = datetime.fromtimestamp(token["exp"], tz=timezone.utc) # 토큰의 실제 만료 시간
    db_token = TokenBlocklist(jti=jti, created_at=datetime.now(timezone.utc))

    try:
        db.session.add(db_token)
        db.session.commit()
        # 사용자 상태를 'offline'으로 변경
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user:
            user.status = 'offline'
            db.session.commit()
        return jsonify({"message": f"Successfully logged out. {token_type.capitalize()} token revoked."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to logout", "error": str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # refresh=True 옵션으로 Refresh Token만 허용
def refresh_access_token():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id, fresh=False) # (non-fresh token)
    return jsonify(access_token=new_access_token), 200