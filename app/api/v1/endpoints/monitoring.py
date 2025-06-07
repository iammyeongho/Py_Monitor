"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 MonitoringController와 유사한 역할을 합니다.
# FastAPI를 사용하여 모니터링 관련 엔드포인트를 정의합니다.
# 
# Laravel과의 주요 차이점:
# 1. APIRouter = Laravel의 Route::controller()와 유사
# 2. Depends = Laravel의 dependency injection과 유사
# 3. HTTPException = Laravel의 abort()와 유사
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.project import Project
from app.schemas.monitoring import MonitoringResponse
from app.core.security import get_current_user
from app.services.monitoring import check_project_status

router = APIRouter()

@router.get("/status/{project_id}", response_model=MonitoringResponse)
def get_project_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """프로젝트의 현재 상태를 확인합니다."""
    db_project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.is_active == True
    ).first()
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    status = check_project_status(db_project)
    return status

@router.get("/status", response_model=List[MonitoringResponse])
def get_all_projects_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """현재 사용자의 모든 프로젝트 상태를 확인합니다."""
    projects = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_active == True
    ).all()
    statuses = [check_project_status(project) for project in projects]
    return statuses
