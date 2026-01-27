"""스케줄러 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.schemas.monitoring import MonitoringLogResponse

router = APIRouter()

# 전역 스케줄러 인스턴스 (애플리케이션 수명 동안 유지)
_scheduler_instance = None


def get_scheduler(db: Session = Depends(get_db)):
    """스케줄러 인스턴스 반환"""
    from app.services.scheduler import MonitoringScheduler
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = MonitoringScheduler(db)
    return _scheduler_instance


@router.post("/scheduler/start")
async def start_scheduler(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모니터링 스케줄러를 시작합니다."""
    scheduler = get_scheduler(db)
    await scheduler.start()
    return {
        "message": "Scheduler started",
        "status": scheduler.get_status()
    }


@router.post("/scheduler/stop")
async def stop_scheduler(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모니터링 스케줄러를 중지합니다."""
    scheduler = get_scheduler(db)
    await scheduler.stop()
    return {
        "message": "Scheduler stopped",
        "status": scheduler.get_status()
    }


@router.get("/scheduler/status")
async def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """스케줄러의 현재 상태를 조회합니다."""
    scheduler = get_scheduler(db)
    return scheduler.get_status()


@router.post("/scheduler/project/{project_id}/start")
async def start_project_monitoring(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 프로젝트의 자동 모니터링을 시작합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scheduler = get_scheduler(db)
    await scheduler.start_monitoring(project_id)
    return {
        "message": f"Monitoring started for project {project_id}",
        "project_status": scheduler.get_project_status(project_id)
    }


@router.post("/scheduler/project/{project_id}/stop")
async def stop_project_monitoring(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 프로젝트의 자동 모니터링을 중지합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scheduler = get_scheduler(db)
    await scheduler.stop_monitoring(project_id)
    return {
        "message": f"Monitoring stopped for project {project_id}",
        "project_status": scheduler.get_project_status(project_id)
    }


@router.get("/scheduler/project/{project_id}/status")
async def get_project_monitoring_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 프로젝트의 모니터링 상태를 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scheduler = get_scheduler(db)
    return scheduler.get_project_status(project_id)


@router.post("/scheduler/project/{project_id}/check-now", response_model=MonitoringLogResponse)
async def check_project_now(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트를 즉시 체크합니다 (수동 트리거)."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scheduler = get_scheduler(db)
    log = await scheduler.check_now(project_id)

    if not log:
        raise HTTPException(status_code=500, detail="Check failed")

    return log
