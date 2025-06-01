# 9. 보안

이 문서에서는 FastAPI 프로젝트의 보안 관련 내용을 Laravel과 비교하면서 설명합니다.

## 9.1 인증과 인가

### 9.1.1 Laravel의 인증
```php
// Laravel의 인증 미들웨어
Route::middleware(['auth'])->group(function () {
    Route::get('/profile', function () {
        // 인증된 사용자만 접근 가능
    });
});

// JWT 인증
use PHPOpenSourceSaver\JWTAuth\Facades\JWTAuth;

$token = JWTAuth::attempt($credentials);
```

### 9.1.2 FastAPI의 인증
```python
# FastAPI의 인증
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 생성
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 인증 의존성
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

## 9.2 입력 검증

### 9.2.1 Laravel의 입력 검증
```php
// Laravel의 요청 검증
class UserRequest extends FormRequest
{
    public function rules()
    {
        return [
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users',
            'password' => 'required|min:8'
        ];
    }
}
```

### 9.2.2 FastAPI의 입력 검증
```python
# FastAPI의 Pydantic 모델을 통한 검증
from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    name: constr(min_length=1, max_length=255)
    email: EmailStr
    password: constr(min_length=8)

@app.post("/users/")
async def create_user(user: UserCreate):
    # 검증된 데이터로 사용자 생성
    return {"user": user}
```

## 9.3 CORS 설정

### 9.3.1 Laravel의 CORS
```php
// Laravel의 CORS 설정
// config/cors.php
return [
    'paths' => ['api/*'],
    'allowed_methods' => ['*'],
    'allowed_origins' => ['*'],
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => [],
    'max_age' => 0,
    'supports_credentials' => false,
];
```

### 9.3.2 FastAPI의 CORS
```python
# FastAPI의 CORS 설정
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 9.4 XSS 방지

### 9.4.1 Laravel의 XSS 방지
```php
// Laravel의 XSS 방지
// Blade 템플릿에서 자동 이스케이프
{{ $user->name }}

// 수동 이스케이프
{!! $user->name !!}
```

### 9.4.2 FastAPI의 XSS 방지
```python
# FastAPI의 XSS 방지
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import html

@app.get("/user/{name}", response_class=HTMLResponse)
async def get_user(name: str):
    # HTML 이스케이프
    safe_name = html.escape(name)
    return f"<h1>Hello, {safe_name}!</h1>"
```

## 9.5 CSRF 보호

### 9.5.1 Laravel의 CSRF 보호
```php
// Laravel의 CSRF 토큰
<form method="POST" action="/profile">
    @csrf
    <input type="text" name="name">
    <button type="submit">Submit</button>
</form>
```

### 9.5.2 FastAPI의 CSRF 보호
```python
# FastAPI의 CSRF 보호
from fastapi import FastAPI, Request
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

@app.post("/profile")
async def update_profile(request: Request):
    # CSRF 토큰 검증
    csrf_token = request.session.get("csrf_token")
    if not csrf_token or csrf_token != request.headers.get("X-CSRF-Token"):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    # 프로필 업데이트 로직
```

## 9.6 SQL 인젝션 방지

### 9.6.1 Laravel의 SQL 인젝션 방지
```php
// Laravel의 쿼리 빌더
$users = DB::table('users')
    ->where('name', $name)
    ->get();

// Eloquent ORM
$user = User::where('email', $email)->first();
```

### 9.6.2 FastAPI의 SQL 인젝션 방지
```python
# FastAPI의 SQLAlchemy를 통한 안전한 쿼리
from sqlalchemy.orm import Session
from sqlalchemy import select

def get_user_by_email(db: Session, email: str):
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()
```

## 9.7 파일 업로드 보안

### 9.7.1 Laravel의 파일 업로드
```php
// Laravel의 파일 업로드 검증
$request->validate([
    'file' => 'required|file|max:10240|mimes:jpeg,png,pdf'
]);

$path = $request->file('file')->store('uploads');
```

### 9.7.2 FastAPI의 파일 업로드
```python
# FastAPI의 파일 업로드 검증
from fastapi import File, UploadFile
from typing import List
import aiofiles
import os

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # 파일 확장자 검증
    if not file.filename.endswith(('.jpg', '.png', '.pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # 파일 크기 검증
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large")
    
    # 안전한 파일명 생성
    safe_filename = secure_filename(file.filename)
    file_path = f"uploads/{safe_filename}"
    
    # 파일 저장
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    return {"filename": safe_filename}
```

## 9.8 보안 헤더 설정

### 9.8.1 Laravel의 보안 헤더
```php
// Laravel의 보안 헤더 미들웨어
namespace App\Http\Middleware;

use Closure;

class SecurityHeaders
{
    public function handle($request, Closure $next)
    {
        $response = $next($request);
        
        $response->headers->set('X-Frame-Options', 'SAMEORIGIN');
        $response->headers->set('X-XSS-Protection', '1; mode=block');
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        
        return $response;
    }
}
```

### 9.8.2 FastAPI의 보안 헤더
```python
# FastAPI의 보안 헤더 미들웨어
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## 9.9 보안 체크리스트

### 9.9.1 기본 보안 설정
- [ ] HTTPS 강제 적용
- [ ] 보안 헤더 설정
- [ ] 세션 보안 설정
- [ ] 쿠키 보안 설정
- [ ] 에러 메시지 보안

### 9.9.2 인증/인가 보안
- [ ] 강력한 비밀번호 정책
- [ ] 계정 잠금 정책
- [ ] 2단계 인증
- [ ] 세션 타임아웃
- [ ] 권한 검사

### 9.9.3 데이터 보안
- [ ] 민감 정보 암호화
- [ ] 입력 데이터 검증
- [ ] 출력 데이터 이스케이프
- [ ] 파일 업로드 제한
- [ ] 로그 보안 