"""
테스트 설정 및 fixture 정의

# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 TestCase 설정과 유사한 역할을 합니다.
# pytest의 fixture를 사용하여 테스트 환경을 설정합니다.
#
# 핵심: 트랜잭션 롤백 패턴
# 각 테스트는 트랜잭션 안에서 실행되며, 테스트 종료 시 자동 롤백됩니다.
# 이렇게 하면 테스트 데이터가 프로덕션 DB에 남지 않습니다.
# Laravel의 RefreshDatabase 트레이트와 유사한 동작입니다.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.db.base_class import Base
from app.core.deps import get_db as deps_get_db
from app.db.session import get_db as session_get_db
# 모든 모델 import하여 Base.metadata에 테이블 등록
from app.models.user import User
from app.models.project import Project  # noqa: F401
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.ssl_domain import SSLDomainStatus  # noqa: F401
from main import app

# 테스트용 데이터베이스 URL (프로덕션 DB 사용하되, 트랜잭션 롤백으로 데이터 보호)
TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

# 테스트용 엔진 생성
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """테스트용 데이터베이스 세션 (commit → flush 패치 + 트랜잭션 롤백)

    커넥션 레벨에서 트랜잭션을 시작하고, session.commit()을 session.flush()로 패치합니다.
    엔드포인트에서 db.commit()을 호출해도 실제로는 flush()만 실행되어
    데이터가 DB에 반영되지 않고, 테스트 종료 시 트랜잭션 롤백으로 정리됩니다.
    Laravel의 RefreshDatabase 트레이트와 유사한 동작입니다.
    """
    # 테이블이 없으면 생성 (최초 1회)
    Base.metadata.create_all(bind=engine)

    # 커넥션 레벨에서 트랜잭션 시작
    connection = engine.connect()
    transaction = connection.begin()

    # 이 커넥션 위에 세션을 바인딩
    session = TestingSessionLocal(bind=connection)

    # commit()을 flush()로 패치하여 실제 커밋 방지
    # flush()는 SQL을 실행하되 트랜잭션은 유지하므로 데이터 조회 가능
    session.commit = session.flush

    try:
        yield session
    finally:
        session.close()
        # 테스트 종료 시 외부 트랜잭션 롤백 → 테스트 데이터가 DB에 남지 않음
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db):
    """테스트용 FastAPI 클라이언트"""

    def override_get_db():
        try:
            yield db
        finally:
            pass  # db.close()는 db fixture에서 처리

    # deps.get_db와 session.get_db 모두 override (엔드포인트마다 import 경로가 다름)
    app.dependency_overrides[deps_get_db] = override_get_db
    app.dependency_overrides[session_get_db] = override_get_db
    with TestClient(app) as test_client:
        # Rate Limiter 상태 초기화 (테스트 간 429 방지)
        _reset_rate_limiter(app)
        yield test_client
    app.dependency_overrides.clear()


def _reset_rate_limiter(application):
    """Rate limiter 내부 상태 초기화"""
    try:
        current = application.middleware_stack
        while current:
            if hasattr(current, "_requests"):
                current._requests.clear()
                break
            current = getattr(current, "app", None)
    except Exception:
        pass


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
        role="user",
    )
    db.add(user)
    db.flush()  # commit 대신 flush 사용 (트랜잭션 안에서 ID 할당)
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
        role="admin",
    )
    db.add(user)
    db.flush()  # commit 대신 flush 사용
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
