# 5. API 문서화

이 문서에서는 FastAPI의 API 문서화 기능을 Laravel과 비교하면서 설명합니다.

## 5.1 기본 문서화

### 5.1.1 Laravel의 API 문서화
```php
// Laravel에서는 보통 별도의 패키지를 사용
// 예: L5-Swagger, Scribe 등

/**
 * @OA\Get(
 *     path="/api/users/{id}",
 *     summary="Get user by ID",
 *     @OA\Parameter(
 *         name="id",
 *         in="path",
 *         required=true,
 *         @OA\Schema(type="integer")
 *     ),
 *     @OA\Response(
 *         response=200,
 *         description="User found"
 *     )
 * )
 */
public function show($id)
{
    return User::findOrFail($id);
}
```

### 5.1.2 FastAPI의 API 문서화
```python
from fastapi import APIRouter, HTTPException
from app.schemas.user import UserOut

router = APIRouter()

@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get user by ID",
    description="Retrieve a user by their ID",
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found"}
    }
)
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## 5.2 스키마 정의

### 5.2.1 Laravel의 스키마 정의
```php
// app/Http/Resources/UserResource.php
class UserResource extends JsonResource
{
    public function toArray($request)
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'created_at' => $this->created_at,
        ];
    }
}
```

### 5.2.2 FastAPI의 스키마 정의
```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
```

## 5.3 응답 모델

### 5.3.1 Laravel의 응답 모델
```php
// app/Http/Controllers/UserController.php
public function index()
{
    $users = User::all();
    return UserResource::collection($users);
}

// app/Http/Resources/UserResource.php
class UserResource extends JsonResource
{
    public function toArray($request)
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'posts' => PostResource::collection($this->whenLoaded('posts')),
        ];
    }
}
```

### 5.3.2 FastAPI의 응답 모델
```python
# app/schemas/user.py
from typing import List
from pydantic import BaseModel

class PostOut(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    posts: List[PostOut] = []

    class Config:
        orm_mode = True

# app/api/v1/endpoints/users.py
@router.get("/", response_model=List[UserOut])
def get_users():
    return get_all_users()
```

## 5.4 API 그룹화

### 5.4.1 Laravel의 API 그룹화
```php
// routes/api.php
Route::prefix('v1')->group(function () {
    Route::apiResource('users', UserController::class);
    Route::apiResource('posts', PostController::class);
});
```

### 5.4.2 FastAPI의 API 그룹화
```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import users, posts

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])

# main.py
app.include_router(api_router, prefix="/api/v1")
```

## 5.5 문서 커스터마이징

### 5.5.1 FastAPI의 문서 커스터마이징
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="My API",
    description="My API description",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="My API description",
        routes=app.routes,
    )
    
    # 커스텀 스키마 수정
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

## 5.6 실전 팁

### 5.6.1 문서화 전략
1. **일관성 유지**
   - 일관된 응답 형식
   - 명확한 에러 메시지
   - 표준화된 상태 코드

2. **버전 관리**
   - API 버전 관리
   - 변경 이력 관리
   - 하위 호환성 유지

### 5.6.2 문서 품질
1. **상세한 설명**
   - 엔드포인트 설명
   - 파라미터 설명
   - 응답 예시

2. **예시 제공**
   - 요청 예시
   - 응답 예시
   - 에러 케이스

### 5.6.3 보안
1. **인증/인가**
   - 보안 스키마 정의
   - 권한 설명
   - 토큰 사용법

2. **민감 정보**
   - 민감 정보 마스킹
   - 보안 헤더 설명
   - HTTPS 사용

## 5.7 문제 해결

### 5.7.1 일반적인 문제
1. **문서 동기화**
   - 코드와 문서 일치
   - 자동화된 문서 생성
   - 변경 사항 추적

2. **성능**
   - 문서 로딩 최적화
   - 캐싱 전략
   - 리소스 관리

### 5.7.2 유지보수
1. **문서 업데이트**
   - 변경 사항 반영
   - 버전 관리
   - 이력 관리

2. **품질 관리**
   - 문서 검토
   - 피드백 수집
   - 지속적 개선 