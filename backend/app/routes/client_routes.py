# backend/app/routes/client_routes.py
from flask import Blueprint, request, jsonify
import os # 파일 저장을 위해
import random # 임시 위험도 할당을 위해
from werkzeug.utils import secure_filename # 안전한 파일명 처리를 위해
from .. import db
from ..models import ClientCall, User
from ..config import Config # 파일 저장 경로 등을 위해 Config 임포트 (선택 사항)

client_bp = Blueprint('client', __name__)

# 파일 업로드 설정 (선택 사항: Config 클래스에서 관리 가능)
UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'} # 허용할 오디오 확장자

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@client_bp.route('/submit', methods=['POST'])
def submit_client_data():
    # 프론트엔드에서 form-data로 음성 파일과 전화번호를 보낸다고 가정
    if 'audio' not in request.files:
        return jsonify({'message': 'No audio file part'}), 400
    audio_file = request.files['audio']
    phone_number = request.form.get('phoneNumber') # 폼 데이터에서 전화번호 추출

    if not phone_number:
        return jsonify({'message': 'Phone number is required'}), 400
    if audio_file.filename == '':
        return jsonify({'message': 'No selected audio file'}), 400

    if audio_file and allowed_file(audio_file.filename):
        filename = secure_filename(audio_file.filename) # 안전한 파일 이름 사용
        # 파일명 중복 방지를 위해 타임스탬프나 UUID 추가 권장
        # 예: import uuid; filename = str(uuid.uuid4()) + "_" + filename
        audio_file_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(audio_file_path)

        # 1. 상담 가능한 상담사 찾기 (가장 대기열이 적은 상담사 - 초기엔 랜덤 또는 첫번째 상담사)
        #    AI 모델이 없으므로 위험도는 랜덤으로 배정
        risk_level = random.choice([1, 2, 3]) # 1:낮음, 2:중간, 3:높음

        # 상담사 배정 로직 (초기 단순화 버전)
        # 'available' 상태인 상담사를 찾아서 배정 (가장 대기열이 적은 순은 나중에 구현)
        available_counselors = User.query.filter_by(status='available').all()
        assigned_counselor = None
        if not available_counselors:
            # 상담 가능한 상담사가 없으면 일단 대기 상태로만 저장하거나, 에러 반환
            # 프론트 요구사항: "상담 대기 중인 상담사가 없다며 제출이 안된다."
            # 임시로 음성 파일만 삭제하고 에러 반환
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'No available counselors at the moment. Please try again later.'}), 503 # Service Unavailable

        # 실제로는 대기열 수 등을 고려해야 함. 여기서는 가장 간단하게 첫번째 상담사에게 배정.
        # 또는 랜덤으로 배정할 수도 있음.
        # assigned_counselor = random.choice(available_counselors) if available_counselors else None
        # 여기서는 가장 대기열이 적은 상담사를 찾는 로직이 필요 (추후 구현)
        # 지금은 일단 첫 번째 상담사로 가정
        assigned_counselor = available_counselors[0]


        new_call = ClientCall(
            phone_number=phone_number,
            audio_file_path=audio_file_path, # DB에는 상대경로나 전체경로 저장
            risk_level=risk_level,
            status='pending', # 또는 'assigned'
            assigned_counselor_id=assigned_counselor.id if assigned_counselor else None
        )
        try:
            db.session.add(new_call)
            db.session.commit()
            return jsonify({
                'message': 'Call data submitted successfully and assigned.',
                'call_id': new_call.id,
                'risk_level': risk_level,
                'assigned_counselor_id': assigned_counselor.id if assigned_counselor else None
            }), 201
        except Exception as e:
            db.session.rollback()
            # 실패 시 저장된 오디오 파일도 삭제하는 것이 좋음
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            return jsonify({'message': 'Failed to submit call data', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'File type not allowed or no file'}), 400