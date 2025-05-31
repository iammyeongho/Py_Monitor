# PostgreSQL 설정 및 프로젝트 연동 가이드

## 1. PostgreSQL 계정 정보 확인

### 1.1 PostgreSQL 서비스 상태 확인
```bash
# macOS (Homebrew)
brew services list | grep postgres

# Linux (systemd)
sudo systemctl status postgresql

# Linux (service)
sudo service postgresql status
```

### 1.2 PostgreSQL 서비스 시작/중지
```bash
# macOS (Homebrew)
brew services start postgresql
brew services stop postgresql
brew services restart postgresql

# Linux (systemd)
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql

# Linux (service)
sudo service postgresql start
sudo service postgresql stop
sudo service postgresql restart
```

### 1.3 현재 PostgreSQL 사용자 목록 확인
```bash
# PostgreSQL에 접속
# macOS/Linux
psql postgres

# 또는 특정 사용자로 접속
psql -U [사용자명] postgres

# 사용자 목록 확인
\du

# 또는 다음 명령어로 확인
SELECT usename AS role_name,
       CASE 
           WHEN usesuper AND usecreatedb THEN 'superuser, create database'
           WHEN usesuper THEN 'superuser'
           WHEN usecreatedb THEN 'create database'
           ELSE 'none'
       END AS role_attributes
FROM pg_user
ORDER BY role_name;
```

### 1.4 데이터베이스 목록 확인
```bash
# PostgreSQL에 접속
psql postgres

# 데이터베이스 목록 확인
\l

# 또는 다음 명령어로 확인
SELECT datname FROM pg_database;
```

### 1.5 스키마 목록 확인
```bash
# 특정 데이터베이스에 접속
psql -d [데이터베이스명]

# 스키마 목록 확인
\dn

# 또는 다음 명령어로 확인
SELECT schema_name 
FROM information_schema.schemata;
```

### 1.6 PostgreSQL 설치 확인 및 버전 확인
```bash
# macOS
brew list postgresql
psql --version

# Linux
dpkg -l | grep postgresql  # Debian/Ubuntu
rpm -qa | grep postgresql  # RHEL/CentOS
psql --version
```

## 2. 프로젝트와 PostgreSQL 연동

### 2.1 환경 변수 설정
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 설정:

```env
# Database settings
POSTGRES_SERVER=localhost
POSTGRES_USER=[사용자명]
POSTGRES_PASSWORD=[비밀번호]
POSTGRES_DB=[데이터베이스명]
```

### 2.2 데이터베이스 연결 설정
`app/core/config.py`에서 데이터베이스 URI가 다음과 같이 설정되어 있는지 확인:

```python
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
    f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
)
```

### 2.3 스키마 설정
PostgreSQL에서 스키마를 생성하고 사용하도록 설정:

```sql
-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS py_monitor;

-- 스키마 권한 설정
GRANT ALL ON SCHEMA py_monitor TO [사용자명];

-- 스키마 사용 설정
SET search_path TO py_monitor;
```

### 2.4 SQLAlchemy 스키마 설정
`app/db/base.py`에서 스키마를 지정:

```python
from sqlalchemy import MetaData

metadata = MetaData(schema="py_monitor")
Base = declarative_base(metadata=metadata)
```

## 3. 테스트 환경 설정

### 3.1 테스트용 데이터베이스 설정
`tests/conftest.py`에서 테스트용 데이터베이스 설정:

```python
TEST_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
)
```

### 3.2 테스트 실행
```bash
# 전체 테스트 실행
pytest tests/ -v

# 특정 테스트 파일 실행
pytest tests/test_users.py -v
```

## 4. 문제 해결

### 4.1 연결 오류
- PostgreSQL 서비스가 실행 중인지 확인
  ```bash
  # macOS
  brew services list | grep postgres
  
  # Linux
  sudo systemctl status postgresql
  ```
- 사용자명과 비밀번호가 올바른지 확인
- 데이터베이스가 존재하는지 확인
- 스키마 권한이 올바르게 설정되어 있는지 확인

### 4.2 권한 오류
- 사용자에게 필요한 권한이 부여되어 있는지 확인
  ```sql
  -- 사용자 권한 확인
  \du [사용자명]
  
  -- 스키마 권한 확인
  SELECT * FROM information_schema.role_table_grants 
  WHERE grantee = '[사용자명]';
  ```
- 스키마에 대한 접근 권한이 있는지 확인

### 4.3 스키마 오류
- 스키마가 존재하는지 확인
  ```sql
  \dn
  SELECT schema_name FROM information_schema.schemata;
  ```
- 테이블이 올바른 스키마에 생성되었는지 확인
  ```sql
  \dt py_monitor.*
  SELECT * FROM information_schema.tables 
  WHERE table_schema = 'py_monitor';
  ```

### 4.4 로그 확인
```bash
# macOS
tail -f /usr/local/var/log/postgres.log

# Linux
tail -f /var/log/postgresql/postgresql-*.log
``` 