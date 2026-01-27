"""
FastAPI 기반의 웹사이트 모니터링 시스템 메인 애플리케이션 파일

이 파일은 애플리케이션의 진입점으로, FastAPI 인스턴스를 생성하고
필요한 미들웨어, 라우터, 스케줄러를 설정합니다.
"""

import time
import logging
from app.core import logging_config  # noqa: F401 로깅 초기화
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions.handlers import register_exception_handlers
from app.services.scheduler import MonitoringScheduler
from app.db.session import SessionLocal

# 로거 설정
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="웹사이트 모니터링 시스템",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""

    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} completed in {process_time:.2f}s"
        )
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """에러 처리 미들웨어"""

    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )


# 미들웨어 등록
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# 커스텀 예외 핸들러 등록
register_exception_handlers(app)

# API 라우터 등록 (정적 파일보다 먼저 등록)
app.include_router(api_router, prefix=settings.API_V1_STR)

# 모니터링 스케줄러 인스턴스
scheduler = None


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트 핸들러"""
    logger.info("Starting application...")
    global scheduler
    scheduler = MonitoringScheduler(SessionLocal())
    await scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트 핸들러"""
    logger.info("Shutting down application...")
    if scheduler:
        await scheduler.stop()


@app.get("/health")
def health_check():
    """시스템 상태 확인"""
    return {"status": "healthy"}


@app.get("/")
def root():
    """루트 경로를 대시보드로 리다이렉트"""
    return RedirectResponse(url="/frontend/html/index.html")


@app.get("/index.html")
def index_redirect():
    """index.html을 실제 경로로 리다이렉트"""
    return RedirectResponse(url="/frontend/html/index.html")


@app.get("/login.html")
def login_redirect():
    """login.html을 실제 경로로 리다이렉트"""
    return RedirectResponse(url="/frontend/html/login.html")


# 정적 파일 제공 설정 (API 라우터 이후에 마운트)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
app.mount(
    "/test_frontend", StaticFiles(directory="tests/test_frontend"), name="test_frontend"
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
