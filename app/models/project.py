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

from datetime import datetime
from urllib.parse import urlparse

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
    description = Column(String(500), nullable=True)  # 프로젝트 설명
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
    is_public = Column(Boolean, default=False)  # 공개 상태 페이지 노출 여부
    category = Column(String(50), nullable=True)  # 프로젝트 카테고리
    tags = Column(String(500), nullable=True)  # 태그 (쉼표 구분)

    # 유지보수 모드 설정
    maintenance_mode = Column(Boolean, default=False)  # 유지보수 모드 활성화
    maintenance_message = Column(String(500), nullable=True)  # 유지보수 안내 메시지
    maintenance_started_at = Column(DateTime, nullable=True)  # 유지보수 시작 시간
    maintenance_ends_at = Column(DateTime, nullable=True)  # 유지보수 종료 예정 시간

    # 커스텀 헤더 설정 (JSON 형식: {"Header-Name": "value", ...})
    custom_headers = Column(String(2000), nullable=True)  # 모니터링 요청 시 추가할 HTTP 헤더

    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())  # 생성 시간
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

    # ==================== 비즈니스 메서드 ====================

    @property
    def is_deleted(self) -> bool:
        """소프트 삭제 여부"""
        return self.deleted_at is not None

    @property
    def is_monitoring_enabled(self) -> bool:
        """모니터링 활성화 여부 (활성 + 상태 정상 + 미삭제 + 유지보수 모드 아님)"""
        return self.is_active and self.status and not self.is_deleted and not self.maintenance_mode

    @property
    def is_in_maintenance(self) -> bool:
        """유지보수 모드 여부"""
        return self.maintenance_mode is True

    @property
    def domain(self) -> str:
        """URL에서 도메인 추출"""
        if not self.url:
            return ""
        parsed = urlparse(self.url)
        return parsed.netloc or parsed.path.split("/")[0]

    @property
    def protocol(self) -> str:
        """URL 프로토콜 (http/https)"""
        if not self.url:
            return ""
        parsed = urlparse(self.url)
        return parsed.scheme or "https"

    @property
    def is_https(self) -> bool:
        """HTTPS 사용 여부"""
        return self.protocol.lower() == "https"

    @property
    def latest_log(self):
        """최신 모니터링 로그"""
        if not self.monitoring_logs:
            return None
        return max(self.monitoring_logs, key=lambda x: x.created_at)

    @property
    def unresolved_alert_count(self) -> int:
        """미해결 알림 개수"""
        return len([a for a in self.monitoring_alerts if not a.is_resolved])

    def get_check_interval_minutes(self) -> int:
        """체크 주기 (분 단위)"""
        return self.status_interval // 60 if self.status_interval else 5

    def needs_snapshot_update(self, hours: int = 24) -> bool:
        """스냅샷 업데이트 필요 여부"""
        if not self.last_snapshot_at:
            return True
        delta = datetime.utcnow() - self.last_snapshot_at
        return delta.total_seconds() > (hours * 3600)

    def is_response_time_exceeded(self, response_time: float) -> bool:
        """응답 시간 제한 초과 여부"""
        return response_time > self.time_limit if self.time_limit else False

    @property
    def tag_list(self) -> list:
        """태그 목록"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def has_tag(self, tag: str) -> bool:
        """특정 태그 포함 여부"""
        return tag.lower() in [t.lower() for t in self.tag_list]
