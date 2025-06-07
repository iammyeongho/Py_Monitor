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
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from .base import BaseSchema

# 기본 User 스키마
class UserBase(BaseModel):
    """사용자 기본 정보"""
    email: EmailStr
    full_name: Optional[str] = None
    status: bool = True

# User 생성 시 사용할 스키마
class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8)

# User 업데이트 시 사용할 스키마
class UserUpdate(UserBase):
    """사용자 업데이트 스키마"""
    password: Optional[str] = Field(None, min_length=8)

# User 응답 시 사용할 스키마
class User(UserBase, BaseSchema):
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
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
    username: Optional[str] = None

# User 응답 시 사용할 스키마
class UserResponse(User):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
