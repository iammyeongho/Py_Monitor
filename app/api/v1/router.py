from fastapi import APIRouter
from app.api.v1.endpoints import users, projects, monitoring

api_router = APIRouter()

# User 라우터 등록
api_router.include_router(
    users.router,
    prefix="/auth",
    tags=["auth"]
)

# Project 라우터 등록
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

# Monitoring 라우터 등록
api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)
