# 개발 가이드

## 1. 개발 환경 설정

### 1.1 필수 요구사항
- Python 3.9 이상
- pip (Python 패키지 관리자)
- Git

### 1.2 가상환경 설정
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 1.3 데이터베이스 설정
```bash
# 데이터베이스 마이그레이션
alembic upgrade head
```

## 2. 개발 워크플로우

### 2.1 브랜치 전략
- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치
- `bugfix/*`: 버그 수정 브랜치

### 2.2 커밋 메시지 규칙
```
[날짜_작성자_타입] 내용

타입:
- feat: 새로운 기능
- fix: 버그 수정
- docs: 문서 수정
- style: 코드 포맷팅
- refactor: 코드 리팩토링
- test: 테스트 코드
- chore: 빌드 프로세스 수정
```

## 3. 테스트

### 3.1 테스트 실행
```bash
# 전체 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_monitoring.py

# 커버리지 리포트 생성
pytest --cov=app tests/
```

### 3.2 테스트 작성 가이드
- 각 기능별로 테스트 파일 생성
- 테스트 케이스는 독립적으로 실행 가능해야 함
- Mock 객체를 활용하여 외부 의존성 제거

## 4. 코드 스타일

### 4.1 Python 코드 스타일
- PEP 8 준수
- Black을 사용한 코드 포맷팅
- isort를 사용한 import 정렬

### 4.2 JavaScript 코드 스타일
- ESLint 규칙 준수
- Prettier를 사용한 코드 포맷팅

## 5. 배포

### 5.1 개발 서버 실행
```bash
uvicorn app.main:app --reload
```

### 5.2 프로덕션 배포
```bash
# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 6. 모니터링 및 로깅

### 6.1 로그 위치
- 애플리케이션 로그: `logs/app.log`
- 에러 로그: `logs/error.log`

### 6.2 로그 레벨
- DEBUG: 개발 시 상세 정보
- INFO: 일반적인 정보
- WARNING: 경고 메시지
- ERROR: 오류 메시지
- CRITICAL: 심각한 오류

## 7. 문제 해결

### 7.1 일반적인 문제
1. 데이터베이스 연결 오류
   - 데이터베이스 서버 실행 확인
   - 연결 문자열 확인

2. 의존성 문제
   - 가상환경 재생성
   - requirements.txt 업데이트

3. 포트 충돌
   - 실행 중인 프로세스 확인
   - 다른 포트 사용

### 7.2 디버깅
- 로그 파일 확인
- 디버거 사용
- print 문 활용 