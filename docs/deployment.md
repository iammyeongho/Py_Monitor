# 배포 가이드

## 1. 환경 준비

### 1.1 서버 요구사항
- CPU: 2코어 이상
- RAM: 4GB 이상
- 디스크: 20GB 이상
- OS: Ubuntu 20.04 LTS

### 1.2 필수 소프트웨어
- Python 3.9+
- PostgreSQL 13+
- Nginx
- Redis
- Docker (선택사항)

## 2. 배포 프로세스

### 2.1 코드 배포
```bash
# 코드 클론
git clone https://github.com/iammyeongho/Py_Monitor.git

# 가상환경 설정
python -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 수정
```

### 2.2 데이터베이스 설정
```bash
# 데이터베이스 생성
createdb py_monitor

# 마이그레이션 실행
alembic upgrade head

# 초기 데이터 로드
python scripts/load_initial_data.py
```

### 2.3 Nginx 설정
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 3. 서비스 관리

### 3.1 systemd 서비스 설정
```ini
[Unit]
Description=Py_Monitor
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/Py_Monitor
Environment="PATH=/path/to/Py_Monitor/.venv/bin"
ExecStart=/path/to/Py_Monitor/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

### 3.2 서비스 시작/중지
```bash
# 서비스 시작
sudo systemctl start py_monitor

# 서비스 상태 확인
sudo systemctl status py_monitor

# 서비스 중지
sudo systemctl stop py_monitor
```

## 4. 모니터링 설정

### 4.1 로그 설정
```python
# logging.conf
[loggers]
keys=root,app

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_app]
level=INFO
handlers=fileHandler
qualname=app
propagate=0
```

### 4.2 알림 설정
```python
# notifications.conf
[email]
smtp_server=smtp.gmail.com
smtp_port=587
username=your-email@gmail.com
password=your-app-password

[webhook]
endpoint=https://your-webhook-url.com
```

## 5. 백업 및 복구

### 5.1 데이터베이스 백업
```bash
# 백업 스크립트
#!/bin/bash
pg_dump py_monitor > backup_$(date +%Y%m%d).sql
```

### 5.2 복구 프로세스
```bash
# 데이터베이스 복구
psql py_monitor < backup_20250601.sql
```

## 6. SSL/TLS 설정

### 6.1 Let's Encrypt 인증서
```bash
# 인증서 발급
sudo certbot --nginx -d your-domain.com
```

### 6.2 Nginx SSL 설정
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

## 7. 유지보수

### 7.1 로그 로테이션
```conf
# /etc/logrotate.d/py_monitor
/path/to/Py_Monitor/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

### 7.2 정기적인 업데이트
```bash
# 의존성 업데이트
pip install --upgrade -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head
``` 