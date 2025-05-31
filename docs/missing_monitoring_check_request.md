# MonitoringCheckRequest 스키마 누락 및 추가 내역

## 개요
- `MonitoringCheckRequest`는 모니터링 API에서 체크 요청의 입력값을 검증하는 데 사용되는 Pydantic 스키마입니다.
- 기존 `app/schemas/monitoring.py`에 정의가 누락되어, 관련 엔드포인트 및 테스트에서 ImportError가 발생했습니다.

## 영향
- FastAPI 엔드포인트 및 테스트 코드에서 `from app.schemas.monitoring import MonitoringCheckRequest` 구문이 실패하여 서비스 및 테스트가 정상 동작하지 않음

## 해결 방법
- 아래와 같이 `MonitoringCheckRequest` 클래스를 추가함

```python
class MonitoringCheckRequest(BaseModel):
    project_id: int
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[dict] = None
    timeout: Optional[int] = 30
```

## 예시
```json
{
  "project_id": 1,
  "url": "https://example.com/health",
  "method": "GET",
  "headers": {"Authorization": "Bearer ..."},
  "timeout": 10
}
```

---

## MonitoringCheckResponse 스키마 누락 및 추가 내역

### 개요
- `MonitoringCheckResponse`는 모니터링 체크 결과를 API 응답으로 반환할 때 사용하는 Pydantic 스키마입니다.
- 기존 `app/schemas/monitoring.py`에 정의가 누락되어, 관련 엔드포인트 및 테스트에서 ImportError가 발생했습니다.

### 영향
- FastAPI 엔드포인트 및 테스트 코드에서 `from app.schemas.monitoring import MonitoringCheckResponse` 구문이 실패하여 서비스 및 테스트가 정상 동작하지 않음

### 해결 방법
- 아래와 같이 `MonitoringCheckResponse` 클래스를 추가함

```python
class MonitoringCheckResponse(BaseModel):
    project_id: int
    url: str
    status: bool
    response_time: Optional[float] = None
    http_code: Optional[int] = None
    error_message: Optional[str] = None
    checked_at: datetime
```

### 예시
```json
{
  "project_id": 1,
  "url": "https://example.com/health",
  "status": true,
  "response_time": 0.123,
  "http_code": 200,
  "checked_at": "2024-05-22T12:34:56"
}
```

---

## MonitoringStatus Enum 누락 및 추가 내역

### 개요
- `MonitoringStatus`는 모니터링 결과의 상태값(UP, DOWN, UNKNOWN 등)을 명확하게 표현하기 위한 Enum 클래스입니다.
- 기존 `app/schemas/monitoring.py`에 정의가 누락되어, 관련 엔드포인트 및 테스트에서 ImportError가 발생했습니다.

### 영향
- FastAPI 엔드포인트 및 테스트 코드에서 `from app.schemas.monitoring import MonitoringStatus` 구문이 실패하여 서비스 및 테스트가 정상 동작하지 않음

### 해결 방법
- 아래와 같이 `MonitoringStatus` Enum 클래스를 추가함

```python
from enum import Enum

class MonitoringStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
```

### 예시
```json
{
  "status": "up"
}
```

---

## SSLStatus Enum 누락 및 추가 내역

### 개요
- `SSLStatus`는 SSL 인증서의 상태(VALID, EXPIRED, UNKNOWN 등)를 명확하게 표현하기 위한 Enum 클래스입니다.
- 기존 `app/schemas/monitoring.py`에 정의가 누락되어, 관련 엔드포인트 및 테스트에서 ImportError가 발생했습니다.

### 영향
- FastAPI 엔드포인트 및 테스트 코드에서 `from app.schemas.monitoring import SSLStatus` 구문이 실패하여 서비스 및 테스트가 정상 동작하지 않음

### 해결 방법
- 아래와 같이 `SSLStatus` Enum 클래스를 추가함

```python
class SSLStatus(str, Enum):
    VALID = "valid"
    EXPIRED = "expired"
    UNKNOWN = "unknown"
```

### 예시
```json
{
  "ssl_status": "valid"
}
```

---

> 이 문서는 스키마 누락으로 인한 장애 및 구조적 개선 사항을 추적하기 위해 작성되었습니다.
