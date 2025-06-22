# Redis 사용법 가이드

이 문서는 Py_Monitor 프로젝트에서 Redis를 사용하는 방법을 상세히 설명합니다.

## 목차

1. [Redis 개요](#redis-개요)
2. [Redis 설치](#redis-설치)
3. [Redis 기본 사용법](#redis-기본-사용법)
4. [Py_Monitor에서 Redis 활용](#py_monitor에서-redis-활용)
5. [캐싱 전략](#캐싱-전략)
6. [세션 관리](#세션-관리)
7. [성능 최적화](#성능-최적화)
8. [모니터링 및 관리](#모니터링-및-관리)
9. [문제 해결](#문제-해결)

## Redis 개요

Redis는 인메모리 데이터 구조 저장소로, Py_Monitor 프로젝트에서 다음과 같은 용도로 사용됩니다:

- **캐싱**: 자주 조회되는 데이터의 빠른 접근
- **세션 저장**: 사용자 세션 정보 관리
- **임시 데이터 저장**: 모니터링 결과 임시 저장
- **큐 관리**: 비동기 작업 큐
- **실시간 알림**: 실시간 상태 업데이트

### Redis의 장점

- **빠른 속도**: 인메모리 기반으로 초당 수만 건 처리
- **다양한 데이터 타입**: String, Hash, List, Set, Sorted Set 지원
- **영속성**: RDB, AOF 방식으로 데이터 영속성 보장
- **확장성**: 클러스터링 지원
- **원자성**: 트랜잭션 및 Lua 스크립트 지원

## Redis 설치

### Docker를 사용한 설치 (권장)

```bash
# Redis 컨테이너 실행
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 또는 Docker Compose 사용
docker-compose up -d redis
```

### Linux (Ubuntu/Debian)

```bash
# Redis 설치
sudo apt update
sudo apt install redis-server

# Redis 서비스 시작
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Redis 상태 확인
sudo systemctl status redis-server
```

### macOS

```bash
# Homebrew를 사용한 설치
brew install redis

# Redis 서비스 시작
brew services start redis
```

### Windows

```bash
# WSL2를 통한 설치 (권장)
# 또는 Redis for Windows 다운로드
# https://github.com/microsoftarchive/redis/releases
```

### 설치 확인

```bash
# Redis 클라이언트 접속
redis-cli

# 연결 테스트
127.0.0.1:6379> ping
PONG

# 버전 확인
127.0.0.1:6379> info server
```

## Redis 기본 사용법

### 1. 기본 명령어

```bash
# Redis 클라이언트 접속
redis-cli

# 기본 명령어들
SET key value          # 값 설정
GET key                # 값 조회
DEL key                # 키 삭제
EXISTS key             # 키 존재 확인
EXPIRE key seconds     # 만료 시간 설정
TTL key                # 남은 시간 확인
KEYS pattern           # 패턴으로 키 검색
FLUSHALL               # 모든 데이터 삭제
```

### 2. 데이터 타입별 사용법

#### String (문자열)
```bash
# 기본 문자열
SET user:1:name "John Doe"
GET user:1:name

# 숫자 증가/감소
SET counter 0
INCR counter
DECR counter
INCRBY counter 10

# 만료 시간 설정
SETEX session:123 3600 "user_data"
```

#### Hash (해시)
```bash
# 해시 필드 설정
HSET user:1 name "John" email "john@example.com" age 30
HGET user:1 name
HGETALL user:1

# 해시 필드 존재 확인
HEXISTS user:1 email

# 해시 필드 삭제
HDEL user:1 age
```

#### List (리스트)
```bash
# 리스트에 값 추가
LPUSH notifications "New alert"
RPUSH notifications "System update"

# 리스트에서 값 가져오기
LPOP notifications
RPOP notifications

# 리스트 범위 조회
LRANGE notifications 0 -1
```

#### Set (집합)
```bash
# 집합에 값 추가
SADD online_users "user1" "user2" "user3"

# 집합 멤버 확인
SISMEMBER online_users "user1"

# 집합 멤버 조회
SMEMBERS online_users

# 집합 크기
SCARD online_users
```

#### Sorted Set (정렬된 집합)
```bash
# 점수와 함께 값 추가
ZADD leaderboard 100 "player1" 200 "player2" 150 "player3"

# 순위 조회
ZRANK leaderboard "player2"

# 점수 범위로 조회
ZRANGEBYSCORE leaderboard 100 200
```

### 3. 고급 기능

#### 트랜잭션
```bash
# 트랜잭션 시작
MULTI

# 명령어들
SET account:1 1000
SET account:2 2000
INCRBY account:1 -100
INCRBY account:2 100

# 트랜잭션 실행
EXEC
```

#### Lua 스크립트
```bash
# Lua 스크립트 실행
EVAL "return redis.call('GET', KEYS[1])" 1 "mykey"

# 조건부 업데이트
EVAL "
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('SET', KEYS[1], ARGV[2])
else
    return 0
end
" 1 "counter" "10" "20"
```

## Py_Monitor에서 Redis 활용

### 1. Redis 연결 설정

```python
# app/core/redis_client.py
import redis
from app.core.settings import settings

# Redis 클라이언트 생성
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

def get_redis_client():
    """Redis 클라이언트 반환"""
    return redis_client
```

### 2. 캐싱 유틸리티

```python
# app/utils/cache.py
import json
import hashlib
from typing import Any, Optional
from app.core.redis_client import get_redis_client

class CacheManager:
    def __init__(self):
        self.redis = get_redis_client()
    
    def _generate_key(self, prefix: str, *args) -> str:
        """캐시 키 생성"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """값을 캐시에 저장"""
        try:
            serialized_value = json.dumps(value)
            return self.redis.setex(key, expire, serialized_value)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 확인"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

# 전역 캐시 매니저 인스턴스
cache_manager = CacheManager()
```

### 3. 모니터링 결과 캐싱

```python
# app/services/monitoring_service.py
from app.utils.cache import cache_manager
from app.models.monitoring import MonitoringLog
import time

class MonitoringService:
    def __init__(self):
        self.cache = cache_manager
    
    def get_monitoring_result(self, project_id: int) -> dict:
        """모니터링 결과 조회 (캐시 우선)"""
        cache_key = f"monitoring:result:{project_id}"
        
        # 캐시에서 조회
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # 데이터베이스에서 조회
        result = self._get_from_database(project_id)
        
        # 캐시에 저장 (5분)
        self.cache.set(cache_key, result, expire=300)
        
        return result
    
    def update_monitoring_result(self, project_id: int, result: dict):
        """모니터링 결과 업데이트"""
        # 데이터베이스 업데이트
        self._update_database(project_id, result)
        
        # 캐시 무효화
        cache_key = f"monitoring:result:{project_id}"
        self.cache.delete(cache_key)
    
    def get_recent_alerts(self, project_id: int, limit: int = 10) -> list:
        """최근 알림 조회"""
        cache_key = f"alerts:recent:{project_id}:{limit}"
        
        cached_alerts = self.cache.get(cache_key)
        if cached_alerts:
            return cached_alerts
        
        alerts = self._get_alerts_from_database(project_id, limit)
        self.cache.set(cache_key, alerts, expire=60)  # 1분 캐시
        
        return alerts
```

### 4. 세션 관리

```python
# app/core/session.py
import json
import uuid
from datetime import datetime, timedelta
from app.core.redis_client import get_redis_client

class SessionManager:
    def __init__(self):
        self.redis = get_redis_client()
        self.session_prefix = "session:"
        self.default_expire = 3600  # 1시간
    
    def create_session(self, user_id: int, user_data: dict) -> str:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        key = f"{self.session_prefix}{session_id}"
        self.redis.setex(
            key,
            self.default_expire,
            json.dumps(session_data)
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> dict:
        """세션 조회"""
        key = f"{self.session_prefix}{session_id}"
        session_data = self.redis.get(key)
        
        if session_data:
            session = json.loads(session_data)
            # 마지막 활동 시간 업데이트
            session["last_activity"] = datetime.utcnow().isoformat()
            self.redis.setex(key, self.default_expire, json.dumps(session))
            return session
        
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        key = f"{self.session_prefix}{session_id}"
        return bool(self.redis.delete(key))
    
    def extend_session(self, session_id: str, expire: int = None) -> bool:
        """세션 만료 시간 연장"""
        key = f"{self.session_prefix}{session_id}"
        if expire is None:
            expire = self.default_expire
        
        return bool(self.redis.expire(key, expire))

# 전역 세션 매니저
session_manager = SessionManager()
```

### 5. 실시간 알림 시스템

```python
# app/services/notification_service.py
import json
from typing import List, Dict
from app.core.redis_client import get_redis_client

class NotificationService:
    def __init__(self):
        self.redis = get_redis_client()
        self.notification_channel = "notifications"
    
    def publish_notification(self, user_id: int, notification: dict):
        """알림 발행"""
        notification_data = {
            "user_id": user_id,
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Redis Pub/Sub으로 알림 발행
        self.redis.publish(
            f"{self.notification_channel}:{user_id}",
            json.dumps(notification_data)
        )
        
        # 최근 알림 목록에 추가
        self._add_to_recent_notifications(user_id, notification_data)
    
    def get_recent_notifications(self, user_id: int, limit: int = 10) -> List[Dict]:
        """최근 알림 조회"""
        key = f"notifications:recent:{user_id}"
        notifications = self.redis.lrange(key, 0, limit - 1)
        
        return [json.loads(n) for n in notifications]
    
    def _add_to_recent_notifications(self, user_id: int, notification: dict):
        """최근 알림 목록에 추가"""
        key = f"notifications:recent:{user_id}"
        
        # 리스트 앞에 추가
        self.redis.lpush(key, json.dumps(notification))
        
        # 최대 100개만 유지
        self.redis.ltrim(key, 0, 99)
        
        # 24시간 만료
        self.redis.expire(key, 86400)
```

## 캐싱 전략

### 1. 캐시 계층 구조

```python
# app/core/cache_strategy.py
from enum import Enum
from typing import Any, Optional
from app.utils.cache import cache_manager

class CacheLevel(Enum):
    L1 = "l1"  # 메모리 캐시 (애플리케이션 레벨)
    L2 = "l2"  # Redis 캐시
    L3 = "l3"  # 데이터베이스

class CacheStrategy:
    def __init__(self):
        self.l1_cache = {}  # 간단한 메모리 캐시
        self.l2_cache = cache_manager
    
    def get(self, key: str, level: CacheLevel = CacheLevel.L2) -> Optional[Any]:
        """계층별 캐시 조회"""
        if level == CacheLevel.L1:
            return self.l1_cache.get(key)
        elif level == CacheLevel.L2:
            return self.l2_cache.get(key)
        return None
    
    def set(self, key: str, value: Any, level: CacheLevel = CacheLevel.L2, expire: int = 3600):
        """계층별 캐시 저장"""
        if level == CacheLevel.L1:
            self.l1_cache[key] = value
        elif level == CacheLevel.L2:
            self.l2_cache.set(key, value, expire)
    
    def invalidate(self, pattern: str, level: CacheLevel = CacheLevel.L2):
        """패턴으로 캐시 무효화"""
        if level == CacheLevel.L1:
            # L1 캐시는 패턴 매칭이 어려우므로 전체 삭제
            self.l1_cache.clear()
        elif level == CacheLevel.L2:
            # Redis에서 패턴 매칭으로 키 삭제
            keys = self.l2_cache.redis.keys(pattern)
            if keys:
                self.l2_cache.redis.delete(*keys)
```

### 2. 캐시 무효화 전략

```python
# app/utils/cache_invalidation.py
from typing import List, Set
from app.core.redis_client import get_redis_client

class CacheInvalidationStrategy:
    def __init__(self):
        self.redis = get_redis_client()
    
    def invalidate_project_cache(self, project_id: int):
        """프로젝트 관련 캐시 무효화"""
        patterns = [
            f"monitoring:result:{project_id}",
            f"alerts:recent:{project_id}:*",
            f"project:stats:{project_id}",
            f"project:config:{project_id}"
        ]
        
        for pattern in patterns:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
    
    def invalidate_user_cache(self, user_id: int):
        """사용자 관련 캐시 무효화"""
        patterns = [
            f"user:sessions:{user_id}",
            f"user:preferences:{user_id}",
            f"notifications:recent:{user_id}"
        ]
        
        for pattern in patterns:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
    
    def invalidate_global_cache(self):
        """전역 캐시 무효화"""
        patterns = [
            "system:stats:*",
            "global:config:*",
            "cache:version:*"
        ]
        
        for pattern in patterns:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
```

## 세션 관리

### 1. 세션 미들웨어

```python
# app/middleware/session_middleware.py
from fastapi import Request, Response
from app.core.session import session_manager
import json

async def session_middleware(request: Request, call_next):
    """세션 관리 미들웨어"""
    
    # 세션 ID 추출
    session_id = request.cookies.get("session_id")
    
    if session_id:
        # 세션 조회
        session = session_manager.get_session(session_id)
        if session:
            request.state.session = session
            request.state.user_id = session["user_id"]
    
    response = await call_next(request)
    
    # 새 세션 생성 (로그인 시)
    if hasattr(request.state, 'new_session_id'):
        response.set_cookie(
            key="session_id",
            value=request.state.new_session_id,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=3600
        )
    
    return response
```

### 2. 세션 기반 인증

```python
# app/core/auth.py
from fastapi import HTTPException, Depends
from app.core.session import session_manager

def get_current_user(request: Request):
    """현재 사용자 조회"""
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return request.state.user_id

def require_auth(user_id: int = Depends(get_current_user)):
    """인증 필요 데코레이터"""
    return user_id

def create_user_session(user_id: int, user_data: dict, request: Request):
    """사용자 세션 생성"""
    session_id = session_manager.create_session(user_id, user_data)
    request.state.new_session_id = session_id
    return session_id
```

## 성능 최적화

### 1. Redis 연결 풀

```python
# app/core/redis_pool.py
import redis
from app.core.settings import settings

# 연결 풀 생성
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=20,
    retry_on_timeout=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

def get_redis_connection():
    """Redis 연결 반환"""
    return redis.Redis(connection_pool=redis_pool, decode_responses=True)
```

### 2. 파이프라인 사용

```python
# app/utils/redis_pipeline.py
from app.core.redis_client import get_redis_client

def batch_cache_operations(operations: list):
    """배치 캐시 작업"""
    redis_client = get_redis_client()
    
    with redis_client.pipeline() as pipe:
        for operation in operations:
            if operation["type"] == "set":
                pipe.setex(operation["key"], operation["expire"], operation["value"])
            elif operation["type"] == "delete":
                pipe.delete(operation["key"])
            elif operation["type"] == "expire":
                pipe.expire(operation["key"], operation["expire"])
        
        # 모든 작업 실행
        pipe.execute()
```

### 3. 캐시 히트율 모니터링

```python
# app/utils/cache_monitoring.py
import time
from app.core.redis_client import get_redis_client

class CacheMonitor:
    def __init__(self):
        self.redis = get_redis_client()
        self.stats_key = "cache:stats"
    
    def record_cache_hit(self, key: str):
        """캐시 히트 기록"""
        today = time.strftime("%Y-%m-%d")
        hit_key = f"{self.stats_key}:hits:{today}"
        self.redis.incr(hit_key)
    
    def record_cache_miss(self, key: str):
        """캐시 미스 기록"""
        today = time.strftime("%Y-%m-%d")
        miss_key = f"{self.stats_key}:misses:{today}"
        self.redis.incr(miss_key)
    
    def get_cache_stats(self, date: str = None) -> dict:
        """캐시 통계 조회"""
        if date is None:
            date = time.strftime("%Y-%m-%d")
        
        hits = int(self.redis.get(f"{self.stats_key}:hits:{date}") or 0)
        misses = int(self.redis.get(f"{self.stats_key}:misses:{date}") or 0)
        total = hits + misses
        
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        return {
            "date": date,
            "hits": hits,
            "misses": misses,
            "total": total,
            "hit_rate": round(hit_rate, 2)
        }
```

## 모니터링 및 관리

### 1. Redis 상태 모니터링

```python
# app/utils/redis_monitoring.py
from app.core.redis_client import get_redis_client

class RedisMonitor:
    def __init__(self):
        self.redis = get_redis_client()
    
    def get_redis_info(self) -> dict:
        """Redis 정보 조회"""
        info = self.redis.info()
        
        return {
            "version": info.get("redis_version"),
            "uptime": info.get("uptime_in_seconds"),
            "connected_clients": info.get("connected_clients"),
            "used_memory": info.get("used_memory_human"),
            "used_memory_peak": info.get("used_memory_peak_human"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "hit_rate": self._calculate_hit_rate(info)
        }
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """히트율 계산"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    def get_memory_usage(self) -> dict:
        """메모리 사용량 조회"""
        info = self.redis.info("memory")
        
        return {
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "used_memory_peak": info.get("used_memory_peak"),
            "used_memory_peak_human": info.get("used_memory_peak_human"),
            "used_memory_rss": info.get("used_memory_rss"),
            "used_memory_rss_human": info.get("used_memory_rss_human")
        }
    
    def get_slow_logs(self, limit: int = 10) -> list:
        """슬로우 로그 조회"""
        return self.redis.slowlog_get(limit)
```

### 2. Redis 관리 명령어

```bash
# Redis 정보 조회
redis-cli info

# 메모리 사용량
redis-cli info memory

# 클라이언트 연결 정보
redis-cli client list

# 키 개수 조회
redis-cli dbsize

# 특정 패턴의 키 조회
redis-cli keys "pattern:*"

# 키 타입 조회
redis-cli type key_name

# 키 만료 시간 조회
redis-cli ttl key_name

# 메모리 사용량 분석
redis-cli memory usage key_name

# 슬로우 로그 조회
redis-cli slowlog get 10
```

## 문제 해결

### 1. 일반적인 문제들

#### 메모리 부족
```bash
# 메모리 사용량 확인
redis-cli info memory

# 메모리 정책 확인
redis-cli config get maxmemory-policy

# 메모리 정책 설정
redis-cli config set maxmemory-policy allkeys-lru
```

#### 연결 문제
```bash
# 연결 테스트
redis-cli ping

# 연결 수 확인
redis-cli info clients

# 연결 제한 확인
redis-cli config get maxclients
```

#### 성능 문제
```bash
# 명령어 통계
redis-cli info stats

# 슬로우 로그 확인
redis-cli slowlog get 10

# 모니터링 모드
redis-cli monitor
```

### 2. 백업 및 복구

```bash
# RDB 백업
redis-cli save

# AOF 백업
redis-cli bgrewriteaof

# 백업 파일 위치 확인
redis-cli config get dir

# 백업에서 복구
redis-server --appendonly yes
```

### 3. 클러스터링

```bash
# Redis Cluster 설정
redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002

# 클러스터 정보 확인
redis-cli --cluster info 127.0.0.1:7000

# 노드 추가
redis-cli --cluster add-node 127.0.0.1:7003 127.0.0.1:7000
```

## 결론

Redis를 활용하면 Py_Monitor 프로젝트의 성능을 크게 향상시킬 수 있습니다. 적절한 캐싱 전략과 세션 관리, 실시간 알림 시스템을 구축하여 사용자 경험을 개선할 수 있습니다.

정기적인 모니터링과 백업을 통해 안정적인 Redis 운영을 유지하세요.

추가 문의사항이나 문제가 발생하면 GitHub Issues를 통해 문의해 주세요. 