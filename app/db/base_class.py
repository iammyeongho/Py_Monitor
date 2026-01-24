"""
# Laravel 개발자를 위한 설명
# 이 파일은 SQLAlchemy의 Base 클래스를 정의합니다.
# Laravel의 Model 클래스와 유사한 역할을 합니다.
"""

from typing import Any
from sqlalchemy.orm import as_declarative, declared_attr


@as_declarative()
class Base:
    id: Any
    __name__: str

    # 테이블 이름 자동 생성
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
