# PHP 개발자를 위한 Python 프로젝트 가이드

## 1. 프로젝트 구조 (PHP vs Python)

### 디렉토리 구조 비교
```
PHP (Laravel)          | Python (FastAPI)
----------------------|------------------
app/                  | app/
├── Http/            | ├── api/
│   ├── Controllers/ | │   └── v1/
│   └── Middleware/  | │       └── endpoints/
├── Models/          | ├── models/
├── Services/        | ├── services/
└── Providers/       | └── core/
config/              | app/core/
database/            | alembic/
├── migrations/      | ├── versions/
└── seeds/          | └── env.py
routes/              | app/api/v1/router.py
tests/               | tests/
```

### 주요 파일 비교
```
PHP (Laravel)          | Python (FastAPI)
----------------------|------------------
.env                  | .env
composer.json         | requirements.txt
artisan               | main.py
phpunit.xml          | pytest.ini
```

## 2. 주요 개념 비교

### 1. 의존성 관리
- **PHP**: Composer (`composer.json`)
- **Python**: pip (`requirements.txt`)
  ```bash
  pip install -r requirements.txt  # composer install과 동일
  ```

### 2. 환경 설정
- **PHP**: `.env` 파일 + `config/` 디렉토리
- **Python**: `.env` 파일 + `app/core/config.py`
  ```python
  # app/core/config.py
  class Settings(BaseSettings):
      POSTGRES_SERVER: str
      POSTGRES_USER: str
      # ... 기타 설정
  ```

### 3. 라우팅
- **PHP**: `routes/web.php`, `routes/api.php`
- **Python**: `app/api/v1/router.py`
  ```python
  # app/api/v1/router.py
  api_router = APIRouter()
  api_router.include_router(users.router, prefix="/users", tags=["users"])
  ```

### 4. 컨트롤러/엔드포인트
- **PHP**: `app/Http/Controllers/`
- **Python**: `app/api/v1/endpoints/`
  ```python
  # app/api/v1/endpoints/users.py
  @router.get("/{user_id}")
  def get_user(user_id: int):
      return {"user_id": user_id}
  ```

### 5. 모델
- **PHP**: Eloquent ORM
- **Python**: SQLAlchemy
  ```python
  # app/models/user.py
  class User(Base):
      __tablename__ = "users"
      id = Column(Integer, primary_key=True)
      email = Column(String, unique=True)
  ```

### 6. 마이그레이션
- **PHP**: `php artisan migrate`
- **Python**: Alembic
  ```bash
  alembic revision --autogenerate -m "create users table"
  alembic upgrade head
  ```

### 7. 테스트
- **PHP**: PHPUnit
- **Python**: pytest
  ```bash
  pytest tests/  # php artisan test와 동일
  ```

## 3. 현재 구현된 기능

### 1. 데이터베이스 설정
- PostgreSQL 연결 설정
- `py_monitor` 스키마 생성
- SQLAlchemy ORM 설정

### 2. 모델 정의
- User
- Project
- MonitoringLog
- MonitoringAlert
- MonitoringSetting

### 3. API 스키마
- MonitoringCheckRequest
- MonitoringCheckResponse
- MonitoringStatus
- SSLStatus

### 4. 서비스 구조
- MonitoringService (더미 구현)

## 4. 다음 단계

### 1. 데이터베이스 마이그레이션
- Alembic을 사용한 테이블 생성
- 초기 데이터 시드

### 2. 서비스 로직 구현
- MonitoringService 실제 구현
- 모니터링 체크 로직
- 알림 발송 로직

### 3. API 엔드포인트 구현
- CRUD 작업 구현
- 인증/인가 구현
- 에러 핸들링

### 4. 테스트 구현
- 단위 테스트
- 통합 테스트
- API 테스트

## 5. 유용한 명령어

```bash
# 가상환경 활성화
source .venv/bin/activate  # composer install과 유사

# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
pytest

# 마이그레이션
alembic revision --autogenerate -m "message"
alembic upgrade head

# 서버 실행
uvicorn main:app --reload
```

## 6. 주의사항

1. **가상환경**
   - 항상 `.venv` 가상환경을 활성화한 상태에서 작업
   - `composer install`과 달리, Python은 프로젝트별로 가상환경 사용

2. **타입 힌트**
   - Python 3.9+ 에서는 타입 힌트를 적극 활용
   - PHP의 타입 힌트와 유사하지만, 런타임에 강제되지 않음

3. **비동기 처리**
   - FastAPI는 기본적으로 비동기 지원
   - `async/await` 구문 사용 (PHP의 비동기와 유사)

4. **의존성 주입**
   - FastAPI의 의존성 주입 시스템은 Laravel의 서비스 컨테이너와 유사
   - `Depends()` 데코레이터 사용 

## 7. 개발 규칙 및 협업 가이드

### 1. 브랜치 전략 (Git Flow)
- **main**: 운영 배포용(프로덕션) 브랜치
- **develop**: 개발 통합 브랜치
- **feature/**: 기능 개발용 브랜치 (ex: `feature/monitoring-api`)
- **fix/**: 버그 수정 브랜치 (ex: `fix/login-bug`)
- **hotfix/**: 운영 긴급 수정 (ex: `hotfix/urgent-error`)
- **release/**: 배포 준비 브랜치 (ex: `release/v1.0.0`)

#### 브랜치 생성 예시
```bash
git checkout -b feature/monitoring-api
git checkout -b fix/login-bug
```

### 2. 커밋 메시지 규칙 (한글/영문 혼용 가능)
- `[YYYYMMDD] <type>: <내용>`
- type 예시: feat, fix, docs, refactor, test, chore
- 예시:
  - `[20240523] feat: 모니터링 API 엔드포인트 추가`
  - `[20240523] fix: 로그인 버그 수정`
  - `[20240523] docs: 개발 가이드 문서 추가`

### 3. PR(Pull Request) 규칙
- PR 제목: `[YYYYMMDD] <type>: <주요 변경점>`
- PR 설명: 변경 내용, 테스트 방법, 관련 이슈 등 상세히 작성
- 리뷰어 지정 및 코드리뷰 필수
- CI 통과 후 머지

### 4. 코드 스타일
- **Python**: PEP8 권장, Black 포매터 사용
- **PHP**: PSR-12 권장
- 함수/클래스/변수명은 명확하게 작성
- 주석은 한글/영문 혼용 가능, 반드시 필요한 곳에만 작성

#### Python 포매팅 예시
```bash
black .
```

### 5. 협업 규칙
- 이슈는 GitHub Issue로 관리
- 작업 시작 전 반드시 이슈 생성 및 할당
- 작업 완료 후 PR 생성, 리뷰 요청
- 리뷰 승인 후 머지
- 불필요한 파일/폴더는 `.gitignore`에 추가

### 6. 환경 변수 및 보안
- `.env` 파일은 절대 커밋 금지 (예시 파일은 `.env.example`로 제공)
- 비밀번호, API 키 등 민감 정보는 환경 변수로만 관리

### 7. 문서화
- 모든 주요 기능/구조/설정은 `docs/`에 마크다운으로 문서화
- API 명세, DB 스키마, 배포 방법 등도 문서화

### 8. 테스트
- 모든 PR은 테스트 코드 포함 권장
- `pytest`로 테스트 실행
- 커버리지 80% 이상 유지 권장

### 9. 기타
- 커밋/PR/이슈/문서 등 모든 기록은 최대한 상세하게 남길 것
- 협업 중 궁금한 점은 슬랙/이슈/PR 코멘트로 적극 소통

## 8. 참고 예시

### 1. .gitignore 예시
```
.venv/
__pycache__/
.pytest_cache/
.env
.DS_Store
```

### 2. .env.example 예시
```
POSTGRES_SERVER=localhost
POSTGRES_USER=jeongmyeongho
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=py_monitor
POSTGRES_PORT=5432
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=yourpassword
SMTP_FROM=your@email.com
```

### 3. PR 템플릿 예시
```
[YYYYMMDD] feat: <주요 변경점>

## 변경 내용
- 무엇을 변경했는지 상세히 작성

## 테스트 방법
- 어떻게 테스트했는지 작성

## 관련 이슈
- #이슈번호
``` 