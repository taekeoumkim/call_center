# backend/app/config.py
import os
from datetime import timedelta
import logging

class Config:
    # basedir를 Config 클래스의 클래스 변수로 정의
    BASEDIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # backend 폴더를 가리킴

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key_here_for_development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'instance', 'app.db') # 여기서도 Config.BASEDIR 대신 BASEDIR 사용 가능 (같은 클래스 내)
                                                                    # 또는 self.BASEDIR (인스턴스 메서드 내에서)
                                                                    # 하지만 URI 설정 시점에는 Config.BASEDIR로 접근
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 파일 업로드 폴더 설정 (선택 사항: 여기서 관리하거나 각 라우트에서 직접 정의)
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'instance', 'uploads')
    
    # JWT 관련 설정
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your_jwt_secret_key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1) # Access Token 만료 시간 (1시간)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30) # Refresh Token 만료 시간 (30일)
    # JWT_TOKEN_LOCATION = ['headers'] # 토큰 위치 (기본값: headers)
    # JWT_HEADER_NAME = 'Authorization' # 헤더 이름 (기본값: Authorization)
    # JWT_HEADER_TYPE = 'Bearer' # 헤더 타입 (기본값: Bearer)

    JWT_VERIFY_SUB = False # 타입 유효성 검사 비활성화 (토큰 검증 시 사용)