"""
# Laravel 개발자를 위한 설명
# 이 파일은 FastAPI 애플리케이션의 진입점입니다.
# Laravel의 public/index.php와 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. FastAPI 애플리케이션 설정
# 2. 라우터 등록
# 3. 미들웨어 설정
# 4. 스케줄러 시작
# 5. 에러 핸들링
# 6. 로깅
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.endpoints import monitoring, projects, users
from app.services.scheduler import MonitoringScheduler
from app.db.session import SessionLocal
import asyncio
import traceback

# 로거 설정
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Py Monitor",
    description="Python 기반 웹사이트 모니터링 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])

# 스케줄러 인스턴스
scheduler = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청 로깅 미들웨어"""
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    global scheduler
    try:
        logger.info("Starting application...")
        db = SessionLocal()
        scheduler = MonitoringScheduler(db)
        await scheduler.start()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    if scheduler:
        try:
            logger.info("Stopping application...")
            await scheduler.stop()
            logger.info("Application stopped successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 