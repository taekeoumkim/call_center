# backend/app/routes/client_routes.py
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc, asc
from .. import db
from ..models import ClientCall, User, ConsultationReport
from ..services import ai_service
from ..config import Config
from ..utils.hybrid_encryption import HybridEncryption

client_bp = Blueprint('client', __name__)

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'webm'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_event(event: str, data: dict = None):
    if data and 'name' in data:
        data = {**data, 'user_name': data.pop('name')}
    current_app.logger.info(f"[Client] {event}", extra=data if data else {})

@client_bp.route('/<int:client_call_id>', methods=['GET'])
@jwt_required()
def get_client_detail(client_call_id):
    log_event('상세 정보 조회 시도', {'client_call_id': client_call_id})
    client_call = ClientCall.query.get(client_call_id)

    if not client_call:
        log_event('상세 정보 조회 실패 - 찾을 수 없음', {'client_call_id': client_call_id})
        return jsonify({"message": "Client call not found"}), 404

    # 프론트엔드 Client 인터페이스에 맞게 데이터 구성
    # interface Client {
    #   id: number;
    #   phone: string;
    #   risk: 0 | 1 | 2;
    # }
    client_data = {
        "id": client_call.id,
        "phone": client_call.phone_number, # ClientCall.phone_number -> phone
        "risk": client_call.risk_level,    # ClientCall.risk_level -> risk
        "transcribed_text": client_call.transcribed_text  # 음성 인식 텍스트 추가
        # 필요에 따라 다른 ClientCall 필드도 추가 가능
        # "status": client_call.status,
        # "received_at": client_call.received_at.isoformat() if client_call.received_at else None,
    }

    log_event('상세 정보 조회 성공', {'client_call_id': client_call_id})
    return jsonify(client_data), 200

@client_bp.route('/queue', methods=['GET'])
@jwt_required()
def get_waiting_queue():
    try:
        log_event('대기열 조회 시도')
        waiting_calls = db.session.query(ClientCall)\
                                  .filter(ClientCall.status.in_(['pending', 'available_for_assignment']))\
                                  .order_by(db.desc(ClientCall.risk_level), db.asc(ClientCall.received_at))\
                                  .all()

        client_list_for_frontend = []
        if waiting_calls:
            for call in waiting_calls:
                client_list_for_frontend.append({
                    'id': call.id,
                    'phone': call.phone_number,
                    'risk': call.risk_level, # 위험도 값 그대로 사용 (0, 1, 2)
                })
            log_event('대기열 조회 성공', {'count': len(client_list_for_frontend)})
        else:
            log_event('대기열 조회 성공 - 대기 중인 통화 없음')
        
        return jsonify(clients=client_list_for_frontend), 200

    except Exception as e:
        log_event('대기열 조회 실패', {'error': str(e)})
        return jsonify({"message": "Failed to fetch waiting queue", "error": str(e)}), 500
    
@client_bp.route('/queue/reset', methods=['DELETE'])
@jwt_required()
def reset_client_queue():
    try:
        log_event('대기열 초기화 시도')
        calls_to_reset = ClientCall.query.filter(ClientCall.status.in_(['pending', 'available_for_assignment'])).all()
        num_reset = len(calls_to_reset)
        
        for call in calls_to_reset:
            call.status = 'cancelled_by_reset'
        
        if num_reset > 0:
            db.session.commit()
            log_event('대기열 초기화 성공', {'reset_count': num_reset})
        else:
            log_event('대기열 초기화 성공 - 초기화할 통화 없음')

        return jsonify({'message': f'Client queue reset successfully. {num_reset} calls affected.'}), 200

    except Exception as e:
        db.session.rollback()
        log_event('대기열 초기화 실패', {'error': str(e)})
        return jsonify({"message": "Failed to reset client queue", "error": str(e)}), 500
    
@client_bp.route('/queue/delete', methods=['POST'])
@jwt_required()
def delete_client_from_queue():
    data = request.get_json()
    client_id_to_delete = data.get('client_id')

    if client_id_to_delete is None:
        log_event('대기열에서 삭제 실패 - client_id 누락')
        return jsonify({"message": "client_id is required in the request body"}), 400

    try:
        client_call_id = int(client_id_to_delete)
    except ValueError:
        log_event('대기열에서 삭제 실패 - 잘못된 client_id 형식', {'client_id': client_id_to_delete})
        return jsonify({"message": "client_id must be an integer"}), 400

    call_to_modify = ClientCall.query.get(client_call_id)

    if not call_to_modify:
        log_event('대기열에서 삭제 실패 - 찾을 수 없음', {'client_call_id': client_call_id})
        return jsonify({"message": f"Client call with ID {client_call_id} not found."}), 404

    log_event('대기열에서 삭제 시도', {'client_call_id': client_call_id, 'current_status': call_to_modify.status})

    if call_to_modify.status == 'completed':
        log_event('대기열에서 삭제 성공 - 이미 완료됨', {'client_call_id': client_call_id})
        return jsonify({"message": f"Client call {client_call_id} is already completed. No further action needed for queue removal."}), 200
    
    if call_to_modify.status in ['pending', 'available_for_assignment', 'assigned']:
        call_to_modify.status = 'completed_manual_dequeue'

    try:
        db.session.commit()
        log_event('대기열에서 삭제 성공', {'client_call_id': client_call_id})
        return jsonify({"message": f"Client call {client_call_id} successfully processed for queue removal."}), 200
    except Exception as e:
        db.session.rollback()
        log_event('대기열에서 삭제 실패', {'client_call_id': client_call_id, 'error': str(e)})
        return jsonify({"message": "Failed to process client call for queue removal", "error": str(e)}), 500

@client_bp.route('/submit', methods=['POST'])
def submit_client_data():
    if 'audio' not in request.files:
        log_event('통화 제출 실패 - 오디오 파일 누락')
        return jsonify({'message': 'No audio file part'}), 400
    
    audio_file = request.files['audio']
    phone_number = request.form.get('phoneNumber')

    if not phone_number:
        log_event('통화 제출 실패 - 전화번호 누락')
        return jsonify({'message': 'Phone number is required'}), 400
    if audio_file.filename == '':
        log_event('통화 제출 실패 - 파일명 누락')
        return jsonify({'message': 'No selected audio file'}), 400

    if audio_file and allowed_file(audio_file.filename):
        try:
            # 파일 데이터 읽기
            file_data = audio_file.read()
            
            # 하이브리드 암호화 적용
            hybrid_encryption = HybridEncryption()
            nonce_for_file, encrypted_file_content, encrypted_dek_trad, pqc_kem_ciphertext, encrypted_dek_by_pqc_shared_secret, pqc_secret_key = hybrid_encryption.encrypt_file_hybrid(file_data)
            
            # 암호화된 데이터를 하나의 파일로 저장
            original_filename = secure_filename(audio_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + original_filename
            audio_file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            with open(audio_file_path, 'wb') as f:
                # 암호화된 데이터를 순서대로 저장
                f.write(nonce_for_file)  # 12 bytes
                f.write(encrypted_file_content)  # variable
                f.write(encrypted_dek_trad)  # 384 bytes for RSA-3072
                f.write(pqc_kem_ciphertext)  # variable
                f.write(encrypted_dek_by_pqc_shared_secret)  # variable
                f.write(pqc_secret_key)  # PQC secret key 추가
            
            log_event('오디오 파일 암호화 및 저장 성공', {
                'file_path': audio_file_path,
                'nonce_size': len(nonce_for_file),
                'content_size': len(encrypted_file_content),
                'dek_trad_size': len(encrypted_dek_trad),
                'kem_ciphertext_size': len(pqc_kem_ciphertext),
                'dek_pqc_size': len(encrypted_dek_by_pqc_shared_secret),
                'pqc_secret_key_size': len(pqc_secret_key)
            })

            try:
                # 음성 인식 및 위험도 분석을 위해 임시로 복호화
                decrypted_data = hybrid_encryption.decrypt_file_hybrid(
                    nonce_for_file, encrypted_file_content,
                    encrypted_dek_trad, pqc_kem_ciphertext,
                    encrypted_dek_by_pqc_shared_secret, pqc_secret_key
                )
                
                # 임시 파일로 저장하여 처리
                temp_file_path = os.path.join(UPLOAD_FOLDER, f"temp_{unique_filename}")
                with open(temp_file_path, 'wb') as f:
                    f.write(decrypted_data)
                
                transcribed_text = ai_service.speech_to_text(temp_file_path)
                risk_level = ai_service.predict_suicide_risk(transcribed_text) if transcribed_text else 0
                
                # 임시 파일 삭제
                os.remove(temp_file_path)

                if risk_level is None:
                    log_event('AI 위험도 분석 실패', {'file_path': audio_file_path})
                    risk_level = 0
                else:
                    log_event('AI 위험도 분석 성공', {'file_path': audio_file_path, 'risk_level': risk_level})

            except Exception as e:
                log_event('파일 복호화 실패', {'error': str(e), 'file_path': audio_file_path})
                # 복호화 실패 시에도 기본값으로 진행
                transcribed_text = None
                risk_level = 0

            # 단일 대기열 방식으로 변경
            new_call = ClientCall(
                phone_number=phone_number,
                audio_file_path=audio_file_path,
                transcribed_text=transcribed_text,
                risk_level=risk_level,
                status='pending',  # 단순히 pending 상태로 설정
                assigned_counselor_id=None  # 상담사 배정은 나중에
            )
            try:
                db.session.add(new_call)
                db.session.commit()
                log_event('통화 제출 성공', {'call_id': new_call.id, 'risk_level': risk_level})
                return jsonify({
                    'message': 'Call data submitted successfully.',
                    'call_id': new_call.id,
                    'risk_level': risk_level
                }), 201
            except Exception as e:
                db.session.rollback()
                log_event('통화 제출 실패', {'call_id': new_call.id, 'error': str(e)})
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                return jsonify({'message': 'Failed to submit call data', 'error': str(e)}), 500
        except Exception as e:
            log_event('파일 처리 중 오류 발생', {'error': str(e)})
            return jsonify({'message': 'Error processing file', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'File type not allowed or no file'}), 400

@client_bp.route('/<int:client_call_id>/previous-reports', methods=['GET'])
@jwt_required()
def get_previous_reports(client_call_id):
    """
    특정 ClientCall과 같은 전화번호를 가진 이전 소견서들을 반환합니다.
    """
    client_call = ClientCall.query.get(client_call_id)
    if not client_call:
        return jsonify({"message": "Client call not found"}), 404

    # 같은 전화번호를 가진 다른 ClientCall들을 찾습니다
    previous_calls = ClientCall.query.filter(
        ClientCall.phone_number == client_call.phone_number,
        ClientCall.id != client_call.id  # 현재 통화는 제외
    ).all()

    previous_reports = []
    for call in previous_calls:
        report = ConsultationReport.query.filter_by(client_call_id=call.id).first()
        if report:
            previous_reports.append({
                'id': report.id,
                'name': report.client_name,
                'age': report.client_age,
                'gender': report.client_gender,
                'phone': call.phone_number,
                'risk': report.risk_level_recorded,
                'memo': report.memo_text,
                'transcribed_text': report.transcribed_text,
                'created_at': report.created_at.isoformat()
            })

    # 생성일 기준으로 정렬 (최신순)
    previous_reports.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify({
        'reports': previous_reports,
        'latest_report': previous_reports[0] if previous_reports else None
    }), 200

@client_bp.route('/audio/<int:client_call_id>', methods=['GET'])
@jwt_required()
def get_audio_file(client_call_id):
    """암호화된 오디오 파일을 복호화하여 재생"""
    try:
        client_call = ClientCall.query.get(client_call_id)
        if not client_call:
            log_event('오디오 파일 조회 실패 - 통화 찾을 수 없음', {'client_call_id': client_call_id})
            return jsonify({"message": "Client call not found"}), 404

        if not os.path.exists(client_call.audio_file_path):
            log_event('오디오 파일 조회 실패 - 파일 찾을 수 없음', {'client_call_id': client_call_id, 'file_path': client_call.audio_file_path})
            return jsonify({"message": "Audio file not found"}), 404

        # 암호화된 파일 읽기
        with open(client_call.audio_file_path, 'rb') as f:
            encrypted_data = f.read()

        # 암호화된 데이터 파싱
        # 각 부분의 크기를 계산
        nonce_size = 12  # AES-GCM nonce 크기
        rsa_size = 384   # RSA-3072 암호문 크기
        kem_size = 768   # Kyber512의 KEM 암호문 크기
        secret_key_size = 1632  # Kyber512의 secret key 크기
        
        # 각 부분 추출
        nonce_for_file = encrypted_data[:nonce_size]
        remaining_data = encrypted_data[nonce_size:]
        
        # RSA 암호문 추출 (마지막 384바이트)
        encrypted_dek_trad = remaining_data[-rsa_size:]
        remaining_data = remaining_data[:-rsa_size]
        
        # PQC KEM 암호문 추출 (마지막 768바이트)
        pqc_kem_ciphertext = remaining_data[-kem_size:]
        remaining_data = remaining_data[:-kem_size]
        
        # PQC secret key 추출 (마지막 1632바이트)
        pqc_secret_key = remaining_data[-secret_key_size:]
        remaining_data = remaining_data[:-secret_key_size]
        
        # 나머지는 암호화된 파일 내용과 PQC로 암호화된 DEK 패키지
        encrypted_file_content = remaining_data[:-60]  # 마지막 60바이트는 PQC DEK 패키지
        encrypted_dek_by_pqc_shared_secret = remaining_data[-60:]

        log_event('암호화된 파일 파싱 성공', {
            'nonce_size': len(nonce_for_file),
            'content_size': len(encrypted_file_content),
            'dek_trad_size': len(encrypted_dek_trad),
            'kem_ciphertext_size': len(pqc_kem_ciphertext),
            'dek_pqc_size': len(encrypted_dek_by_pqc_shared_secret),
            'pqc_secret_key_size': len(pqc_secret_key),
            'total_size': len(encrypted_data)
        })

        # 하이브리드 복호화
        hybrid_encryption = HybridEncryption()
        decrypted_data = hybrid_encryption.decrypt_file_hybrid(
            nonce_for_file, encrypted_file_content,
            encrypted_dek_trad, pqc_kem_ciphertext,
            encrypted_dek_by_pqc_shared_secret, pqc_secret_key
        )

        # 임시 파일로 저장
        temp_file_path = os.path.join(UPLOAD_FOLDER, f"temp_play_{client_call_id}.webm")
        with open(temp_file_path, 'wb') as f:
            f.write(decrypted_data)

        # 파일 전송
        response = send_file(
            temp_file_path,
            mimetype='audio/webm',
            as_attachment=False
        )

        # 임시 파일 삭제를 위한 콜백 설정
        @response.call_on_close
        def cleanup():
            try:
                os.remove(temp_file_path)
            except Exception as e:
                log_event('임시 파일 삭제 실패', {'error': str(e)})

        return response

    except Exception as e:
        log_event('오디오 파일 재생 실패', {'client_call_id': client_call_id, 'error': str(e)})
        return jsonify({"message": "Failed to play audio file", "error": str(e)}), 500