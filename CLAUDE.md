# Py_Monitor 프로젝트 가이드

이 문서는 Py_Monitor 프로젝트의 구조, 코딩 컨벤션, 주석 스타일을 정의합니다.
코드 수정 시 반드시 이 가이드를 참고하여 일관성을 유지해주세요.

---

## 1. 프로젝트 개요

**Py_Monitor**는 웹사이트 가용성, SSL 인증서, 도메인 만료일을 모니터링하고 알림을 제공하는 시스템입니다.

### 기술 스택
| 계층 | 기술 |
|------|------|
| 웹 프레임워크 | FastAPI 0.104+ |
| ORM | SQLAlchemy 2.0+ |
| 데이터베이스 | PostgreSQL 15+ |
| 데이터 검증 | Pydantic v2 |
| 인증 | JWT (python-jose) |
| 비동기 HTTP | aiohttp |
| 캐싱 | Redis |

### Python 버전
- **최소 요구사항**: Python 3.11+
- **권장 버전**: Python 3.11 또는 3.12

---

## 2. 디렉토리 구조

```
Py_Monitor/
├── main.py                       # 애플리케이션 진입점 (유일한 main)
│
├── app/                          # 메인 애플리케이션
│   ├── api/                      # API 레이어
│   │   └── v1/
│   │       ├── endpoints/        # API v1 엔드포인트
│   │       │   ├── users.py      # 사용자/인증 엔드포인트
│   │       │   ├── projects.py   # 프로젝트 CRUD
│   │       │   ├── monitoring.py # 모니터링 상태 조회
│   │       │   └── notifications.py # 알림 관리
│   │       └── router.py         # API 라우터 통합
│   │
│   ├── core/                     # 핵심 설정
│   │   ├── config.py             # 메인 설정 (Settings 클래스)
│   │   ├── settings.py           # 환경별 설정 헬퍼
│   │   ├── security.py           # JWT, 비밀번호 해싱
│   │   ├── deps.py               # 의존성 주입 (DB, 인증)
│   │   └── logging_config.py     # 로깅 설정
│   │
│   ├── db/                       # 데이터베이스
│   │   ├── base.py               # 모델 임포트 집합
│   │   ├── base_class.py         # SQLAlchemy Base 클래스
│   │   └── session.py            # DB 세션 관리
│   │
│   ├── models/                   # SQLAlchemy ORM 모델
│   │   ├── user.py               # 사용자 모델
│   │   ├── project.py            # 프로젝트 모델
│   │   ├── monitoring.py         # 모니터링 로그/알림/설정 모델
│   │   ├── notification.py       # 알림 모델
│   │   └── ...
│   │
│   ├── schemas/                  # Pydantic 스키마 (요청/응답 DTO)
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── monitoring.py
│   │   └── base.py               # 공통 스키마
│   │
│   ├── services/                 # 비즈니스 로직
│   │   ├── user_service.py
│   │   ├── project_service.py
│   │   ├── monitoring.py         # 모니터링 서비스 (핵심)
│   │   ├── email_service.py
│   │   └── scheduler.py          # 백그라운드 스케줄러
│   │
│   └── utils/                    # 유틸리티 함수
│       ├── monitoring.py         # SSL/도메인 체크 유틸
│       ├── email.py              # 이메일 발송 유틸
│       └── notifications.py      # 알림 유틸
│
├── frontend/                     # 프론트엔드
│   ├── html/                     # HTML 템플릿
│   ├── js/                       # JavaScript 모듈
│   └── style/                    # CSS 스타일시트
│
├── tests/                        # 테스트
│   ├── test_api/                 # API 통합 테스트
│   ├── test_services/            # 서비스 단위 테스트
│   └── conftest.py               # 테스트 설정 및 fixture
│
├── alembic/                      # 데이터베이스 마이그레이션
├── docs/                         # 문서
├── scripts/                      # 유틸리티 스크립트
│
├── requirements.txt              # Python 의존성
├── pyproject.toml                # 프로젝트 설정 및 도구 설정
├── Dockerfile                    # Docker 이미지 설정
└── docker-compose.yml            # Docker Compose 설정
```

### 제거된 파일 (중복/레거시)
- `app/main.py` - 루트 main.py로 통합됨
- `app/api/deps.py` - app/core/deps.py로 통합됨
- `app/api/v1/api.py` - router.py와 중복
- `app/api/endpoints/` - 레거시 엔드포인트
- `app/services/monitoring_service.py` - 더미 클래스

---

## 3. 아키텍처 패턴

### 3.1 레이어드 아키텍처
```
[API Endpoint] → [Service] → [Model/Schema] → [Database]
     ↓               ↓              ↓
  deps.py      비즈니스 로직    ORM/Pydantic
```

### 3.2 파일 역할 및 책임

| 레이어 | 파일 위치 | 역할 |
|--------|----------|------|
| **Endpoint** | `app/api/v1/endpoints/` | HTTP 요청 처리, 응답 반환 |
| **Service** | `app/services/` | 비즈니스 로직, 트랜잭션 관리 |
| **Model** | `app/models/` | 데이터베이스 테이블 정의 |
| **Schema** | `app/schemas/` | 요청/응답 데이터 검증 |
| **Utils** | `app/utils/` | 재사용 가능한 헬퍼 함수 |

---

## 4. 코딩 컨벤션

### 4.1 파일 헤더 주석 (필수)

모든 Python 파일은 다음 형식의 docstring으로 시작해야 합니다:

```python
"""
# Laravel 개발자를 위한 설명
# 이 파일은 [Laravel의 XXX]와 유사한 역할을 합니다.
# [프레임워크/라이브러리]를 사용하여 [기능]을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. [Python 문법] = Laravel의 [PHP 문법]과 유사
# 2. [Python 문법] = Laravel의 [PHP 문법]과 유사
# ...
#
# 주요 기능:
# 1. [기능 1]
# 2. [기능 2]
"""
```

### 4.2 클래스 및 함수 docstring

```python
class UserService:
    """사용자 관련 비즈니스 로직을 구현합니다."""

    def create_user(self, user: UserCreate) -> User:
        """사용자 생성

        Args:
            user: 생성할 사용자 정보

        Returns:
            생성된 사용자 객체

        Raises:
            HTTPException: 이메일이 이미 존재하는 경우
        """
        pass
```

### 4.3 주석 작성 규칙

**핵심 원칙:** 주석은 학습 목적으로 작성하며, 코드를 처음 보는 개발자도 이해할 수 있도록 한글로 상세히 작성한다.

```python
# [좋은 예시] 왜(Why)를 설명하는 주석
# 비밀번호는 bcrypt 알고리즘으로 해싱하여 저장
# 평문 저장 시 DB 유출 시 보안 위험
hashed_password = pwd_context.hash(user.password)

# [좋은 예시] 복잡한 로직 설명
# 프로젝트와 사용자의 1:N 관계 설정
# 사용자 삭제 시 관련 프로젝트도 함께 삭제됨 (cascade)
projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

# [좋은 예시] 비즈니스 로직 설명
# 만료일이 7일 이내인 경우 경고 알림 발송
# 고객 요청으로 7일 기준 적용 (2024-01-15)
if days_until_expiry <= 7:
    send_warning_notification(project)

# [나쁜 예시] 코드 그대로 번역 (불필요)
# i를 1 증가시킴
i += 1
```

**주석 유형별 작성법:**

| 유형 | 용도 | 예시 |
|------|------|------|
| `# TODO:` | 나중에 할 작업 | `# TODO: 이메일 발송 실패 시 재시도 로직 추가` |
| `# FIXME:` | 수정 필요한 버그 | `# FIXME: 동시 접속 시 경합 조건 발생 가능` |
| `# NOTE:` | 중요한 참고사항 | `# NOTE: 이 API는 v2에서 deprecated 예정` |
| `# HACK:` | 임시 해결책 | `# HACK: 라이브러리 버그로 우회 처리` |

**Laravel 비교 주석 (학습용):**
```python
# SQLAlchemy의 relationship()은 Laravel의 hasMany()와 유사
# back_populates는 양방향 관계 설정 (Laravel에서는 자동)
projects = relationship("Project", back_populates="user")

# Pydantic의 Field()는 Laravel의 validation rules와 유사
# min_length=8은 Laravel의 'min:8' 규칙과 동일
password: str = Field(..., min_length=8)
```

### 4.4 코드 포맷팅

| 도구 | 설정 | 명령어 |
|------|------|--------|
| **Black** | line-length=88 | `black app/` |
| **isort** | profile=black | `isort app/` |
| **flake8** | max-line-length=120 | `flake8 app/` |

```bash
# 포맷팅 실행
make format

# 린팅 검사
make lint
```

### 4.5 Import 순서

```python
# 1. 표준 라이브러리
from datetime import datetime
from typing import Optional, List

# 2. 서드파티 라이브러리
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 3. 로컬 애플리케이션
from app.api import deps
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
```

---

## 5. 모델 작성 규칙

### 5.1 SQLAlchemy 모델 (app/models/)

```python
"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 [Model명] 모델과 유사한 역할을 합니다.
# SQLAlchemy ORM을 사용하여 [테이블명] 테이블을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. __tablename__ = "xxx"  # Laravel의 protected $table = 'xxx'와 동일
# 2. Column() = Laravel의 $fillable과 유사하지만, 타입과 제약조건을 직접 지정
# 3. relationship() = Laravel의 hasMany(), belongsTo()와 유사
# 4. func.now() = Laravel의 now()와 유사
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class ModelName(Base):
    """모델 설명 (한글)"""
    __tablename__ = "table_name"  # Laravel의 protected $table

    # 기본 키
    id = Column(Integer, primary_key=True, index=True)

    # 외래 키 (Laravel의 foreign()와 유사)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 일반 필드
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    # 타임스탬프 (Laravel의 $timestamps와 유사)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # 소프트 삭제

    # 관계 설정 (Laravel의 belongsTo와 유사)
    user = relationship("User", back_populates="items")

    # 역방향 관계 (Laravel의 hasMany와 유사)
    # cascade="all, delete-orphan"은 Laravel의 onDelete('cascade')와 유사
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
```

### 5.2 Pydantic 스키마 (app/schemas/)

```python
"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 [Model명] Request/Resource와 유사한 역할을 합니다.
# Pydantic을 사용하여 데이터 검증 스키마를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. BaseModel = Laravel의 Form Request와 유사
# 2. Field = Laravel의 validation rules와 유사
# 3. Config.from_attributes = Laravel의 Resource toArray()와 유사
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# 기본 스키마 (공통 필드)
class ItemBase(BaseModel):
    """아이템 기본 정보"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


# 생성 요청 스키마
class ItemCreate(ItemBase):
    """아이템 생성 요청"""
    pass


# 업데이트 요청 스키마
class ItemUpdate(BaseModel):
    """아이템 업데이트 요청 (모든 필드 선택적)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


# 응답 스키마
class ItemResponse(ItemBase):
    """아이템 응답"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # ORM 모델에서 자동 변환
```

---

## 6. API 엔드포인트 작성 규칙

### 6.1 엔드포인트 파일 구조

```python
"""
# Laravel 개발자를 위한 설명
# 이 파일은 [리소스] 관련 API 엔드포인트를 정의합니다.
# Laravel의 [Resource]Controller와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. [기능 1]
# 2. [기능 2]
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.services.item_service import ItemService

router = APIRouter()


@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """아이템 생성"""
    service = ItemService(db)
    return service.create_item(item, current_user.id)


@router.get("/", response_model=List[ItemResponse])
async def read_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """아이템 목록 조회"""
    service = ItemService(db)
    return service.get_items(current_user.id, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse)
async def read_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """아이템 상세 조회"""
    service = ItemService(db)
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """아이템 수정"""
    service = ItemService(db)
    db_item = service.update_item(item_id, item)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """아이템 삭제"""
    service = ItemService(db)
    if not service.delete_item(item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}
```

### 6.2 HTTP 상태 코드 규칙

| 작업 | 성공 코드 | 에러 코드 |
|------|----------|----------|
| 생성 (POST) | 200 또는 201 | 400 (잘못된 요청), 409 (충돌) |
| 조회 (GET) | 200 | 404 (없음) |
| 수정 (PUT/PATCH) | 200 | 404 (없음), 400 (잘못된 요청) |
| 삭제 (DELETE) | 200 | 404 (없음) |
| 인증 실패 | - | 401 (Unauthorized) |
| 권한 없음 | - | 403 (Forbidden) |

---

## 7. 서비스 작성 규칙

### 7.1 서비스 클래스 구조

```python
"""
# Laravel 개발자를 위한 설명
# 이 파일은 [리소스] 관련 비즈니스 로직을 구현합니다.
# Laravel의 [Resource]Service와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. [기능 1]
# 2. [기능 2]
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """아이템 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def create_item(self, item: ItemCreate, user_id: int) -> Item:
        """아이템 생성"""
        db_item = Item(
            **item.model_dump(),
            user_id=user_id
        )
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def get_item(self, item_id: int) -> Optional[Item]:
        """아이템 조회"""
        return self.db.query(Item).filter(Item.id == item_id).first()

    def get_items(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Item]:
        """아이템 목록 조회"""
        return self.db.query(Item)\
            .filter(Item.user_id == user_id)\
            .filter(Item.deleted_at.is_(None))\
            .order_by(Item.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_item(self, item_id: int, item: ItemUpdate) -> Optional[Item]:
        """아이템 수정"""
        db_item = self.get_item(item_id)
        if not db_item:
            return None

        # exclude_unset=True: 명시적으로 설정된 값만 업데이트
        update_data = item.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)

        db_item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def delete_item(self, item_id: int) -> bool:
        """아이템 삭제 (소프트 삭제)"""
        db_item = self.get_item(item_id)
        if not db_item:
            return False

        db_item.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
```

---

## 8. 테스트 작성 규칙

### 8.1 테스트 파일 구조

```python
"""
[리소스] API 테스트
"""

import pytest
from fastapi.testclient import TestClient


class TestItemAPI:
    """아이템 API 테스트"""

    def test_create_item(self, client: TestClient, auth_headers: dict):
        """아이템 생성 테스트"""
        response = client.post(
            "/api/v1/items/",
            json={"name": "Test Item"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Item"

    def test_get_item_not_found(self, client: TestClient, auth_headers: dict):
        """존재하지 않는 아이템 조회 테스트"""
        response = client.get("/api/v1/items/99999", headers=auth_headers)
        assert response.status_code == 404
```

### 8.2 테스트 실행

```bash
# 전체 테스트
make test

# 특정 파일 테스트
pytest tests/test_api/test_users.py -v

# 커버리지 리포트
pytest --cov=app --cov-report=html
```

---

## 9. 환경 변수

### 9.1 필수 환경 변수 (.env)

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=py_monitor
POSTGRES_PORT=5432

# Security (반드시 프로덕션에서는 강력한 키 사용)
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
SMTP_TLS=True
SMTP_USERNAME=Py Monitor
SMTP_FROM=your_email@example.com

# Monitoring
DEFAULT_CHECK_INTERVAL=300
DEFAULT_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

---

## 10. 자주 사용하는 패턴

### 10.1 의존성 주입

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user, get_current_active_user, get_current_superuser

# DB 세션 주입
db: Session = Depends(get_db)

# 현재 사용자 (인증 필요)
current_user: User = Depends(get_current_user)

# 활성 사용자 (인증 + is_active=True)
current_user: User = Depends(get_current_active_user)

# 관리자 권한 (인증 + is_superuser=True)
current_user: User = Depends(get_current_superuser)
```

### 10.2 쿼리 필터링

```python
# 소프트 삭제된 항목 제외
.filter(Item.deleted_at.is_(None))

# 활성 항목만
.filter(Item.is_active == True)  # noqa: E712

# 사용자별 필터
.filter(Item.user_id == user_id)

# 정렬
.order_by(Item.created_at.desc())

# 페이지네이션
.offset(skip).limit(limit)
```

### 10.3 에러 처리

```python
from fastapi import HTTPException, status

# 404 Not Found
raise HTTPException(status_code=404, detail="Item not found")

# 400 Bad Request
raise HTTPException(status_code=400, detail="Invalid input")

# 401 Unauthorized
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# 403 Forbidden
raise HTTPException(status_code=403, detail="Not enough permissions")
```

---

## 11. Laravel vs FastAPI 용어 매핑

| Laravel | FastAPI/Python | 설명 |
|---------|----------------|------|
| `Controller` | `endpoints/*.py` | HTTP 요청 처리 |
| `Service` | `services/*.py` | 비즈니스 로직 |
| `Model` | `models/*.py` | ORM 모델 |
| `Request` | `schemas/*Create` | 입력 검증 |
| `Resource` | `schemas/*Response` | 응답 변환 |
| `Middleware` | `Depends()` | 의존성 주입 |
| `$fillable` | `Column()` | 필드 정의 |
| `hasMany()` | `relationship(..., back_populates=...)` | 1:N 관계 |
| `belongsTo()` | `relationship(..., back_populates=...)` | N:1 관계 |
| `protected $table` | `__tablename__` | 테이블명 지정 |
| `$timestamps` | `created_at`, `updated_at` Column | 타임스탬프 |
| `SoftDeletes` | `deleted_at` Column | 소프트 삭제 |
| `.env` | `.env` + `pydantic-settings` | 환경 변수 |
| `php artisan migrate` | `alembic upgrade head` | 마이그레이션 |

---

## 12. 체크리스트

코드 수정 전 확인사항:

- [ ] 파일 상단에 Laravel 비교 주석 포함
- [ ] 클래스/함수에 한글 docstring 작성
- [ ] 타입 힌트 추가 (`def func(param: Type) -> ReturnType:`)
- [ ] Pydantic v2 문법 사용 (`model_dump()`, `from_attributes`)
- [ ] 에러 처리 및 적절한 HTTP 상태 코드 사용
- [ ] 소프트 삭제 패턴 적용 (deleted_at 사용)
- [ ] 테스트 코드 작성 또는 업데이트
- [ ] `make format && make lint` 실행

---

## 13. 명령어 참조

```bash
# 개발 서버 실행
make dev

# 테스트 실행
make test

# 코드 포맷팅
make format

# 린팅 검사
make lint

# 데이터베이스 마이그레이션
make migrate

# Docker 실행
make docker-up

# Docker 중지
make docker-down
```

---

---

## 14. 클린 코드 원칙

### 14.1 레이어 분리 (Clean Architecture)

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │  ← API Endpoints (HTTP 처리)
├─────────────────────────────────────────┤
│           Application Layer             │  ← Services (비즈니스 로직)
├─────────────────────────────────────────┤
│             Domain Layer                │  ← Models/Schemas (도메인 규칙)
├─────────────────────────────────────────┤
│          Infrastructure Layer           │  ← DB Session, External APIs
└─────────────────────────────────────────┘
```

| 레이어 | 위치 | 책임 | 의존 방향 |
|--------|------|------|----------|
| **Presentation** | `app/api/v1/endpoints/` | HTTP 요청/응답 처리 | → Application |
| **Application** | `app/services/` | 비즈니스 로직, 트랜잭션 | → Domain |
| **Domain** | `app/models/`, `app/schemas/` | 엔티티, 값 객체, 규칙 | 없음 (핵심) |
| **Infrastructure** | `app/db/`, `app/utils/` | DB, 외부 서비스 | → Domain |

### 14.2 SOLID 원칙 적용

```python
# SRP (단일 책임 원칙)
# 하나의 클래스/함수는 하나의 책임만 가진다
class UserService:       # 사용자 비즈니스 로직만
class EmailService:      # 이메일 발송만
class AuthService:       # 인증/인가만

# OCP (개방-폐쇄 원칙)
# 확장에는 열려있고, 수정에는 닫혀있다
class MonitoringService:
    def check_status(self, checker: StatusChecker):  # 인터페이스로 확장
        return checker.check()

# DIP (의존성 역전 원칙)
# 상위 모듈은 하위 모듈에 의존하지 않는다
def create_user(
    db: Session = Depends(get_db),           # 추상화된 의존성 주입
    service: UserService = Depends()
):
    pass
```

### 14.3 함수/메서드 작성 규칙

```python
# 1. 함수는 한 가지 일만 한다
def validate_email(email: str) -> bool:
    """이메일 검증만 수행"""
    pass

def send_email(to: str, subject: str, body: str) -> bool:
    """이메일 발송만 수행"""
    pass

# 2. 함수 길이는 20줄 이내 권장
# 3. 인자는 3개 이하 권장 (많으면 객체로 묶기)
# 4. 부작용(side effect) 최소화
# 5. 명확한 이름 사용 (get_, create_, update_, delete_, is_, has_)
```

---

## 15. Git 커밋 규칙

### 15.1 커밋 메시지 형식

```
<type>: <subject>

[optional body]
```

**타입 종류:**
| 타입 | 설명 | 예시 |
|------|------|------|
| `feat` | 새로운 기능 추가 | `feat: 프로젝트 상태 알림 기능 추가` |
| `fix` | 버그 수정 | `fix: 로그인 토큰 만료 처리 수정` |
| `refactor` | 코드 리팩토링 | `refactor: 모니터링 서비스 구조 개선` |
| `style` | 코드 포맷팅, 세미콜론 등 | `style: Black 포맷팅 적용` |
| `docs` | 문서 수정 | `docs: API 문서 업데이트` |
| `test` | 테스트 추가/수정 | `test: 사용자 인증 테스트 추가` |
| `chore` | 빌드, 패키지 등 기타 | `chore: requirements.txt 업데이트` |

### 15.2 커밋 규칙

```bash
# 올바른 예시
git commit -m "fix: SQLAlchemy Boolean 비교 수정"
git commit -m "feat: 이메일 알림 기능 구현"
git commit -m "refactor: 중복 코드 제거 및 서비스 분리"

# 잘못된 예시 (금지)
git commit -m "🐛 fix bug"           # 이모지 사용 금지
git commit -m "Fixed stuff"          # 모호한 설명
git commit -m "WIP"                  # 작업 중 커밋

# AI 도구 사용 시 주의사항
# - AI가 생성한 워터마크, 서명 포함 금지 (예: "Generated with...", "Co-Authored-By: AI...")
# - 커밋 메시지는 사람이 작성한 것처럼 자연스럽게 작성
# - 이모지, AI 관련 태그, 자동 생성 문구 모두 제외
```

### 15.3 브랜치 전략

```
main                    # 프로덕션 배포 브랜치
├── develop            # 개발 통합 브랜치
│   ├── feature/xxx    # 기능 개발
│   ├── fix/xxx        # 버그 수정
│   └── refactor/xxx   # 리팩토링
└── release/x.x.x      # 릴리즈 준비
```

---

## 16. 버전 관리

### 16.1 시맨틱 버저닝 (SemVer)

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── 버그 수정 (하위 호환)
  │     └────── 기능 추가 (하위 호환)
  └──────────── 호환성 깨지는 변경
```

**예시:**
- `1.0.0` → `1.0.1`: 버그 수정
- `1.0.1` → `1.1.0`: 새 기능 추가
- `1.1.0` → `2.0.0`: API 변경 (하위 호환 X)

### 16.2 버전 관리 위치

```python
# pyproject.toml
[project]
name = "py-monitor"
version = "1.0.0"

# main.py의 FastAPI 앱
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",  # 여기서도 관리
)
```

### 16.3 변경 로그 (CHANGELOG.md)

```markdown
# Changelog

## [1.1.0] - 2024-01-15
### Added
- 이메일 알림 기능 추가
- SSL 인증서 만료 알림 추가

### Changed
- 모니터링 주기 설정 UI 개선

### Fixed
- 로그인 토큰 갱신 버그 수정

## [1.0.0] - 2024-01-01
### Added
- 초기 릴리즈
- 프로젝트 모니터링 기능
- 사용자 인증 기능
```

### 16.4 릴리즈 프로세스

```bash
# 1. develop에서 release 브랜치 생성
git checkout develop
git checkout -b release/1.1.0

# 2. 버전 번호 업데이트
# - pyproject.toml
# - main.py
# - CHANGELOG.md

# 3. 테스트 및 버그 수정
make test

# 4. main으로 머지 및 태그
git checkout main
git merge release/1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags

# 5. develop에 머지
git checkout develop
git merge release/1.1.0

# 6. release 브랜치 삭제
git branch -d release/1.1.0
```

### 16.5 API 버전 관리

```python
# 현재 구조: /api/v1/...
app.include_router(api_router, prefix="/api/v1")

# 새 버전 추가 시: /api/v2/...
# app/api/v2/router.py 생성
app.include_router(api_v2_router, prefix="/api/v2")
```

**버전 병행 운영 규칙:**
- v1은 최소 6개월간 유지
- Deprecated 헤더로 사용 중단 예고
- v1 → v2 마이그레이션 가이드 제공

---

*이 문서는 프로젝트의 일관성을 위해 작성되었습니다. 수정 시 팀원들과 협의 후 업데이트해주세요.*
