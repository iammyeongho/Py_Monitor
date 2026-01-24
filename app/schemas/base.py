from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BaseSchema(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # SQLAlchemy 모델과의 호환성을 위한 설정
