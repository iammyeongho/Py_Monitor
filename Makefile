.PHONY: help install test run dev docker-build docker-up docker-down clean

# 기본 타겟
help:
	@echo "사용 가능한 명령어:"
	@echo "  install      - 의존성 설치"
	@echo "  test         - 테스트 실행"
	@echo "  run          - 프로덕션 서버 실행"
	@echo "  dev          - 개발 서버 실행"
	@echo "  docker-build - Docker 이미지 빌드"
	@echo "  docker-up    - Docker Compose로 서비스 시작"
	@echo "  docker-down  - Docker Compose로 서비스 중지"
	@echo "  clean        - 캐시 및 임시 파일 정리"
	@echo "  migrate      - 데이터베이스 마이그레이션"
	@echo "  lint         - 코드 린팅"
	@echo "  format       - 코드 포맷팅"

# 의존성 설치
install:
	pip install -r requirements.txt

# 테스트 실행
test:
	pytest tests/ -v --cov=app --cov-report=html

# 프로덕션 서버 실행
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# 개발 서버 실행
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker 이미지 빌드
docker-build:
	docker build -t py-monitor .

# Docker Compose로 서비스 시작
docker-up:
	docker-compose up -d

# Docker Compose로 서비스 중지
docker-down:
	docker-compose down

# 캐시 및 임시 파일 정리
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# 데이터베이스 마이그레이션
migrate:
	alembic upgrade head

# 코드 린팅
lint:
	flake8 app/ tests/
	black --check app/ tests/

# 코드 포맷팅
format:
	black app/ tests/
	isort app/ tests/ 