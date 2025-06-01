from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from .base import BaseSchema

# 기본 User 스키마
class UserBase(BaseModel):
    email: EmailStr
    status: bool = True

# User 생성 시 사용할 스키마
class UserCreate(UserBase):
    password: str

# User 업데이트 시 사용할 스키마
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    status: Optional[bool] = None

# User 응답 시 사용할 스키마
class User(UserBase, BaseSchema):
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    deleted_at: Optional[datetime] = None

# User 로그인 시 사용할 스키마
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# User 토큰 스키마
class Token(BaseModel):
    access_token: str
    token_type: str

# User 토큰 데이터 스키마
class TokenData(BaseModel):
    email: Optional[str] = None
