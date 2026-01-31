"""
의존성 주입 모듈

이 파일은 FastAPI의 의존성 주입 시스템을 활용하여 공통 의존성을 정의합니다.
Laravel의 Service Container와 유사한 역할을 합니다.

주요 의존성:
1. get_db - 데이터베이스 세션 주입
2. get_current_user - JWT 토큰에서 현재 사용자 추출
3. get_current_active_user - 활성화된 사용자만 허용
4. get_current_superuser - 관리자 권한 필요 시 사용
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import TokenData

# OAuth2 인증 스키마 설정
# tokenUrl은 로그인 엔드포인트 경로 (Swagger UI에서 사용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_db() -> Generator:
    """
    데이터베이스 세션 의존성

    각 요청마다 새로운 DB 세션을 생성하고, 요청 완료 후 자동으로 닫습니다.
    Laravel의 DB 파사드와 유사하지만, 명시적인 세션 관리가 필요합니다.

    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    현재 인증된 사용자 가져오기

    Authorization 헤더의 Bearer 토큰을 검증하고 해당 사용자를 반환합니다.
    Laravel의 Auth::user()와 유사한 역할을 합니다.

    Args:
        db: 데이터베이스 세션 (자동 주입)
        token: JWT 토큰 (Authorization 헤더에서 자동 추출)

    Returns:
        User: 인증된 사용자 객체

    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자를 찾을 수 없는 경우
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # JWT 토큰 디코딩 및 검증
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # 토큰의 sub 클레임에서 이메일 추출
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    현재 활성화된 사용자 가져오기

    인증된 사용자 중 is_active=True인 사용자만 허용합니다.
    비활성화된 계정은 접근이 차단됩니다.

    Args:
        current_user: 인증된 사용자 (자동 주입)

    Returns:
        User: 활성화된 사용자 객체

    Raises:
        HTTPException: 사용자가 비활성화된 경우 (400)
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    현재 superuser인 사용자 가져오기

    관리자 권한이 필요한 엔드포인트에서 사용합니다.
    Laravel의 Gate::allows('admin')와 유사한 역할입니다.

    Args:
        current_user: 인증된 사용자 (자동 주입)

    Returns:
        User: 관리자 권한을 가진 사용자 객체

    Raises:
        HTTPException: 관리자 권한이 없는 경우 (400)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    관리자 역할 사용자 가져오기 (role=admin 또는 is_superuser)

    사용자 관리, 시스템 설정 등 관리자 전용 엔드포인트에서 사용합니다.
    """
    if not (current_user.is_superuser or current_user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다",
        )
    return current_user


async def get_current_manager_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    매니저 이상 역할 사용자 가져오기 (role=manager, admin 또는 is_superuser)

    프로젝트 관리 등 쓰기 권한이 필요한 엔드포인트에서 사용합니다.
    """
    allowed_roles = ("admin", "manager")
    if not (current_user.is_superuser or current_user.role in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="매니저 이상 권한이 필요합니다",
        )
    return current_user


async def get_non_viewer_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    뷰어가 아닌 사용자 (role != viewer)

    프로젝트 생성/수정/삭제 등 쓰기 작업에서 사용합니다.
    viewer 역할은 읽기만 가능합니다.
    """
    if current_user.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="읽기 전용 계정은 이 작업을 수행할 수 없습니다",
        )
    return current_user
