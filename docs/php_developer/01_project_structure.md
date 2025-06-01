# 1. 프로젝트 구조와 주요 개념

이 문서에서는 FastAPI 프로젝트의 기본 구조와 Laravel과의 비교를 통해 주요 개념을 설명합니다.

## 1.1 디렉토리/파일 구조

### 1.1.1 전체 구조
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
tests/              # 테스트 코드
.venv/              # 가상환경(커밋 금지)
```

### 1.1.2 주요 디렉토리 설명

#### app/
- Laravel의 `app/` 디렉토리와 유사한 역할
- 비즈니스 로직, API, 모델 등 핵심 코드가 위치
- 각 하위 디렉토리는 특정 역할을 담당

#### app/api/
- Laravel의 `routes/` 디렉토리와 유사
- API 엔드포인트 정의
- 버전 관리(v1, v2 등)를 위한 구조

#### app/core/
- Laravel의 `config/` 디렉토리와 유사
- 환경 설정, 유틸리티 함수 등
- 애플리케이션 전반에 걸쳐 사용되는 설정

#### app/db/
- Laravel의 `database/` 디렉토리의 일부 기능
- 데이터베이스 연결, 세션 관리
- SQLAlchemy 설정

#### app/models/
- Laravel의 `app/Models/` 디렉토리와 유사
- SQLAlchemy ORM 모델 정의
- 데이터베이스 테이블과 매핑

#### app/schemas/
- Laravel의 Form Request Validation과 유사
- Pydantic 모델을 사용한 데이터 검증
- API 요청/응답 데이터 구조 정의

#### app/services/
- Laravel의 `app/Services/` 디렉토리와 유사
- 비즈니스 로직 구현
- 재사용 가능한 서비스 로직

## 1.2 Laravel vs FastAPI 주요 파일 비교

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

## 1.3 기본 개념 설명

### 1.3.1 의존성 관리
- Laravel: Composer
- FastAPI: pip + requirements.txt 또는 poetry

### 1.3.2 환경 설정
- Laravel: .env + config/*.php
- FastAPI: .env + Pydantic Settings

### 1.3.3 라우팅
- Laravel: routes/*.php
- FastAPI: APIRouter

### 1.3.4 컨트롤러
- Laravel: Controller 클래스
- FastAPI: 함수 기반 엔드포인트

### 1.3.5 미들웨어
- Laravel: 미들웨어 클래스
- FastAPI: 미들웨어 함수 또는 클래스

### 1.3.6 데이터베이스
- Laravel: Eloquent ORM
- FastAPI: SQLAlchemy ORM

### 1.3.7 검증
- Laravel: Form Request Validation
- FastAPI: Pydantic 모델

## 1.4 주요 차이점

1. **함수형 vs 클래스형**
   - Laravel: 주로 클래스 기반
   - FastAPI: 주로 함수 기반

2. **의존성 주입**
   - Laravel: 서비스 컨테이너
   - FastAPI: Depends() 데코레이터

3. **비동기 처리**
   - Laravel: 기본적으로 동기
   - FastAPI: 비동기 지원

4. **API 문서화**
   - Laravel: 별도 패키지 필요
   - FastAPI: 자동 생성

5. **타입 시스템**
   - Laravel: PHP 타입 힌트
   - FastAPI: Python 타입 힌트 + Pydantic

## 1.5 실무 팁

1. **프로젝트 시작시**
   - 가상환경 설정 필수
   - 의존성 관리 도구 선택 (pip/poetry)
   - .env 파일 설정

2. **코드 구조화**
   - 기능별로 모듈 분리
   - 재사용 가능한 컴포넌트 설계
   - 명확한 네이밍 컨벤션

3. **개발 환경**
   - IDE 설정 (VSCode/PyCharm)
   - 코드 포매터 설정 (Black, isort)
   - 린터 설정 (flake8, mypy)

4. **문서화**
   - API 문서 자동화 활용
   - 코드 주석 작성
   - README.md 관리 