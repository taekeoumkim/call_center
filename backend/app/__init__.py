# backend/app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
# from flask_jwt_extended import JWTManager

from .config import Config

db = SQLAlchemy()
migrate = Migrate()
# jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app) # 기본 CORS 설정. 필요시 옵션 추가 (origins=["http://localhost:3000"] 등)
    # jwt.init_app(app)

    from . import models

    with app.app_context():
        db.create_all()
        print("Database tables created (if they didn't exist).")

    # --- 블루프린트 등록 ---
    from .routes.auth_routes import auth_bp
    from .routes.client_routes import client_bp
    from .routes.counselor_routes import counselor_bp
    # from .routes.main_routes import main_bp # 필요하다면

    app.register_blueprint(auth_bp, url_prefix='/api/auth') # /api/auth/signup, /api/auth/login
    app.register_blueprint(client_bp, url_prefix='/api/client') # /api/client/submit
    app.register_blueprint(counselor_bp, url_prefix='/api/counselor') # /api/counselor/status
    # app.register_blueprint(main_bp) # url_prefix 없이 루트에 등록

    # 기존 테스트 라우트 삭제 또는 main_routes.py로 이동
    # @app.route('/hello_models')
    # ...
    # @app.route('/hello')
    # ...

    return app