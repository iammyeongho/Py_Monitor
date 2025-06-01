# 6. 테스트 작성

이 문서에서는 FastAPI의 테스트 작성 방법을 Laravel과 비교하면서 설명합니다.

## 6.1 테스트 환경 설정

### 6.1.1 Laravel의 테스트 환경
```php
// phpunit.xml
<php>
    <env name="APP_ENV" value="testing"/>
    <env name="DB_CONNECTION" value="sqlite"/>
    <env name="DB_DATABASE" value=":memory:"/>
</php>

// tests/TestCase.php
namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    use CreatesApplication;
}
```

### 6.1.2 FastAPI의 테스트 환경
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

## 6.2 단위 테스트

### 6.2.1 Laravel의 단위 테스트
```php
// tests/Unit/UserTest.php
namespace Tests\Unit;

use Tests\TestCase;
use App\Models\User;

class UserTest extends TestCase
{
    public function test_user_creation()
    {
        $user = User::factory()->create([
            'name' => 'John Doe',
            'email' => 'john@example.com'
        ]);

        $this->assertEquals('John Doe', $user->name);
        $this->assertEquals('john@example.com', $user->email);
    }
}
```

### 6.2.2 FastAPI의 단위 테스트
```python
# tests/unit/test_user.py
import pytest
from app.models.user import User
from app.schemas.user import UserCreate

def test_user_creation(db):
    user_data = UserCreate(
        name="John Doe",
        email="john@example.com",
        password="password123"
    )
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.name == "John Doe"
    assert user.email == "john@example.com"
```

## 6.3 기능 테스트

### 6.3.1 Laravel의 기능 테스트
```php
// tests/Feature/UserTest.php
namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;

class UserTest extends TestCase
{
    public function test_can_get_user()
    {
        $user = User::factory()->create();

        $response = $this->getJson("/api/users/{$user->id}");

        $response->assertStatus(200)
            ->assertJson([
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email
            ]);
    }
}
```

### 6.3.2 FastAPI의 기능 테스트
```python
# tests/functional/test_user_api.py
def test_get_user(client, db):
    # Create test user
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    response = client.post("/api/v1/users/", json=user_data)
    user_id = response.json()["id"]

    # Test get user
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"
    assert response.json()["email"] == "john@example.com"
```

## 6.4 통합 테스트

### 6.4.1 Laravel의 통합 테스트
```php
// tests/Integration/UserServiceTest.php
namespace Tests\Integration;

use Tests\TestCase;
use App\Services\UserService;
use App\Models\User;

class UserServiceTest extends TestCase
{
    private $userService;

    protected function setUp(): void
    {
        parent::setUp();
        $this->userService = new UserService();
    }

    public function test_user_service_operations()
    {
        $user = $this->userService->create([
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'password' => 'password123'
        ]);

        $foundUser = $this->userService->findById($user->id);
        $this->assertEquals($user->id, $foundUser->id);
    }
}
```

### 6.4.2 FastAPI의 통합 테스트
```python
# tests/integration/test_user_service.py
from app.services.user_service import create_user, get_user_by_id

def test_user_service_operations(db):
    # Create user
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    user = create_user(db, user_data)

    # Get user
    found_user = get_user_by_id(db, user.id)
    assert found_user.id == user.id
    assert found_user.name == user.name
```

## 6.5 테스트 데이터 생성

### 6.5.1 Laravel의 팩토리
```php
// database/factories/UserFactory.php
namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

class UserFactory extends Factory
{
    protected $model = User::class;

    public function definition()
    {
        return [
            'name' => $this->faker->name,
            'email' => $this->faker->unique()->safeEmail,
            'password' => bcrypt('password'),
        ];
    }
}
```

### 6.5.2 FastAPI의 테스트 데이터 생성
```python
# tests/utils/factories.py
from faker import Faker
from app.models.user import User

fake = Faker()

def create_test_user(db):
    user_data = {
        "name": fake.name(),
        "email": fake.email(),
        "password": "password123"
    }
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

## 6.6 실전 팁

### 6.6.1 테스트 구조화
1. **테스트 분류**
   - 단위 테스트
   - 기능 테스트
   - 통합 테스트
   - E2E 테스트

2. **테스트 데이터**
   - 팩토리 사용
   - 픽스처 활용
   - 데이터 정리

### 6.6.2 테스트 작성 전략
1. **테스트 범위**
   - 핵심 기능 테스트
   - 엣지 케이스
   - 에러 케이스

2. **테스트 품질**
   - 테스트 격리
   - 재사용성
   - 유지보수성

### 6.6.3 성능 최적화
1. **테스트 실행**
   - 병렬 실행
   - 캐싱 활용
   - 리소스 관리

2. **데이터베이스**
   - 인메모리 DB 사용
   - 트랜잭션 활용
   - 데이터 정리

## 6.7 문제 해결

### 6.7.1 일반적인 문제
1. **테스트 실패**
   - 디버깅 전략
   - 로그 분석
   - 환경 문제

2. **성능 문제**
   - 테스트 최적화
   - 리소스 관리
   - 병목 지점

### 6.7.2 유지보수
1. **테스트 관리**
   - 테스트 정리
   - 중복 제거
   - 문서화

2. **품질 관리**
   - 테스트 커버리지
   - 코드 품질
   - 리팩토링 