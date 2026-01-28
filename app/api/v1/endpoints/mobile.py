"""모바일 최적화 API 엔드포인트"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert
from app.schemas.base import MobileProjectSummary, PaginatedResponse

router = APIRouter()


@router.get("/projects", response_model=PaginatedResponse[MobileProjectSummary])
def get_mobile_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모바일 최적화된 프로젝트 목록을 조회합니다."""
    # 쿼리 빌드
    query = db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.is_active.is_(True),
        Project.deleted_at.is_(None)
    )

    if category:
        query = query.filter(Project.category == category)

    if tag:
        query = query.filter(Project.tags.ilike(f"%{tag}%"))

    # 전체 개수
    total = query.count()

    # 페이지네이션
    skip = (page - 1) * page_size
    projects = query.order_by(Project.created_at.desc()).offset(skip).limit(page_size).all()

    # 모바일용 요약 정보 생성
    items = []
    for project in projects:
        # 최신 로그 조회
        latest_log = (
            db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project.id)
            .order_by(MonitoringLog.created_at.desc())
            .first()
        )

        # 24시간 가용률 계산
        period_start = datetime.now(timezone.utc) - timedelta(hours=24)
        logs_24h = (
            db.query(MonitoringLog)
            .filter(
                MonitoringLog.project_id == project.id,
                MonitoringLog.created_at >= period_start
            )
            .all()
        )

        total_checks = len(logs_24h)
        available_checks = sum(1 for log in logs_24h if log.is_available)
        availability_pct = (available_checks / total_checks * 100) if total_checks > 0 else None

        # 미해결 알림 여부
        has_unresolved = (
            db.query(MonitoringAlert)
            .filter(
                MonitoringAlert.project_id == project.id,
                MonitoringAlert.is_resolved.is_(False)
            )
            .first() is not None
        )

        items.append(MobileProjectSummary(
            id=project.id,
            title=project.title,
            url=project.url,
            is_available=latest_log.is_available if latest_log else None,
            availability_percentage=round(availability_pct, 2) if availability_pct else None,
            last_response_time=round(latest_log.response_time * 1000, 2) if latest_log and latest_log.response_time else None,
            last_checked_at=latest_log.created_at if latest_log else None,
            has_unresolved_alerts=has_unresolved
        ))

    # 페이지네이션 정보 계산
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@router.get("/dashboard")
def get_mobile_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모바일 대시보드 요약 정보를 조회합니다."""
    # 프로젝트 조회
    projects = (
        db.query(Project)
        .filter(
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
            Project.deleted_at.is_(None)
        )
        .all()
    )

    total_projects = len(projects)
    available_count = 0
    unavailable_count = 0

    for project in projects:
        latest_log = (
            db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project.id)
            .order_by(MonitoringLog.created_at.desc())
            .first()
        )
        if latest_log:
            if latest_log.is_available:
                available_count += 1
            else:
                unavailable_count += 1

    # 미해결 알림 수
    project_ids = [p.id for p in projects]
    unresolved_alerts = 0
    if project_ids:
        unresolved_alerts = (
            db.query(MonitoringAlert)
            .filter(
                MonitoringAlert.project_id.in_(project_ids),
                MonitoringAlert.is_resolved.is_(False)
            )
            .count()
        )

    return {
        "total_projects": total_projects,
        "available": available_count,
        "unavailable": unavailable_count,
        "unresolved_alerts": unresolved_alerts,
        "overall_status": "healthy" if unavailable_count == 0 else "warning" if unavailable_count < total_projects / 2 else "critical"
    }


@router.get("/alerts")
def get_mobile_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    unresolved_only: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모바일용 알림 목록을 조회합니다."""
    # 사용자의 프로젝트 ID
    project_ids = [
        p.id for p in db.query(Project.id)
        .filter(Project.user_id == current_user.id)
        .all()
    ]

    if not project_ids:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
        }

    # 쿼리 빌드
    query = db.query(MonitoringAlert).filter(
        MonitoringAlert.project_id.in_(project_ids)
    )

    if unresolved_only:
        query = query.filter(MonitoringAlert.is_resolved.is_(False))

    total = query.count()
    skip = (page - 1) * page_size

    alerts = (
        query
        .order_by(MonitoringAlert.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    items = []
    for alert in alerts:
        project = db.query(Project).filter(Project.id == alert.project_id).first()
        items.append({
            "id": alert.id,
            "project_id": alert.project_id,
            "project_title": project.title if project else "Unknown",
            "alert_type": alert.alert_type,
            "message": alert.message,
            "is_resolved": alert.is_resolved,
            "created_at": alert.created_at
        })

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
