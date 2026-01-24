"""
환경별 설정을 관리하는 모듈
개발, 테스트, 운영 환경에 따른 설정을 분리하여 관리합니다.

# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 config/app.php와 유사한 역할을 합니다.
# pydantic-settings를 사용하여 환경 변수를 자동으로 로드합니다.
#
# Pydantic v2에서는 Field(env=...)가 deprecated되었습니다.
# 대신 필드명이 환경 변수명과 자동으로 매핑됩니다.
# 예: POSTGRES_SERVER 필드 → POSTGRES_SERVER 환경 변수
"""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정

    pydantic-settings는 필드명을 대문자로 변환하여 환경 변수와 매핑합니다.
    예: database_url → DATABASE_URL 환경 변수
    """

    # 환경 설정
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # 데이터베이스 설정
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "py_monitor"
    POSTGRES_PORT: int = 5432

    # Redis 설정
    REDIS_URL: Optional[str] = None

    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 이메일 설정
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_USERNAME: str = "Py Monitor"
    SMTP_FROM: Optional[str] = None

    # 모니터링 설정
    DEFAULT_CHECK_INTERVAL: int = 300
    DEFAULT_TIMEOUT: int = 30

    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Py_Monitor"

    # CORS 설정
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Pydantic v2 설정 (ConfigDict 사용)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 정의되지 않은 환경 변수 무시
    )


# 환경별 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스를 반환합니다."""
    return settings


# 환경별 설정 함수들
def is_development() -> bool:
    """개발 환경인지 확인합니다."""
    return settings.ENVIRONMENT == "development"


def is_production() -> bool:
    """운영 환경인지 확인합니다."""
    return settings.ENVIRONMENT == "production"


def is_testing() -> bool:
    """테스트 환경인지 확인합니다."""
    return settings.ENVIRONMENT == "testing"
