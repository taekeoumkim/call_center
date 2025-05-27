# backend/app/__init__.py
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, send_from_directory # send_from_directory 추가
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
from .services import ai_service # services 폴더가 app 폴더 내에 있다고 가정
from . import errors # errors.py (또는 errors 폴더)가 app 폴더 내에 있다고 가정

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# config.py가 app 폴더 내에 있다고 가정
from .config import Config # config.py 임포트

# --- 프론트엔드 빌드 디렉토리 경로 설정 ---
# backend/app/__init__.py 파일 기준
# app 폴더의 부모 디렉토리(backend)의 부모 디렉토리(프로젝트 루트) 아래 frontend/build
APP_DIR = os.path.abspath(os.path.dirname(__file__)) # 현재 app 폴더
BACKEND_DIR = os.path.dirname(APP_DIR) # backend 폴더
PROJECT_ROOT_DIR = os.path.dirname(BACKEND_DIR) # 프로젝트 루트
FRONTEND_BUILD_DIR = os.path.join(PROJECT_ROOT_DIR, 'frontend', 'build')

def create_app(config_class=Config):
    # Flask 앱 인스턴스 생성 시 static_folder를 frontend/build/static으로 지정
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder=os.path.join(FRONTEND_BUILD_DIR, 'static') # React 빌드 static 폴더
               )
    app.config.from_object(config_class)

    # --- 로깅 설정 ---
    if not app.debug and not app.testing:
        log_dir = os.path.join(app.instance_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True) # exist_ok=True 추가
        log_file_path = app.config.get('LOG_FILE_PATH', os.path.join(log_dir, 'production.log'))
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=1024 * 1024 * 10, backupCount=5
        )
        log_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(app.config.get('LOG_LEVEL', logging.INFO))
        if not app.logger.handlers:
             app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))
        app.logger.info('Production-like logging initialized.')
    elif app.debug:
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Debug logging initialized.')

    db.init_app(app)
    migrate.init_app(app, db)
    # CORS 설정은 프론트엔드 개발 서버(localhost:3000)와 통신 시 유용.
    # Flask가 직접 프론트엔드를 서빙할 때는 같은 origin이므로 필수 아님. 그러나 유지해도 무방.
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["http://localhost:3000"]) }})
    jwt.init_app(app)

    app.register_error_handler(HTTPException, errors.handle_http_exception)
    app.register_error_handler(Exception, errors.handle_general_exception)

    try:
        app.logger.info("Attempting to load AI models...") # Flask 로거 사용
        ai_service.load_models()
        app.logger.info("AI models loaded (or were already loaded).")
    except Exception as e:
        app.logger.error(f"Failed to load AI models on startup: {e}")

    # 순환참조를 막기위해 db.init_app(db 초기화) 이후에 모델 임포트
    from . import models # models.py (또는 models 폴더)가 app 폴더 내에 있다고 가정

    # --- JWT 콜백 함수들 (models 임포트 필요) ---
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload["jti"]
        # TokenBlocklist 모델이 models.py 안에 정의되어 있다고 가정
        token = models.TokenBlocklist.query.filter_by(jti=jti).one_or_none()
        return token is not None

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload: dict):
        return jsonify({"message": "The token has been revoked.", "error": "token_revoked"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload: dict):
        return jsonify({"message": "The token has expired.", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({"message": "Signature verification failed.", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return jsonify({"message": "Request does not contain an access token.", "error": "authorization_required"}), 401

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity): # identity는 create_access_token에 전달된 값 (user.id)
        user = models.User.query.get(identity) # models.User 사용
        if user:
            # 프론트엔드 DecodedToken { id: number; name: string; exp: number; } 등 필요한 정보 추가
            return {
                'name': user.name,
                'id': user.id,
                'username': user.username
            }
        return {}

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"] # "sub"는 create_access_token의 identity
        return models.User.query.get(identity) # models.User 사용
    # --- JWT 콜백 함수들 끝 ---

    with app.app_context():
        # db.create_all() # Flask-Migrate를 사용
        app.logger.info("Checked for database tables (db.create_all called).")


    # --- 블루프린트 등록 ---
    # routes 폴더가 app 폴더 내에 있다고 가정
    from .routes.auth_routes import auth_bp
    from .routes.client_routes import client_bp
    from .routes.counselor_routes import counselor_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(counselor_bp, url_prefix='/api/counselor')


    # --- 프론트엔드 앱 제공 라우트 (가장 마지막에 등록하는 것이 좋음) ---
    # API 블루프린트 다음, 앱 반환 전에 위치해야 함.
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react_app(path):
        # 1. static 파일 요청인지 확인 (app.static_folder 에서 처리)

        # 2. path가 FRONTEND_BUILD_DIR 내의 실제 파일/디렉토리를 가리키는지 확인
        if path != "" and os.path.exists(os.path.join(FRONTEND_BUILD_DIR, path)):
            return send_from_directory(FRONTEND_BUILD_DIR, path)
        else:
            # 3. React Router에 의해 처리되어야 하는 모든 다른 경로 (예: /main, /patient/1 등)
            if os.path.exists(os.path.join(FRONTEND_BUILD_DIR, 'index.html')):
                return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')
            else:
                app.logger.error(f"Frontend index.html not found at {os.path.join(FRONTEND_BUILD_DIR, 'index.html')}")
                return jsonify({"error": "React app index.html not found."}), 404
    # --- 프론트엔드 앱 제공 라우트 끝 ---

    app.logger.info("Flask App Startup complete.")
    if app.debug:
        app.logger.info("Application is running in DEBUG mode.")

    return app