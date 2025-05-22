from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl
from .base import BaseSchema

# 기본 Project 스키마
class ProjectBase(BaseModel):
    host_name: Optional[str] = None
    ip_address: Optional[str] = None
    url: Optional[HttpUrl] = None
    title: str
    status: bool = True
    status_interval: Optional[int] = None
    expiry_d_day: Optional[int] = None
    expiry_interval: Optional[int] = None
    time_limit: Optional[int] = None
    time_limit_interval: Optional[int] = None

# Project 생성 시 사용할 스키마
class ProjectCreate(ProjectBase):
    pass

# Project 업데이트 시 사용할 스키마
class ProjectUpdate(BaseModel):
    host_name: Optional[str] = None
    ip_address: Optional[str] = None
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    status: Optional[bool] = None
    status_interval: Optional[int] = None
    expiry_d_day: Optional[int] = None
    expiry_interval: Optional[int] = None
    time_limit: Optional[int] = None
    time_limit_interval: Optional[int] = None

# Project 응답 시 사용할 스키마
class Project(ProjectBase, BaseSchema):
    user_id: int
    open_date: Optional[datetime] = None
    snapshot_path: Optional[str] = None
    last_snapshot_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
