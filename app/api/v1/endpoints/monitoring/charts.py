"""차트 데이터 API"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringLog
from app.models.project import Project
from app.schemas.monitoring import (
    AvailabilityChartData,
    ChartDataPoint,
    DashboardChartData,
    ResponseTimeChartData,
)

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
