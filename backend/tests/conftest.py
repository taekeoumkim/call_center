# backend/tests/conftest.py
import os
import sys
import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app import create_app, db as _db # _db로 alias하여 원래 db와 구분
from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # 테스트 시 인메모리 SQLite 사용
    # 또는 별도의 테스트 DB 파일 경로 지정: 'sqlite:///' + os.path.join(Config.BASEDIR, 'instance', 'test_app.db')
    WTF_CSRF_ENABLED = False # 폼 테스트 시 CSRF 비활성화 (Flask-WTF 사용 시)
    JWT_SECRET_KEY = 'test-jwt-secret-key' # 테스트용 JWT 시크릿 키

@pytest.fixture(scope='session') # 세션 단위로 Flask 애플리케이션 생성
def app():
    """Flask 애플리케이션 인스턴스를 생성하고 반환합니다."""
    _app = create_app(TestConfig) # 테스트 설정을 사용하여 앱 생성

    # 테스트용 애플리케이션 컨텍스트 설정
    ctx = _app.app_context()
    ctx.push()

    yield _app # 테스트 실행 동안 앱 인스턴스 제공

    ctx.pop() # 컨텍스트 제거

@pytest.fixture
def client(app):
    """Flask 테스트 클라이언트를 반환합니다."""
    return app.test_client()

@pytest.fixture(scope='function') # 각 테스트 함수마다 DB 초기화
def db(app):
    """데이터베이스 세션과 테이블을 설정하고 테스트 후 정리합니다."""
    with app.app_context(): # 앱 컨텍스트 내에서 DB 작업 수행
        _db.create_all() # 모든 테이블 생성

    yield _db # 테스트 실행 동안 DB 객체 제공

    # 테스트 후 모든 테이블 삭제 (각 테스트의 독립성 보장)
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def runner(app):
    """Flask CLI 테스트 러너를 반환합니다."""
    return app.test_cli_runner()