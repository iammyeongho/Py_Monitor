"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 Project 모델과 유사한 역할을 합니다.
# Pydantic을 사용하여 프로젝트 관련 스키마를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. BaseModel = Laravel의 Model과 유사
# 2. Field = Laravel의 $fillable과 유사
# 3. Config = Laravel의 $casts와 유사
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from .base import BaseSchema


# 기본 Project 스키마
class ProjectBase(BaseModel):
    """프로젝트 기본 스키마"""

    host_name: Optional[str] = None
    ip_address: Optional[str] = None
    url: HttpUrl
    title: str
    description: Optional[str] = Field(None, max_length=500)
    status_interval: Optional[int] = Field(None, ge=1)
    expiry_d_day: Optional[int] = None
    expiry_interval: Optional[int] = Field(None, ge=1)
    time_limit: Optional[int] = Field(None, ge=1)
    time_limit_interval: Optional[int] = Field(None, ge=1)
    is_public: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=500)
    custom_headers: Optional[str] = Field(None, max_length=2000, description="커스텀 HTTP 헤더 (JSON 형식)")


# Project 생성 시 사용할 스키마
class ProjectCreate(ProjectBase):
    """프로젝트 생성 스키마"""

    pass


# Project 업데이트 시 사용할 스키마
class ProjectUpdate(ProjectBase):
    """프로젝트 업데이트 스키마"""

    pass


# 유지보수 모드 설정 스키마
class MaintenanceModeUpdate(BaseModel):
    """유지보수 모드 설정 스키마"""

    maintenance_mode: bool = Field(..., description="유지보수 모드 활성화 여부")
    maintenance_message: Optional[str] = Field(None, max_length=500, description="유지보수 안내 메시지")
    maintenance_ends_at: Optional[datetime] = Field(None, description="유지보수 종료 예정 시간")


# Project 응답 시 사용할 스키마
class Project(ProjectBase, BaseSchema):
    user_id: int
    open_date: Optional[datetime] = None
    snapshot_path: Optional[str] = None
    last_snapshot_at: Optional[datetime] = None
    status: bool = True
    is_active: bool = True
    deleted_at: Optional[datetime] = None
    # 유지보수 모드 필드
    maintenance_mode: bool = False
    maintenance_message: Optional[str] = None
    maintenance_started_at: Optional[datetime] = None
    maintenance_ends_at: Optional[datetime] = None
    # 커스텀 헤더
    custom_headers: Optional[str] = None


# Project 응답 시 사용할 스키마
class ProjectResponse(Project):
    """프로젝트 응답 스키마"""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 유지보수 모드 응답 스키마
class MaintenanceModeResponse(BaseModel):
    """유지보수 모드 응답 스키마"""

    id: int
    title: str
    maintenance_mode: bool
    maintenance_message: Optional[str] = None
    maintenance_started_at: Optional[datetime] = None
    maintenance_ends_at: Optional[datetime] = None

    class Config:
        from_attributes = True
