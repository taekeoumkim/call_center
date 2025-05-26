# backend/app/errors.py
from flask import jsonify
from werkzeug.exceptions import HTTPException # 일반적인 HTTP 예외 클래스

def handle_http_exception(e):
    """HTTP 예외 발생 시 JSON 응답을 반환합니다."""
    response = e.get_response()
    # 기본 HTTP 예외 메시지를 사용하거나, 커스텀 메시지 구조로 변경
    response.data = jsonify({
        "status": "error",
        "error": {
            "code": e.code, # HTTP 상태 코드
            "name": e.name, # 예: Not Found, Internal Server Error
            "description": e.description,
        }
    }).data
    response.content_type = "application/json"
    return response

def handle_validation_error(e): # 커스텀 Validation Error를 만든다면
    """입력값 유효성 검사 오류 처리 (예시)"""
    response = jsonify({
        "status": "error",
        "error": {
            "code": "VALIDATION_ERROR", # 내부 에러 코드
            "message": "Input validation failed.",
            "details": e.errors # 유효성 검사 라이브러리가 제공하는 오류 상세 정보
        }
    })
    response.status_code = 400 # Bad Request
    return response

def handle_general_exception(e):
    """처리되지 않은 예외 발생 시 (500 Internal Server Error)"""
    # 프로덕션 환경에서는 실제 오류 내용을 반환하지 않는 것이 보안상 좋음
    # 대신 로그를 철저히 남기고, 일반적인 오류 메시지만 반환
    # 개발 환경에서는 디버깅을 위해 상세 내용을 포함할 수 있음
    from flask import current_app # current_app 임포트
    current_app.logger.error(f"Unhandled exception: {e}", exc_info=True) # 로그 남기기

    # is_debug = current_app.config.get("DEBUG", False) # config.py에 DEBUG 설정 추가 가능
    # error_message = str(e) if is_debug else "An unexpected error occurred. Please try again later."

    response = jsonify({
        "status": "error",
        "error": {
            "code": 500,
            "name": "Internal Server Error",
            "description": "An unexpected error occurred on the server."
        }
    })
    response.status_code = 500
    return response