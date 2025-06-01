# backend/app/models.py
from . import db # app/__init__.py 에서 생성된 db 객체를 가져옴
from datetime import datetime, timezone
import logging
from .utils.hybrid_encryption import EncryptionError
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

class User(db.Model): # 예시 모델, 실제 모델명으로 대체
    __tablename__ = 'users' # 테이블명 명시 권장
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False) # 해시된 비밀번호 저장
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='offline', nullable=False) # 'offline', 'available', 'busy'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        """비밀번호를 해시하여 저장합니다."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """비밀번호가 일치하는지 확인합니다."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class ClientCall(db.Model):
    __tablename__ = 'client_calls'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    audio_file_path = db.Column(db.String(255))
    transcribed_text = db.Column(db.Text) # Whisper로 인식된 텍스트
    risk_level = db.Column(db.Integer, default=0) # 0: unassigned, 1: low, 2: medium, 3: high
    status = db.Column(db.String(20), default='available_for_assignment', nullable=False) # 'available_for_assignment', 'assigned', 'completed'
    assigned_counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    received_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ClientCall {self.id} - {self.phone_number}>'

class ConsultationReport(db.Model):
    __tablename__ = 'consultation_reports'
    id = db.Column(db.Integer, primary_key=True)
    client_call_id = db.Column(db.Integer, db.ForeignKey('client_calls.id'), nullable=False, unique=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 암호화된 필드들
    encrypted_client_name = db.Column(db.LargeBinary)
    encrypted_client_age = db.Column(db.LargeBinary)
    encrypted_memo_text = db.Column(db.LargeBinary)
    encrypted_transcribed_text = db.Column(db.LargeBinary)
    
    # DEK 관련 필드
    encrypted_dek_trad = db.Column(db.LargeBinary)
    pqc_kem_ciphertext = db.Column(db.LargeBinary)
    pqc_secret_key = db.Column(db.LargeBinary)
    nonce_for_dek_encryption = db.Column(db.LargeBinary)
    encrypted_dek_by_pqc_shared_secret = db.Column(db.LargeBinary)
    
    # 기존 필드들
    client_gender = db.Column(db.String(10))
    risk_level_recorded = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 복호화된 필드들을 위한 속성
    client_name = None
    client_age = None
    memo_text = None
    transcribed_text = None

    # 관계 설정
    authoring_counselor = db.relationship('User', backref=db.backref('consultation_reports', lazy=True), foreign_keys=[counselor_id])
    originating_call = db.relationship('ClientCall', backref=db.backref('consultation_report', uselist=False, lazy=True), foreign_keys=[client_call_id])

    def __repr__(self):
        return f'<ConsultationReport {self.id} for ClientCall {self.client_call_id}>'
    
    def encrypt_fields(self, hybrid_encryption):
        """필드를 암호화합니다."""
        try:
            # DEK 생성 및 저장
            dek = hybrid_encryption._generate_dek()
            
            # DEK를 두 가지 방식으로 암호화
            encrypted_dek_trad = hybrid_encryption._encrypt_dek_trad(dek)
            pqc_kem_ciphertext, encrypted_dek_pqc_package, pqc_secret_key = hybrid_encryption._encrypt_dek_pqc(dek)
            
            # nonce와 암호문 분리
            nonce_for_dek_encryption = encrypted_dek_pqc_package[:12]
            encrypted_dek_by_pqc_shared_secret = encrypted_dek_pqc_package[12:]
            
            # DEK 관련 필드 저장
            self.encrypted_dek_trad = encrypted_dek_trad
            self.pqc_kem_ciphertext = pqc_kem_ciphertext
            self.pqc_secret_key = pqc_secret_key
            self.nonce_for_dek_encryption = nonce_for_dek_encryption
            self.encrypted_dek_by_pqc_shared_secret = encrypted_dek_by_pqc_shared_secret
            
            # DEK 관련 필드가 제대로 저장되었는지 확인
            if not all([self.encrypted_dek_trad, self.pqc_kem_ciphertext, self.pqc_secret_key, 
                       self.nonce_for_dek_encryption, self.encrypted_dek_by_pqc_shared_secret]):
                raise EncryptionError("DEK 관련 필드 저장 실패")
            
            # 필드 암호화
            if hasattr(self, 'client_name') and self.client_name:
                nonce, ciphertext = hybrid_encryption._encrypt_file_with_dek(self.client_name.encode(), dek)
                self.encrypted_client_name = nonce + ciphertext
            if hasattr(self, 'client_age') and self.client_age:
                nonce, ciphertext = hybrid_encryption._encrypt_file_with_dek(str(self.client_age).encode(), dek)
                self.encrypted_client_age = nonce + ciphertext
            if hasattr(self, 'memo_text') and self.memo_text:
                nonce, ciphertext = hybrid_encryption._encrypt_file_with_dek(self.memo_text.encode(), dek)
                self.encrypted_memo_text = nonce + ciphertext
            if hasattr(self, 'transcribed_text') and self.transcribed_text:
                nonce, ciphertext = hybrid_encryption._encrypt_file_with_dek(self.transcribed_text.encode(), dek)
                self.encrypted_transcribed_text = nonce + ciphertext
                
        except Exception as e:
            logger.error(f"필드 암호화 실패: {e}")
            raise EncryptionError(f"필드 암호화 실패: {e}")

    def decrypt_fields(self, hybrid_encryption):
        """필드들을 복호화합니다."""
        try:
            # DEK 관련 필드 확인
            if not all([self.encrypted_dek_trad, self.pqc_kem_ciphertext, self.pqc_secret_key, 
                       self.nonce_for_dek_encryption, self.encrypted_dek_by_pqc_shared_secret]):
                logger.error("DEK 관련 필드가 누락되었습니다.")
                return

            # DEK 복호화 시도
            try:
                # RSA로 DEK 복호화 시도
                dek = hybrid_encryption._decrypt_dek_trad(self.encrypted_dek_trad)
                logger.debug("RSA DEK 복호화 성공")
            except Exception as e:
                logger.error(f"RSA DEK 복호화 실패: {e}")
                try:
                    # PQC로 DEK 복호화 시도
                    encrypted_dek_package = self.nonce_for_dek_encryption + self.encrypted_dek_by_pqc_shared_secret
                    dek = hybrid_encryption._decrypt_dek_pqc(
                        self.pqc_kem_ciphertext,
                        encrypted_dek_package,
                        self.pqc_secret_key
                    )
                    logger.debug("PQC DEK 복호화 성공")
                except Exception as e:
                    logger.error(f"PQC DEK 복호화 실패: {e}")
                    raise EncryptionError("모든 DEK 복호화 방식이 실패했습니다.")
            
            # 필드 복호화 시도
            fields_to_decrypt = [
                ('client_name', self.encrypted_client_name),
                ('client_age', self.encrypted_client_age),
                ('memo_text', self.encrypted_memo_text),
                ('transcribed_text', self.encrypted_transcribed_text)
            ]
            
            for field_name, encrypted_value in fields_to_decrypt:
                if not encrypted_value:
                    logger.debug(f"{field_name} 필드가 비어있습니다.")
                    continue
                    
                try:
                    # nonce와 암호문 분리
                    nonce = encrypted_value[:12]
                    ciphertext = encrypted_value[12:]
                    
                    # AES-GCM으로 복호화
                    decrypted_bytes = hybrid_encryption._decrypt_file_with_dek(nonce, ciphertext, dek)
                    
                    if field_name == 'client_age':
                        setattr(self, field_name, int(decrypted_bytes.decode()))
                    else:
                        setattr(self, field_name, decrypted_bytes.decode())
                    logger.debug(f"{field_name} 복호화 성공")
                except Exception as e:
                    logger.error(f"{field_name} 복호화 실패: {str(e)}")
                    setattr(self, field_name, None)
                
        except Exception as e:
            logger.error(f"필드 복호화 중 예외 발생: {str(e)}")
            # 개별 필드 복호화 실패는 전체 실패로 처리하지 않음
            pass

class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True) # JWT ID
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"

class EncryptedFile(db.Model):
    """암호화된 파일 메타데이터"""
    __tablename__ = 'encrypted_files'

    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.String(10), nullable=False)  # 'audio' 또는 'report'
    file_storage_path = db.Column(db.String(255), unique=True, nullable=False)
    nonce_for_file = db.Column(db.LargeBinary, nullable=False)
    encrypted_dek_trad = db.Column(db.LargeBinary, nullable=False)
    pqc_kem_ciphertext = db.Column(db.LargeBinary, nullable=False)
    nonce_for_dek_encryption = db.Column(db.LargeBinary, nullable=False)
    encrypted_dek_by_pqc_shared_secret = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 관계 설정
    creator = db.relationship('User', backref=db.backref('encrypted_files', lazy=True))
    permissions = db.relationship('FilePermission', backref='file', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EncryptedFile {self.id}: {self.file_type}>'

class FilePermission(db.Model):
    """파일 접근 권한"""
    __tablename__ = 'file_permissions'

    file_id = db.Column(db.Integer, db.ForeignKey('encrypted_files.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    granted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 관계 설정
    user = db.relationship('User', backref=db.backref('file_permissions', lazy=True))

    def __repr__(self):
        return f'<FilePermission file_id={self.file_id} user_id={self.user_id}>' 