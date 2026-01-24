"""
내부 로그 모델

이 파일은 시스템 내부 로그를 저장하는 모델을 정의합니다.
에러, 경고, 정보 등 시스템 이벤트를 기록합니다.

주요 필드:
- log_type: 로그 유형 (error, warning, info 등)
- message: 로그 메시지
- created_at: 생성 시간
"""

from sqlalchemy import Column, DateTime, Integer, String, func

from app.db.base_class import Base


class InternalLog(Base):
    """내부 시스템 로그 모델"""
    __tablename__ = "internal_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(String(50), nullable=False)
    message = Column(String(1024), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
