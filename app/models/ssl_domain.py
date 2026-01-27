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

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


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

    __tablename__ = (
        "ssl_domain_status"  # Laravel의 protected $table = 'ssl_domain_status'
    )

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    domain = Column(String(255), nullable=False)  # 도메인 주소
    ssl_status = Column(Boolean)  # SSL 상태
    ssl_issuer = Column(String(255), nullable=True)  # SSL 발급 기관
    ssl_expiry = Column(DateTime)  # SSL 만료일
    domain_expiry = Column(DateTime)  # 도메인 만료일
    last_checked_at = Column(DateTime, nullable=True)  # 마지막 확인 시간
    check_error = Column(String(500), nullable=True)  # 확인 오류 메시지
    created_at = Column(DateTime, default=func.now())  # Laravel의 $timestamps
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now()
    )  # Laravel의 $timestamps

    # 관계 설정 (Laravel의 belongsTo와 유사)
    project = relationship("Project", back_populates="ssl_domain_status")

    # ==================== 비즈니스 메서드 ====================

    @property
    def ssl_days_remaining(self) -> int:
        """SSL 만료까지 남은 일수"""
        if not self.ssl_expiry:
            return -1
        delta = self.ssl_expiry - datetime.utcnow()
        return max(0, delta.days)

    @property
    def domain_days_remaining(self) -> int:
        """도메인 만료까지 남은 일수"""
        if not self.domain_expiry:
            return -1
        delta = self.domain_expiry - datetime.utcnow()
        return max(0, delta.days)

    @property
    def is_ssl_expiring_soon(self) -> bool:
        """SSL 곧 만료 여부 (30일 이내)"""
        return 0 <= self.ssl_days_remaining <= 30

    @property
    def is_domain_expiring_soon(self) -> bool:
        """도메인 곧 만료 여부 (30일 이내)"""
        return 0 <= self.domain_days_remaining <= 30

    @property
    def is_ssl_expired(self) -> bool:
        """SSL 만료 여부"""
        if not self.ssl_expiry:
            return False
        return self.ssl_expiry < datetime.utcnow()

    @property
    def is_domain_expired(self) -> bool:
        """도메인 만료 여부"""
        if not self.domain_expiry:
            return False
        return self.domain_expiry < datetime.utcnow()

    @property
    def needs_attention(self) -> bool:
        """주의 필요 여부 (SSL/도메인 만료 임박 또는 상태 이상)"""
        return (
            not self.ssl_status
            or self.is_ssl_expiring_soon
            or self.is_domain_expiring_soon
            or self.check_error is not None
        )

    def get_ssl_status_text(self) -> str:
        """SSL 상태 텍스트"""
        if self.is_ssl_expired:
            return "만료됨"
        if self.is_ssl_expiring_soon:
            return f"만료 임박 ({self.ssl_days_remaining}일)"
        if not self.ssl_status:
            return "비정상"
        return "정상"

    def get_domain_status_text(self) -> str:
        """도메인 상태 텍스트"""
        if self.is_domain_expired:
            return "만료됨"
        if self.is_domain_expiring_soon:
            return f"만료 임박 ({self.domain_days_remaining}일)"
        return "정상"
