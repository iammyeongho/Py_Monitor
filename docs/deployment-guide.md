# Py_Monitor 배포 가이드

이 문서는 Py_Monitor 프로젝트를 다양한 환경에 배포하는 방법을 설명합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [Docker를 사용한 배포](#docker를-사용한-배포)
3. [수동 배포](#수동-배포)
4. [클라우드 배포](#클라우드-배포)
5. [모니터링 및 로깅](#모니터링-및-로깅)
6. [백업 및 복구](#백업-및-복구)
7. [문제 해결](#문제-해결)

## 사전 요구사항

### 시스템 요구사항

- **CPU**: 최소 2코어, 권장 4코어 이상
- **메모리**: 최소 4GB, 권장 8GB 이상
- **저장공간**: 최소 20GB, 권장 50GB 이상
- **네트워크**: 안정적인 인터넷 연결

### 소프트웨어 요구사항

#### Docker 배포 시
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

#### 수동 배포 시
- Python 3.11+
- PostgreSQL 13+
- Redis 6+ (선택사항)
- Nginx (선택사항)

## Docker를 사용한 배포

### 1. 프로젝트 클론

```bash
git clone https://github.com/iammyeongho/Py_Monitor.git
cd Py_Monitor
```

### 2. 환경 변수 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# 환경 변수 편집
nano .env
```

**필수 환경 변수 설정:**

```env
# 환경 설정
ENVIRONMENT=production
DEBUG=false

# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:your_secure_password@postgres:5432/py_monitor
POSTGRES_PASSWORD=your_secure_password

# Redis 설정
REDIS_URL=redis://redis:6379

# 보안 설정
SECRET_KEY=your_very_secure_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 이메일 설정 (선택사항)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_TLS=true
SMTP_FROM=your_email@gmail.com

# 로깅 설정
LOG_LEVEL=INFO
LOG_DIR=logs
```

### 3. Docker Compose로 배포

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

### 4. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
docker-compose exec app alembic upgrade head

# 또는 Makefile 사용
make migrate
```

### 5. 초기 관리자 계정 생성

```bash
# 컨테이너 내부 접속
docker-compose exec app bash

# 관리자 계정 생성 스크립트 실행
python scripts/create_admin.py
```

### 6. 서비스 확인

- **애플리케이션**: http://your-server-ip:8000
- **API 문서**: http://your-server-ip:8000/docs
- **헬스체크**: http://your-server-ip:8000/health

## 수동 배포

### 1. 시스템 패키지 설치

#### Ubuntu/Debian
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 및 필수 패키지 설치
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server nginx

# Git 설치
sudo apt install -y git
```

#### CentOS/RHEL
```bash
# EPEL 저장소 활성화
sudo yum install -y epel-release

# Python 및 필수 패키지 설치
sudo yum install -y python3.11 python3.11-devel
sudo yum install -y postgresql postgresql-server postgresql-contrib
sudo yum install -y redis nginx

# Git 설치
sudo yum install -y git
```

### 2. PostgreSQL 설정

```bash
# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# PostgreSQL 사용자 생성
sudo -u postgres createuser --interactive
# Enter name of role to add: py_monitor
# Shall the new role be a superuser? (y/n) n
# Shall the new role be allowed to create databases? (y/n) y
# Shall the new role be allowed to create more new roles? (y/n) n

# 데이터베이스 생성
sudo -u postgres createdb py_monitor

# 비밀번호 설정
sudo -u postgres psql
postgres=# ALTER USER py_monitor WITH PASSWORD 'your_secure_password';
postgres=# \q
```

### 3. Redis 설정

```bash
# Redis 서비스 시작
sudo systemctl start redis
sudo systemctl enable redis

# Redis 설정 확인
redis-cli ping
# 응답: PONG
```

### 4. 애플리케이션 배포

```bash
# 프로젝트 클론
git clone https://github.com/iammyeongho/Py_Monitor.git
cd Py_Monitor

# 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
nano .env

# 데이터베이스 마이그레이션
alembic upgrade head

# 애플리케이션 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Nginx 설정

```bash
# Nginx 설정 파일 생성
sudo nano /etc/nginx/sites-available/py-monitor
```

**Nginx 설정 내용:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/Py_Monitor/frontend/;
        expires 30d;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/py-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Systemd 서비스 설정

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/py-monitor.service
```

**서비스 파일 내용:**

```ini
[Unit]
Description=Py_Monitor Web Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/Py_Monitor
Environment=PATH=/path/to/Py_Monitor/.venv/bin
ExecStart=/path/to/Py_Monitor/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable py-monitor
sudo systemctl start py-monitor
```

## 클라우드 배포

### AWS EC2 배포

#### 1. EC2 인스턴스 생성
- **AMI**: Ubuntu 22.04 LTS
- **인스턴스 타입**: t3.medium 이상
- **스토리지**: 20GB 이상
- **보안 그룹**: SSH(22), HTTP(80), HTTPS(443), Custom(8000)

#### 2. 인스턴스 접속 및 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 3. 애플리케이션 배포

```bash
# 프로젝트 클론
git clone https://github.com/iammyeongho/Py_Monitor.git
cd Py_Monitor

# 환경 변수 설정
cp .env.example .env
nano .env

# Docker Compose로 배포
docker-compose up -d
```

### Google Cloud Platform 배포

#### 1. Compute Engine 인스턴스 생성
- **머신 타입**: e2-medium 이상
- **부팅 디스크**: Ubuntu 22.04 LTS
- **방화벽 규칙**: HTTP, HTTPS, Custom(8000)

#### 2. 배포 스크립트

```bash
# 배포 스크립트 생성
nano deploy.sh
```

**배포 스크립트 내용:**

```bash
#!/bin/bash

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 프로젝트 클론
git clone https://github.com/iammyeongho/Py_Monitor.git
cd Py_Monitor

# 환경 변수 설정
cp .env.example .env
# 환경 변수 편집 필요

# 서비스 시작
docker-compose up -d
```

```bash
# 스크립트 실행 권한 부여
chmod +x deploy.sh
./deploy.sh
```

## 모니터링 및 로깅

### 1. 애플리케이션 로그 확인

```bash
# Docker 로그
docker-compose logs -f app

# 시스템 로그
sudo journalctl -u py-monitor -f

# 로그 파일 확인
tail -f logs/app.log
```

### 2. 시스템 모니터링

```bash
# 시스템 리소스 확인
htop
df -h
free -h

# 네트워크 연결 확인
netstat -tulpn | grep :8000
```

### 3. 데이터베이스 모니터링

```bash
# PostgreSQL 연결 확인
docker-compose exec postgres psql -U postgres -d py_monitor -c "SELECT version();"

# Redis 연결 확인
docker-compose exec redis redis-cli ping
```

## 백업 및 복구

### 1. 데이터베이스 백업

```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U postgres py_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 자동 백업 스크립트
nano backup.sh
```

**백업 스크립트 내용:**

```bash
#!/bin/bash

BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# PostgreSQL 백업
docker-compose exec -T postgres pg_dump -U postgres py_monitor > $BACKUP_DIR/db_backup_$DATE.sql

# Redis 백업
docker-compose exec redis redis-cli BGSAVE
docker cp py-monitor_redis_1:/data/dump.rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# 로그 백업
tar -czf $BACKUP_DIR/logs_backup_$DATE.tar.gz logs/

# 30일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. 데이터베이스 복구

```bash
# PostgreSQL 복구
docker-compose exec -T postgres psql -U postgres py_monitor < backup_20231201_120000.sql

# Redis 복구
docker cp backup_20231201_120000.rdb py-monitor_redis_1:/data/dump.rdb
docker-compose restart redis
```

## 문제 해결

### 1. 일반적인 문제들

#### 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :8000

# 프로세스 종료
sudo kill -9 <PID>
```

#### 데이터베이스 연결 실패
```bash
# PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql

# 연결 테스트
psql -h localhost -U postgres -d py_monitor
```

#### Docker 컨테이너 문제
```bash
# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 재시작
docker-compose restart

# 컨테이너 로그 확인
docker-compose logs app
```

### 2. 성능 최적화

#### 데이터베이스 최적화
```sql
-- 인덱스 생성
CREATE INDEX idx_monitoring_logs_project_id ON monitoring_logs(project_id);
CREATE INDEX idx_monitoring_logs_created_at ON monitoring_logs(created_at);

-- 테이블 분석
ANALYZE monitoring_logs;
```

#### Redis 캐싱 설정
```python
# app/core/cache.py
import redis
from app.core.settings import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)

def cache_result(key: str, value: str, expire: int = 3600):
    """결과를 Redis에 캐싱"""
    redis_client.setex(key, expire, value)

def get_cached_result(key: str) -> str:
    """캐시된 결과 조회"""
    return redis_client.get(key)
```

### 3. 보안 강화

#### 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
sudo ufw enable
```

#### SSL/TLS 설정
```bash
# Let's Encrypt 인증서 설치
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 결론

이 가이드를 따라 Py_Monitor를 성공적으로 배포할 수 있습니다. 배포 후에는 정기적인 모니터링과 백업을 통해 안정적인 서비스를 제공하세요.

추가 문의사항이나 문제가 발생하면 GitHub Issues를 통해 문의해 주세요. 