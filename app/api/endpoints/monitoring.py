"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 관련 API 엔드포인트를 정의합니다.
# Laravel의 Controller와 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 모니터링 상태 조회
# 2. 모니터링 설정 관리
# 3. 알림 관리
# 4. 로그 조회
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    MonitoringLogResponse,
    MonitoringAlertResponse,
    MonitoringSettingResponse,
    MonitoringSettingUpdate,
    SSLDomainStatusResponse
)
from app.services.monitoring import MonitoringService
from app.core.scheduler import scheduler

router = APIRouter()

@router.get("/projects/{project_id}/status", response_model=MonitoringLogResponse)
async def get_project_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    프로젝트 모니터링 상태 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    monitoring_service = MonitoringService(db)
    status = await monitoring_service.check_project_status(project)
    return status

@router.get("/projects/{project_id}/ssl", response_model=SSLDomainStatusResponse)
async def get_ssl_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    SSL 인증서 상태 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    monitoring_service = MonitoringService(db)
    status = await monitoring_service.check_ssl_status(project)
    return status

@router.get("/projects/{project_id}/logs", response_model=List[MonitoringLogResponse])
async def get_project_logs(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    프로젝트 모니터링 로그 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logs = db.query(MonitoringLog)\
        .filter(MonitoringLog.project_id == project_id)\
        .order_by(MonitoringLog.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return logs

@router.get("/projects/{project_id}/alerts", response_model=List[MonitoringAlertResponse])
async def get_project_alerts(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    프로젝트 알림 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    alerts = db.query(MonitoringAlert)\
        .filter(MonitoringAlert.project_id == project_id)\
        .order_by(MonitoringAlert.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return alerts

@router.get("/projects/{project_id}/settings", response_model=MonitoringSettingResponse)
async def get_monitoring_settings(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    모니터링 설정 조회
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    settings = db.query(MonitoringSetting)\
        .filter(MonitoringSetting.project_id == project_id)\
        .first()
    
    if not settings:
        raise HTTPException(status_code=404, detail="Monitoring settings not found")
    
    return settings

@router.put("/projects/{project_id}/settings", response_model=MonitoringSettingResponse)
async def update_monitoring_settings(
    project_id: int,
    settings: MonitoringSettingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    모니터링 설정 업데이트
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_settings = db.query(MonitoringSetting)\
        .filter(MonitoringSetting.project_id == project_id)\
        .first()
    
    if not db_settings:
        db_settings = MonitoringSetting(project_id=project_id)
        db.add(db_settings)
    
    for key, value in settings.dict(exclude_unset=True).items():
        setattr(db_settings, key, value)
    
    db.commit()
    db.refresh(db_settings)
    
    # 모니터링 간격이 변경된 경우 스케줄러 업데이트
    if settings.status_interval:
        project.status_interval = settings.status_interval
        db.commit()
        await scheduler.stop_monitoring(project_id)
        await scheduler.start_monitoring(project_id)
    
    return db_settings

@router.post("/projects/{project_id}/monitoring/start")
async def start_monitoring(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    프로젝트 모니터링 시작
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await scheduler.start_monitoring(project_id)
    return {"message": "Monitoring started"}

@router.post("/projects/{project_id}/monitoring/stop")
async def stop_monitoring(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    프로젝트 모니터링 중지
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await scheduler.stop_monitoring(project_id)
    return {"message": "Monitoring stopped"} 