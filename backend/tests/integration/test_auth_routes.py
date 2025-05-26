# backend/tests/integration/test_auth_routes.py
import pytest
from app.models import User

def test_signup(client, db): # client와 db fixture 사용
    """사용자 회원가입 API 테스트"""
    response = client.post('/api/auth/signup', json={
        'username': 'newuser',
        'password': 'newpassword',
        'name': 'New User'
    })
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == 'User created successfully'
    assert User.query.filter_by(username='newuser').first() is not None

def test_login(client, db):
    """사용자 로그인 API 테스트"""
    # 테스트용 사용자 먼저 생성
    client.post('/api/auth/signup', json={
        'username': 'loginuser',
        'password': 'loginpassword',
        'name': 'Login User'
    })

    response = client.post('/api/auth/login', json={
        'username': 'loginuser',
        'password': 'loginpassword'
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == 'Login successful'
    assert 'access_token' in json_data
    assert 'refresh_token' in json_data
    assert json_data['username'] == 'loginuser'

def test_login_invalid_credentials(client, db):
    """잘못된 정보로 로그인 시도 시 API 테스트"""
    response = client.post('/api/auth/login', json={
        'username': 'nonexistentuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401 # Unauthorized (또는 설정한 오류 코드)
    json_data = response.get_json()

    assert 'message' in json_data
    assert json_data['message'] == 'Invalid username or password'