"""
데이터베이스 세션 설정 모듈

이 파일은 SQLAlchemy를 사용하여 데이터베이스 연결과 세션을 관리합니다.
Laravel의 database.php 설정 파일과 DB 파사드의 역할을 합니다.

주요 구성요소:
1. engine - 데이터베이스 연결 엔진 (커넥션 풀 관리)
2. SessionLocal - 세션 팩토리 (각 요청마다 새 세션 생성)
3. get_db - FastAPI 의존성 주입용 제너레이터

Laravel과의 차이점:
- Laravel은 자동으로 커넥션을 관리하지만, SQLAlchemy는 명시적 세션 관리 필요
- pool_pre_ping=True는 커넥션 유효성 검사 (Laravel의 reconnect와 유사)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# 데이터베이스 엔진 생성
# pool_pre_ping: 쿼리 전 커넥션 상태 확인 (끊어진 연결 자동 재연결)
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

# 세션 팩토리 생성
# autocommit=False: 명시적 commit() 필요 (Laravel의 트랜잭션과 유사)
# autoflush=False: 명시적 flush() 필요 (성능 최적화)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (SQLAlchemy 2.0 스타일)
# 모든 모델은 이 Base를 상속받아 정의
Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 의존성 (FastAPI Depends에서 사용)

    각 요청마다 새로운 세션을 생성하고, 요청 완료 후 자동으로 닫습니다.
    Laravel의 request lifecycle과 유사한 패턴입니다.

    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
