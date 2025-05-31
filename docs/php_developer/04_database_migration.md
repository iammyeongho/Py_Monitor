# 4. 데이터베이스와 마이그레이션

이 문서에서는 FastAPI에서의 데이터베이스 사용과 마이그레이션을 Laravel과 비교하면서 설명합니다.

## 4.1 ORM 비교

### 4.1.1 Laravel의 Eloquent ORM
```php
// app/Models/User.php
class User extends Model
{
    protected $fillable = [
        'name',
        'email',
        'password',
    ];

    public function posts()
    {
        return $this->hasMany(Post::class);
    }
}

// 사용 예시
$user = User::find(1);
$posts = $user->posts;
```

### 4.1.2 FastAPI의 SQLAlchemy ORM
```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    posts = relationship("Post", back_populates="user")

# 사용 예시
user = db.query(User).filter(User.id == 1).first()
posts = user.posts
```

## 4.2 마이그레이션

### 4.2.1 Laravel의 마이그레이션
```php
// database/migrations/2024_03_20_create_users_table.php
class CreateUsersTable extends Migration
{
    public function up()
    {
        Schema::create('users', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('email')->unique();
            $table->string('password');
            $table->timestamps();
        });
    }

    public function down()
    {
        Schema::dropIfExists('users');
    }
}
```

### 4.2.2 FastAPI의 Alembic 마이그레이션
```python
# alembic/versions/xxxx_create_users_table.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('password', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

## 4.3 데이터베이스 연결

### 4.3.1 Laravel의 데이터베이스 연결
```php
// config/database.php
return [
    'default' => env('DB_CONNECTION', 'mysql'),
    'connections' => [
        'mysql' => [
            'driver' => 'mysql',
            'host' => env('DB_HOST', '127.0.0.1'),
            'database' => env('DB_DATABASE', 'forge'),
            'username' => env('DB_USERNAME', 'forge'),
            'password' => env('DB_PASSWORD', ''),
        ],
    ],
];
```

### 4.3.2 FastAPI의 데이터베이스 연결
```python
# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# app/core/config.py
class Settings(BaseSettings):
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: str = None

    @property
    def get_database_url(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
```

## 4.4 쿼리 빌더

### 4.4.1 Laravel의 쿼리 빌더
```php
// 기본 쿼리
$users = DB::table('users')
    ->where('active', 1)
    ->orderBy('name')
    ->get();

// 관계 쿼리
$users = User::with('posts')
    ->where('active', 1)
    ->get();
```

### 4.4.2 FastAPI의 SQLAlchemy 쿼리
```python
# 기본 쿼리
users = db.query(User)\
    .filter(User.active == True)\
    .order_by(User.name)\
    .all()

# 관계 쿼리
users = db.query(User)\
    .options(joinedload(User.posts))\
    .filter(User.active == True)\
    .all()
```

## 4.5 트랜잭션 처리

### 4.5.1 Laravel의 트랜잭션
```php
DB::transaction(function () {
    $user = User::create([
        'name' => 'John',
        'email' => 'john@example.com'
    ]);

    $user->posts()->create([
        'title' => 'First Post'
    ]);
});
```

### 4.5.2 FastAPI의 트랜잭션
```python
from sqlalchemy.orm import Session

def create_user_with_post(db: Session):
    try:
        user = User(name="John", email="john@example.com")
        db.add(user)
        db.flush()

        post = Post(title="First Post", user_id=user.id)
        db.add(post)
        
        db.commit()
    except Exception:
        db.rollback()
        raise
```

## 4.6 실전 팁

### 4.6.1 데이터베이스 설계
1. **스키마 설계**
   - 명확한 테이블 구조
   - 적절한 인덱스 설정
   - 관계 설정

2. **성능 최적화**
   - N+1 문제 해결
   - 인덱스 최적화
   - 쿼리 최적화

### 4.6.2 마이그레이션 관리
1. **버전 관리**
   - 마이그레이션 파일 관리
   - 롤백 전략
   - 데이터 마이그레이션

2. **실행 순서**
   - 의존성 고려
   - 순서 보장
   - 충돌 방지

### 4.6.3 쿼리 최적화
1. **인덱스 활용**
   - 적절한 인덱스 설정
   - 복합 인덱스 사용
   - 인덱스 유지보수

2. **쿼리 작성**
   - 효율적인 쿼리
   - N+1 문제 해결
   - 캐싱 활용

### 4.6.4 트랜잭션 관리
1. **원자성 보장**
   - 트랜잭션 범위 설정
   - 롤백 처리
   - 데드락 방지

2. **성능 고려**
   - 트랜잭션 시간 최소화
   - 격리 수준 설정
   - 동시성 제어

## 4.7 문제 해결

### 4.7.1 일반적인 문제
1. **연결 문제**
   - 연결 풀 설정
   - 타임아웃 설정
   - 재시도 로직

2. **성능 문제**
   - 쿼리 최적화
   - 인덱스 최적화
   - 캐싱 전략

### 4.7.2 디버깅
1. **쿼리 로깅**
   - SQL 로깅
   - 실행 시간 측정
   - 에러 추적

2. **프로파일링**
   - 성능 프로파일링
   - 병목 지점 식별
   - 최적화 포인트 