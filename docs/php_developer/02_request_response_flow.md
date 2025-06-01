# 2. 요청-응답 흐름

이 문서에서는 FastAPI의 요청-응답 흐름을 Laravel과 비교하면서 설명합니다. 실제 예시를 통해 각 단계별로 어떻게 처리되는지 살펴보겠습니다.

## 2.1 전체 흐름 비교

### 2.1.1 Laravel의 요청-응답 흐름
1. HTTP 요청 → `public/index.php`
2. 라우팅 (`routes/api.php`)
3. 미들웨어 처리
4. 컨트롤러 실행
5. 서비스 레이어 (선택적)
6. 모델 처리
7. 응답 반환

### 2.1.2 FastAPI의 요청-응답 흐름
1. HTTP 요청 → `main.py`
2. 라우팅 (`app/api/v1/router.py`)
3. 미들웨어 처리
4. 엔드포인트 함수 실행
5. 서비스 레이어 (선택적)
6. 모델 처리
7. 응답 반환

## 2.2 실제 예시: 사용자 정보 조회

### 2.2.1 라우터 설정

#### Laravel (routes/api.php)
```php
Route::get('/users/{id}', [UserController::class, 'show']);
```

#### FastAPI (app/api/v1/router.py)
```python
from fastapi import APIRouter
from app.api.v1.endpoints import users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

### 2.2.2 컨트롤러/엔드포인트

#### Laravel (app/Http/Controllers/UserController.php)
```php
class UserController extends Controller
{
    public function show($id)
    {
        $user = User::findOrFail($id);
        return response()->json($user);
    }
}
```

#### FastAPI (app/api/v1/endpoints/users.py)
```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserOut
from app.services.user_service import get_user_by_id

router = APIRouter()

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### 2.2.3 서비스 레이어

#### Laravel (app/Services/UserService.php)
```php
class UserService
{
    public function findById($id)
    {
        return User::find($id);
    }
}
```

#### FastAPI (app/services/user_service.py)
```python
from app.models.user import User
from app.db.session import SessionLocal

def get_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user
    finally:
        db.close()
```

### 2.2.4 모델

#### Laravel (app/Models/User.php)
```php
class User extends Model
{
    protected $fillable = [
        'name',
        'email',
    ];
}
```

#### FastAPI (app/models/user.py)
```python
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
```

### 2.2.5 데이터 검증/직렬화

#### Laravel (app/Http/Requests/UserRequest.php)
```php
class UserRequest extends FormRequest
{
    public function rules()
    {
        return [
            'name' => 'required|string',
            'email' => 'required|email',
        ];
    }
}
```

#### FastAPI (app/schemas/user.py)
```python
from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        orm_mode = True
```

## 2.3 주요 차이점 분석

### 2.3.1 라우팅
- Laravel: 클래스 기반 컨트롤러와 메서드 매핑
- FastAPI: 함수 기반 엔드포인트와 데코레이터

### 2.3.2 의존성 주입
- Laravel: 생성자 주입 또는 메서드 주입
- FastAPI: Depends() 데코레이터 사용

### 2.3.3 데이터 검증
- Laravel: Form Request Validation
- FastAPI: Pydantic 모델

### 2.3.4 응답 처리
- Laravel: response() 헬퍼 또는 Resource 클래스
- FastAPI: 자동 직렬화 (Pydantic)

## 2.4 실전 팁

### 2.4.1 코드 구조화
1. **라우터 구성**
   - 기능별로 라우터 분리
   - 버전 관리 고려
   - 태그를 통한 API 그룹화

2. **엔드포인트 작성**
   - 명확한 함수명 사용
   - 타입 힌트 활용
   - 적절한 예외 처리

3. **서비스 레이어**
   - 비즈니스 로직 분리
   - 재사용성 고려
   - 트랜잭션 관리

### 2.4.2 성능 최적화
1. **데이터베이스**
   - N+1 문제 해결
   - 적절한 인덱스 사용
   - 쿼리 최적화

2. **캐싱**
   - Redis 활용
   - 응답 캐싱
   - 데이터 캐싱

### 2.4.3 보안
1. **인증/인가**
   - JWT 토큰 사용
   - 권한 검사
   - CORS 설정

2. **데이터 검증**
   - 입력값 검증
   - SQL 인젝션 방지
   - XSS 방지

## 2.5 디버깅과 로깅

### 2.5.1 디버깅
- FastAPI의 자동 문서화 활용
- 로그 레벨 조정
- 예외 처리와 로깅

### 2.5.2 로깅
- 구조화된 로깅
- 로그 레벨별 처리
- 로그 파일 관리 