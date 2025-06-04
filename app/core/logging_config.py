"""
애플리케이션의 로깅 설정을 관리하는 모듈입니다.
이 모듈은 다음과 같은 기능을 제공합니다:
1. 로그 파일의 자동 생성 및 관리
2. 로그 레벨 설정
3. 로그 포맷 설정
4. 로그 파일의 자동 순환 (최대 10MB, 최대 5개 백업 파일)
"""

import logging
from logging.handlers import RotatingFileHandler
import os

# 로그 디렉토리 설정
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 로그 파일 경로 설정
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# 로깅 기본 설정
# - 로그 레벨: INFO
# - 로그 포맷: 시간 [로그레벨] 모듈명: 메시지
# - 핸들러: 
#   1. RotatingFileHandler: 로그 파일 자동 순환
#   2. StreamHandler: 콘솔 출력
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"),
        logging.StreamHandler()
    ]
) 