"""
# Laravel 개발자를 위한 설명
# 이 파일은 애플리케이션 설정을 관리합니다.
# Laravel의 config 디렉토리와 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 환경 변수 로드
# 2. 데이터베이스 설정
# 3. 이메일 설정
# 4. 보안 설정
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # 데이터베이스 설정
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # 보안 설정
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 이메일 설정
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_TLS: bool = True
    SMTP_FROM: str
    
    # 모니터링 설정
    DEFAULT_CHECK_INTERVAL: int = int(os.getenv("DEFAULT_CHECK_INTERVAL", "300"))
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )

settings = Settings()
