"""
애플리케이션의 로깅 설정을 관리하는 모듈입니다.
이 모듈은 다음과 같은 기능을 제공합니다:
1. 로그 파일의 자동 생성 및 관리
2. 로그 레벨 설정 (환경 변수로 제어)
3. 로그 포맷 설정
4. 로그 파일의 자동 순환 (최대 10MB, 최대 5개 백업 파일)
5. 로그 필터링 및 포맷팅
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from app.core.config import settings

# 로그 디렉토리 설정
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 로그 파일 경로 설정
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# 로그 레벨 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 로그 포맷 설정
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 로그 필터 설정
class RequestFilter(logging.Filter):
    """요청 관련 로그 필터"""
    def filter(self, record):
        return not record.getMessage().startswith("Request:")

class ResponseFilter(logging.Filter):
    """응답 관련 로그 필터"""
    def filter(self, record):
        return not record.getMessage().startswith("Response:")

# 로깅 기본 설정
logging.basicConfig(
    level=LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

# 로그 필터 적용
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.addFilter(RequestFilter())
        handler.addFilter(ResponseFilter())

# 로거 설정
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized with level: {LOG_LEVEL}") 