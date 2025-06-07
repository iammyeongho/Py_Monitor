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

5. 데이터베이스 마이그레이션
```bash
PYTHONPATH=$PYTHONPATH:. alembic upgrade head
```

6. 서버 실행
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

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
├── tests/               # 테스트 코드
├── .env                 # 환경 변수
├── .env.example         # 환경 변수 예제
├── requirements.txt     # 의존성 목록
└── README.md           # 프로젝트 문서
```

## 테스트

테스트를 실행하려면 다음 명령어를 사용합니다:

```bash
pytest
```

## 라이선스

MIT License 