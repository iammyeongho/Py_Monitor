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
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import monitoring, projects, users
from app.services.scheduler import MonitoringScheduler
from app.db.session import SessionLocal
import asyncio

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

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    global scheduler
    db = SessionLocal()
    scheduler = MonitoringScheduler(db)
    await scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    if scheduler:
        await scheduler.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 