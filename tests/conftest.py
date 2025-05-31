import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
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
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
