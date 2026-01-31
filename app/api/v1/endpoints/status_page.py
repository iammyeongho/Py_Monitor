"""
# Laravel 개발자를 위한 설명
# 이 파일은 공개 상태 페이지 API 엔드포인트를 정의합니다.
# 인증 없이 접근 가능한 공개 API입니다.
#
# Laravel과의 주요 차이점:
# 1. 인증 미들웨어를 거치지 않는 공개 라우트
# 2. Depends(get_db)만 사용하여 DB 세션 주입
#
# 주요 기능:
# 1. 공개 프로젝트 목록 + 현재 상태 조회
# 2. 개별 프로젝트 상세 상태 조회
# 3. 90일 uptime 이력 조회
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.deps import get_db
from app.models.monitoring import MonitoringLog
from app.models.project import Project

router = APIRouter()


# ==================== 응답 스키마 ====================

class StatusProjectItem(BaseModel):
    """공개 상태 페이지 프로젝트 항목"""
    id: int
    title: str
    url: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_available: bool = True
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    last_checked_at: Optional[datetime] = None
    uptime_24h: float = 100.0
    uptime_7d: float = 100.0
    uptime_30d: float = 100.0


class StatusPageResponse(BaseModel):
    """공개 상태 페이지 전체 응답"""
    overall_status: str  # "operational", "degraded", "major_outage"
    projects: list[StatusProjectItem] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class StatusIncident(BaseModel):
    """상태 페이지 인시던트 (장애 이력)"""
    timestamp: datetime
    is_available: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None


class UptimeDayEntry(BaseModel):
    """일별 uptime 데이터"""
    date: str  # YYYY-MM-DD
    uptime_percentage: float
    total_checks: int
    available_checks: int


class StatusProjectDetail(BaseModel):
    """프로젝트 상세 상태"""
    id: int
    title: str
    url: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_available: bool = True
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    avg_response_time: Optional[float] = None
    last_checked_at: Optional[datetime] = None
    uptime_24h: float = 100.0
    uptime_7d: float = 100.0
    uptime_30d: float = 100.0
    uptime_90d: float = 100.0
    daily_uptime: list[UptimeDayEntry] = Field(default_factory=list)
    recent_incidents: list[StatusIncident] = Field(default_factory=list)


# ==================== 헬퍼 함수 ====================

def _calculate_uptime(db: Session, project_id: int, hours: int) -> float:
    """특정 기간 동안의 uptime 퍼센트 계산"""
    since = datetime.utcnow() - timedelta(hours=hours)

    total = db.query(func.count(MonitoringLog.id)).filter(
        MonitoringLog.project_id == project_id,
        MonitoringLog.created_at >= since,
    ).scalar() or 0

    if total == 0:
        return 100.0

    available = db.query(func.count(MonitoringLog.id)).filter(
        MonitoringLog.project_id == project_id,
        MonitoringLog.created_at >= since,
        MonitoringLog.is_available == True,  # noqa: E712
    ).scalar() or 0

    return round((available / total) * 100, 2)


def _get_latest_log(db: Session, project_id: int) -> Optional[MonitoringLog]:
    """최신 모니터링 로그 조회"""
    return (
        db.query(MonitoringLog)
        .filter(MonitoringLog.project_id == project_id)
        .order_by(MonitoringLog.created_at.desc())
        .first()
    )


# ==================== API 엔드포인트 ====================

@router.get("/", response_model=StatusPageResponse)
def get_public_status(db: Session = Depends(get_db)):
    """
    공개 상태 페이지 - 모든 공개 프로젝트의 현재 상태를 반환합니다.
    인증 없이 접근 가능합니다. 결과는 60초간 캐싱됩니다.
    """
    # 캐시 확인 (60초 TTL)
    cached = cache.get_json("status_page:list")
    if cached:
        return StatusPageResponse(**cached)

    # 공개 설정된 활성 프로젝트만 조회
    projects = (
        db.query(Project)
        .filter(
            Project.is_public == True,  # noqa: E712
            Project.is_active == True,  # noqa: E712
            Project.deleted_at.is_(None),
        )
        .order_by(Project.title)
        .all()
    )

    items = []
    has_degraded = False
    has_outage = False

    for project in projects:
        latest_log = _get_latest_log(db, project.id)

        is_available = True
        status_code = None
        response_time = None
        last_checked_at = None

        if latest_log:
            is_available = latest_log.is_available or False
            status_code = latest_log.status_code
            response_time = latest_log.response_time
            last_checked_at = latest_log.created_at

        uptime_24h = _calculate_uptime(db, project.id, 24)
        uptime_7d = _calculate_uptime(db, project.id, 24 * 7)
        uptime_30d = _calculate_uptime(db, project.id, 24 * 30)

        if not is_available:
            has_outage = True
        elif uptime_24h < 99.0:
            has_degraded = True

        items.append(StatusProjectItem(
            id=project.id,
            title=project.title,
            url=str(project.url),
            description=project.description,
            category=project.category,
            is_available=is_available,
            status_code=status_code,
            response_time=response_time,
            last_checked_at=last_checked_at,
            uptime_24h=uptime_24h,
            uptime_7d=uptime_7d,
            uptime_30d=uptime_30d,
        ))

    # 전체 상태 판단
    if has_outage:
        overall_status = "major_outage"
    elif has_degraded:
        overall_status = "degraded"
    else:
        overall_status = "operational"

    response = StatusPageResponse(
        overall_status=overall_status,
        projects=items,
        last_updated=datetime.utcnow(),
    )

    # 결과를 캐시에 저장 (60초 TTL)
    cache.set_json("status_page:list", response.model_dump(mode="json"), ttl=60)

    return response


@router.get("/{project_id}", response_model=StatusProjectDetail)
def get_public_project_status(
    project_id: int,
    days: int = Query(90, ge=1, le=90, description="일별 uptime 이력 기간 (일)"),
    db: Session = Depends(get_db),
):
    """
    공개 프로젝트의 상세 상태를 반환합니다.
    90일간의 일별 uptime 이력과 최근 장애 이력을 포함합니다.
    인증 없이 접근 가능합니다. 결과는 120초간 캐싱됩니다.
    """
    # 캐시 확인 (120초 TTL)
    cache_key = f"status_page:detail:{project_id}:{days}"
    cached = cache.get_json(cache_key)
    if cached:
        return StatusProjectDetail(**cached)

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.is_public == True,  # noqa: E712
            Project.is_active == True,  # noqa: E712
            Project.deleted_at.is_(None),
        )
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    latest_log = _get_latest_log(db, project.id)

    is_available = True
    status_code = None
    response_time = None
    last_checked_at = None

    if latest_log:
        is_available = latest_log.is_available or False
        status_code = latest_log.status_code
        response_time = latest_log.response_time
        last_checked_at = latest_log.created_at

    # 평균 응답 시간 (24시간)
    since_24h = datetime.utcnow() - timedelta(hours=24)
    avg_response_time = db.query(func.avg(MonitoringLog.response_time)).filter(
        MonitoringLog.project_id == project.id,
        MonitoringLog.created_at >= since_24h,
        MonitoringLog.is_available == True,  # noqa: E712
    ).scalar()

    # 일별 uptime 이력
    daily_uptime = []
    for i in range(days - 1, -1, -1):
        day_start = (datetime.utcnow() - timedelta(days=i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        total = db.query(func.count(MonitoringLog.id)).filter(
            MonitoringLog.project_id == project.id,
            MonitoringLog.created_at >= day_start,
            MonitoringLog.created_at < day_end,
        ).scalar() or 0

        available = db.query(func.count(MonitoringLog.id)).filter(
            MonitoringLog.project_id == project.id,
            MonitoringLog.created_at >= day_start,
            MonitoringLog.created_at < day_end,
            MonitoringLog.is_available == True,  # noqa: E712
        ).scalar() or 0

        percentage = round((available / total) * 100, 2) if total > 0 else 100.0

        daily_uptime.append(UptimeDayEntry(
            date=day_start.strftime("%Y-%m-%d"),
            uptime_percentage=percentage,
            total_checks=total,
            available_checks=available,
        ))

    # 최근 장애 이력 (최근 20건)
    incidents = (
        db.query(MonitoringLog)
        .filter(
            MonitoringLog.project_id == project.id,
            MonitoringLog.is_available == False,  # noqa: E712
        )
        .order_by(MonitoringLog.created_at.desc())
        .limit(20)
        .all()
    )

    recent_incidents = [
        StatusIncident(
            timestamp=log.created_at,
            is_available=log.is_available or False,
            status_code=log.status_code,
            response_time=log.response_time,
            error_message=log.error_message,
        )
        for log in incidents
    ]

    response = StatusProjectDetail(
        id=project.id,
        title=project.title,
        url=str(project.url),
        description=project.description,
        category=project.category,
        is_available=is_available,
        status_code=status_code,
        response_time=response_time,
        avg_response_time=round(avg_response_time, 3) if avg_response_time else None,
        last_checked_at=last_checked_at,
        uptime_24h=_calculate_uptime(db, project.id, 24),
        uptime_7d=_calculate_uptime(db, project.id, 24 * 7),
        uptime_30d=_calculate_uptime(db, project.id, 24 * 30),
        uptime_90d=_calculate_uptime(db, project.id, 24 * 90),
        daily_uptime=daily_uptime,
        recent_incidents=recent_incidents,
    )

    # 결과를 캐시에 저장 (120초 TTL)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl=120)

    return response
