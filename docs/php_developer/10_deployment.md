# 10. 배포와 운영

이 문서에서는 FastAPI 프로젝트의 배포와 운영 방법을 Laravel과 비교하면서 설명합니다.

## 10.1 개발 환경 설정

### 10.1.1 Laravel의 개발 환경
```bash
# Laravel 개발 환경 설정
composer install
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve
```

### 10.1.2 FastAPI의 개발 환경
```bash
# FastAPI 개발 환경 설정
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload
```

## 10.2 프로덕션 환경 설정

### 10.2.1 Laravel의 프로덕션 설정
```bash
# Laravel 프로덕션 설정
composer install --no-dev --optimize-autoloader
php artisan config:cache
php artisan route:cache
php artisan view:cache
php artisan migrate --force
```

### 10.2.2 FastAPI의 프로덕션 설정
```bash
# FastAPI 프로덕션 설정
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 10.3 Docker 배포

### 10.3.1 Laravel의 Docker 설정
```dockerfile
# Laravel Dockerfile
FROM php:8.1-fpm

WORKDIR /var/www/html

COPY . .
RUN composer install --no-dev --optimize-autoloader

RUN chown -R www-data:www-data /var/www/html
```

### 10.3.2 FastAPI의 Docker 설정
```dockerfile
# FastAPI Dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 10.4 Nginx 설정

### 10.4.1 Laravel의 Nginx 설정
```nginx
# Laravel Nginx 설정
server {
    listen 80;
    server_name example.com;
    root /var/www/html/public;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

### 10.4.2 FastAPI의 Nginx 설정
```nginx
# FastAPI Nginx 설정
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 10.5 SSL/TLS 설정

### 10.5.1 Let's Encrypt 인증서 설정
```bash
# Let's Encrypt 인증서 발급
sudo certbot --nginx -d example.com
```

### 10.5.2 Nginx SSL 설정
```nginx
# Nginx SSL 설정
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

## 10.6 모니터링 설정

### 10.6.1 Prometheus 설정
```yaml
# Prometheus 설정
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
```

### 10.6.2 Grafana 대시보드
```json
{
  "dashboard": {
    "title": "FastAPI Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## 10.7 로깅 설정

### 10.7.1 로그 로테이션
```conf
# logrotate 설정
/var/log/fastapi/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload fastapi
    endscript
}
```

### 10.7.2 로그 포맷
```python
# FastAPI 로깅 설정
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)
```

## 10.8 백업 전략

### 10.8.1 데이터베이스 백업
```bash
# PostgreSQL 백업
pg_dump -U postgres -d mydb > backup.sql

# 백업 복원
psql -U postgres -d mydb < backup.sql
```

### 10.8.2 파일 백업
```bash
# 파일 백업 스크립트
#!/bin/bash
BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
pg_dump -U postgres -d mydb > $BACKUP_DIR/db.sql

# 파일 백업
tar -czf $BACKUP_DIR/files.tar.gz /var/www/html

# 오래된 백업 삭제
find /backup -type d -mtime +30 -exec rm -rf {} \;
```

## 10.9 무중단 배포

### 10.9.1 Blue-Green 배포
```yaml
# Docker Compose Blue-Green 배포
version: '3'
services:
  app-blue:
    build: .
    ports:
      - "8001:8000"
  app-green:
    build: .
    ports:
      - "8002:8000"
  nginx:
    image: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 10.9.2 롤백 전략
```bash
# 롤백 스크립트
#!/bin/bash

# 이전 버전으로 롤백
git checkout $PREVIOUS_VERSION
docker-compose down
docker-compose up -d

# 데이터베이스 롤백
psql -U postgres -d mydb < backup.sql
```

## 10.10 운영 체크리스트

### 10.10.1 배포 전 체크리스트
- [ ] 모든 테스트 통과
- [ ] 환경 변수 설정
- [ ] 데이터베이스 마이그레이션
- [ ] 백업 생성
- [ ] SSL 인증서 확인

### 10.10.2 배포 후 체크리스트
- [ ] 애플리케이션 상태 확인
- [ ] 로그 모니터링
- [ ] 성능 메트릭 확인
- [ ] 에러 모니터링
- [ ] 사용자 피드백 수집

### 10.10.3 정기 점검 항목
- [ ] 보안 업데이트
- [ ] 성능 최적화
- [ ] 백업 검증
- [ ] 로그 분석
- [ ] 리소스 사용량 모니터링 