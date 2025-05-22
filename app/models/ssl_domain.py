"""
# Laravel 개발자를 위한 설명
# 이 파일은 SSL 도메인 상태 관련 모델을 정의합니다.
# SQLAlchemy ORM을 사용하여 ssl_domain_status 테이블을 정의합니다.
# 
# Laravel과의 주요 차이점:
# 1. ForeignKey() = Laravel의 foreign()와 유사
# 2. relationship() = Laravel의 belongsTo()와 유사
# 3. ondelete="CASCADE" = Laravel의 onDelete('cascade')와 유사
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class SSLDomainStatus(Base):
    """
    # SSL 도메인 상태 모델
    # 
    # 주요 필드:
    # - id: 기본 키
    # - project_id: 프로젝트 외래 키
    # - domain: 도메인 주소
    # - ssl_status: SSL 상태
    # - ssl_expiry: SSL 만료일
    # - domain_expiry: 도메인 만료일
    # - created_at: 생성 시간
    # - updated_at: 수정 시간
    """
    __tablename__ = "ssl_domain_status"  # Laravel의 protected $table = 'ssl_domain_status'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)  # Laravel의 foreign()와 유사
    domain = Column(String(255), nullable=False)  # 도메인 주소
    ssl_status = Column(Boolean)  # SSL 상태
    ssl_expiry = Column(DateTime)  # SSL 만료일
    domain_expiry = Column(DateTime)  # 도메인 만료일
    created_at = Column(DateTime, default=func.now())  # Laravel의 $timestamps
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Laravel의 $timestamps

    # 관계 설정 (Laravel의 belongsTo와 유사)
    project = relationship("Project", back_populates="ssl_domain_status")

