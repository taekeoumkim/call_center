# backend/app/__init__.py
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
from .services import ai_service
from . import errors

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # --- 로깅 설정 ---
    if not app.debug and not app.testing:
        # 로그 파일 경로 설정
        log_dir = os.path.join(app.instance_path) # instance 폴더 사용
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = app.config.get('LOG_FILE_PATH', os.path.join(log_dir, 'production.log'))

        # 파일 핸들러 설정 (파일 크기 기반 로테이션)
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=5 # 최대 5개 백업 파일 유지
        )
        # 로그 포맷 설정
        log_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(log_formatter)

        # 핸들러의 로그 레벨 설정
        file_handler.setLevel(app.config.get('LOG_LEVEL', logging.INFO))

        # Flask 앱의 기본 로거 외에 다른 로거들도 이 핸들러를 사용하도록 할 수 있음
        # 여기서는 앱의 기본 로거에 핸들러 추가
        if not app.logger.handlers: # 기본 핸들러가 없는 경우에만 추가 (중복 방지)
             app.logger.addHandler(file_handler)

        app.logger.setLevel(app.config.get('LOG_LEVEL', logging.INFO))
        app.logger.info('Production-like logging initialized.')

    elif app.debug: # 디버그 모드일 때는 콘솔에 더 상세한 로그가 나오도록
        app.logger.setLevel(logging.DEBUG) # 디버그 모드에서는 DEBUG 레벨까지
        app.logger.info('Debug logging initialized.')

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    jwt.init_app(app)

    # --- 전역 에러 핸들러 등록 ---
    # 모든 HTTP 예외를 errors.handle_http_exception 으로 처리
    app.register_error_handler(HTTPException, errors.handle_http_exception)

    # 처리되지 않은 모든 예외 (Python 내장 Exception 포함)를 errors.handle_general_exception 으로 처리
    # HTTPException을 상속하지 않는 예외들이 여기에 해당됨
    app.register_error_handler(Exception, errors.handle_general_exception)

    # --- AI 모델 로드 ---
    # create_app 호출 시 로드하도록 함
    try:
        print("Attempting to load AI models...")
        ai_service.load_models() # <<< AI 모델 로드 함수 호출
        print("AI models loaded (or were already loaded).")
    except Exception as e:
        app.logger.error(f"Failed to load AI models on startup: {e}") # Flask 로거 사용
        # 모델 로드 실패 시 애플리케이션을 중단할지, 아니면 경고만 하고 계속할지 결정 필요


    # 순환참조를 막기위해 db.init_app(db 초기화) 이후에 모델 임포트
    from . import models

    # --- JWT 콜백 함수들 (models 임포트 필요) ---
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
        jti = jwt_payload["jti"]
        token = models.TokenBlocklist.query.filter_by(jti=jti).one_or_none()
        return token is not None # 토큰이 존재하면 True (블랙리스트에 있음)

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
    # --- JWT 콜백 함수들 끝 ---


    with app.app_context():
        db.create_all()
        print("Database tables created (if they didn't exist).")

    # --- 블루프린트 등록 ---
    from .routes.auth_routes import auth_bp
    from .routes.client_routes import client_bp
    from .routes.counselor_routes import counselor_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(counselor_bp, url_prefix='/api/counselor')

    # 애플리케이션 시작 시 로그
    app.logger.info("Flask App Startup complete.")
    if app.debug:
        app.logger.info("Application is running in DEBUG mode.")
    
    return app