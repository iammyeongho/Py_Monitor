# Py_Monitor

웹사이트 모니터링 시스템

## 기능

- 웹사이트 가용성 모니터링
- SSL 인증서 만료 모니터링
- 이메일 알림 시스템
- 사용자 관리
- 프로젝트 관리
- 상세한 로깅 시스템

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/Py_Monitor.git
cd Py_Monitor
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
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
alembic upgrade head
```

## 실행 방법

```bash
uvicorn main:app --reload
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 테스트

```bash
pytest
```

## 라이선스

MIT 