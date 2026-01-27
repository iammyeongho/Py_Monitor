"""모니터링 알림 API"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringAlert
from app.models.project import Project
from app.schemas.monitoring import MonitoringAlertResponse

router = APIRouter()


@router.get("/alerts/{project_id}", response_model=List[MonitoringAlertResponse])
def get_monitoring_alerts(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 알림을 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    alerts = (
        db.query(MonitoringAlert)
        .filter(MonitoringAlert.project_id == project_id)
        .order_by(MonitoringAlert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return alerts


@router.post("/notification/test/{project_id}")
async def send_test_notification(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """테스트 알림을 발송합니다."""
    from app.services.notification_service import NotificationService

    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    notification_service = NotificationService(db)
    success = await notification_service.send_alert_notification(
        project_id=project_id,
        alert_type="test",
        message="테스트 알림입니다. 알림 설정이 정상적으로 작동합니다.",
        details={"테스트 유형": "수동 테스트"}
    )

    return {
        "success": success,
        "message": "테스트 알림이 발송되었습니다." if success else "알림 발송에 실패했습니다. 알림 설정을 확인하세요."
    }
