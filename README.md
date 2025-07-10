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
- 실시간 대시보드
- 프로젝트별 모니터링 설정

## 기술 스택

### 백엔드
- **FastAPI** - 웹 프레임워크
- **SQLAlchemy** - ORM
- **PostgreSQL** - 데이터베이스
- **Alembic** - 데이터베이스 마이그레이션
- **JWT** - 인증 토큰
- **aiohttp** - 비동기 HTTP 클라이언트
- **python-whois** - 도메인 정보 조회
- **Redis** - 캐싱 및 세션 관리
- **uvicorn** - ASGI 서버

### 프론트엔드
- **HTML5/CSS3** - 마크업 및 스타일링
- **JavaScript (ES6+)** - 클라이언트 사이드 로직
- **Fetch API** - HTTP 요청

### 인프라
- **Docker** - 컨테이너화
- **Docker Compose** - 멀티 컨테이너 관리

## 의존성 설치

### Python 의존성

```bash
# requirements.txt에 포함된 주요 패키지들
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
aiohttp>=3.9.0
python-whois>=0.8.0
redis>=5.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

### 시스템 의존성

```bash
# macOS
brew install postgresql redis

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib redis-server

# CentOS/RHEL
sudo yum install postgresql postgresql-server redis
```

## 빠른 시작

### 1. 저장소 클론 및 환경 설정

```bash
# 저장소 클론
git clone https://github.com/iammyeongho/Py_Monitor.git
cd Py_Monitor

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# 환경 변수 파일 복사
cp .env.example .env

# .env 파일 편집 (아래 설정 참고)
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 서버 시작
sudo systemctl start postgresql  # Linux
brew services start postgresql    # macOS

# 데이터베이스 생성
createdb py_monitor

# 마이그레이션 실행
alembic upgrade head
```

### 4. 서버 실행

```bash
# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 Makefile 사용
make dev
```

### 5. 접속 확인

브라우저에서 다음 URL로 접속:
- **메인 대시보드**: http://localhost:8000/
- **로그인 페이지**: http://localhost:8000/login.html
- **회원가입 페이지**: http://localhost:8000/register.html
- **프로젝트 등록**: http://localhost:8000/project.html
- **API 문서**: http://localhost:8000/docs

## Docker를 사용한 실행 (권장)

```bash
# Docker Compose로 서비스 시작
make docker-up

# 또는 직접 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 최근 업데이트 (2025-06-29)

### ✅ 해결된 문제들

1. **정적 파일 서빙 문제**
   - `/frontend/login.html` 등에서 "Not Found" 오류 해결
   - `main.py`에 `frontend/html` 디렉토리 직접 마운트 추가
   - 이제 `/login.html`, `/index.html` 등이 정상 접근 가능

2. **회원가입 405 오류**
   - `/api/v1/auth/register` 엔드포인트 추가
   - `users.py`에 `register_user` 함수 구현
   - 프론트엔드 리다이렉트 경로 수정

3. **루트 경로 리다이렉트**
   - `/` → `/index.html`로 단순화
   - 기존 `/frontend/html/index.html`에서 변경

### 🔧 수정된 파일들

- `main.py` - 정적 파일 마운트 및 루트 리다이렉트
- `app/api/v1/endpoints/users.py` - 회원가입 엔드포인트 추가
- `frontend/js/auth.js` - 리다이렉트 경로 수정

## Makefile 명령어

```bash
make help          # 사용 가능한 명령어 확인
make install       # 의존성 설치
make test          # 테스트 실행
make run           # 프로덕션 서버 실행
make dev           # 개발 서버 실행
make docker-build  # Docker 이미지 빌드
make docker-up     # Docker Compose로 서비스 시작
make docker-down   # Docker Compose로 서비스 중지
make clean         # 캐시 및 임시 파일 정리
make migrate       # 데이터베이스 마이그레이션
make lint          # 코드 린팅
make format        # 코드 포맷팅
```

## 환경 변수 설정

`.env` 파일에 다음 설정이 필요합니다:

```env
# 환경 설정
ENVIRONMENT=development
DEBUG=true

# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:password@localhost:5432/py_monitor
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=py_monitor
POSTGRES_PORT=5432

# Redis 설정 (선택사항)
REDIS_URL=redis://localhost:6379

# 보안 설정
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

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

# 로깅 설정
LOG_LEVEL=INFO
LOG_DIR=logs
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
│   │   └── v1/
│   │       ├── endpoints/  # 사용자, 프로젝트, 모니터링 엔드포인트
│   │       └── router.py   # API 라우터 설정
│   ├── core/            # 핵심 설정
│   ├── db/              # 데이터베이스 설정
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 스키마
│   ├── services/        # 비즈니스 로직
│   └── utils/           # 유틸리티 함수
├── frontend/
│   ├── html/           # HTML 파일 (index.html, login.html, register.html, project.html)
│   ├── js/             # JavaScript 모듈 (auth.js, project.js, monitoring.js)
│   └── style/          # 스타일시트
├── tests/
│   ├── test_api/       # API 테스트
│   ├── test_services/  # 서비스 테스트
│   ├── test_frontend/  # 프론트엔드 테스트
│   └── conftest.py     # 테스트 설정
├── docs/               # 문서
├── scripts/            # 스크립트
├── logs/               # 로그 파일
├── .env                # 환경 변수
├── requirements.txt    # 의존성 목록
├── Dockerfile          # Docker 이미지 설정
├── docker-compose.yml  # Docker Compose 설정
├── Makefile           # 개발 명령어
├── pyproject.toml     # 프로젝트 설정
└── README.md          # 프로젝트 문서
```

## 개발 가이드

### 코드 품질 관리

```bash
# 코드 포맷팅
make format

# 코드 린팅
make lint

# 테스트 실행 (커버리지 포함)
make test
```

### Docker 개발 환경

```bash
# 개발용 Docker Compose 실행
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose logs -f app

# 컨테이너 내부 접속
docker-compose exec app bash
```

## 테스트

테스트를 실행하려면 다음 명령어를 사용합니다:

```bash
# 전체 테스트
make test

# 특정 테스트만 실행
pytest tests/test_api/ -v

# 커버리지 리포트 생성
pytest --cov=app --cov-report=html
```

## 배포

### Docker를 사용한 배포

```bash
# 프로덕션 빌드
docker build -t py-monitor:latest .

# 프로덕션 실행
docker run -d -p 8000:8000 --env-file .env.prod py-monitor:latest
```

### 수동 배포

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export ENVIRONMENT=production

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 문제 해결

### 1. 정적 파일 접근 문제

**증상**: `/login.html` 등에서 "Not Found" 오류
**해결**: 서버가 정상적으로 실행되고 있는지 확인
```bash
# 서버 상태 확인
curl -I http://localhost:8000/login.html
```

### 2. 회원가입 405 오류

**증상**: 회원가입 시 "Method Not Allowed" 오류
**해결**: 서버 재시작 후 다시 시도
```bash
# 서버 재시작
pkill -f uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 데이터베이스 연결 오류

**증상**: 500 Internal Server Error
**해결**:
- PostgreSQL 서버가 실행 중인지 확인
- 데이터베이스 접속 정보가 올바른지 확인
- 데이터베이스가 생성되어 있는지 확인
```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql
```

### 4. 이메일 알림 오류

**해결**:
- SMTP 설정이 올바른지 확인
- Gmail을 사용하는 경우 앱 비밀번호 설정 필요

### 5. 모니터링 실패

**해결**:
- 대상 URL이 올바른지 확인
- 방화벽 설정 확인
- 네트워크 연결 상태 확인

### 6. Docker 관련 문제

**해결**:
- Docker와 Docker Compose가 설치되어 있는지 확인
- 포트 충돌이 없는지 확인 (8000, 5432, 6379)
- 컨테이너 로그 확인: `docker-compose logs -f`

### 7. 프론트엔드 문제

**중요**: 프론트엔드는 반드시 FastAPI 서버를 통해 접근해야 합니다.
- ✅ 올바른 방법: http://localhost:8000/login.html
- ❌ 잘못된 방법: file:// 경로로 직접 HTML 파일 열기

## 라이선스

MIT License

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 연락처

프로젝트 링크: https://github.com/iammyeongho/Py_Monitor 