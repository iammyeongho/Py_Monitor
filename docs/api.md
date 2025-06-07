# API 문서

## 1. 인증 API

### 1.1 로그인
- **엔드포인트**: `/api/v1/login/access-token`
- **메소드**: POST
- **요청 본문**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **응답**:
  ```json
  {
    "access_token": "string",
    "token_type": "bearer"
  }
  ```

## 2. 모니터링 API

### 2.1 시스템 상태 조회
- **엔드포인트**: `/api/v1/monitoring/status`
- **메소드**: GET
- **응답**:
  ```json
  {
    "cpu_usage": "float",
    "memory_usage": "float",
    "disk_usage": "float",
    "network_usage": "float"
  }
  ```

### 2.2 알림 설정
- **엔드포인트**: `/api/v1/monitoring/notifications`
- **메소드**: POST
- **요청 본문**:
  ```json
  {
    "type": "email|webhook",
    "threshold": "float",
    "recipient": "string"
  }
  ```

## 3. 프로젝트 API

### 3.1 프로젝트 목록
- **엔드포인트**: `/api/v1/projects`
- **메소드**: GET
- **응답**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "status": "string"
    }
  ]
  ```

### 3.2 프로젝트 생성
- **엔드포인트**: `/api/v1/projects`
- **메소드**: POST
- **요청 본문**:
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```

## 4. 데이터 모델

### 4.1 User
```python
class User(Base):
    id: int
    email: str
    is_active: bool
    is_superuser: bool
    hashed_password: str
```

### 4.2 Project
```python
class Project(Base):
    id: int
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
```

### 4.3 Alert
```python
class Alert(Base):
    id: int
    type: str
    message: str
    status: str
    created_at: datetime
```

## 5. 에러 응답

모든 API는 다음과 같은 에러 응답 형식을 따릅니다:

```json
{
  "detail": "string",
  "status_code": "integer"
}
```

### 5.1 일반적인 에러 코드
- 400: 잘못된 요청
- 401: 인증 실패
- 403: 권한 없음
- 404: 리소스를 찾을 수 없음
- 500: 서버 내부 오류 