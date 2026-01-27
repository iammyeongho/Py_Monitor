"""모니터링 상태 조회 API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.schemas.monitoring import MonitoringResponse
from app.services.monitoring import check_project_status

router = APIRouter()


@router.get("/status/{project_id}", response_model=MonitoringResponse)
def get_project_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 현재 상태를 확인합니다."""
    db_project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
        )
        .first()
    )
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project_status = check_project_status(db_project)
    return project_status


@router.get("/status", response_model=List[MonitoringResponse])
def get_all_projects_status(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """현재 사용자의 모든 프로젝트 상태를 확인합니다."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.is_active.is_(True))
        .all()
    )
    statuses = [check_project_status(project) for project in projects]
    return statuses
