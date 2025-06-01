# 8. 성능 최적화

이 문서에서는 FastAPI 프로젝트의 성능 최적화 방법을 Laravel과 비교하면서 설명합니다.

## 8.1 비동기 처리

### 8.1.1 Laravel의 비동기 처리
```php
// Laravel의 비동기 작업
class ProcessPodcast implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function handle()
    {
        // 비동기로 처리할 작업
    }
}

// 작업 실행
ProcessPodcast::dispatch();
```

### 8.1.2 FastAPI의 비동기 처리
```python
# FastAPI의 비동기 엔드포인트
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()

@app.get("/async-endpoint")
async def async_endpoint():
    # 비동기 작업
    result = await some_async_operation()
    return JSONResponse(content=result)

# 백그라운드 작업
from fastapi import BackgroundTasks

@app.post("/send-notification")
async def send_notification(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_notification)
    return {"message": "Notification will be sent"}
```

## 8.2 캐싱 전략

### 8.2.1 Laravel의 캐싱
```php
// Laravel의 캐시 사용
use Illuminate\Support\Facades\Cache;

// 데이터 캐싱
Cache::put('key', 'value', 3600);

// 캐시된 데이터 조회
$value = Cache::get('key');

// 캐시 태그 사용
Cache::tags(['users', 'posts'])->put('key', 'value', 3600);
```

### 8.2.2 FastAPI의 캐싱
```python
# FastAPI의 캐시 사용
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Redis 백엔드 설정
FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

# 캐시 데코레이터 사용
@app.get("/cached-endpoint")
@cache(expire=3600)
async def cached_endpoint():
    return {"data": "cached data"}
```

## 8.3 데이터베이스 최적화

### 8.3.1 Laravel의 데이터베이스 최적화
```php
// Laravel의 쿼리 최적화
// Eager Loading
$users = User::with('posts')->get();

// 청크 처리
User::chunk(100, function ($users) {
    foreach ($users as $user) {
        // 처리
    }
});

// 인덱스 사용
Schema::table('users', function (Blueprint $table) {
    $table->index(['email', 'created_at']);
});
```

### 8.3.2 FastAPI의 데이터베이스 최적화
```python
# FastAPI의 쿼리 최적화
from sqlalchemy.orm import joinedload
from sqlalchemy import Index

# Eager Loading
users = db.query(User).options(joinedload(User.posts)).all()

# 청크 처리
def process_users_in_chunks(session, chunk_size=100):
    offset = 0
    while True:
        users = session.query(User).offset(offset).limit(chunk_size).all()
        if not users:
            break
        for user in users:
            # 처리
        offset += chunk_size

# 인덱스 생성
Index('idx_user_email_created', User.email, User.created_at)
```

## 8.4 API 응답 최적화

### 8.4.1 응답 압축
```python
# FastAPI의 응답 압축
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 8.4.2 응답 캐싱
```python
# FastAPI의 응답 캐싱
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

@app.get("/cached-response")
async def cached_response(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return JSONResponse(content={"data": "cached response"})
```

## 8.5 리소스 관리

### 8.5.1 메모리 관리
1. **메모리 사용량 모니터링**
   ```python
   import psutil
   import os

   def get_memory_usage():
       process = psutil.Process(os.getpid())
       return process.memory_info().rss / 1024 / 1024  # MB
   ```

2. **메모리 누수 방지**
   ```python
   from contextlib import contextmanager

   @contextmanager
   def resource_manager():
       try:
           yield
       finally:
           # 리소스 정리
           pass
   ```

### 8.5.2 연결 풀링
```python
# FastAPI의 데이터베이스 연결 풀
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:password@localhost/dbname",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10
)
```

## 8.6 비동기 작업 처리

### 8.6.1 Celery 작업 큐
```python
# Celery 설정
from celery import Celery

celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

@celery.task
def long_running_task():
    # 시간이 오래 걸리는 작업
    pass
```

### 8.6.2 비동기 이메일 전송
```python
# FastAPI의 비동기 이메일
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME="user",
    MAIL_PASSWORD="password",
    MAIL_FROM="from@example.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False
)

fastmail = FastMail(conf)

@app.post("/send-email")
async def send_email(background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject="Test email",
        recipients=["to@example.com"],
        body="Test email body"
    )
    background_tasks.add_task(fastmail.send_message, message)
    return {"message": "Email will be sent"}
```

## 8.7 모니터링과 프로파일링

### 8.7.1 성능 모니터링
```python
# FastAPI의 미들웨어를 통한 성능 모니터링
from fastapi import FastAPI, Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### 8.7.2 프로파일링
```python
# cProfile을 사용한 프로파일링
import cProfile
import pstats

def profile_function(func):
    profiler = cProfile.Profile()
    profiler.enable()
    func()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

## 8.8 최적화 체크리스트

### 8.8.1 코드 최적화
- [ ] 비동기 처리 적용
- [ ] 캐싱 전략 구현
- [ ] 데이터베이스 쿼리 최적화
- [ ] 응답 압축 설정
- [ ] 리소스 관리 구현

### 8.8.2 인프라 최적화
- [ ] 로드 밸런싱 설정
- [ ] CDN 구성
- [ ] 데이터베이스 인덱스 최적화
- [ ] 캐시 서버 구성
- [ ] 모니터링 시스템 구축 