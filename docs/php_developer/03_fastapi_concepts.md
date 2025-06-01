# 3. FastAPI 주요 개념

이 문서에서는 FastAPI의 주요 개념들을 Laravel과 비교하면서 설명합니다. 각 개념의 차이점과 사용법을 자세히 살펴보겠습니다.

## 3.1 의존성 주입 (Dependency Injection)

### 3.1.1 Laravel의 의존성 주입
```php
class UserController extends Controller
{
    private $userService;

    public function __construct(UserService $userService)
    {
        $this->userService = $userService;
    }

    public function show($id)
    {
        return $this->userService->findById($id);
    }
}
```

### 3.1.2 FastAPI의 의존성 주입
```python
from fastapi import Depends
from app.services.user_service import get_user_service

@router.get("/{user_id}")
def get_user(
    user_id: int,
    user_service = Depends(get_user_service)
):
    return user_service.find_by_id(user_id)
```

### 3.1.3 주요 차이점
- Laravel: 생성자 주입, 서비스 컨테이너
- FastAPI: 함수 주입, Depends() 데코레이터

## 3.2 비동기 처리 (Async/Await)

### 3.2.1 Laravel의 비동기 처리
```php
// Laravel 8 이상에서의 비동기 처리
use Illuminate\Support\Facades\Http;

public function getData()
{
    $response = Http::async()->get('api.example.com/data');
    return $response->wait();
}
```

### 3.2.2 FastAPI의 비동기 처리
```python
from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/data")
async def get_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("api.example.com/data")
        return response.json()
```

### 3.2.3 주요 차이점
- Laravel: 기본적으로 동기, 비동기는 제한적
- FastAPI: 기본적으로 비동기 지원, async/await 문법

## 3.3 예외처리 (Exception Handling)

### 3.3.1 Laravel의 예외처리
```php
// app/Exceptions/Handler.php
public function register()
{
    $this->renderable(function (ModelNotFoundException $e) {
        return response()->json(['error' => 'Not found'], 404);
    });
}

// Controller
public function show($id)
{
    $user = User::findOrFail($id);
    return $user;
}
```

### 3.3.2 FastAPI의 예외처리
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@router.get("/{user_id}")
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### 3.3.3 주요 차이점
- Laravel: 글로벌 예외 핸들러
- FastAPI: 데코레이터 기반 예외 핸들러

## 3.4 미들웨어 (Middleware)

### 3.4.1 Laravel의 미들웨어
```php
// app/Http/Middleware/Authenticate.php
class Authenticate
{
    public function handle($request, Closure $next)
    {
        if (!auth()->check()) {
            return redirect('login');
        }
        return $next($request);
    }
}

// Kernel.php
protected $routeMiddleware = [
    'auth' => \App\Http\Middleware\Authenticate::class,
];
```

### 3.4.2 FastAPI의 미들웨어
```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not request.headers.get("Authorization"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"}
            )
        response = await call_next(request)
        return response

app = FastAPI()
app.add_middleware(AuthMiddleware)
```

### 3.4.3 주요 차이점
- Laravel: 클래스 기반 미들웨어
- FastAPI: 함수 또는 클래스 기반 미들웨어

## 3.5 환경설정 (Configuration)

### 3.5.1 Laravel의 환경설정
```php
// config/app.php
return [
    'name' => env('APP_NAME', 'Laravel'),
    'debug' => env('APP_DEBUG', false),
];

// .env
APP_NAME=Laravel
APP_DEBUG=true
```

### 3.5.2 FastAPI의 환경설정
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FastAPI"
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.5.3 주요 차이점
- Laravel: config/*.php + .env
- FastAPI: Pydantic Settings + .env

## 3.6 실전 팁

### 3.6.1 의존성 주입
1. **서비스 레이어 분리**
   - 비즈니스 로직을 서비스로 분리
   - 의존성 주입을 통한 테스트 용이성 확보

2. **의존성 관리**
   - 명확한 인터페이스 정의
   - 순환 의존성 방지

### 3.6.2 비동기 처리
1. **적절한 사용**
   - I/O 작업에 비동기 사용
   - CPU 집약적 작업은 동기 처리

2. **성능 최적화**
   - 비동기 클라이언트 사용
   - 연결 풀링

### 3.6.3 예외처리
1. **일관된 에러 응답**
   - 표준화된 에러 형식
   - 적절한 HTTP 상태 코드

2. **로깅**
   - 에러 로깅
   - 디버깅 정보 포함

### 3.6.4 미들웨어
1. **순서 고려**
   - 미들웨어 실행 순서
   - 의존성 관계

2. **성능**
   - 불필요한 미들웨어 제거
   - 캐싱 활용

### 3.6.5 환경설정
1. **보안**
   - 민감 정보 관리
   - 환경별 설정 분리

2. **유지보수**
   - 설정 문서화
   - 기본값 설정 