# Docker 사용법 가이드

이 문서는 Py_Monitor 프로젝트에서 Docker를 사용하는 방법을 상세히 설명합니다.

## 목차

1. [Docker 개요](#docker-개요)
2. [Docker 설치](#docker-설치)
3. [Dockerfile 설명](#dockerfile-설명)
4. [Docker Compose 설명](#docker-compose-설명)
5. [개발 환경에서 Docker 사용](#개발-환경에서-docker-사용)
6. [프로덕션 환경에서 Docker 사용](#프로덕션-환경에서-docker-사용)
7. [Docker 명령어 참조](#docker-명령어-참조)
8. [문제 해결](#문제-해결)

## Docker 개요

Docker는 애플리케이션을 컨테이너로 패키징하여 배포하는 플랫폼입니다. Py_Monitor 프로젝트에서는 다음과 같은 이점을 제공합니다:

- **일관된 환경**: 개발, 테스트, 운영 환경의 일관성 보장
- **빠른 배포**: 컨테이너 이미지로 즉시 배포 가능
- **확장성**: 마이크로서비스 아키텍처 지원
- **격리**: 애플리케이션 간 독립성 보장

## Docker 설치

### Linux (Ubuntu/Debian)

```bash
# 기존 Docker 제거 (있다면)
sudo apt-get remove docker docker-engine docker.io containerd runc

# 필요한 패키지 설치
sudo apt-get update
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Docker 공식 GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 저장소 설정
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker
```

### macOS

```bash
# Homebrew를 사용한 설치
brew install --cask docker

# 또는 Docker Desktop 다운로드
# https://www.docker.com/products/docker-desktop
```

### Windows

```bash
# Docker Desktop 다운로드 및 설치
# https://www.docker.com/products/docker-desktop
```

### 설치 확인

```bash
# Docker 버전 확인
docker --version
docker-compose --version

# Docker 실행 테스트
docker run hello-world
```

## Dockerfile 설명

Py_Monitor의 Dockerfile을 단계별로 설명합니다:

```dockerfile
# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile 최적화

```dockerfile
# 멀티스테이지 빌드를 사용한 최적화된 Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 프로덕션 이미지
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 복사
COPY --from=builder /root/.local /root/.local

# 애플리케이션 코드 복사
COPY . .

# PATH 설정
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose 설명

### 기본 docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL 데이터베이스
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: py_monitor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (캐싱 및 세션 저장용)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Py_Monitor 애플리케이션
  app:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/py_monitor
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key-here
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 개발용 docker-compose.dev.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: py_monitor_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data

  app:
    build: .
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/py_monitor_dev
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=dev-secret-key
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./logs:/app/logs
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    depends_on:
      - postgres
      - redis

volumes:
  postgres_dev_data:
  redis_dev_data:
```

### 프로덕션용 docker-compose.prod.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: py_monitor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  app:
    build: .
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/py_monitor
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## 개발 환경에서 Docker 사용

### 1. 개발 환경 시작

```bash
# 개발용 Docker Compose 실행
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f app

# 컨테이너 내부 접속
docker-compose -f docker-compose.dev.yml exec app bash
```

### 2. 코드 변경사항 반영

```bash
# 코드 변경 후 컨테이너 재시작
docker-compose -f docker-compose.dev.yml restart app

# 또는 전체 재빌드
docker-compose -f docker-compose.dev.yml up -d --build
```

### 3. 데이터베이스 작업

```bash
# 마이그레이션 실행
docker-compose -f docker-compose.dev.yml exec app alembic upgrade head

# 데이터베이스 접속
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d py_monitor_dev

# 백업 생성
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U postgres py_monitor_dev > backup.sql
```

### 4. 테스트 실행

```bash
# 컨테이너 내부에서 테스트 실행
docker-compose -f docker-compose.dev.yml exec app pytest

# 특정 테스트 실행
docker-compose -f docker-compose.dev.yml exec app pytest tests/test_api/ -v
```

## 프로덕션 환경에서 Docker 사용

### 1. 프로덕션 배포

```bash
# 환경 변수 설정
export POSTGRES_PASSWORD=your_secure_password
export SECRET_KEY=your_very_secure_secret_key

# 프로덕션 서비스 시작
docker-compose -f docker-compose.prod.yml up -d

# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### 2. 로그 관리

```bash
# 애플리케이션 로그 확인
docker-compose -f docker-compose.prod.yml logs -f app

# 모든 서비스 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 로그 파일 확인
tail -f logs/app.log
```

### 3. 백업 및 복구

```bash
# 데이터베이스 백업
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres py_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# Redis 백업
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# 데이터베이스 복구
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres py_monitor < backup.sql
```

### 4. 스케일링

```bash
# 애플리케이션 인스턴스 확장
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# 로드 밸런서 설정 (nginx.conf 수정 필요)
```

## Docker 명령어 참조

### 기본 명령어

```bash
# 이미지 빌드
docker build -t py-monitor .

# 컨테이너 실행
docker run -d -p 8000:8000 --name py-monitor py-monitor

# 컨테이너 중지
docker stop py-monitor

# 컨테이너 삭제
docker rm py-monitor

# 이미지 삭제
docker rmi py-monitor
```

### Docker Compose 명령어

```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 서비스 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f app

# 서비스 상태 확인
docker-compose ps

# 컨테이너 내부 접속
docker-compose exec app bash

# 이미지 재빌드
docker-compose up -d --build

# 볼륨 삭제
docker-compose down -v
```

### 유용한 명령어

```bash
# 사용하지 않는 리소스 정리
docker system prune -a

# 디스크 사용량 확인
docker system df

# 컨테이너 리소스 사용량 확인
docker stats

# 이미지 히스토리 확인
docker history py-monitor

# 컨테이너 내부 파일 복사
docker cp py-monitor:/app/logs/app.log ./local_logs/
```

## 문제 해결

### 1. 일반적인 문제들

#### 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :8000

# 다른 포트 사용
docker run -d -p 8001:8000 py-monitor
```

#### 권한 문제
```bash
# Docker 그룹에 사용자 추가
sudo usermod -aG docker $USER

# 로그아웃 후 재로그인
```

#### 메모리 부족
```bash
# Docker 메모리 제한 설정
docker run -d -p 8000:8000 --memory=512m py-monitor
```

### 2. 디버깅

#### 컨테이너 로그 확인
```bash
# 실시간 로그
docker logs -f container_name

# 마지막 100줄
docker logs --tail 100 container_name

# 타임스탬프 포함
docker logs -f -t container_name
```

#### 컨테이너 내부 접속
```bash
# bash 접속
docker exec -it container_name bash

# sh 접속 (alpine 이미지)
docker exec -it container_name sh
```

#### 네트워크 문제 해결
```bash
# 네트워크 확인
docker network ls
docker network inspect bridge

# 컨테이너 간 통신 테스트
docker exec container1 ping container2
```

### 3. 성능 최적화

#### 이미지 크기 최적화
```dockerfile
# .dockerignore 파일 생성
node_modules
.git
.env
*.log
__pycache__
.pytest_cache
```

#### 멀티스테이지 빌드
```dockerfile
# 빌드 스테이지
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 프로덕션 스테이지
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
```

#### 볼륨 최적화
```yaml
# docker-compose.yml
volumes:
  - ./logs:/app/logs:delegated
  - ./data:/app/data:cached
```

## 결론

Docker를 사용하면 Py_Monitor 프로젝트를 일관되고 안정적으로 배포할 수 있습니다. 개발 환경에서는 빠른 반복 개발이 가능하고, 프로덕션 환경에서는 확장 가능하고 관리하기 쉬운 인프라를 구축할 수 있습니다.

추가 문의사항이나 문제가 발생하면 GitHub Issues를 통해 문의해 주세요. 