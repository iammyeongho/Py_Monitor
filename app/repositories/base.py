"""
Repository 베이스 클래스

이 파일은 모든 Repository의 공통 기능을 정의합니다.
Laravel의 Eloquent ORM과 유사한 인터페이스를 제공하면서,
데이터 접근 로직을 Service 계층과 분리합니다.

클린 아키텍처 원칙:
- Repository는 Infrastructure Layer에 위치
- Domain Layer(Model)와 Application Layer(Service) 사이의 인터페이스 역할
- 데이터베이스 구현 세부사항을 캡슐화
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from app.db.base_class import Base

# 제네릭 타입 변수 (모델 타입)
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(ABC, Generic[ModelType]):
    """
    추상 Repository 베이스 클래스

    모든 Repository가 구현해야 하는 공통 인터페이스를 정의합니다.
    CRUD 작업의 기본 메서드를 제공합니다.
    """

    def __init__(self, db: Session, model: type[ModelType]):
        """
        Repository 초기화

        Args:
            db: SQLAlchemy 세션
            model: ORM 모델 클래스
        """
        self.db = db
        self.model = model

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        ID로 엔티티 조회

        Args:
            id: 엔티티 ID

        Returns:
            조회된 엔티티 또는 None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        """
        모든 엔티티 조회 (페이지네이션)

        Args:
            skip: 건너뛸 개수
            limit: 최대 조회 개수
            order_by: 정렬 기준

        Returns:
            엔티티 목록
        """
        query = self.db.query(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        """
        새 엔티티 생성

        Args:
            obj_in: 생성할 데이터 딕셔너리

        Returns:
            생성된 엔티티
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """
        엔티티 업데이트

        Args:
            db_obj: 업데이트할 엔티티
            obj_in: 업데이트 데이터 딕셔너리

        Returns:
            업데이트된 엔티티
        """
        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        if hasattr(db_obj, "updated_at"):
            db_obj.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """
        엔티티 삭제 (하드 삭제)

        Args:
            id: 삭제할 엔티티 ID

        Returns:
            삭제 성공 여부
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def soft_delete(self, id: int) -> bool:
        """
        엔티티 소프트 삭제 (deleted_at 설정)

        Args:
            id: 삭제할 엔티티 ID

        Returns:
            삭제 성공 여부
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False

        if hasattr(db_obj, "deleted_at"):
            db_obj.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def exists(self, id: int) -> bool:
        """
        엔티티 존재 여부 확인

        Args:
            id: 엔티티 ID

        Returns:
            존재 여부
        """
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

    def count(self) -> int:
        """
        전체 엔티티 개수 조회

        Returns:
            엔티티 개수
        """
        return self.db.query(self.model).count()
