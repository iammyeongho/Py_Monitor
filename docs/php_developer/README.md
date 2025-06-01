# PHP 개발자를 위한 Python 프로젝트 가이드

이 문서는 PHP 개발자가 Python/FastAPI 프로젝트를 이해하고 개발하는데 도움을 주기 위해 작성되었습니다. Laravel과 FastAPI의 주요 개념을 비교하면서 설명하여, PHP 개발자가 쉽게 이해할 수 있도록 구성했습니다.

## 문서 목차

1. [프로젝트 구조와 주요 개념](01_project_structure.md)
   - 디렉토리/파일 구조
   - Laravel vs FastAPI 주요 파일 비교
   - 기본 개념 설명

2. [요청-응답 흐름](02_request_response_flow.md)
   - 실제 예시를 통한 흐름 설명
   - 라우터, 엔드포인트, 서비스, 모델 예시
   - 코드 비교 분석

3. [FastAPI 주요 개념](03_fastapi_concepts.md)
   - 의존성 주입
   - 비동기 처리
   - 예외처리
   - 미들웨어
   - 환경설정

4. [데이터베이스와 마이그레이션](04_database_migration.md)
   - SQLAlchemy ORM
   - 트랜잭션 처리
   - Alembic 마이그레이션
   - 실전 예시

5. [API 문서화](05_api_documentation.md)
   - OpenAPI/Swagger
   - API 명세 작성
   - 문서 자동화

6. [테스트 작성](06_testing.md)
   - pytest 사용법
   - 테스트 코드 구조
   - 실전 테스트 예시

7. [실무 협업/운영 팁](07_best_practices.md)
   - 개발 환경 설정
   - 코드 품질 관리
   - 협업 프로세스
   - 운영 팁

8. [자주 묻는 질문](08_faq.md)
   - PHP vs Python 개념 비교
   - 실전 상황별 Q&A
   - 문제 해결 가이드

9. [로깅 시스템](09_logging.md)
   - 로깅 설정
   - 로그 레벨
   - 로그 파일 관리
   - Laravel vs Python 로깅 비교

## 시작하기

1. 이 가이드는 순서대로 읽는 것을 추천합니다.
2. 각 문서는 독립적으로도 읽을 수 있도록 구성되어 있습니다.
3. 코드 예시는 실제 프로젝트에서 바로 사용할 수 있도록 작성되었습니다.
4. Laravel과 FastAPI의 개념을 비교하면서 설명하여, PHP 개발자가 쉽게 이해할 수 있도록 했습니다.

## 기여하기

이 문서는 지속적으로 업데이트되고 있습니다. 오류나 개선사항이 있다면 Pull Request를 보내주세요. 