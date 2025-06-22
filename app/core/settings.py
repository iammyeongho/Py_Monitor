"""
환경별 설정을 관리하는 모듈
개발, 테스트, 운영 환경에 따른 설정을 분리하여 관리합니다.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 환경 설정
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # 데이터베이스 설정
    DATABASE_URL: str = Field(env="DATABASE_URL")
    POSTGRES_SERVER: str = Field(default="localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="password", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="py_monitor", env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # Redis 설정
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # 보안 설정
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 이메일 설정
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_USERNAME: str = Field(default="Py Monitor", env="SMTP_USERNAME")
    SMTP_FROM: Optional[str] = Field(default=None, env="SMTP_FROM")
    
    # 모니터링 설정
    DEFAULT_CHECK_INTERVAL: int = Field(default=300, env="DEFAULT_CHECK_INTERVAL")
    DEFAULT_TIMEOUT: int = Field(default=30, env="DEFAULT_TIMEOUT")
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Py_Monitor"
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: list = Field(default=["*"], env="BACKEND_CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


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