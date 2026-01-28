"""
기본 스키마 정의

이 파일은 모든 스키마의 공통 기반 클래스를 정의합니다.
id, created_at, updated_at 등 공통 필드를 포함합니다.

Laravel의 Model 트레이트와 유사한 역할을 합니다.
"""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """모든 스키마의 기본 클래스"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # SQLAlchemy 모델과의 호환성을 위한 설정


# 제네릭 타입 변수
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 (모바일 최적화)"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def skip(self) -> int:
        """offset 계산"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """limit 반환"""
        return self.page_size


class MobileProjectSummary(BaseModel):
    """모바일용 프로젝트 간략 정보"""
    id: int
    title: str
    url: str
    is_available: Optional[bool] = None
    availability_percentage: Optional[float] = None
    last_response_time: Optional[float] = None
    last_checked_at: Optional[datetime] = None
    has_unresolved_alerts: bool = False

    class Config:
        from_attributes = True
