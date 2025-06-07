# Py_Monitor

웹 서비스 모니터링 시스템

## 기능

- 웹 서비스 상태 모니터링
- SSL 인증서 상태 확인
- 도메인 만료일 확인
- 실시간 알림 (이메일, 웹훅)
- 대시보드 UI

## 기술 스택

### 백엔드
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Celery

### 프론트엔드
- HTML5
- CSS3
- JavaScript (ES6+)
- Font Awesome

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/iammyeongho/Py_Monitor.git
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
alembic upgrade head
```

6. 서버 실행
```bash
uvicorn app.main:app --reload
```

## 사용 방법

1. 회원가입 및 로그인
2. 프로젝트 등록
   - 프로젝트 URL 입력
   - 모니터링 설정 구성
3. 대시보드에서 모니터링 상태 확인
4. 알림 설정
   - 이메일 알림
   - 웹훅 설정

## API 문서

API 문서는 서버 실행 후 다음 URL에서 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 모니터링 항목

1. 서비스 상태
   - HTTP 응답 코드
   - 응답 시간
   - 가용성

2. SSL 인증서
   - 유효성
   - 만료일
   - 발급자

3. 도메인
   - 만료일
   - 등록자
   - DNS 레코드

## 알림 설정

1. 이메일 알림
   - 서비스 다운
   - SSL 인증서 만료 임박
   - 도메인 만료 임박

2. 웹훅
   - JSON 형식의 알림 데이터
   - 커스텀 엔드포인트 설정

## 개발 가이드

### 코드 스타일
- PEP 8 준수
- Type hints 사용
- Docstring 작성

### 테스트
```bash
pytest
```

### 린트
```bash
flake8
black .
```

## 라이선스

MIT License

## 기여 방법

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 연락처

- 이메일: [your-email@example.com]
- GitHub: [https://github.com/iammyeongho] 