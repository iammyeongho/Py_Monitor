"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 app/Http/Kernel.php와 유사한 역할을 합니다.
# FastAPI 애플리케이션의 핵심 설정과 미들웨어를 정의합니다.
# 
# Laravel과의 주요 차이점:
# 1. FastAPI = Laravel의 Illuminate\Foundation\Application
# 2. CORSMiddleware = Laravel의 CORS 미들웨어
# 3. RequestLoggingMiddleware = Laravel의 로깅 미들웨어
# 4. ErrorHandlingMiddleware = Laravel의 예외 처리 미들웨어
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from app.core.config import settings
from app.api.v1.api import api_router
from app.services.scheduler import MonitoringScheduler
from app.db.session import SessionLocal
from app.models.base import Base, User, Project

# 로거 설정
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 로깅 미들웨어
class RequestLoggingMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} completed in {process_time:.2f}s")
        return response

# 에러 처리 미들웨어
class ErrorHandlingMiddleware:
    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

# 미들웨어 등록
app.middleware("http")(RequestLoggingMiddleware)
app.middleware("http")(ErrorHandlingMiddleware)

# API 라우터 등록
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

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Welcome to Py_Monitor API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 