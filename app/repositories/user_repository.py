"""
사용자 Repository

사용자(User) 엔티티에 대한 데이터 접근 로직을 캡슐화합니다.
Laravel의 User Repository 패턴과 유사합니다.

주요 기능:
- 사용자 CRUD
- 이메일로 사용자 조회
- 활성 사용자 조회
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """사용자 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회

        Args:
            email: 사용자 이메일

        Returns:
            조회된 사용자 또는 None
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        활성 사용자 목록 조회

        Args:
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            활성 사용자 목록
        """
        return (
            self.db.query(User)
            .filter(User.is_active == True)  # noqa: E712
            .filter(User.deleted_at.is_(None))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def email_exists(self, email: str) -> bool:
        """
        이메일 존재 여부 확인

        Args:
            email: 확인할 이메일

        Returns:
            존재 여부
        """
        return self.db.query(User).filter(User.email == email).first() is not None

    def update_last_login(self, user_id: int) -> Optional[User]:
        """
        마지막 로그인 시간 업데이트

        Args:
            user_id: 사용자 ID

        Returns:
            업데이트된 사용자 또는 None
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.last_login_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def toggle_active_status(self, user_id: int) -> Optional[User]:
        """
        사용자 활성화 상태 토글

        Args:
            user_id: 사용자 ID

        Returns:
            업데이트된 사용자 또는 None
        """
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_users_with_email_notifications(self) -> List[User]:
        """
        이메일 알림이 활성화된 사용자 목록 조회

        Returns:
            이메일 알림 활성화된 사용자 목록
        """
        return (
            self.db.query(User)
            .filter(User.is_active == True)  # noqa: E712
            .filter(User.email_notifications == True)  # noqa: E712
            .filter(User.deleted_at.is_(None))
            .all()
        )
