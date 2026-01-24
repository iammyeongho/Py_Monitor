"""
알림(Notification) 스키마

이 파일은 알림 관련 Pydantic 스키마를 정의합니다.
Laravel의 Notification 리소스와 유사한 역할을 합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# 알림 기본 스키마
class NotificationBase(BaseModel):
    project_id: int
    type: str  # email, webhook 등
    title: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical
    recipient: str
    message: str


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = None
    is_sent: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: int
    is_read: bool = False
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
