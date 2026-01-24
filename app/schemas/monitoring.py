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
    status: bool
    response_time: Optional[float] = None
    http_code: Optional[int] = None
    error_message: Optional[str] = None


class MonitoringLogCreate(MonitoringLogBase):
    pass


class MonitoringLogResponse(MonitoringLogBase):
    id: int
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


class MonitoringSettingResponse(MonitoringSettingBase):
    id: int
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
