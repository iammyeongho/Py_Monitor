"""모니터링 설정 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringSetting
from app.models.project import Project
from app.schemas.monitoring import (
    MonitoringSettingCreate,
    MonitoringSettingResponse,
    MonitoringSettingUpdate,
)

router = APIRouter()


@router.post("/settings", response_model=MonitoringSettingResponse)
def create_monitoring_setting(
    setting: MonitoringSettingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 설정을 생성합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == setting.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 이미 설정이 있는지 확인
    existing = (
        db.query(MonitoringSetting)
        .filter(MonitoringSetting.project_id == setting.project_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Setting already exists")

    db_setting = MonitoringSetting(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


@router.get("/settings/{project_id}", response_model=MonitoringSettingResponse)
def get_monitoring_setting(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 설정을 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    setting = (
        db.query(MonitoringSetting)
        .filter(MonitoringSetting.project_id == project_id)
        .first()
    )
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    return setting


@router.put("/settings/{project_id}", response_model=MonitoringSettingResponse)
def update_monitoring_setting(
    project_id: int,
    setting: MonitoringSettingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 설정을 업데이트합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_setting = (
        db.query(MonitoringSetting)
        .filter(MonitoringSetting.project_id == project_id)
        .first()
    )
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")

    update_data = setting.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_setting, key, value)

    db.commit()
    db.refresh(db_setting)
    return db_setting
