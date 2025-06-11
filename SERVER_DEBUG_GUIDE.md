# Py_Monitor 서버 실행 및 문제 해결 가이드

## 1. 서버 실행 방법

- 반드시 FastAPI 서버를 실행한 뒤, 브라우저에서 아래 주소로 접속해야 합니다.
  - `http://127.0.0.1:8000/frontend/index.html`
- **절대** `file://`로 직접 HTML 파일을 열지 마세요. (CSS/JS가 동작하지 않음)

## 2. 정적 파일 제공 설정

- FastAPI에서 정적 파일을 제공하려면 아래와 같이 설정해야 합니다.

```python
from fastapi.staticfiles import StaticFiles
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
```

- HTML에서 CSS/JS 경로는 `/frontend/style.css`처럼 작성해야 합니다.

## 3. API 404 Not Found 문제

- 프론트엔드에서 `/api/monitoring/projects` 등으로 요청할 때 404가 발생하면, 해당 엔드포인트가 서버에 구현되어 있는지 확인하세요.
- 예시 로그:
  ```
  "GET /api/monitoring/projects HTTP/1.1" 404 Not Found
  ```
- 해결 방법:
  - `app/api/v1/router.py` 등에서 해당 경로가 실제로 구현되어 있는지 확인
  - 라우터가 `main.py`에 정상적으로 include되어 있는지 확인

### 예시: FastAPI 엔드포인트 추가
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/monitoring/projects")
def get_projects():
    return [{"id": 1, "name": "테스트 서버"}]
```

## 4. 서버 실행 체크리스트

- [ ] FastAPI 서버 실행됨 (에러 없이 기동되는지 확인)
- [ ] `/frontend/style.css` 등 정적 파일이 정상적으로 제공되는지 확인
- [ ] 프론트엔드에서 호출하는 API가 404가 아닌지 확인
- [ ] 브라우저에서 반드시 서버 주소(`http://127.0.0.1:8000/...`)로 접근

## 5. 프론트엔드-백엔드 API 경로 일치 체크

- 프론트엔드 JS에서 호출하는 API 경로와 백엔드 라우터의 실제 경로가 반드시 일치해야 합니다.
- 예시:
  - 백엔드 라우터가 `/api/v1/projects`로 등록되어 있다면, 프론트엔드에서도 `/api/v1/projects`로 요청해야 합니다.
- 인증이 필요한 API라면, 프론트엔드에서 토큰 등 인증정보를 반드시 헤더에 포함해야 합니다.
- 예시 데이터(더미 데이터)는 실제 서비스에서는 제거하고, 실제 API 연동 코드만 남겨야 합니다.

### 점검 체크리스트
- [ ] 프론트엔드의 API 요청 경로가 실제 백엔드 라우터 경로와 일치하는가?
- [ ] 인증이 필요한 API라면, 프론트엔드에서 인증정보를 포함하는가?
- [ ] 예시 데이터가 남아있지 않고, 실제 API 연동 코드만 남아있는가?

---

이 문서는 Py_Monitor 프로젝트의 서버 실행 및 디버깅을 위한 가이드입니다. 문제가 발생하면 위 항목을 순서대로 점검하세요. 