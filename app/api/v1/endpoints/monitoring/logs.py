"""모니터링 로그 API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringLog
from app.models.project import Project
from app.schemas.monitoring import MonitoringLogResponse

router = APIRouter()


@router.get("/logs/{project_id}", response_model=List[MonitoringLogResponse])
def get_monitoring_logs(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 로그를 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = (
        db.query(MonitoringLog)
        .filter(MonitoringLog.project_id == project_id)
        .order_by(MonitoringLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs


@router.get("/logs/{project_id}/latest", response_model=MonitoringLogResponse)
def get_latest_monitoring_log(
    project_id: int,
    check_type: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 최신 모니터링 로그를 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(MonitoringLog).filter(MonitoringLog.project_id == project_id)

    if check_type:
        query = query.filter(MonitoringLog.check_type == check_type)

    log = query.order_by(MonitoringLog.created_at.desc()).first()

    if not log:
        raise HTTPException(status_code=404, detail="No monitoring log found")

    return log
