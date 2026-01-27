"""
사용자 서비스

사용자 관련 비즈니스 로직을 구현합니다.
Laravel의 UserService와 유사한 역할을 합니다.

클린 아키텍처:
- Application Layer에 위치
- Repository를 통해 데이터 접근
- 비즈니스 규칙 적용
- 커스텀 예외 발생

주요 기능:
1. 사용자 CRUD
2. 인증 관리
3. 권한 관리
"""

from typing import List, Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
)
from app.models.user import User
from app.repositories import UserRepository
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """사용자 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def create_user(self, user: UserCreate) -> User:
        """
        사용자 생성

        Args:
            user: 생성할 사용자 정보

        Returns:
            생성된 사용자

        Raises:
            ConflictError: 이메일이 이미 존재하는 경우
        """
        # 이메일 중복 검사
        if self.repository.email_exists(user.email):
            raise ConflictError("이미 등록된 이메일입니다", field="email")

        # 비밀번호 해싱
        hashed_password = pwd_context.hash(user.password)

        # 사용자 데이터 준비
        user_data = {
            "email": user.email,
            "hashed_password": hashed_password,
            "full_name": user.full_name,
            "profile_image": user.profile_image,
            "phone": user.phone,
            "email_notifications": user.email_notifications,
            "is_active": True,
        }

        return self.repository.create(user_data)

    def get_user(self, user_id: int) -> User:
        """
        사용자 조회

        Args:
            user_id: 사용자 ID

        Returns:
            조회된 사용자

        Raises:
            NotFoundError: 사용자를 찾을 수 없는 경우
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회

        Args:
            email: 사용자 이메일

        Returns:
            조회된 사용자 또는 None
        """
        return self.repository.get_by_email(email)

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        사용자 목록 조회

        Args:
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            사용자 목록
        """
        return self.repository.get_active_users(skip=skip, limit=limit)

    def update_user(self, user_id: int, user: UserUpdate) -> User:
        """
        사용자 정보 업데이트

        Args:
            user_id: 사용자 ID
            user: 업데이트할 정보

        Returns:
            업데이트된 사용자

        Raises:
            NotFoundError: 사용자를 찾을 수 없는 경우
        """
        db_user = self.repository.get_by_id(user_id)
        if not db_user:
            raise NotFoundError("User", user_id)

        update_data = user.dict(exclude_unset=True)

        # 비밀번호가 포함된 경우 해싱
        if "password" in update_data:
            update_data["hashed_password"] = pwd_context.hash(
                update_data.pop("password")
            )

        return self.repository.update(db_user, update_data)

    def delete_user(self, user_id: int) -> bool:
        """
        사용자 삭제 (소프트 삭제)

        Args:
            user_id: 사용자 ID

        Returns:
            삭제 성공 여부

        Raises:
            NotFoundError: 사용자를 찾을 수 없는 경우
        """
        if not self.repository.exists(user_id):
            raise NotFoundError("User", user_id)

        return self.repository.soft_delete(user_id)

    def authenticate_user(self, email: str, password: str) -> User:
        """
        사용자 인증

        Args:
            email: 사용자 이메일
            password: 비밀번호

        Returns:
            인증된 사용자

        Raises:
            AuthenticationError: 인증 실패 시
        """
        user = self.repository.get_by_email(email)

        if not user:
            raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

        if not pwd_context.verify(password, user.hashed_password):
            raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")

        if not user.is_active:
            raise AuthenticationError("비활성화된 계정입니다")

        # 마지막 로그인 시간 업데이트
        self.repository.update_last_login(user.id)

        return user

    def toggle_user_status(self, user_id: int) -> User:
        """
        사용자 활성화/비활성화 토글

        Args:
            user_id: 사용자 ID

        Returns:
            업데이트된 사용자

        Raises:
            NotFoundError: 사용자를 찾을 수 없는 경우
        """
        user = self.repository.toggle_active_status(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        비밀번호 검증

        Args:
            plain_password: 평문 비밀번호
            hashed_password: 해싱된 비밀번호

        Returns:
            검증 결과
        """
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """
        비밀번호 해싱

        Args:
            password: 평문 비밀번호

        Returns:
            해싱된 비밀번호
        """
        return pwd_context.hash(password)
