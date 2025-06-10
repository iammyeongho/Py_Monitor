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

---

이 문서는 Py_Monitor 프로젝트의 서버 실행 및 디버깅을 위한 가이드입니다. 문제가 발생하면 위 항목을 순서대로 점검하세요. 