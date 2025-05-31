"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 관련 데이터 스키마를 정의합니다.
# Laravel의 Request/Resource 클래스와 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 요청 데이터 검증
# 2. 응답 데이터 구조화
# 3. 데이터 변환
"""

from typing import Optional
from datetime import datetime
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

class MonitoringSettingCreate(MonitoringSettingBase):
    pass

class MonitoringSettingUpdate(BaseModel):
    check_interval: Optional[int] = Field(None, ge=60, le=3600)
    timeout: Optional[int] = Field(None, ge=5, le=300)
    retry_count: Optional[int] = Field(None, ge=1, le=5)
    alert_threshold: Optional[int] = Field(None, ge=1, le=10)

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
    ssl_expiry: Optional[datetime] = None
    domain_expiry: Optional[datetime] = None

class SSLDomainStatusCreate(SSLDomainStatusBase):
    pass

class SSLDomainStatusResponse(SSLDomainStatusBase):
    id: int
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
