# 프로젝트 소개 (Python 모니터링 시스템)

## 1. 개요
- 이 프로젝트는 FastAPI, SQLAlchemy, Alembic, PostgreSQL 기반의 모니터링 시스템입니다.
- PHP(Laravel) 개발자도 쉽게 이해할 수 있도록 구조와 규칙을 문서화했습니다.

## 2. 디렉토리 구조
```
app/         # 비즈니스 로직, API, 모델 등
alembic/     # DB 마이그레이션
frontend/    # 프론트엔드(필요시)
docs/        # 문서
scripts/     # 유틸리티 스크립트
tests/       # 테스트 코드
.venv/       # 가상환경(커밋 금지)
```

## 3. 개발/협업 규칙
- 브랜치 전략: main, develop, feature/*, fix/*, hotfix/*, release/*
- 커밋 메시지: `[YYYYMMDD] <type>: <내용>`
- PR: 상세 설명, 리뷰 필수, CI 통과 후 머지
- 코드 스타일: Python(PEP8, Black), PHP(PSR-12)
- 환경 변수: `.env` 커밋 금지, `.env.example` 제공
- 문서화: docs/에 마크다운 파일로 작성

## 4. 환경설정
1. Python 3.9+ 설치
2. 가상환경 생성 및 활성화
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
4. 환경 변수 설정
   - `.env.example` 참고하여 `.env` 파일 생성

## 5. 실행/테스트 방법
- 서버 실행: `uvicorn main:app --reload`
- 테스트: `pytest`
- 마이그레이션: `alembic revision --autogenerate -m "msg" && alembic upgrade head`

## 6. 주요 명령어
```bash
source .venv/bin/activate
pip install -r requirements.txt
pytest
alembic revision --autogenerate -m "msg"
alembic upgrade head
uvicorn main:app --reload
```

## 7. 문서화 위치
- docs/ 디렉토리 내 마크다운 파일 참고
  - `postgres_setup.md`: PostgreSQL 연동/설정 가이드
  - `php_developer_guide.md`: PHP 개발자용 가이드
  - `CONTRIBUTING.md`: 협업/기여 가이드

## 8. 기타
- 불필요한 파일/폴더는 `.gitignore`에 추가
- 궁금한 점은 이슈/PR/슬랙 등으로 문의 