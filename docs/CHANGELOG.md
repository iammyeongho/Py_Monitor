# Py_Monitor 변경 이력 (Changelog)

---

## [2025-06-04] jeongmyeongho
- feat: 로깅 설정 기능 강화
  - 동적 로그 레벨 설정 (환경변수)
  - 요청/응답 로그 필터 추가
  - 로그 포맷, 날짜 포맷 설정
  - 초기화 메시지 출력

## [2025-06-04] jeongmyeongho
- feat: 모니터링 스케줄러 및 서비스 구현
  - 프로젝트별 모니터링 스케줄러 구현
  - 상태/SSL/도메인 만료 체크 및 알림
  - 에러 핸들링 및 재시도 로직

## [2025-06-04] jeongmyeongho
- feat: 알림 시스템 구현 및 UI/UX 개선
  - 이메일/웹훅 알림 시스템 구현
  - 알림 템플릿 관리
  - 프론트엔드 대시보드 UI/UX 개선
  - 반응형 스타일 적용
  - 실시간 알림 표시

## [2025-06-04] jeongmyeongho
- docs: README.md 및 개발 가이드 작성
  - 설치/실행/테스트/배포 방법 문서화
  - API 문서 링크 추가
  - 코드 스타일, 기여 가이드 추가

## [2025-06-04] jeongmyeongho
- test: 백엔드/프론트엔드 테스트 코드 작성
  - pytest 기반 서비스/알림 테스트
  - Jest 기반 프론트엔드 유닛테스트

## [2025-06-07] jeongmyeongho
- fix: 서버 실행 및 테스트 환경 점검
  - 포트 충돌, 의존성 누락, ImportError 등 점검 및 수정
  - 누락된 Base/relationship import, whois/aiosmtplib 설치
  - 서버 정상 기동 및 테스트 통과 확인

## [2025-06-07] 전체 점검 및 초보자용 상세 이력

- **서버 실행 시 포트 충돌 오류(이미 사용 중) 발생**
  - 해결: `lsof -i :8000` 명령어로 사용 중인 프로세스 확인 후 `kill [PID]`로 종료
- **서버 실행 시 ImportError: cannot import name 'deps' from 'app.api' 오류**
  - 원인: `app/api/deps.py` 파일이 없거나, import 경로가 잘못됨
  - 해결: 파일 존재 여부 확인, 필요시 파일 생성 또는 import 경로 수정
- **테스트 실행 시 모듈 누락 오류**
  - `ModuleNotFoundError: No module named 'whois'` → `pip install whois`로 설치
  - `ModuleNotFoundError: No module named 'aiosmtplib'` → `pip install aiosmtplib`로 설치
- **SQLAlchemy relationship import 오류**
  - `NameError: name 'relationship' is not defined` → `from sqlalchemy.orm import relationship` 추가
- **Base 클래스 누락 오류**
  - `app/db/base_class.py`에 SQLAlchemy Base 클래스 정의 추가
- **테스트 실행 방법**
  - `pytest tests/ -v` 명령어로 전체 테스트 실행
  - 오류 발생 시 에러 메시지 확인 후, 누락된 패키지 설치 또는 코드 수정
- **서버 실행 방법**
  - `uvicorn app.main:app --reload` 명령어로 서버 실행
  - 브라우저에서 `http://localhost:8000` 접속
  - API 문서는 `http://localhost:8000/docs`에서 확인
- **기본적인 리눅스 명령어**
  - `ps aux | grep uvicorn` : 실행 중인 uvicorn 프로세스 확인
  - `kill [PID]` : 프로세스 종료
  - `pip install [패키지명]` : 파이썬 패키지 설치
  - `lsof -i :포트번호` : 해당 포트를 사용 중인 프로세스 확인

## 2025-06-08 프로젝트 구조 점검 및 마이그레이션 체인 정리

### 주요 변경 및 점검 내역
- .env 파일 환경 변수 정상 로딩 확인
- app/models/__init__.py에서 불필요한 import 및 존재하지 않는 모델(import) 제거
    - InternalLog, Notification, Alert 등 실제 정의되지 않은 모델 import 제거
    - MonitoringLog, MonitoringAlert, MonitoringSetting만 import 및 __all__에 포함
- Alembic 마이그레이션 체인 정리
    - 중복/불필요한 create_monitoring_tables.py 파일 삭제
    - initial_migration.py → monitoring_tables.py로 단일 체인 구성
    - alembic/env.py에서 settings.DATABASE_URL → settings.SQLALCHEMY_DATABASE_URI로 수정
- DB 마이그레이션 정상 완료 및 테이블 생성 확인
- 전체 구간(환경 변수, DB, 모델, 마이그레이션) 순차 점검 및 정상화

### 향후 작업
- 서버 실행 및 엔드포인트 정상 동작 확인
- 추가적인 기능 개발 및 문서화

---

> 모든 커밋 및 작업 내역은 GitHub 저장소의 커밋 히스토리와 일치합니다.
> 추가적인 변경사항 발생 시 이 파일에 계속 기록해 주세요. 