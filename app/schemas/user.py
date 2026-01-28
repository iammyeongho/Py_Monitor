"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 User 모델과 유사한 역할을 합니다.
# Pydantic을 사용하여 사용자 관련 스키마를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. BaseModel = Laravel의 Model과 유사
# 2. Field = Laravel의 $fillable과 유사
# 3. Config = Laravel의 $casts와 유사
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from .base import BaseSchema


# 테마 옵션
THEME_OPTIONS = ["light", "dark", "system"]
LANGUAGE_OPTIONS = ["ko", "en"]


# 기본 User 스키마
class UserBase(BaseModel):
    """사용자 기본 정보"""

    email: EmailStr
    full_name: Optional[str] = None
    profile_image: Optional[str] = None
    phone: Optional[str] = None
    email_notifications: Optional[bool] = True
    theme: Optional[str] = "light"
    language: Optional[str] = "ko"
    timezone: Optional[str] = "Asia/Seoul"


# User 생성 시 사용할 스키마
class UserCreate(UserBase):
    """사용자 생성 요청"""

    password: str = Field(..., min_length=8)


# User 업데이트 시 사용할 스키마
class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""

    full_name: Optional[str] = None
    profile_image: Optional[str] = None
    phone: Optional[str] = None
    email_notifications: Optional[bool] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


# 사용자 설정 스키마
class UserSettings(BaseModel):
    """사용자 설정 스키마"""

    theme: str = "light"
    language: str = "ko"
    timezone: str = "Asia/Seoul"
    email_notifications: bool = True

    class Config:
        from_attributes = True


# 사용자 설정 업데이트 스키마
class UserSettingsUpdate(BaseModel):
    """사용자 설정 업데이트 스키마"""

    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None


# User 응답 시 사용할 스키마
class User(UserBase, BaseSchema):
    is_active: bool = True
    is_superuser: bool = False
    last_login_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# User 로그인 시 사용할 스키마
class UserLogin(BaseModel):
    """사용자 로그인 스키마"""

    email: EmailStr
    password: str


# User 토큰 스키마
class Token(BaseModel):
    """토큰 스키마"""

    access_token: str
    token_type: str = "bearer"


# User 토큰 데이터 스키마
class TokenData(BaseModel):
    """토큰 데이터"""

    email: Optional[str] = None  # JWT 페이로드의 sub 필드에서 추출한 이메일


# User 응답 시 사용할 스키마
class UserResponse(User):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
