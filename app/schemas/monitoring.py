"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 Monitoring 모델과 유사한 역할을 합니다.
# Pydantic을 사용하여 모니터링 관련 스키마를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. BaseModel = Laravel의 Model과 유사
# 2. Field = Laravel의 $fillable과 유사
# 3. Config = Laravel의 $casts와 유사
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# 모니터링 로그 스키마
class MonitoringLogBase(BaseModel):
    project_id: int
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    is_available: Optional[bool] = None
    error_message: Optional[str] = None


class MonitoringLogCreate(MonitoringLogBase):
    pass


class MonitoringLogResponse(BaseModel):
    id: int
    project_id: int
    check_type: Optional[str] = "http"
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    is_available: Optional[bool] = None
    error_message: Optional[str] = None

    # Playwright 심층 모니터링 메트릭
    dom_content_loaded: Optional[float] = None
    page_load_time: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    time_to_first_byte: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    total_blocking_time: Optional[float] = None
    js_errors: Optional[str] = None
    console_errors: Optional[int] = 0
    resource_count: Optional[int] = None
    resource_size: Optional[int] = None
    failed_resources: Optional[int] = None
    redirect_count: Optional[int] = None
    js_heap_size: Optional[int] = None
    is_dom_ready: Optional[bool] = None
    is_js_healthy: Optional[bool] = None

    created_at: datetime

    class Config:
        from_attributes = True


# 모니터링 알림 스키마
class MonitoringAlertBase(BaseModel):
    project_id: int
    alert_type: str
    message: str
    status: str = "pending"


class MonitoringAlertCreate(MonitoringAlertBase):
    pass


class MonitoringAlertResponse(MonitoringAlertBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 모니터링 설정 스키마
class MonitoringSettingBase(BaseModel):
    project_id: int
    check_interval: int = Field(default=300, ge=60, le=3600)  # 1분~1시간
    timeout: int = Field(default=30, ge=5, le=300)  # 5초~5분
    retry_count: int = Field(default=3, ge=1, le=5)
    alert_threshold: int = Field(default=3, ge=1, le=10)
    is_alert_enabled: bool = True
    alert_email: Optional[str] = None
    webhook_url: Optional[str] = None
    # 콘텐츠 변경 감지 설정
    content_change_detection: bool = False
    content_selector: Optional[str] = None
    # 키워드 모니터링 설정
    keyword_monitoring: bool = False
    keywords: Optional[str] = None  # JSON 배열 문자열
    keyword_alert_on_found: bool = True


class MonitoringSettingCreate(MonitoringSettingBase):
    pass


class MonitoringSettingUpdate(BaseModel):
    check_interval: Optional[int] = Field(None, ge=60, le=3600)
    timeout: Optional[int] = Field(None, ge=5, le=300)
    retry_count: Optional[int] = Field(None, ge=1, le=5)
    alert_threshold: Optional[int] = Field(None, ge=1, le=10)
    is_alert_enabled: Optional[bool] = None
    alert_email: Optional[str] = None
    webhook_url: Optional[str] = None
    # 콘텐츠 변경 감지 설정
    content_change_detection: Optional[bool] = None
    content_selector: Optional[str] = None
    # 키워드 모니터링 설정
    keyword_monitoring: Optional[bool] = None
    keywords: Optional[str] = None
    keyword_alert_on_found: Optional[bool] = None


class MonitoringSettingResponse(MonitoringSettingBase):
    id: int
    content_hash: Optional[str] = None
    last_content_check_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# SSL 도메인 상태 스키마
class SSLDomainStatusBase(BaseModel):
    project_id: int
    domain: str
    ssl_status: bool
    ssl_issuer: Optional[str] = None
    ssl_expiry: Optional[datetime] = None
    domain_expiry: Optional[datetime] = None


class SSLDomainStatusCreate(SSLDomainStatusBase):
    pass


class SSLDomainStatusUpdate(BaseModel):
    ssl_status: Optional[bool] = None
    ssl_issuer: Optional[str] = None
    ssl_expiry: Optional[datetime] = None
    domain_expiry: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    check_error: Optional[str] = None


class SSLDomainStatusResponse(SSLDomainStatusBase):
    id: int
    last_checked_at: Optional[datetime] = None
    check_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 모니터링 체크 요청 스키마
class MonitoringCheckRequest(BaseModel):
    project_id: int
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[dict] = None
    timeout: Optional[int] = 30


# 모니터링 체크 응답 스키마
class MonitoringCheckResponse(BaseModel):
    project_id: int
    url: str
    status: bool
    response_time: Optional[float] = None
    http_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: datetime


# SSL 상태 스키마
class SSLStatus(BaseModel):
    """SSL 상태 스키마"""

    is_valid: bool
    issuer: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    days_remaining: Optional[int] = None


# 모니터링 상태 스키마
class MonitoringStatus(BaseModel):
    """모니터링 상태 스키마"""

    is_available: bool
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    content: Optional[str] = None  # 콘텐츠 변경 감지용


# 모니터링 응답 스키마
class MonitoringResponse(BaseModel):
    """모니터링 응답 스키마"""

    project_id: int
    project_title: str
    url: str
    status: MonitoringStatus
    ssl: Optional[SSLStatus] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# TCP 포트 체크 스키마
class TCPPortCheckRequest(BaseModel):
    """TCP 포트 체크 요청 스키마"""

    host: str
    port: int = Field(ge=1, le=65535)
    timeout: int = Field(default=5, ge=1, le=30)


class TCPPortCheckResponse(BaseModel):
    """TCP 포트 체크 응답 스키마"""

    host: str
    port: int
    is_open: bool
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# UDP 포트 체크 스키마
class UDPPortCheckRequest(BaseModel):
    """UDP 포트 체크 요청 스키마"""

    host: str
    port: int = Field(ge=1, le=65535)
    timeout: int = Field(default=5, ge=1, le=30)


class UDPPortCheckResponse(BaseModel):
    """UDP 포트 체크 응답 스키마"""

    host: str
    port: int
    is_open: bool  # UDP는 응답 없음 = 열림으로 추정
    is_filtered: bool = False  # 응답 없으면 open|filtered
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# DNS 조회 스키마
class DNSLookupRequest(BaseModel):
    """DNS 조회 요청 스키마"""

    domain: str
    record_type: str = Field(default="A", pattern="^(A|AAAA|CNAME|MX|NS|TXT|SOA)$")


class DNSRecord(BaseModel):
    """DNS 레코드 스키마"""

    record_type: str
    value: str
    ttl: Optional[int] = None


class DNSLookupResponse(BaseModel):
    """DNS 조회 응답 스키마"""

    domain: str
    records: list[DNSRecord] = []
    is_resolved: bool
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# API 엔드포인트 체크 스키마
class APIEndpointCheckRequest(BaseModel):
    """API 엔드포인트 체크 요청 스키마"""

    url: str
    method: str = Field(default="GET", pattern="^(GET|POST|PUT|PATCH|DELETE|HEAD)$")
    headers: Optional[dict] = None  # 커스텀 헤더
    body: Optional[str] = None  # 요청 바디 (JSON 문자열)
    timeout: int = Field(default=30, ge=5, le=120)
    expected_status: Optional[int] = Field(None, ge=100, le=599)  # 기대 상태 코드
    expected_json_path: Optional[str] = None  # 검증할 JSON 경로 (예: "data.id")
    expected_json_value: Optional[str] = None  # 기대 JSON 값


class APIEndpointValidation(BaseModel):
    """API 엔드포인트 검증 결과"""

    field: str  # 검증 필드명 (status_code, json_path 등)
    expected: str  # 기대값
    actual: str  # 실제값
    passed: bool  # 통과 여부


class APIEndpointCheckResponse(BaseModel):
    """API 엔드포인트 체크 응답 스키마"""

    url: str
    method: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    response_body: Optional[str] = None  # 응답 본문 (최대 1000자)
    content_type: Optional[str] = None
    is_json: bool = False  # JSON 응답 여부
    validations: list[APIEndpointValidation] = Field(default_factory=list)
    all_passed: bool = False  # 모든 검증 통과 여부
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# Synthetic 모니터링 스키마
class SyntheticStep(BaseModel):
    """시나리오 단일 스텝 정의"""

    action: str = Field(
        ...,
        pattern="^(navigate|click|type|select|wait|screenshot|assert_text|assert_element|assert_url)$",
        description="수행할 액션 종류",
    )
    selector: Optional[str] = Field(
        None, description="CSS 선택자 (click, type, select, assert_element에 필요)"
    )
    value: Optional[str] = Field(
        None, description="입력값 (navigate=URL, type=텍스트, select=옵션값, wait=ms, assert_text=기대문자열)"
    )
    description: Optional[str] = Field(
        None, description="스텝 설명 (예: '로그인 버튼 클릭')"
    )


class SyntheticTestRequest(BaseModel):
    """Synthetic 모니터링 테스트 요청"""

    name: str = Field(..., min_length=1, max_length=200, description="테스트 시나리오 이름")
    start_url: str = Field(..., description="시작 URL")
    steps: list[SyntheticStep] = Field(..., min_length=1, description="실행할 스텝 목록")
    timeout: int = Field(default=30000, ge=5000, le=120000, description="전체 타임아웃 (ms)")
    viewport_width: int = Field(default=1280, ge=320, le=1920)
    viewport_height: int = Field(default=800, ge=480, le=1080)


class SyntheticStepResult(BaseModel):
    """시나리오 스텝 실행 결과"""

    step_number: int
    action: str
    description: Optional[str] = None
    passed: bool = False
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None  # 스크린샷 저장 경로 (있는 경우)
    current_url: Optional[str] = None


class SyntheticTestResponse(BaseModel):
    """Synthetic 모니터링 테스트 응답"""

    name: str
    start_url: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    all_passed: bool = False
    total_duration_ms: float = 0.0
    step_results: list[SyntheticStepResult] = Field(default_factory=list)
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# 콘텐츠 검증 스키마
class ContentCheckRequest(BaseModel):
    """콘텐츠 검증 요청 스키마"""

    url: str
    expected_content: str
    timeout: int = Field(default=30, ge=5, le=120)


class ContentCheckResponse(BaseModel):
    """콘텐츠 검증 응답 스키마"""

    url: str
    expected_content: str
    is_found: bool
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# 보안 헤더 체크 스키마
class SecurityHeadersRequest(BaseModel):
    """보안 헤더 체크 요청 스키마"""

    url: str
    timeout: int = Field(default=30, ge=5, le=120)


class SecurityHeader(BaseModel):
    """보안 헤더 정보 스키마"""

    name: str
    value: Optional[str] = None
    is_present: bool
    is_recommended: bool = True
    description: str = ""


class SecurityHeadersResponse(BaseModel):
    """보안 헤더 체크 응답 스키마"""

    url: str
    headers: list[SecurityHeader] = []
    score: int = Field(ge=0, le=100)  # 보안 점수 (0-100)
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


# 종합 상태 체크 스키마
class HealthCheckRequest(BaseModel):
    """종합 상태 체크 요청 스키마"""

    project_id: int
    check_http: bool = True
    check_ssl: bool = True
    check_tcp_ports: list[int] = Field(default_factory=list)
    check_dns: bool = True
    check_content: Optional[str] = None
    check_security_headers: bool = False


class HealthCheckResponse(BaseModel):
    """종합 상태 체크 응답 스키마"""

    project_id: int
    http_status: Optional[MonitoringStatus] = None
    ssl_status: Optional[SSLStatus] = None
    tcp_port_results: list[TCPPortCheckResponse] = Field(default_factory=list)
    dns_result: Optional[DNSLookupResponse] = None
    content_result: Optional[ContentCheckResponse] = None
    security_headers_result: Optional[SecurityHeadersResponse] = None
    overall_healthy: bool
    checked_at: datetime = Field(default_factory=datetime.now)


# Playwright 심층 체크 스키마
class PlaywrightPerformance(BaseModel):
    """Playwright 성능 메트릭"""
    dom_content_loaded: Optional[float] = None  # ms
    page_load_time: Optional[float] = None  # ms
    first_contentful_paint: Optional[float] = None  # ms
    largest_contentful_paint: Optional[float] = None  # ms
    time_to_first_byte: Optional[float] = None  # ms (TTFB)
    cumulative_layout_shift: Optional[float] = None  # CLS
    total_blocking_time: Optional[float] = None  # ms (TBT)


class PlaywrightHealth(BaseModel):
    """Playwright 건강 상태"""
    is_dom_ready: Optional[bool] = None
    is_js_healthy: Optional[bool] = None
    js_errors: list[str] = Field(default_factory=list)
    console_errors: int = 0


class PlaywrightResources(BaseModel):
    """Playwright 리소스 정보"""
    count: int = 0
    size: int = 0  # bytes
    failed: int = 0  # 실패한 리소스 개수


class PlaywrightNetwork(BaseModel):
    """Playwright 네트워크 정보"""
    redirect_count: int = 0


class PlaywrightMemory(BaseModel):
    """Playwright 메모리 정보"""
    js_heap_size: Optional[int] = None  # bytes


class PlaywrightCheckResponse(BaseModel):
    """Playwright 심층 체크 응답 스키마"""
    project_id: int
    url: str
    is_available: bool
    status_code: Optional[int] = None
    response_time: float = 0.0
    error_message: Optional[str] = None
    performance: PlaywrightPerformance = Field(default_factory=PlaywrightPerformance)
    health: PlaywrightHealth = Field(default_factory=PlaywrightHealth)
    resources: PlaywrightResources = Field(default_factory=PlaywrightResources)
    network: PlaywrightNetwork = Field(default_factory=PlaywrightNetwork)
    memory: PlaywrightMemory = Field(default_factory=PlaywrightMemory)
    checked_at: datetime = Field(default_factory=datetime.now)


# 스케줄러 상태 스키마
class SchedulerStatus(BaseModel):
    """스케줄러 상태 스키마"""
    is_running: bool
    active_projects: list[int] = Field(default_factory=list)
    project_count: int = 0
    consecutive_failures: dict[int, int] = Field(default_factory=dict)


class ProjectMonitoringStatus(BaseModel):
    """프로젝트 모니터링 상태 스키마"""
    project_id: int
    is_monitoring: bool
    consecutive_failures: int = 0


# 차트 데이터 스키마
class ChartDataPoint(BaseModel):
    """차트 데이터 포인트"""
    timestamp: datetime
    value: Optional[float] = None
    is_available: Optional[bool] = None


class ResponseTimeChartData(BaseModel):
    """응답 시간 차트 데이터"""
    project_id: int
    project_title: str
    data_points: list[ChartDataPoint] = Field(default_factory=list)
    avg_response_time: Optional[float] = None
    min_response_time: Optional[float] = None
    max_response_time: Optional[float] = None


class AvailabilityChartData(BaseModel):
    """가용성 차트 데이터"""
    project_id: int
    project_title: str
    total_checks: int = 0
    available_checks: int = 0
    availability_percentage: float = 0.0
    data_points: list[ChartDataPoint] = Field(default_factory=list)


class DashboardChartData(BaseModel):
    """대시보드 차트 데이터"""
    response_time: list[ResponseTimeChartData] = Field(default_factory=list)
    availability: list[AvailabilityChartData] = Field(default_factory=list)
    period_start: datetime
    period_end: datetime


# Uptime SLA 리포트 스키마
class SLAIncident(BaseModel):
    """SLA 장애 인시던트"""

    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: float  # 장애 지속 시간 (분)
    error_message: Optional[str] = None


class SLADailyEntry(BaseModel):
    """일별 SLA 데이터"""

    date: str  # YYYY-MM-DD
    total_checks: int = 0
    available_checks: int = 0
    uptime_percentage: float = 100.0
    avg_response_time: Optional[float] = None  # ms
    incidents_count: int = 0


class SLAMetrics(BaseModel):
    """SLA 핵심 지표"""

    target_uptime: float = 99.9  # SLA 목표 (%)
    achieved_uptime: float = 100.0  # 실제 달성 가용률 (%)
    sla_met: bool = True  # SLA 충족 여부
    total_checks: int = 0
    available_checks: int = 0
    failed_checks: int = 0
    total_downtime_minutes: float = 0.0  # 총 다운타임 (분)
    allowed_downtime_minutes: float = 0.0  # SLA 허용 다운타임 (분)
    incidents_count: int = 0
    avg_response_time: Optional[float] = None  # 평균 응답시간 (ms)
    max_response_time: Optional[float] = None  # 최대 응답시간 (ms)
    min_response_time: Optional[float] = None  # 최소 응답시간 (ms)
    p95_response_time: Optional[float] = None  # P95 응답시간 (ms)


class SLAReport(BaseModel):
    """Uptime SLA 리포트"""

    project_id: int
    project_title: str
    project_url: str
    period_start: datetime
    period_end: datetime
    period_days: int
    metrics: SLAMetrics
    daily_breakdown: list[SLADailyEntry] = Field(default_factory=list)
    incidents: list[SLAIncident] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


# 이상 탐지 스키마
class AnomalyDetail(BaseModel):
    """개별 이상 징후 상세"""

    type: str  # response_time_spike, availability_drop, error_rate_increase, pattern_change
    severity: str = "warning"  # info, warning, critical
    message: str
    detected_at: datetime
    metric_name: str  # 관련 메트릭 이름
    current_value: float  # 현재 값
    baseline_value: float  # 기준 값 (정상 범위)
    deviation_percent: float  # 편차 (%)


class AnomalyAnalysis(BaseModel):
    """이상 탐지 분석 결과"""

    project_id: int
    project_title: str
    analysis_period_hours: int
    baseline_period_hours: int
    total_anomalies: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    anomalies: list[AnomalyDetail] = Field(default_factory=list)
    baseline_stats: dict = Field(default_factory=dict)
    current_stats: dict = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.now)
