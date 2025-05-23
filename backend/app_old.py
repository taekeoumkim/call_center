# ----------------------------- 기본 설정 및 모듈 -----------------------------
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
from werkzeug.utils import secure_filename
from io import BytesIO
import sqlite3
import bcrypt
import jwt
import datetime
import random
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F


# Flask 앱 생성 및 CORS 설정
app = Flask(__name__)
CORS(app, supports_credentials=True)  # 쿠키 포함한 CORS 허용

app.config['SECRET_KEY'] = 'your_secret_key'  # JWT 비밀 키
DB_PATH = 'database.db'  # SQLite DB 파일 경로


#---------------------------- Whisper 모델 -------------------------------
# 모델 로드 코드 및 함수 작성

#--------------------------- 자살 위험도 예측 모델 -----------------------------------------------
tokenizer = AutoTokenizer.from_pretrained("seungb1027/koelectra-suicide-risk")
model = AutoModelForSequenceClassification.from_pretrained("seungb1027/koelectra-suicide-risk")

# CUDA 사용 가능하면 GPU, 아니면 CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

#------------------------------ 위험도 예측 함수-------------------------------------------------
def predict_label(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1)
        label = torch.argmax(probs, dim=-1).item()
    return label  # 0 / 1 / 2
# ----------------------------- DB 연결 함수 -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 결과를 dict처럼 다룰 수 있게 설정
    return conn

# ----------------------------- JWT 토큰 인증 데코레이터 -----------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            bearer = request.headers['Authorization']
            token = bearer.split(" ")[1] if " " in bearer else bearer

        if not token:
            return jsonify({'error': '토큰이 없습니다.'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = data  # 토큰에서 유저 정보 추출
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '토큰이 만료되었습니다.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '유효하지 않은 토큰입니다.'}), 401

        return f(*args, **kwargs)
    return decorated

# ----------------------------- DB 초기화 -----------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 상담사 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS counselors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_active INTEGER DEFAULT 0
        )
    ''')

    # 내담자 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            risk INTEGER NOT NULL CHECK (risk IN (1, 2, 3)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            counselor_id INTEGER
        )
    ''')

    # 내담자-상담사 배정 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS client_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            counselor_id INTEGER NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(counselor_id) REFERENCES counselors(id)
        )
    ''')

    # 소견서 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            counselor_id INTEGER,
            name TEXT,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            risk INTEGER,
            memo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(counselor_id) REFERENCES counselors(id)
        )
    ''')

    conn.commit()
    conn.close()

# 앱 실행 시 DB 초기화 실행
init_db()

# ----------------------------- 상담사 회원가입 -----------------------------
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')

    # 필수 항목 검증
    if not name or not username or not password:
        return jsonify({'error': '모든 항목을 입력해주세요.'}), 400

    # 유효성 검사
    if not (4 <= len(username) <= 12) or not username.isalnum():
        return jsonify({'error': '아이디는 4~12자의 영문 또는 숫자여야 합니다.'}), 400

    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return jsonify({'error': '비밀번호는 8자 이상이며 영문과 숫자를 포함해야 합니다.'}), 400

    # 비밀번호 해시화
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO counselors (name, username, password) VALUES (?, ?, ?)',
                    (name, username, hashed_pw.decode('utf-8')))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': '이미 존재하는 아이디입니다.'}), 409
    finally:
        conn.close()

    return jsonify({'message': '회원가입 성공'}), 201

# ----------------------------- 상담사 로그인 -----------------------------
@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, password FROM counselors WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()

    if not user:
        return jsonify({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401

    user_id, name, hashed_pw = user['id'], user['name'], user['password']

    # 비밀번호 검증
    if not bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
        return jsonify({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401

    # JWT 토큰 발급 (24시간 유효)
    token = jwt.encode({
        'id': user_id,
        'name': name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({'token': token}), 200

# ----------------------------- 상담사 상태 설정 -----------------------------
@app.route('/api/status', methods=['POST'])
@token_required
def update_status():
    data = request.get_json()
    is_active = data.get('is_active')

    if is_active not in [0, 1]:
        return jsonify({'error': 'is_active는 0 또는 1이어야 합니다.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE counselors SET is_active = ? WHERE id = ?', (is_active, request.user['id']))
    conn.commit()
    conn.close()

    return jsonify({'message': '상태가 업데이트되었습니다.'}), 200

# ----------------------------- 상담사 상태 조회 -----------------------------
@app.route('/api/status', methods=['GET'])
@token_required
def get_status():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT is_active FROM counselors WHERE id = ?', (request.user['id'],))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({'error': '상담사를 찾을 수 없습니다.'}), 404

    return jsonify({'is_active': row['is_active']}), 200

# ----------------------------- 오디오 제출 및 내담자 등록/배정 -----------------------------
@app.route('/api/submit', methods=['POST'])
def submit_audio():
    if 'audio' not in request.files or 'phone' not in request.form:
        return jsonify({'error': '오디오 파일과 전화번호가 필요합니다.'}), 400

    audio_file = request.files['audio']
    phone_number = request.form['phone']
    filename = secure_filename(audio_file.filename)
    _ = audio_file.read()  # 오디오 파일 내용은 실제 사용 안 함 (시뮬레이션)

    # 위험도 랜덤 지정 (1~3)
    risk = random.choice([1, 2, 3])

    conn = get_db_connection()
    cur = conn.cursor()

    # 활성 상담사 목록
    cur.execute('SELECT id FROM counselors WHERE is_active = 1')
    active_counselors = cur.fetchall()

    if not active_counselors:
        conn.close()
        return jsonify({'error': 'No available counselors'}), 400

    # 가장 적게 배정된 상담사 선택
    counselor_loads = []
    for counselor in active_counselors:
        cid = counselor['id']
        cur.execute('SELECT COUNT(*) FROM client_assignments WHERE counselor_id = ?', (cid,))
        count = cur.fetchone()[0]
        counselor_loads.append((cid, count))

    counselor_loads.sort(key=lambda x: x[1])
    selected_counselor_id = counselor_loads[0][0]

    # 내담자 등록 및 배정
    cur.execute('INSERT INTO clients (phone, risk, counselor_id) VALUES (?, ?, ?)', (phone_number, risk, selected_counselor_id))
    client_id = cur.lastrowid

    cur.execute('INSERT INTO client_assignments (client_id, counselor_id) VALUES (?, ?)',
                (client_id, selected_counselor_id))

    conn.commit()
    conn.close()

    return jsonify({'message': '내담자가 성공적으로 배정되었습니다.'}), 200

# ----------------------------- 상담사 대기열 조회 -----------------------------
@app.route('/api/queue', methods=['GET'])
@token_required
def get_queue():
    counselor_id = request.user['id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT clients.id, clients.phone, clients.risk
        FROM clients
        JOIN client_assignments ON clients.id = client_assignments.client_id
        WHERE client_assignments.counselor_id = ?
        ORDER BY clients.risk DESC, clients.created_at ASC
    ''', (counselor_id,))
    rows = cur.fetchall()
    conn.close()

    clients = [{'id': row['id'], 'phone': row['phone'], 'risk': row['risk']} for row in rows]
    return jsonify({'clients': clients}), 200

# ----------------------------- 내담자 상세 정보 조회 -----------------------------
@app.route('/api/client/<int:client_id>', methods=['GET'])
@token_required
def get_client_info(client_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, phone, risk FROM clients WHERE id = ?', (client_id,))
    client = cur.fetchone()
    conn.close()

    if client is None:
        return jsonify({'error': '내담자를 찾을 수 없습니다.'}), 404

    return jsonify({
        'id': client['id'],
        'phone': client['phone'],
        'risk': client['risk']
    }), 200

# ----------------------------- 소견서 저장 -----------------------------
@app.route('/api/report', methods=['POST'])
@token_required
def save_report():
    data = request.get_json()
    client_id = data.get('client_id')
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    memo = data.get('memo')
    phone = data.get('phone')
    risk = data.get('risk')

    if not all([client_id, name, age, gender, memo, phone, risk]):
        return jsonify({'error': '모든 항목을 입력해주세요.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO reports (client_id, counselor_id, name, age, gender, phone, risk, memo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (client_id, request.user['id'], name, age, gender, phone, risk, memo))

    conn.commit()
    conn.close()

    return jsonify({'message': '소견서가 저장되었습니다.'}), 201

# ----------------------------- 대기열 내 내담자 삭제 -----------------------------
@app.route('/api/queue/delete', methods=['POST'])
@token_required
def delete_client_from_queue():
    data = request.get_json()
    client_id = data.get('client_id')

    if not client_id:
        return jsonify({'error': 'client_id가 필요합니다.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM client_assignments WHERE client_id = ?', (client_id,))
    cur.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': '내담자가 대기열에서 삭제되었습니다.'}), 200

# ----------------------------- 상담사의 소견서 목록 조회 -----------------------------
@app.route('/api/myreports', methods=['GET'])
@token_required
def get_my_reports():
    counselor_id = request.user['id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, name, age, gender, phone, risk, memo, created_at
        FROM reports
        WHERE counselor_id = ?
        ORDER BY created_at DESC
    ''', (counselor_id,))
    rows = cur.fetchall()
    conn.close()

    reports = [{
        'id': row['id'],
        'name': row['name'],
        'age': row['age'],
        'gender': row['gender'],
        'phone': row['phone'],
        'risk': row['risk'],
        'memo': row['memo'],
        'created_at': row['created_at']
    } for row in rows]

    return jsonify({'reports': reports}), 200

# ----------------------------- 상담사의 전체 대기열 초기화 -----------------------------
@app.route('/api/queue/reset', methods=['DELETE'])
@token_required
def reset_queue():
    counselor_id = request.user['id']

    conn = get_db_connection()
    cur = conn.cursor()

    # 해당 상담사에게 배정된 client_id 목록 조회
    cur.execute('SELECT client_id FROM client_assignments WHERE counselor_id = ?', (counselor_id,))
    client_ids = [row['client_id'] for row in cur.fetchall()]

    if not client_ids:
        conn.close()
        return jsonify({'message': '삭제할 내담자가 없습니다.'}), 200

    # 배정 테이블에서 삭제
    cur.execute('DELETE FROM client_assignments WHERE counselor_id = ?', (counselor_id,))
    
    # clients 테이블에서 삭제
    cur.execute(f'DELETE FROM clients WHERE id IN ({",".join(["?"]*len(client_ids))})', client_ids)

    conn.commit()
    conn.close()

    return jsonify({'message': '대기열이 초기화되었습니다.'}), 200

# ----------------------------- 실행 엔트리포인트 -----------------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)