"""
# Laravel 개발자를 위한 설명
# 이 파일은 JWT 토큰 처리를 위한 스키마를 정의합니다.
# Laravel의 JWT 토큰 처리와 유사한 역할을 합니다.
"""

from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None  # user id 