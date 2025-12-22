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
# 5. 모니터링 설정
# 6. 로깅 설정
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # 프로젝트 설정
    PROJECT_NAME: str = "Py_Monitor"
    # CORS 허용 도메인 목록
    # 개발 환경에서는 localhost를 허용하고, 운영 환경에서는 실제 도메인을 지정해야 합니다.
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # 데이터베이스 설정
    # PostgreSQL 데이터베이스 연결 정보
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # 보안 설정
    # JWT 토큰 관련 설정
    SECRET_KEY: str  # JWT 토큰 서명에 사용되는 비밀 키
    ALGORITHM: str = "HS256"  # JWT 토큰 서명 알고리즘
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 이메일 설정
    # SMTP 서버 설정
    SMTP_HOST: str  # SMTP 서버 호스트
    SMTP_PORT: int  # SMTP 서버 포트
    SMTP_USER: str  # SMTP 사용자 이름
    SMTP_PASSWORD: str  # SMTP 비밀번호
    SMTP_TLS: bool = True  # TLS 사용 여부
    SMTP_USERNAME: str  # 발신자 이름
    SMTP_FROM: str  # 발신자 이메일 주소
    
    # 모니터링 설정
    # 웹사이트 모니터링 관련 기본 설정
    DEFAULT_CHECK_INTERVAL: int = int(os.getenv("DEFAULT_CHECK_INTERVAL", "300"))  # 기본 체크 간격 (초)
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))  # 기본 타임아웃 (초)

    # 로깅 설정
    # 로그 관련 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")  # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")  # 로그 디렉토리
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 로그 파일 최대 크기 (10MB)
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # 로그 파일 백업 개수
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")  # 로그 포맷
    LOG_DATE_FORMAT: str = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")  # 로그 날짜 포맷

    API_V1_STR: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # PostgreSQL 연결 문자열 생성
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()
