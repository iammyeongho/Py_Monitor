"""로그 정리 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter()


@router.get("/cleanup/statistics")
async def get_cleanup_statistics(
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """로그 통계를 조회합니다."""
    from app.services.cleanup_service import CleanupService

    cleanup_service = CleanupService(db)
    stats = cleanup_service.get_log_statistics(project_id)
    disk_usage = cleanup_service.get_disk_usage_estimate()

    return {
        "statistics": stats,
        "disk_usage": disk_usage,
    }


@router.post("/cleanup/logs")
async def cleanup_logs(
    retention_days: int = 30,
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """오래된 모니터링 로그를 정리합니다."""
    from app.services.cleanup_service import CleanupService

    if retention_days < 7:
        raise HTTPException(status_code=400, detail="최소 보관 기간은 7일입니다.")

    cleanup_service = CleanupService(db)
    deleted_count = cleanup_service.cleanup_monitoring_logs(
        retention_days=retention_days,
        project_id=project_id
    )

    return {
        "deleted_count": deleted_count,
        "retention_days": retention_days,
        "message": f"{deleted_count}개의 로그가 삭제되었습니다."
    }


@router.post("/cleanup/alerts")
async def cleanup_alerts(
    retention_days: int = 90,
    project_id: int = None,
    only_resolved: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """오래된 알림을 정리합니다."""
    from app.services.cleanup_service import CleanupService

    if retention_days < 7:
        raise HTTPException(status_code=400, detail="최소 보관 기간은 7일입니다.")

    cleanup_service = CleanupService(db)
    deleted_count = cleanup_service.cleanup_alerts(
        retention_days=retention_days,
        project_id=project_id,
        only_resolved=only_resolved
    )

    return {
        "deleted_count": deleted_count,
        "retention_days": retention_days,
        "message": f"{deleted_count}개의 알림이 삭제되었습니다."
    }


@router.post("/cleanup/all")
async def cleanup_all(
    log_retention_days: int = 30,
    alert_retention_days: int = 90,
    email_log_retention_days: int = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모든 오래된 로그를 정리합니다."""
    from app.services.cleanup_service import CleanupService

    if log_retention_days < 7 or alert_retention_days < 7 or email_log_retention_days < 7:
        raise HTTPException(status_code=400, detail="최소 보관 기간은 7일입니다.")

    cleanup_service = CleanupService(db)
    results = cleanup_service.cleanup_all(
        log_retention_days=log_retention_days,
        alert_retention_days=alert_retention_days,
        email_log_retention_days=email_log_retention_days
    )

    return results
