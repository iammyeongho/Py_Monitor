# PHP 개발자를 위한 Python 프로젝트 가이드 (상세)

---

## 1. 전체 구조와 주요 개념

### 1.1 디렉토리/파일 구조
```
app/                # 비즈니스 로직, API, 모델, 서비스 등
├── api/            # FastAPI 라우터 및 엔드포인트
│   └── v1/
│       ├── endpoints/  # 실제 API 함수(컨트롤러)
│       └── router.py   # 라우터 등록
├── core/           # 환경설정, 유틸리티
├── db/             # DB 세션, 베이스, 초기화 등
├── models/         # SQLAlchemy ORM 모델
├── schemas/        # Pydantic 데이터 검증/직렬화
├── services/       # 비즈니스 로직
alembic/            # DB 마이그레이션
frontend/           # 프론트엔드(필요시)
docs/               # 문서
scripts/            # 유틸리티 스크립트
.tests/             # 테스트 코드
.venv/              # 가상환경(커밋 금지)
```

### 1.2 주요 파일 비교 (Laravel vs FastAPI)
| Laravel                | FastAPI                   | 설명                      |
|------------------------|---------------------------|---------------------------|
| routes/api.php         | app/api/v1/router.py      | API 라우팅                |
| app/Http/Controllers/  | app/api/v1/endpoints/     | 컨트롤러                  |
| app/Services/          | app/services/             | 서비스(비즈니스 로직)     |
| app/Models/            | app/models/               | ORM 모델                  |
| database/migrations/   | alembic/versions/         | DB 마이그레이션           |
| config/*.php           | app/core/config.py        | 환경설정                  |
| app/Http/Middleware/   | 미들웨어(직접 구현)       | 미들웨어                  |
| tests/                 | tests/                    | 테스트                    |

---

## 2. 요청-응답 흐름 (실제 예시)

1. 클라이언트가 `/api/v1/users/1`로 GET 요청
2. `app/api/v1/router.py`에서 해당 엔드포인트로 라우팅
3. `app/api/v1/endpoints/users.py`의 함수 실행
4. 필요한 경우 `app/services/user_service.py`에서 비즈니스 로직 처리
5. `app/models/user.py`의 SQLAlchemy 모델을 통해 DB 접근
6. 결과를 JSON으로 반환

#### FastAPI 라우터 예시
```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

#### 엔드포인트(컨트롤러) 예시
```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserOut
from app.services.user_service import get_user_by_id

router = APIRouter()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

#### 서비스 예시
```python
# app/services/user_service.py
from app.models.user import User
from app.db.session import SessionLocal

def get_user_by_id(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    return user
```

#### 모델 예시
```python
# app/models/user.py
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
```

#### 스키마(Pydantic) 예시
```python
# app/schemas/user.py
from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    email: str
    class Config:
        orm_mode = True
```

---

## 3. FastAPI의 주요 개념 (PHP와 비교)

### 3.1 의존성 주입(Dependency Injection)
- **FastAPI**: `Depends()`로 함수/클래스 의존성 주입
- **Laravel**: 서비스 컨테이너, 타입힌트 기반 DI
```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items/")
def read_items(db=Depends(get_db)):
    ...
```

### 3.2 비동기(Async/Await)
- FastAPI는 비동기 지원, PHP는 기본적으로 동기
```python
@router.get("/async-example")
async def async_example():
    await some_async_func()
    return {"result": "ok"}
```

### 3.3 예외처리
- FastAPI: `HTTPException`, 커스텀 예외 핸들러
- Laravel: Exception Handler
```python
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Not found")
```

### 3.4 미들웨어
- FastAPI: 직접 미들웨어 클래스 구현
- Laravel: 미들웨어 클래스 등록
```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 사전/사후 처리
        response = await call_next(request)
        return response
```

### 3.5 환경설정
- FastAPI: Pydantic Settings, `.env` 파일
- Laravel: `.env` + config/*.php
```python
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    POSTGRES_SERVER: str
    ...
```

---

## 4. 데이터베이스 및 마이그레이션

### 4.1 SQLAlchemy ORM
- Eloquent와 유사, Pythonic ORM
- 관계, 제약조건, Index 등 모두 지원

### 4.2 트랜잭션 처리
```python
from sqlalchemy.orm import Session

def do_something(db: Session):
    try:
        # 작업
        db.commit()
    except:
        db.rollback()
        raise
```

### 4.3 Alembic 마이그레이션 실전
```bash
alembic revision --autogenerate -m "add user table"
alembic upgrade head
```
- 마이그레이션 파일은 alembic/versions/에 생성
- DB 스키마 변경시 반드시 Alembic 사용

---

## 5. API 문서화
- FastAPI는 OpenAPI/Swagger 자동 지원
- `/docs`(Swagger UI), `/redoc`(ReDoc)에서 API 명세 확인 가능
- PHP(Laravel)는 별도 패키지 필요

---

## 6. 테스트
- pytest 사용, 테스트 코드 구조는 tests/에 위치
- Laravel의 PHPUnit과 유사
```python
# tests/test_user.py
from fastapi.testclient import TestClient
from app.main import app

def test_get_user():
    client = TestClient(app)
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
```

---

## 7. 실무 협업/운영 팁
- 가상환경 활성화 필수
- Black, isort 등 코드 포매터 사용
- .env 커밋 금지, .env.example 제공
- PR/이슈/문서화 적극 활용
- DB, API, 서비스별로 테스트 코드 작성 권장
- Alembic 마이그레이션 충돌 주의(동시 작업시)
- API 명세 자동화 활용

---

## 8. 자주 묻는 질문(FAQ) & 실전 상황별 Q&A
- **Q. PHP의 ServiceProvider, Middleware는 어디에?**
  - Python에서는 필요시 직접 미들웨어 작성, 의존성 주입은 FastAPI의 Depends 사용
- **Q. artisan 명령어는?**
  - Python은 `alembic`, `pytest`, `uvicorn` 등 명령어로 대체
- **Q. DB 시드/팩토리?**
  - 별도 스크립트(`scripts/` 폴더)로 작성 가능
- **Q. API 문서 자동화는?**
  - FastAPI는 기본 제공(`/docs`)
- **Q. 비동기/동기 혼용은?**
  - FastAPI는 동기/비동기 함수 모두 지원, 혼용 가능
- **Q. 환경변수 관리?**
  - Pydantic Settings + .env 파일로 일원화

---

## 9. 참고 자료/링크
- FastAPI 공식문서: https://fastapi.tiangolo.com/ko/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- [Laravel ↔ FastAPI 구조 비교] 

---

## 10. Python 로그 저장 방식 (Laravel과 비교)

### 10.1 라라벨 로그 방식
- 기본적으로 `storage/logs/laravel.log`에 기록
- 로그 레벨: debug, info, warning, error 등
- 예시: `Log::info('메시지');`

### 10.2 Python(FastAPI) 로그 방식
- 표준 라이브러리 `logging` 사용
- 로그 파일: `logs/app.log` (커스텀 가능)
- 로그 레벨: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 로그 포맷: 시간, 레벨, 모듈, 메시지 등
- 파일 분할: RotatingFileHandler로 용량별 자동 분할

#### logging 설정 예시 (`app/core/logging_config.py`)
```python
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
```

#### 사용 예시
```python
import logging
logger = logging.getLogger(__name__)

logger.info("정상 동작 메시지")
logger.error("에러 발생!")
```

### 10.3 실무 팁
- 로그 파일은 `.gitignore`에 반드시 추가 (커밋 금지)
- 로그 레벨별로 구분하여 사용 (운영: INFO/ERROR, 개발: DEBUG)
- 로그 파일 용량 관리(분할, 백업)
- 민감 정보(비밀번호 등)는 로그에 남기지 않기
- 로그 파일 위치: `logs/app.log` (커스텀 가능)

### 10.4 라라벨과의 비교 요약
| Laravel                | Python(FastAPI)           |
|------------------------|---------------------------|
| Log::info(), Log::error() | logger.info(), logger.error() |
| storage/logs/laravel.log  | logs/app.log                |
| 로그 채널/스택            | 핸들러/포맷터                |
| .env로 로그 레벨 설정      | logging.basicConfig()        |

--- 