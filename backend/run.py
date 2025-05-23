# backend/run.py
from app import create_app

app = create_app()

# ----------------------------- 실행 엔트리포인트 -----------------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)