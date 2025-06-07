"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 RouteServiceProvider와 유사한 역할을 합니다.
# FastAPI의 API 라우터를 설정하고 관리합니다.
# 
# Laravel과의 주요 차이점:
# 1. APIRouter = Laravel의 Route::group()과 유사
# 2. prefix = Laravel의 Route::prefix()와 유사
# 3. tags = Laravel의 Route::name()과 유사
"""

from fastapi import APIRouter
from app.api.v1.endpoints import users, projects, monitoring

api_router = APIRouter()

# 사용자 관련 엔드포인트
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# 프로젝트 관련 엔드포인트
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

# 모니터링 관련 엔드포인트
api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
) 