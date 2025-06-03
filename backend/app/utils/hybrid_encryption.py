import os
import traceback
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import oqs
from typing import Tuple, Optional
import logging
import cryptography.exceptions
import ctypes as ct

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    """암호화 관련 기본 예외"""
    pass

class KeyVerificationError(EncryptionError):
    """DEK 검증 실패 예외"""
    pass

class HybridEncryption:
    # PQC KEM 알고리즘 설정
    PQC_KEM_ALG = "Kyber512"  # 또는 보안 레벨에 따라 "Kyber768" 사용

    def __init__(self):
        # 키 파일 디렉토리 설정
        self.keys_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'keys')
        try:
            os.makedirs(self.keys_dir, exist_ok=True)
            logger.info(f"키 디렉토리 생성/확인 완료: {self.keys_dir}")
        except Exception as e:
            logger.error(f"키 디렉토리 생성 실패: {e}")
            raise EncryptionError(f"키 디렉토리 생성 실패: {e}")
        
        # 시스템 키 로드 또는 생성
        self.trad_private_key, self.trad_public_key = self._load_or_generate_trad_keys()
        self.pqc_public_key, self.pqc_private_key = self._load_or_generate_pqc_keys()

    def _load_or_generate_trad_keys(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """RSA 키 쌍을 로드하거나 생성"""
        private_key_path = os.path.join(self.keys_dir, 'trad_private_key.pem')
        public_key_path = os.path.join(self.keys_dir, 'trad_public_key.pem')
        
        try:
            # 키 파일이 존재하는 경우 로드
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                with open(private_key_path, "rb") as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
                with open(public_key_path, "rb") as f:
                    public_key = serialization.load_pem_public_key(f.read())
                logger.info("RSA 키 쌍을 성공적으로 로드했습니다.")
                return private_key, public_key
        except Exception as e:
            logger.warning(f"RSA 키 로드 실패: {e}. 새로운 키 쌍을 생성합니다.")
        
        # 새로운 RSA 키 쌍 생성
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=3072
            )
            public_key = private_key.public_key()
            
            # 키 저장
            with open(private_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(public_key_path, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            logger.info("새로운 RSA 키 쌍을 생성하고 저장했습니다.")
            return private_key, public_key
            
        except Exception as e:
            logger.error(f"RSA 키 생성/저장 실패: {e}")
            raise EncryptionError(f"RSA 키 생성/저장 실패: {e}")

    def _load_or_generate_pqc_keys(self) -> Tuple[bytes, bytes]:
        """PQC 공개키와 개인키를 로드하거나 생성"""
        public_key_path = os.path.join(self.keys_dir, 'pqc_public_key.bin')
        private_key_path = os.path.join(self.keys_dir, 'pqc_private_key.bin')
        
        try:
            if os.path.exists(public_key_path) and os.path.exists(private_key_path):
                with open(public_key_path, "rb") as f_pub:
                    public_key = f_pub.read()
                with open(private_key_path, "rb") as f_priv:
                    private_key = f_priv.read()
                logger.info("PQC 공개키와 개인키를 성공적으로 로드했습니다.")
                return public_key, private_key # 올바른 튜플 반환
        except Exception as e:
            logger.warning(f"PQC 키 로드 실패: {e}. 새로운 키 쌍을 생성합니다.")
        
        try:
            # 새로운 키쌍 생성
            with oqs.KeyEncapsulation(self.PQC_KEM_ALG) as kem:
                # 키쌍 생성
                public_key = kem.generate_keypair()
                secret_key = kem.export_secret_key()
                
                # 키 저장
                with open(public_key_path, "wb") as f_pub:
                    f_pub.write(public_key)
                with open(private_key_path, "wb") as f_priv:
                    f_priv.write(secret_key)
                
                logger.info("새로운 PQC 공개키와 개인키를 생성하고 저장했습니다.")
                return public_key, secret_key
            
        except Exception as e:
            logger.error(f"PQC 키 생성/저장 실패: {e}")
            raise EncryptionError(f"PQC 키 생성/저장 실패: {e}")

    def _generate_dek(self) -> bytes:
        """DEK 생성"""
        return os.urandom(32)  # AES-256용 32바이트 DEK

    def _encrypt_dek_trad(self, dek: bytes) -> bytes:
        """RSA로 DEK 암호화"""
        try:
            encrypted_dek = self.trad_public_key.encrypt(
                dek,
                rsa_padding.OAEP(
                    mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted_dek
        except Exception as e:
            logger.error(f"RSA DEK 암호화 실패: {e}")
            raise EncryptionError(f"RSA DEK 암호화 실패: {e}")

    def _decrypt_dek_trad(self, encrypted_dek_trad: bytes) -> bytes:
        """RSA로 DEK 복호화"""
        try:
            dek = self.trad_private_key.decrypt(
                encrypted_dek_trad,
                rsa_padding.OAEP(
                    mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return dek
        except Exception as e:
            logger.error(f"RSA DEK 복호화 실패: {e}")
            raise EncryptionError(f"RSA DEK 복호화 실패: {e}")

    def _encrypt_dek_pqc(self, dek: bytes) -> Tuple[bytes, bytes, bytes]:
        """PQC KEM을 사용하여 DEK를 암호화"""
        try:
            # 새로운 KeyEncapsulation 인스턴스 생성
            with oqs.KeyEncapsulation(self.PQC_KEM_ALG) as kem:
                # 키쌍 생성
                public_key = kem.generate_keypair()
                secret_key = kem.export_secret_key()
                
                # 공유 비밀 생성 및 KEM 암호문 생성
                kem_ciphertext, shared_secret = kem.encap_secret(public_key)
                
                # 공유 비밀의 크기와 첫 8바이트 로깅
                logger.info(f"PQC 암호화 - 공유 비밀 크기: {len(shared_secret)}, KEM 암호문 크기: {len(kem_ciphertext)}")
                logger.info(f"PQC 암호화 - 공유 비밀 첫 8바이트: {shared_secret[:8].hex()}")
                
                # AES-GCM으로 DEK 암호화
                nonce = os.urandom(12)
                aes_gcm_for_dek = AESGCM(shared_secret)
                ciphertext = aes_gcm_for_dek.encrypt(nonce, dek, None)
                
                # nonce와 암호문을 하나의 패키지로 결합
                encrypted_dek_package = nonce + ciphertext
                
                logger.info(f"PQC 암호화 - DEK 패키지 크기: {len(encrypted_dek_package)}")
                logger.info(f"PQC 암호화 - nonce 첫 8바이트: {nonce[:8].hex()}")
                
                return kem_ciphertext, encrypted_dek_package, secret_key
                
        except Exception as e:
            error_msg = f"PQC DEK 암호화 실패 ({type(e).__name__}): {str(e)}"
            logger.error(error_msg)
            logger.debug(f"상세 오류:\n{traceback.format_exc()}")
            raise EncryptionError(error_msg)

    def _decrypt_dek_pqc(self, kem_ciphertext: bytes, encrypted_dek_package: bytes, secret_key: bytes) -> bytes:
        """PQC KEM을 사용하여 DEK를 복호화"""
        try:
            # 새로운 KeyEncapsulation 인스턴스 생성
            kem = oqs.KeyEncapsulation(self.PQC_KEM_ALG)
            try:
                # secret_key를 ctypes.create_string_buffer로 변환
                secret_key_buffer = ct.create_string_buffer(secret_key)
                kem.secret_key = secret_key_buffer
                
                # KEM 복호화로 공유 비밀 복구
                shared_secret = kem.decap_secret(kem_ciphertext)
                
                # 공유 비밀의 크기와 첫 8바이트 로깅
                logger.info(f"PQC 복호화 - 공유 비밀 크기: {len(shared_secret)}, KEM 암호문 크기: {len(kem_ciphertext)}")
                logger.info(f"PQC 복호화 - 공유 비밀 첫 8바이트: {shared_secret[:8].hex()}")
                
                # nonce와 암호문 분리
                nonce = encrypted_dek_package[:12]
                ciphertext = encrypted_dek_package[12:]
                
                logger.info(f"PQC 복호화 - nonce 크기: {len(nonce)}, ciphertext 크기: {len(ciphertext)}")
                logger.info(f"PQC 복호화 - nonce 첫 8바이트: {nonce[:8].hex()}")
                
                # 공유 비밀 검증
                if len(shared_secret) != 32:
                    raise ValueError(f"Invalid shared secret length: {len(shared_secret)}")
                
                # AES-GCM으로 DEK 복호화
                aes_gcm_for_dek = AESGCM(shared_secret)
                dek = aes_gcm_for_dek.decrypt(nonce, ciphertext, None)
                
                return dek
                
            finally:
                # 명시적으로 리소스 해제
                kem.free()
            
        except Exception as e:
            error_msg = f"PQC DEK 복호화 실패 ({type(e).__name__}): {str(e)}"
            logger.error(error_msg)
            logger.debug(f"상세 오류:\n{traceback.format_exc()}")
            raise EncryptionError(error_msg)

    def _encrypt_file_with_dek(self, file_data: bytes, dek: bytes) -> Tuple[bytes, bytes]:
        """DEK로 파일 암호화"""
        try:
            aes_gcm_for_file = AESGCM(dek)
            nonce_for_file = os.urandom(12)
            encrypted_file_content = aes_gcm_for_file.encrypt(nonce_for_file, file_data, None)
            return nonce_for_file, encrypted_file_content
            
        except Exception as e:
            logger.error(f"파일 암호화 실패: {e}")
            raise EncryptionError(f"파일 암호화 실패: {e}")

    def _decrypt_file_with_dek(self, nonce_for_file: bytes, encrypted_file_content: bytes, 
                              dek: bytes) -> bytes:
        """DEK로 파일 복호화"""
        try:
            aes_gcm_for_file = AESGCM(dek)
            decrypted_file_data = aes_gcm_for_file.decrypt(nonce_for_file, encrypted_file_content, None)
            return decrypted_file_data
            
        except Exception as e:
            logger.error(f"파일 복호화 실패: {e}")
            raise EncryptionError(f"파일 복호화 실패: {e}")

    def encrypt_file_hybrid(self, file_data: bytes) -> Tuple[bytes, bytes, bytes, bytes, bytes, bytes]:
        """하이브리드 방식으로 파일 암호화"""
        try:
            # DEK 생성
            dek = self._generate_dek()
            
            # DEK를 두 가지 방식으로 암호화
            encrypted_dek_trad = self._encrypt_dek_trad(dek)
            pqc_kem_ciphertext, encrypted_dek_pqc_package, pqc_secret_key = self._encrypt_dek_pqc(dek)
            
            # 파일 암호화
            nonce_for_file, encrypted_file_content = self._encrypt_file_with_dek(file_data, dek)
            
            return (
                nonce_for_file, encrypted_file_content,
                encrypted_dek_trad,
                pqc_kem_ciphertext, encrypted_dek_pqc_package, pqc_secret_key
            )
            
        except Exception as e:
            logger.error(f"하이브리드 파일 암호화 실패: {e}")
            raise EncryptionError(f"하이브리드 파일 암호화 실패: {e}")

    def decrypt_file_hybrid(self, nonce_for_file: bytes, encrypted_file_content: bytes,
                          encrypted_dek_trad: bytes, pqc_kem_ciphertext: bytes,
                          encrypted_dek_pqc_package: bytes, pqc_secret_key: bytes) -> bytes:
        """하이브리드 방식으로 파일 복호화"""
        dek_from_trad = None
        dek_from_pqc = None
        
        # 전통 방식으로 DEK 복호화 시도
        try:
            dek_from_trad = self._decrypt_dek_trad(encrypted_dek_trad)
            logger.info("전통 방식 DEK 복호화 성공")
        except Exception as e:
            logger.warning(f"전통 방식 DEK 복호화 실패: {str(e)}")

        # PQC 방식으로 DEK 복호화 시도
        try:
            logger.info(f"PQC KEM 암호문 크기: {len(pqc_kem_ciphertext)}, 암호화된 DEK 크기: {len(encrypted_dek_pqc_package)}")
            dek_from_pqc = self._decrypt_dek_pqc(pqc_kem_ciphertext, encrypted_dek_pqc_package, pqc_secret_key)
            logger.info("PQC 방식 DEK 복호화 성공")
        except Exception as e:
            logger.warning(f"PQC 방식 DEK 복호화 실패: {str(e)}")

        # DEK 검증 및 선택
        if dek_from_trad and dek_from_pqc:
            if dek_from_trad != dek_from_pqc:
                logger.error("DEK 불일치: 전통 방식과 PQC 방식의 DEK가 다릅니다.")
                raise KeyVerificationError("DEK 불일치: 전통 방식과 PQC 방식의 DEK가 다릅니다.")
            final_dek = dek_from_trad
            logger.info("두 방식 모두 성공적으로 DEK를 복호화했습니다.")
        elif dek_from_trad:
            final_dek = dek_from_trad
            logger.info("전통 방식으로만 DEK를 복호화했습니다.")
        elif dek_from_pqc:
            final_dek = dek_from_pqc
            logger.info("PQC 방식으로만 DEK를 복호화했습니다.")
        else:
            logger.error("모든 DEK 복호화 방식이 실패했습니다.")
            raise EncryptionError("모든 DEK 복호화 방식이 실패했습니다.")

        # 파일 복호화
        try:
            decrypted_file = self._decrypt_file_with_dek(nonce_for_file, encrypted_file_content, final_dek)
            logger.info("파일 복호화 성공")
            return decrypted_file
        except Exception as e:
            logger.error(f"파일 복호화 실패: {str(e)}")
            raise EncryptionError(f"파일 복호화 실패: {str(e)}")

    def encrypt_field(self, field_value: str) -> bytes:
        """문자열 필드를 암호화합니다."""
        try:
            # DEK가 없으면 생성
            if not hasattr(self, 'encrypted_dek_trad') or not self.encrypted_dek_trad:
                # DEK 생성
                dek = self._generate_dek()
                
                # DEK를 RSA로 암호화
                self.encrypted_dek_trad = self._encrypt_dek_trad(dek)
                
                # DEK를 PQC로 암호화
                self.pqc_kem_ciphertext, encrypted_dek_package, self.pqc_secret_key = self._encrypt_dek_pqc(dek)
                
                # nonce와 암호문 분리
                self.nonce_for_dek_encryption = encrypted_dek_package[:12]
                self.encrypted_dek_by_pqc_shared_secret = encrypted_dek_package[12:]
                
                # DEK 저장
                self._current_dek = dek
            else:
                # 기존 DEK 복호화
                self._current_dek = self._decrypt_dek_trad(self.encrypted_dek_trad)
            
            # 필드 데이터를 DEK로 암호화
            nonce = os.urandom(12)
            aes_gcm = AESGCM(self._current_dek)
            ciphertext = aes_gcm.encrypt(nonce, field_value.encode('utf-8'), None)
            
            # nonce와 암호문을 결합하여 반환
            return nonce + ciphertext
            
        except Exception as e:
            logger.error(f"필드 암호화 실패: {e}")
            raise EncryptionError(f"필드 암호화 실패: {e}")

    def decrypt_field(self, encrypted_field: bytes) -> str:
        """암호화된 필드를 복호화합니다."""
        try:
            # DEK 관련 필드 확인
            if not all([self.encrypted_dek_trad, self.pqc_kem_ciphertext, self.pqc_secret_key, 
                       self.nonce_for_dek_encryption, self.encrypted_dek_by_pqc_shared_secret]):
                raise EncryptionError("DEK 관련 필드가 누락되었습니다.")

            # DEK 복호화 (RSA)
            try:
                dek = self._decrypt_dek_trad(self.encrypted_dek_trad)
                logger.debug("RSA DEK 복호화 성공")
            except Exception as e:
                logger.error(f"RSA DEK 복호화 실패: {e}")
                raise EncryptionError(f"RSA DEK 복호화 실패: {e}")
            
            # 필드 데이터 복호화
            try:
                nonce = encrypted_field[:12]
                ciphertext = encrypted_field[12:]
                aes_gcm = AESGCM(dek)
                decrypted_data = aes_gcm.decrypt(nonce, ciphertext, None)
                logger.debug("필드 데이터 복호화 성공")
                return decrypted_data.decode('utf-8')
            except Exception as e:
                logger.error(f"필드 데이터 복호화 실패: {e}")
                raise EncryptionError(f"필드 데이터 복호화 실패: {e}")
            
        except Exception as e:
            logger.error(f"필드 복호화 실패: {e}")
            raise EncryptionError(f"필드 복호화 실패: {e}") 