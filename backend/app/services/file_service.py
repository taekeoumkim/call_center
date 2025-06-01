import os
import uuid
from datetime import datetime
from typing import Optional, Tuple
import logging
from ..models import EncryptedFile, FilePermission, User
from ..utils.hybrid_encryption import HybridEncryption, EncryptionError, KeyVerificationError
from .. import db

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.encryption = HybridEncryption()
        self.base_path = os.getenv('FILE_STORAGE_PATH', 'encrypted_files')
        os.makedirs(self.base_path, exist_ok=True)

    def save_file(self, file_data: bytes, file_type: str, user: User) -> EncryptedFile:
        """
        파일을 암호화하여 저장하고 메타데이터를 DB에 기록
        """
        try:
            # 파일 암호화
            (
                nonce_for_file, encrypted_file_content,
                encrypted_dek_trad,
                pqc_kem_ciphertext, nonce_for_dek_encryption, encrypted_dek_by_pqc_shared_secret
            ) = self.encryption.encrypt_file_hybrid(file_data)

            # 파일 저장 경로 생성
            file_storage_path = str(uuid.uuid4())
            file_path = os.path.join(self.base_path, file_storage_path)
            
            with open(file_path, "wb") as f:
                f.write(encrypted_file_content)

            # DB에 메타데이터 저장
            encrypted_file = EncryptedFile(
                file_type=file_type,
                file_storage_path=file_storage_path,
                nonce_for_file=nonce_for_file,
                encrypted_dek_trad=encrypted_dek_trad,
                pqc_kem_ciphertext=pqc_kem_ciphertext,
                nonce_for_dek_encryption=nonce_for_dek_encryption,
                encrypted_dek_by_pqc_shared_secret=encrypted_dek_by_pqc_shared_secret,
                created_at=datetime.utcnow(),
                created_by=user.id
            )
            
            # 파일 생성자에게 권한 부여
            permission = FilePermission(
                file_id=encrypted_file.id,
                user_id=user.id,
                granted_at=datetime.utcnow()
            )
            encrypted_file.permissions.append(permission)

            logger.info(f"파일이 성공적으로 저장되었습니다. (ID: {encrypted_file.id})")
            return encrypted_file

        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            raise

    def get_file(self, file_id: int, user: User) -> Tuple[bytes, str]:
        """
        파일을 복호화하여 반환
        """
        try:
            # 파일 메타데이터 조회
            encrypted_file = EncryptedFile.query.get_or_404(file_id)

            # 권한 확인
            if not self._has_permission(encrypted_file, user):
                logger.warning(f"사용자 {user.id}가 파일 {file_id}에 대한 접근 권한이 없습니다.")
                raise PermissionError("파일에 대한 접근 권한이 없습니다.")

            # 암호화된 파일 읽기
            file_path = os.path.join(self.base_path, encrypted_file.file_storage_path)
            with open(file_path, "rb") as f:
                encrypted_file_content = f.read()

            # 파일 복호화
            decrypted_file = self.encryption.decrypt_file_hybrid(
                encrypted_file.nonce_for_file,
                encrypted_file_content,
                encrypted_file.encrypted_dek_trad,
                encrypted_file.pqc_kem_ciphertext,
                encrypted_file.nonce_for_dek_encryption,
                encrypted_file.encrypted_dek_by_pqc_shared_secret
            )

            logger.info(f"파일 {file_id}가 성공적으로 조회되었습니다.")
            return decrypted_file, encrypted_file.file_type

        except Exception as e:
            logger.error(f"파일 조회 실패: {e}")
            raise

    def grant_permission(self, file_id: int, creator: User, target_user: User) -> None:
        """
        파일 접근 권한 부여
        """
        try:
            encrypted_file = EncryptedFile.query.get_or_404(file_id)

            # 권한 부여자 확인
            if encrypted_file.created_by != creator.id:
                logger.warning(f"사용자 {creator.id}가 파일 {file_id}의 생성자가 아닙니다.")
                raise PermissionError("파일 생성자만 권한을 부여할 수 있습니다.")

            # 이미 권한이 있는지 확인
            if self._has_permission(encrypted_file, target_user):
                logger.info(f"사용자 {target_user.id}는 이미 파일 {file_id}에 대한 접근 권한이 있습니다.")
                return

            # 권한 부여
            permission = FilePermission(
                file_id=file_id,
                user_id=target_user.id,
                granted_at=datetime.utcnow()
            )
            encrypted_file.permissions.append(permission)

            logger.info(f"사용자 {target_user.id}에게 파일 {file_id}에 대한 접근 권한이 부여되었습니다.")

        except Exception as e:
            logger.error(f"권한 부여 실패: {e}")
            raise

    def revoke_permission(self, file_id: int, creator: User, target_user: User) -> None:
        """
        파일 접근 권한 취소
        """
        try:
            encrypted_file = EncryptedFile.query.get_or_404(file_id)

            # 권한 취소자 확인
            if encrypted_file.created_by != creator.id:
                logger.warning(f"사용자 {creator.id}가 파일 {file_id}의 생성자가 아닙니다.")
                raise PermissionError("파일 생성자만 권한을 취소할 수 있습니다.")

            # 권한 취소
            permission = FilePermission.query.filter_by(
                file_id=file_id,
                user_id=target_user.id
            ).first()

            if permission:
                encrypted_file.permissions.remove(permission)
                logger.info(f"사용자 {target_user.id}의 파일 {file_id}에 대한 접근 권한이 취소되었습니다.")
            else:
                logger.info(f"사용자 {target_user.id}는 파일 {file_id}에 대한 접근 권한이 없습니다.")

        except Exception as e:
            logger.error(f"권한 취소 실패: {e}")
            raise

    def delete_file(self, file_id: int, user: User) -> None:
        """
        파일 삭제
        """
        try:
            encrypted_file = EncryptedFile.query.get_or_404(file_id)

            # 삭제 권한 확인
            if encrypted_file.created_by != user.id:
                logger.warning(f"사용자 {user.id}가 파일 {file_id}의 생성자가 아닙니다.")
                raise PermissionError("파일 생성자만 삭제할 수 있습니다.")

            # 파일 시스템에서 삭제
            file_path = os.path.join(self.base_path, encrypted_file.file_storage_path)
            if os.path.exists(file_path):
                os.remove(file_path)

            # DB에서 메타데이터 삭제
            encrypted_file.delete()

            logger.info(f"파일 {file_id}가 성공적으로 삭제되었습니다.")

        except Exception as e:
            logger.error(f"파일 삭제 실패: {e}")
            raise

    def _has_permission(self, encrypted_file: EncryptedFile, user: User) -> bool:
        """사용자의 파일 접근 권한 확인"""
        return any(p.user_id == user.id for p in encrypted_file.permissions) 