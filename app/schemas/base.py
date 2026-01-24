"""
기본 스키마 정의

이 파일은 모든 스키마의 공통 기반 클래스를 정의합니다.
id, created_at, updated_at 등 공통 필드를 포함합니다.

Laravel의 Model 트레이트와 유사한 역할을 합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """모든 스키마의 기본 클래스"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # SQLAlchemy 모델과의 호환성을 위한 설정
