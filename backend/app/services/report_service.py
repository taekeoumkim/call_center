from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import ConsultationReport
from app.utils.hybrid_encryption import HybridEncryption
import logging

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self):
        self.hybrid_encryption = HybridEncryption()

    def create_report(self, db: Session, report_data: Dict[str, Any]) -> ConsultationReport:
        """새 소견서 생성"""
        try:
            # Report 인스턴스 생성
            report = ConsultationReport(
                client_call_id=report_data.get("client_call_id"),
                counselor_id=report_data.get("counselor_id"),
                client_name=report_data.get("client_name"),
                client_age=report_data.get("client_age"),
                client_gender=report_data.get("client_gender"),
                memo_text=report_data.get("memo_text"),
                risk_level_recorded=report_data.get("risk_level_recorded"),
                transcribed_text=report_data.get("transcribed_text")
            )
            
            # 필드 암호화
            report.encrypt_fields(self.hybrid_encryption)
            
            db.add(report)
            db.commit()
            db.refresh(report)
            return report
            
        except Exception as e:
            db.rollback()
            logger.error(f"소견서 생성 실패: {str(e)}")
            raise

    def get_report(self, db: Session, report_id: int) -> Optional[ConsultationReport]:
        """소견서 조회"""
        try:
            report = db.query(ConsultationReport).filter(ConsultationReport.id == report_id).first()
            if not report:
                return None
                
            # 필드 복호화
            report.decrypt_fields(self.hybrid_encryption)
            return report
            
        except Exception as e:
            logger.error(f"소견서 조회 실패: {str(e)}")
            raise

    def get_reports(self, db: Session, skip: int = 0, limit: int = 100) -> List[ConsultationReport]:
        """소견서 목록 조회"""
        try:
            reports = db.query(ConsultationReport).offset(skip).limit(limit).all()
            for report in reports:
                report.decrypt_fields(self.hybrid_encryption)
            return reports
            
        except Exception as e:
            logger.error(f"소견서 목록 조회 실패: {str(e)}")
            raise

    def update_report(self, db: Session, report_id: int, report_data: Dict[str, Any]) -> Optional[ConsultationReport]:
        """소견서 수정"""
        try:
            report = db.query(ConsultationReport).filter(ConsultationReport.id == report_id).first()
            if not report:
                return None
                
            # 필드 업데이트
            for key, value in report_data.items():
                if hasattr(report, key):
                    setattr(report, key, value)
            
            # 필드 암호화
            report.encrypt_fields(self.hybrid_encryption)
            
            db.commit()
            db.refresh(report)
            return report
            
        except Exception as e:
            db.rollback()
            logger.error(f"소견서 수정 실패: {str(e)}")
            raise

    def delete_report(self, db: Session, report_id: int) -> bool:
        """소견서 삭제"""
        try:
            report = db.query(ConsultationReport).filter(ConsultationReport.id == report_id).first()
            if not report:
                return False
                
            db.delete(report)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"소견서 삭제 실패: {str(e)}")
            raise

    def search_reports(self, db: Session, query: str) -> List[ConsultationReport]:
        """소견서 검색 (암호화된 필드는 검색에서 제외)"""
        try:
            # 암호화되지 않은 필드로만 검색
            reports = db.query(ConsultationReport).filter(
                ConsultationReport.id.ilike(f"%{query}%")
            ).all()
            
            for report in reports:
                report.decrypt_fields(self.hybrid_encryption)
            return reports
            
        except Exception as e:
            logger.error(f"소견서 검색 실패: {str(e)}")
            raise 