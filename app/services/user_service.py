"""
# Laravel 개발자를 위한 설명
# 이 파일은 사용자 관련 비즈니스 로직을 구현합니다.
# Laravel의 UserService와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 사용자 CRUD
# 2. 인증 관리
# 3. 권한 관리
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserCreate) -> User:
        """사용자 생성"""
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            is_active=True,
            is_superuser=user.is_superuser,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user(self, user_id: int) -> Optional[User]:
        """사용자 조회"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """사용자 목록 조회"""
        return (
            self.db.query(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_user(self, user_id: int, user: UserUpdate) -> Optional[User]:
        """사용자 정보 업데이트"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None

        update_data = user.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = pwd_context.hash(
                update_data.pop("password")
            )

        for key, value in update_data.items():
            setattr(db_user, key, value)

        db_user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def delete_user(self, user_id: int) -> bool:
        """사용자 삭제"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False

        db_user.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """사용자 인증"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user

    def toggle_user_status(self, user_id: int) -> Optional[User]:
        """사용자 활성화/비활성화"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None

        db_user.is_active = not db_user.is_active
        db_user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
