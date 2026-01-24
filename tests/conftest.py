"""
테스트 설정 및 fixture 정의

# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 TestCase 설정과 유사한 역할을 합니다.
# pytest의 fixture를 사용하여 테스트 환경을 설정합니다.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from main import app

# 테스트용 데이터베이스 URL (PostgreSQL py_monitor 스키마 사용)
TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# 테스트용 엔진 생성
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """테스트용 데이터베이스 세션"""
    # 테스트 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 테스트용 세션 생성
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 테스트 후 테이블 삭제는 하지 않음 (실제 DB 사용)


@pytest.fixture(scope="function")
def client(db):
    """테스트용 FastAPI 클라이언트"""

    def override_get_db():
        try:
            yield db
        finally:
            pass  # db.close()는 db fixture에서 처리

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db) -> User:
    """테스트용 사용자 생성"""
    import uuid

    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    user = User(
        email=unique_email,
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_superuser(db) -> User:
    """테스트용 슈퍼유저 생성"""
    import uuid

    unique_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"

    user = User(
        email=unique_email,
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(test_user) -> str:
    """테스트용 인증 토큰"""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture(scope="function")
def auth_headers(auth_token) -> dict:
    """테스트용 인증 헤더"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def superuser_token(test_superuser) -> str:
    """테스트용 슈퍼유저 인증 토큰"""
    return create_access_token(data={"sub": test_superuser.email})


@pytest.fixture(scope="function")
def superuser_headers(superuser_token) -> dict:
    """테스트용 슈퍼유저 인증 헤더"""
    return {"Authorization": f"Bearer {superuser_token}"}
