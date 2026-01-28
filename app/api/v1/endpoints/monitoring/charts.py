"""차트 데이터 API"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringLog, MonitoringAlert
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    AvailabilityChartData,
    ChartDataPoint,
    DashboardChartData,
    ResponseTimeChartData,
)
from pydantic import BaseModel
from typing import List, Optional


class DashboardStats(BaseModel):
    """대시보드 통계 요약"""
    total_projects: int
    active_projects: int
    available_projects: int
    unavailable_projects: int
    overall_availability: float
    avg_response_time: Optional[float]
    total_alerts: int
    unresolved_alerts: int
    ssl_expiring_soon: int
    domain_expiring_soon: int

router = APIRouter()


@router.get("/charts/dashboard", response_model=DashboardChartData)
def get_dashboard_chart_data(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """대시보드 차트 데이터를 조회합니다."""
    # 기간 설정
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(hours=hours)

    # 사용자의 모든 프로젝트 조회
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.is_active.is_(True))
        .all()
    )

    response_time_data = []
    availability_data = []

    for project in projects:
        # 해당 프로젝트의 로그 조회
        logs = (
            db.query(MonitoringLog)
            .filter(
                MonitoringLog.project_id == project.id,
                MonitoringLog.created_at >= period_start,
                MonitoringLog.created_at <= period_end,
            )
            .order_by(MonitoringLog.created_at.asc())
            .all()
        )

        if not logs:
            continue

        # 응답 시간 데이터 수집
        response_times = []
        data_points = []
        for log in logs:
            data_points.append(ChartDataPoint(
                timestamp=log.created_at,
                value=log.response_time * 1000 if log.response_time else None,
                is_available=log.is_available,
            ))
            if log.response_time:
                response_times.append(log.response_time * 1000)

        # 응답 시간 통계
        avg_rt = sum(response_times) / len(response_times) if response_times else None
        min_rt = min(response_times) if response_times else None
        max_rt = max(response_times) if response_times else None

        response_time_data.append(ResponseTimeChartData(
            project_id=project.id,
            project_title=project.title,
            data_points=data_points,
            avg_response_time=avg_rt,
            min_response_time=min_rt,
            max_response_time=max_rt,
        ))

        # 가용성 데이터 수집
        total_checks = len(logs)
        available_checks = sum(1 for log in logs if log.is_available)
        availability_pct = (available_checks / total_checks * 100) if total_checks > 0 else 0

        availability_data.append(AvailabilityChartData(
            project_id=project.id,
            project_title=project.title,
            total_checks=total_checks,
            available_checks=available_checks,
            availability_percentage=round(availability_pct, 2),
            data_points=data_points,
        ))

    return DashboardChartData(
        response_time=response_time_data,
        availability=availability_data,
        period_start=period_start,
        period_end=period_end,
    )


@router.get("/charts/project/{project_id}/response-time", response_model=ResponseTimeChartData)
def get_project_response_time_chart(
    project_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 응답 시간 차트 데이터를 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 기간 설정
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(hours=hours)

    logs = (
        db.query(MonitoringLog)
        .filter(
            MonitoringLog.project_id == project_id,
            MonitoringLog.created_at >= period_start,
            MonitoringLog.created_at <= period_end,
        )
        .order_by(MonitoringLog.created_at.asc())
        .all()
    )

    response_times = []
    data_points = []
    for log in logs:
        data_points.append(ChartDataPoint(
            timestamp=log.created_at,
            value=log.response_time * 1000 if log.response_time else None,
            is_available=log.is_available,
        ))
        if log.response_time:
            response_times.append(log.response_time * 1000)

    avg_rt = sum(response_times) / len(response_times) if response_times else None
    min_rt = min(response_times) if response_times else None
    max_rt = max(response_times) if response_times else None

    return ResponseTimeChartData(
        project_id=project_id,
        project_title=project.title,
        data_points=data_points,
        avg_response_time=avg_rt,
        min_response_time=min_rt,
        max_response_time=max_rt,
    )


@router.get("/charts/project/{project_id}/availability", response_model=AvailabilityChartData)
def get_project_availability_chart(
    project_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 가용성 차트 데이터를 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 기간 설정
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(hours=hours)

    logs = (
        db.query(MonitoringLog)
        .filter(
            MonitoringLog.project_id == project_id,
            MonitoringLog.created_at >= period_start,
            MonitoringLog.created_at <= period_end,
        )
        .order_by(MonitoringLog.created_at.asc())
        .all()
    )

    data_points = []
    for log in logs:
        data_points.append(ChartDataPoint(
            timestamp=log.created_at,
            value=log.response_time * 1000 if log.response_time else None,
            is_available=log.is_available,
        ))

    total_checks = len(logs)
    available_checks = sum(1 for log in logs if log.is_available)
    availability_pct = (available_checks / total_checks * 100) if total_checks > 0 else 0

    return AvailabilityChartData(
        project_id=project_id,
        project_title=project.title,
        total_checks=total_checks,
        available_checks=available_checks,
        availability_percentage=round(availability_pct, 2),
        data_points=data_points,
    )


@router.get("/charts/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """대시보드 통계 요약 데이터를 조회합니다."""
    # 사용자의 프로젝트 조회
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.deleted_at.is_(None))
        .all()
    )

    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.is_active)

    # 최근 로그 기반 가용성 체크
    available_count = 0
    unavailable_count = 0
    response_times = []

    for project in projects:
        if not project.is_active:
            continue

        # 최신 로그 조회
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

            if latest_log.response_time:
                response_times.append(latest_log.response_time * 1000)

    # 가용률 계산
    total_checked = available_count + unavailable_count
    overall_availability = (
        (available_count / total_checked * 100) if total_checked > 0 else 100.0
    )

    # 평균 응답 시간
    avg_response_time = (
        sum(response_times) / len(response_times) if response_times else None
    )

    # 알림 통계
    project_ids = [p.id for p in projects]
    total_alerts = (
        db.query(MonitoringAlert)
        .filter(MonitoringAlert.project_id.in_(project_ids))
        .count()
    ) if project_ids else 0

    unresolved_alerts = (
        db.query(MonitoringAlert)
        .filter(
            MonitoringAlert.project_id.in_(project_ids),
            MonitoringAlert.is_resolved.is_(False)
        )
        .count()
    ) if project_ids else 0

    # SSL/도메인 만료 임박 체크
    ssl_expiring = 0
    domain_expiring = 0

    for project in projects:
        ssl_status = (
            db.query(SSLDomainStatus)
            .filter(SSLDomainStatus.project_id == project.id)
            .first()
        )
        if ssl_status:
            if ssl_status.is_ssl_expiring_soon:
                ssl_expiring += 1
            if ssl_status.is_domain_expiring_soon:
                domain_expiring += 1

    return DashboardStats(
        total_projects=total_projects,
        active_projects=active_projects,
        available_projects=available_count,
        unavailable_projects=unavailable_count,
        overall_availability=round(overall_availability, 2),
        avg_response_time=round(avg_response_time, 2) if avg_response_time else None,
        total_alerts=total_alerts,
        unresolved_alerts=unresolved_alerts,
        ssl_expiring_soon=ssl_expiring,
        domain_expiring_soon=domain_expiring,
    )
