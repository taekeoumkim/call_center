# backend/app/__init__.py
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    jwt.init_app(app)

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
    
    return app