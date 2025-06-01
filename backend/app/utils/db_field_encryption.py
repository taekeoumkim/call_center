from typing import Dict, Any, Tuple, Optional
import json
from .hybrid_encryption import HybridEncryption
import logging

logger = logging.getLogger(__name__)

class DBFieldEncryption:
    def __init__(self):
        self.hybrid_encryption = HybridEncryption()

    def _serialize_field_value(self, value: Any) -> bytes:
        """필드 값을 바이트로 직렬화"""
        if value is None:
            return b''
        if isinstance(value, (int, float, bool)):
            value = str(value)
        if isinstance(value, str):
            return value.encode('utf-8')
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False).encode('utf-8')
        raise ValueError(f"지원하지 않는 필드 타입: {type(value)}")

    def _deserialize_field_value(self, value_bytes: bytes, original_type: type) -> Any:
        """바이트를 원래 타입으로 역직렬화"""
        if not value_bytes:
            return None
        value_str = value_bytes.decode('utf-8')
        
        if original_type == str:
            return value_str
        if original_type == int:
            return int(value_str)
        if original_type == float:
            return float(value_str)
        if original_type == bool:
            return value_str.lower() == 'true'
        if original_type in (dict, list):
            return json.loads(value_str)
        raise ValueError(f"지원하지 않는 필드 타입: {original_type}")

    def encrypt_record_fields(self, record: Dict[str, Any], fields_to_encrypt: Dict[str, type]) -> Tuple[Dict[str, bytes], Dict[str, bytes]]:
        """
        레코드의 지정된 필드들을 암호화
        
        Args:
            record: 암호화할 필드들을 포함하는 딕셔너리
            fields_to_encrypt: 암호화할 필드명과 해당 타입을 지정하는 딕셔너리
            
        Returns:
            Tuple[Dict[str, bytes], Dict[str, bytes]]: 
                - 암호화된 필드값과 nonce를 포함하는 딕셔너리
                - 암호화된 DEK 정보를 포함하는 딕셔너리
        """
        try:
            # DEK 생성
            dek = self.hybrid_encryption._generate_dek()
            
            # DEK를 하이브리드 방식으로 암호화
            encrypted_dek_trad = self.hybrid_encryption._encrypt_dek_trad(dek)
            pqc_kem_ciphertext, encrypted_dek_pqc_package, pqc_secret_key = self.hybrid_encryption._encrypt_dek_pqc(dek)
            
            # 암호화된 필드값과 nonce를 저장할 딕셔너리
            encrypted_fields = {}
            nonces = {}
            
            # 각 필드 암호화
            for field_name, field_type in fields_to_encrypt.items():
                if field_name not in record:
                    continue
                    
                # 필드값 직렬화
                field_value = self._serialize_field_value(record[field_name])
                
                # AES-GCM으로 암호화
                nonce, encrypted_value = self.hybrid_encryption._encrypt_file_with_dek(field_value, dek)
                
                # 결과 저장
                encrypted_fields[f"{field_name}_encrypted"] = encrypted_value
                nonces[f"{field_name}_nonce"] = nonce
            
            # DEK 정보 저장
            dek_info = {
                "dek_trad_encrypted": encrypted_dek_trad,
                "dek_pqc_kem_ciphertext": pqc_kem_ciphertext,
                "dek_pqc_package": encrypted_dek_pqc_package,
                "dek_pqc_secret_key": pqc_secret_key
            }
            
            return encrypted_fields, nonces, dek_info
            
        except Exception as e:
            logger.error(f"레코드 필드 암호화 실패: {str(e)}")
            raise

    def decrypt_record_fields(self, encrypted_fields: Dict[str, bytes], 
                            nonces: Dict[str, bytes],
                            dek_info: Dict[str, bytes],
                            fields_to_decrypt: Dict[str, type]) -> Dict[str, Any]:
        """
        암호화된 레코드 필드들을 복호화
        
        Args:
            encrypted_fields: 암호화된 필드값을 포함하는 딕셔너리
            nonces: 각 필드의 nonce를 포함하는 딕셔너리
            dek_info: 암호화된 DEK 정보를 포함하는 딕셔너리
            fields_to_decrypt: 복호화할 필드명과 해당 타입을 지정하는 딕셔너리
            
        Returns:
            Dict[str, Any]: 복호화된 필드값을 포함하는 딕셔너리
        """
        try:
            # DEK 복호화
            dek_from_trad = None
            dek_from_pqc = None
            
            # 전통 방식으로 DEK 복호화 시도
            try:
                dek_from_trad = self.hybrid_encryption._decrypt_dek_trad(dek_info["dek_trad_encrypted"])
            except Exception as e:
                logger.warning(f"전통 방식 DEK 복호화 실패: {str(e)}")

            # PQC 방식으로 DEK 복호화 시도
            try:
                dek_from_pqc = self.hybrid_encryption._decrypt_dek_pqc(
                    dek_info["dek_pqc_kem_ciphertext"],
                    dek_info["dek_pqc_package"],
                    dek_info["dek_pqc_secret_key"]
                )
            except Exception as e:
                logger.warning(f"PQC 방식 DEK 복호화 실패: {str(e)}")

            # DEK 검증 및 선택
            if dek_from_trad and dek_from_pqc:
                if dek_from_trad != dek_from_pqc:
                    raise ValueError("DEK 불일치: 전통 방식과 PQC 방식의 DEK가 다릅니다.")
                final_dek = dek_from_trad
            elif dek_from_trad:
                final_dek = dek_from_trad
            elif dek_from_pqc:
                final_dek = dek_from_pqc
            else:
                raise ValueError("모든 DEK 복호화 방식이 실패했습니다.")

            # 각 필드 복호화
            decrypted_fields = {}
            for field_name, field_type in fields_to_decrypt.items():
                encrypted_key = f"{field_name}_encrypted"
                nonce_key = f"{field_name}_nonce"
                
                if encrypted_key not in encrypted_fields or nonce_key not in nonces:
                    continue
                
                # 필드값 복호화
                decrypted_bytes = self.hybrid_encryption._decrypt_file_with_dek(
                    nonces[nonce_key],
                    encrypted_fields[encrypted_key],
                    final_dek
                )
                
                # 원래 타입으로 역직렬화
                decrypted_fields[field_name] = self._deserialize_field_value(decrypted_bytes, field_type)
            
            return decrypted_fields
            
        except Exception as e:
            logger.error(f"레코드 필드 복호화 실패: {str(e)}")
            raise 