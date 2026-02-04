"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 관련 모델들을 정의합니다.
# SQLAlchemy ORM을 사용하여 모니터링 관련 테이블들을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. 각 모델이 하나의 파일에 정의됨 (Laravel은 보통 각 모델을 별도 파일로 분리)
# 2. datetime.utcnow = Laravel의 now()와 유사하지만 UTC 기준
# 3. relationship() = Laravel의 hasMany(), belongsTo()와 유사
# 4. ondelete='CASCADE' = Laravel의 onDelete('cascade')와 유사
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class MonitoringLog(Base):
    """
    # 모니터링 로그 모델 (Laravel의 MonitoringLog 모델과 유사)
    #
    # 주요 필드:
    # - project_id: 프로젝트 외래 키 (Laravel의 belongsTo('Project')와 유사)
    # - status_code: HTTP 상태 코드
    # - response_time: 응답 시간 (초)
    # - is_available: 서비스 가용성
    # - error_message: 오류 메시지
    # - created_at: 로그 생성 시간 (Laravel의 $timestamps와 유사)
    #
    # Playwright 심층 모니터링 필드:
    # - dom_content_loaded: DOM 로드 완료 시간 (ms)
    # - page_load_time: 전체 페이지 로드 시간 (ms)
    # - first_contentful_paint: FCP (ms)
    # - largest_contentful_paint: LCP (ms)
    # - time_to_first_byte: TTFB (ms)
    # - cumulative_layout_shift: CLS (레이아웃 변경 지표)
    # - total_blocking_time: TBT (ms)
    # - js_errors: JavaScript 에러 목록 (JSON)
    # - console_errors: 콘솔 에러 개수
    # - resource_count: 로드된 리소스 개수
    # - resource_size: 총 리소스 크기 (bytes)
    # - failed_resources: 실패한 리소스 개수
    # - redirect_count: 리다이렉트 횟수
    # - js_heap_size: JS 힙 메모리 (bytes)
    # - is_dom_ready: DOM 정상 로드 여부
    # - is_js_healthy: JS 에러 없음 여부
    # - check_type: 체크 유형 (http, playwright)
    """

    __tablename__ = "monitoring_logs"  # Laravel의 protected $table = 'monitoring_logs'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    status_code = Column(Integer)  # HTTP 상태 코드
    response_time = Column(Float)  # 응답 시간 (초)
    is_available = Column(Boolean)  # 서비스 가용성
    error_message = Column(Text)  # 오류 메시지

    # Playwright 심층 모니터링 메트릭
    check_type = Column(String(20), default="http")  # http 또는 playwright
    dom_content_loaded = Column(Float, nullable=True)  # DOM 로드 시간 (ms)
    page_load_time = Column(Float, nullable=True)  # 전체 페이지 로드 시간 (ms)
    first_contentful_paint = Column(Float, nullable=True)  # FCP (ms)
    largest_contentful_paint = Column(Float, nullable=True)  # LCP (ms)
    time_to_first_byte = Column(Float, nullable=True)  # TTFB (ms)
    cumulative_layout_shift = Column(Float, nullable=True)  # CLS
    total_blocking_time = Column(Float, nullable=True)  # TBT (ms)
    js_errors = Column(Text, nullable=True)  # JS 에러 목록 (JSON)
    console_errors = Column(Integer, default=0)  # 콘솔 에러 개수
    resource_count = Column(Integer, nullable=True)  # 로드된 리소스 개수
    resource_size = Column(Integer, nullable=True)  # 총 리소스 크기 (bytes)
    failed_resources = Column(Integer, nullable=True)  # 실패한 리소스 개수
    redirect_count = Column(Integer, nullable=True)  # 리다이렉트 횟수
    js_heap_size = Column(Integer, nullable=True)  # JS 힙 메모리 (bytes)
    is_dom_ready = Column(Boolean, nullable=True)  # DOM 정상 로드 여부
    is_js_healthy = Column(Boolean, nullable=True)  # JS 에러 없음 여부

    created_at = Column(DateTime, default=datetime.utcnow)  # Laravel의 $timestamps

    # 관계 설정
    project = relationship("Project", back_populates="monitoring_logs")

    # ==================== 비즈니스 메서드 ====================

    @property
    def is_success(self) -> bool:
        """성공 여부 (가용성 O + 상태코드 2xx)"""
        return self.is_available and self.status_code and 200 <= self.status_code < 300

    @property
    def is_slow(self) -> bool:
        """느린 응답 여부 (3초 초과)"""
        return self.response_time and self.response_time > 3.0

    @property
    def response_time_ms(self) -> float:
        """응답 시간 (밀리초)"""
        return (self.response_time or 0) * 1000

    @property
    def status_text(self) -> str:
        """상태 텍스트"""
        if not self.is_available:
            return "장애"
        if self.is_slow:
            return "느림"
        return "정상"

    def get_performance_grade(self) -> str:
        """성능 등급 (A~F)"""
        if not self.response_time:
            return "N/A"
        if self.response_time < 0.5:
            return "A"
        if self.response_time < 1.0:
            return "B"
        if self.response_time < 2.0:
            return "C"
        if self.response_time < 3.0:
            return "D"
        return "F"

    def has_js_errors(self) -> bool:
        """JavaScript 에러 존재 여부"""
        return self.console_errors and self.console_errors > 0


class MonitoringAlert(Base):
    """
    # 모니터링 알림 모델 (Laravel의 MonitoringAlert 모델과 유사)
    #
    # 주요 필드:
    # - project_id: 프로젝트 외래 키 (Laravel의 belongsTo('Project')와 유사)
    # - alert_type: 알림 유형 (예: 'error', 'warning', 'info')
    # - message: 알림 메시지
    # - is_resolved: 해결 여부
    # - resolved_at: 해결 시간
    # - created_at, updated_at: 타임스탬프 (Laravel의 $timestamps와 유사)
    """

    __tablename__ = (
        "monitoring_alerts"  # Laravel의 protected $table = 'monitoring_alerts'
    )

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    alert_type = Column(String(50), nullable=False)  # 알림 유형
    message = Column(Text, nullable=False)  # 알림 메시지
    is_resolved = Column(Boolean, default=False)  # 해결 여부
    resolved_at = Column(DateTime)  # 해결 시간
    created_at = Column(DateTime, default=datetime.utcnow)  # Laravel의 $timestamps
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # Laravel의 $timestamps

    # 관계 설정
    project = relationship("Project", back_populates="monitoring_alerts")

    # ==================== 비즈니스 메서드 ====================

    @property
    def is_critical(self) -> bool:
        """심각한 알림 여부"""
        return self.alert_type in ("error", "critical", "availability")

    @property
    def duration_hours(self) -> float:
        """알림 지속 시간 (시간)"""
        if self.is_resolved and self.resolved_at:
            delta = self.resolved_at - self.created_at
        else:
            delta = datetime.utcnow() - self.created_at
        return delta.total_seconds() / 3600

    def can_resolve(self) -> bool:
        """해결 가능 여부"""
        return not self.is_resolved


class MonitoringSetting(Base):
    """
    # 모니터링 설정 모델 (Laravel의 MonitoringSetting 모델과 유사)
    #
    # 주요 필드:
    # - project_id: 프로젝트 외래 키 (Laravel의 belongsTo('Project')와 유사)
    # - check_interval: 체크 주기 (초)
    # - timeout: 타임아웃 (초)
    # - retry_count: 재시도 횟수
    # - alert_threshold: 알림 임계값
    # - created_at, updated_at: 타임스탬프 (Laravel의 $timestamps와 유사)
    """

    __tablename__ = (
        "monitoring_settings"  # Laravel의 protected $table = 'monitoring_settings'
    )

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    check_interval = Column(Integer, default=300)  # 체크 주기 (초)
    timeout = Column(Integer, default=30)  # 타임아웃 (초)
    retry_count = Column(Integer, default=3)  # 재시도 횟수
    alert_threshold = Column(Integer, default=3)  # 알림 임계값
    is_alert_enabled = Column(Boolean, default=True)  # 알림 활성화 여부
    alert_email = Column(String(255), nullable=True)  # 알림 이메일
    webhook_url = Column(String(500), nullable=True)  # 웹훅 URL

    # 콘텐츠 변경 감지 설정
    content_change_detection = Column(Boolean, default=False)  # 콘텐츠 변경 감지 활성화
    content_hash = Column(String(64), nullable=True)  # 마지막 콘텐츠 해시 (SHA-256)
    content_selector = Column(String(255), nullable=True)  # 감지할 CSS 셀렉터 (전체 페이지: null)
    last_content_check_at = Column(DateTime, nullable=True)  # 마지막 콘텐츠 체크 시간

    # 키워드 모니터링 설정
    keyword_monitoring = Column(Boolean, default=False)  # 키워드 모니터링 활성화
    keywords = Column(Text, nullable=True)  # 모니터링할 키워드 (JSON 배열)
    keyword_alert_on_found = Column(Boolean, default=True)  # True: 키워드 발견 시 알림, False: 키워드 없을 때 알림

    created_at = Column(DateTime, default=datetime.utcnow)  # Laravel의 $timestamps
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # Laravel의 $timestamps

    # 관계 설정
    project = relationship("Project", back_populates="monitoring_settings")
