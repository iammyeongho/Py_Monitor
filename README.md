# Py_Monitor

웹사이트 모니터링 시스템으로, 웹사이트의 가용성, SSL 인증서 상태, 도메인 만료일 등을 모니터링하고 알림을 제공합니다.

## 주요 기능

- 웹사이트 가용성 모니터링
- SSL 인증서 상태 확인
- 도메인 만료일 모니터링
- 이메일 알림
- 웹훅 알림
- 모니터링 로그 및 알림 관리
- 사용자 인증 및 권한 관리

## 기술 스택

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT
- aiohttp
- python-whois

## 설치 및 실행

1. 저장소 클론
```bash
git clone https://github.com/yourusername/Py_Monitor.git
cd Py_Monitor
```

2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정을 입력
```

5. 데이터베이스 설정
```bash
# PostgreSQL 데이터베이스 생성
createdb py_monitor

# 데이터베이스 마이그레이션
PYTHONPATH=$PYTHONPATH:. alembic upgrade head
```

6. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 환경 변수 설정

`.env` 파일에 다음 설정이 필요합니다:

```env
# 데이터베이스 설정
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=py_monitor
POSTGRES_PORT=5432

# 보안 설정
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days

# 이메일 설정
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_TLS=True
SMTP_USERNAME=Py Monitor
SMTP_FROM=your_email@gmail.com

# 모니터링 설정
DEFAULT_CHECK_INTERVAL=300  # 5분
DEFAULT_TIMEOUT=30  # 30초
```

## 모니터링 설정

각 프로젝트별로 다음 설정을 관리할 수 있습니다:

- 상태 체크 주기 (기본값: 300초)
- 응답 시간 제한 (기본값: 5초)
- 만료일 D-day (기본값: 30일)
- 알림 주기 설정
  - 상태 체크 실패 시 알림 주기
  - 만료일 알림 주기
  - 응답 시간 초과 시 알림 주기

## API 문서

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
Py_Monitor/
├── alembic/              # 데이터베이스 마이그레이션
├── app/
│   ├── api/             # API 엔드포인트
│   ├── core/            # 핵심 설정
│   ├── db/              # 데이터베이스 설정
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 스키마
│   ├── services/        # 비즈니스 로직
│   └── utils/           # 유틸리티 함수
├── frontend/
│   ├── html/           # HTML 파일
│   ├── js/             # JavaScript 모듈
│   └── style/          # 스타일시트
├── tests/
│   ├── test_api/       # API 테스트
│   ├── test_services/  # 서비스 테스트
│   ├── test_frontend/  # 프론트엔드 테스트
│   └── conftest.py     # 테스트 설정
├── .env                # 환경 변수
├── requirements.txt    # 의존성 목록
└── README.md          # 프로젝트 문서
```

## 테스트

테스트를 실행하려면 다음 명령어를 사용합니다:

```bash
pytest
```

## 라이선스

MIT License

## 프론트엔드 실행 및 접근 방법

- 프론트엔드(대시보드 등)는 반드시 FastAPI 서버를 통해 접근해야 합니다.
- 브라우저에서 아래 주소로 접속하세요:
  - http://localhost:8000/frontend/index.html
- **절대 file:// 경로로 직접 HTML 파일을 열지 마세요.** (CSS/JS가 동작하지 않음)

## 문제 해결

1. 데이터베이스 연결 오류
   - PostgreSQL 서버가 실행 중인지 확인
   - 데이터베이스 접속 정보가 올바른지 확인
   - 데이터베이스가 생성되어 있는지 확인

2. 이메일 알림 오류
   - SMTP 설정이 올바른지 확인
   - Gmail을 사용하는 경우 앱 비밀번호 설정 필요

3. 모니터링 실패
   - 대상 URL이 올바른지 확인
   - 방화벽 설정 확인
   - 네트워크 연결 상태 확인 