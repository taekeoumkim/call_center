# backend/tests/integration/test_counselor_routes.py
import pytest
from app.models import User

def get_auth_headers(client, username='testuser', password='password'):
    """테스트용 인증 토큰을 가져오는 헬퍼 함수"""
    # 테스트 사용자 생성 (이미 있다면 생략 가능, 또는 fixture로 관리)
    client.post('/api/auth/signup', json={'username': username, 'password': password, 'name': 'Test Counselor'})
    login_resp = client.post('/api/auth/login', json={'username': username, 'password': password})
    login_data = login_resp.get_json()

    # 실제 로그인 응답 구조에 맞춰 토큰 추출
    # 예시 1: 토큰이 최상위에 있는 경우
    if login_resp.status_code == 200 and 'access_token' in login_data:
        access_token = login_data['access_token']
        return {'Authorization': f"Bearer {access_token}"}
    # 예시 2: 토큰이 'data' 키 내부에 있는 경우 (이전 표준 응답 형식)
    # elif login_resp.status_code == 200 and 'data' in login_data and 'access_token' in login_data['data']:
    #     access_token = login_data['data']['access_token']
    #     return {'Authorization': f"Bearer {access_token}"}
    else:
        pytest.fail(f"Failed to get auth tokens in get_auth_headers. Login status: {login_resp.status_code}, Response: {login_data}")
        return {}

def test_update_counselor_status_authenticated(client, db):
    """인증된 사용자의 상담사 상태 변경 API 테스트"""
    headers = get_auth_headers(client, username='statususer', password='password123')

    response = client.post('/api/counselor/status', json={'status': 'busy'}, headers=headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == 'Status updated to busy'

    user = User.query.filter_by(username='statususer').first()
    assert user.status == 'busy'

def test_update_counselor_status_unauthenticated(client, db):
    """인증되지 않은 사용자의 상담사 상태 변경 시도 API 테스트"""
    response = client.post('/api/counselor/status', json={'status': 'available'})
    assert response.status_code == 401 # JWT 미인증 시 Flask-JWT-Extended가 반환하는 기본 코드
    # 또는 에러 핸들러에서 정의한 응답 형식 검증