"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 Project 모델과 유사한 역할을 합니다.
# SQLAlchemy ORM을 사용하여 projects 테이블을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. ForeignKey() = Laravel의 foreign()와 유사
# 2. relationship() = Laravel의 belongsTo()와 유사
# 3. ondelete="CASCADE" = Laravel의 onDelete('cascade')와 유사
"""

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


class Project(Base):
    """
    # Laravel의 Project 모델과 유사한 역할
    #
    # 주요 필드:
    # - id: 기본 키
    # - user_id: 외래 키 (users 테이블 참조)
    # - host_name: 호스트 이름
    # - ip_address: IP 주소 (IPv6 지원)
    # - url: 모니터링할 URL
    # - title: 프로젝트 제목
    # - open_date: 프로젝트 시작일
    # - snapshot_path: 스냅샷 이미지 경로
    # - last_snapshot_at: 마지막 스냅샷 시간
    # - status: 프로젝트 상태
    # - status_interval: 상태 체크 주기
    # - expiry_d_day: 만료일 D-day
    # - expiry_interval: 만료일 알림 주기
    # - time_limit: 응답 시간 제한
    # - time_limit_interval: 제한 초과 시 알림 주기
    # - created_at, updated_at: 타임스탬프
    # - deleted_at: 소프트 삭제
    """

    __tablename__ = "projects"  # Laravel의 protected $table = 'projects'

    id = Column(Integer, primary_key=True, index=True)  # 기본 키
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # 외래 키
    host_name = Column(String(50))  # 호스트 이름
    ip_address = Column(String(45))  # IPv6 대응
    url = Column(String(255))  # 모니터링 URL
    title = Column(String(255))  # 프로젝트 제목
    open_date = Column(DateTime, default=func.now())
    snapshot_path = Column(String(255))  # 스냅샷 경로
    last_snapshot_at = Column(DateTime, default=func.now())  # 마지막 스냅샷 시간
    status = Column(Boolean, default=True)  # 프로젝트 상태
    is_active = Column(Boolean, default=True)  # 프로젝트 활성화 상태
    status_interval = Column(Integer, default=300)  # 상태 체크 주기 (초)
    expiry_d_day = Column(Integer, default=30)  # 만료일 D-day
    expiry_interval = Column(Integer, default=7)  # 만료일 알림 주기 (일)
    time_limit = Column(Integer, default=5)  # 응답 시간 제한 (초)
    time_limit_interval = Column(Integer, default=15)  # 제한 초과 시 알림 주기 (분)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 생성 시간
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 수정 시간
    deleted_at = Column(DateTime, nullable=True)  # 삭제 시간

    # 관계 설정 (Laravel의 belongsTo와 유사)
    user = relationship("User", back_populates="projects", lazy="joined")
    monitoring_logs = relationship(
        "MonitoringLog", back_populates="project", cascade="all, delete-orphan"
    )
    project_logs = relationship(
        "ProjectLog", back_populates="project", cascade="all, delete-orphan"
    )
    monitoring_alerts = relationship(
        "MonitoringAlert", back_populates="project", cascade="all, delete-orphan"
    )
    monitoring_settings = relationship(
        "MonitoringSetting",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    notifications = relationship(
        "Notification", back_populates="project", cascade="all, delete-orphan"
    )
    request_logs = relationship(
        "RequestLog", back_populates="project", cascade="all, delete-orphan"
    )
    ssl_domain_status = relationship(
        "SSLDomainStatus", back_populates="project", cascade="all, delete-orphan"
    )
