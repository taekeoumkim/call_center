# backend/app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_jwt_extended import create_access_token, create_refresh_token # JWT 사용 시
from .. import db # app/__init__.py 의 db 객체
from ..models import User # app/models.py 의 User 모델

auth_bp = Blueprint('auth', __name__) # 'auth' 라는 이름의 블루프린트 생성

@auth_bp.route('/signup', methods=['POST'])
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

    # JWT 토큰 생성 (예시)
    # access_token = create_access_token(identity=user.id)
    # refresh_token = create_refresh_token(identity=user.id)
    # return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    # JWT를 사용하지 않는 경우, 세션 기반 로그인 또는 간단한 성공 메시지
    # 여기서는 임시로 성공 메시지만 반환 (실제 프로젝트에서는 JWT 또는 세션 사용)
    user.status = 'available' # 로그인 시 상담 가능 상태로 변경 (예시)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update user status', 'error': str(e)}), 500

    return jsonify({'message': 'Login successful', 'user_id': user.id, 'name': user.name}), 200

# 필요한 경우 로그아웃 라우트 등 추가
@auth_bp.route('/logout', methods=['POST']) # JWT를 사용한다면 토큰 블랙리스트 처리 등이 필요
def logout():
    # data = request.get_json()
    # user_id = data.get('user_id') # 또는 JWT 토큰에서 사용자 식별
    # user = User.query.get(user_id)
    # if user:
    #     user.status = 'offline'
    #     db.session.commit()
    return jsonify({'message': 'Logout successful (implement proper session/token invalidation)'}), 200