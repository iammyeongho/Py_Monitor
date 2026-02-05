"""차트 데이터 API"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringLog, MonitoringAlert
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    AnomalyAnalysis,
    AnomalyDetail,
    AvailabilityChartData,
    ChartDataPoint,
    DashboardChartData,
    ResponseTimeChartData,
    SLADailyEntry,
    SLAIncident,
    SLAMetrics,
    SLAReport,
)
from pydantic import BaseModel
from typing import Optional


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
    """대시보드 통계 요약 데이터를 조회합니다. 결과는 30초간 캐싱됩니다."""
    # 캐시 확인 (30초 TTL)
    cache_key = f"dashboard:stats:{current_user.id}"
    cached = cache.get_json(cache_key)
    if cached:
        return DashboardStats(**cached)

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

    response = DashboardStats(
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

    # 결과를 캐시에 저장 (30초 TTL)
    cache.set_json(cache_key, response.model_dump(mode="json"), ttl=30)

    return response


@router.get("/reports/sla/{project_id}", response_model=SLAReport)
def get_sla_report(
    project_id: int,
    days: int = Query(default=30, ge=1, le=365, description="리포트 기간 (일)"),
    target_uptime: float = Query(
        default=99.9, ge=90.0, le=100.0, description="SLA 목표 가용률 (%)"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Uptime SLA 리포트를 생성합니다.

    지정된 기간 동안의 가용성, 응답시간, 장애 인시던트를 분석하여
    SLA 준수 여부를 확인합니다.
    """
    # 프로젝트 확인
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 기간 설정
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=days)

    # 해당 기간의 모니터링 로그 조회 (시간순 정렬)
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

    # 전체 통계 계산
    total_checks = len(logs)
    available_checks = sum(1 for log in logs if log.is_available)
    failed_checks = total_checks - available_checks

    # 응답시간 통계 (가용한 체크만)
    response_times = [
        log.response_time * 1000
        for log in logs
        if log.is_available and log.response_time
    ]
    avg_rt = round(sum(response_times) / len(response_times), 2) if response_times else None
    max_rt = round(max(response_times), 2) if response_times else None
    min_rt = round(min(response_times), 2) if response_times else None

    # P95 응답시간 계산
    p95_rt = None
    if response_times:
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_rt = round(sorted_times[min(p95_index, len(sorted_times) - 1)], 2)

    # 가용률 계산
    achieved_uptime = (
        round((available_checks / total_checks) * 100, 4)
        if total_checks > 0 else 100.0
    )

    # 다운타임 추정 (분): 체크 간격을 기반으로 계산
    # 모니터링 간격 추정 (로그가 2개 이상일 때)
    check_interval_minutes = 5.0  # 기본값 5분
    if len(logs) >= 2:
        total_span = (logs[-1].created_at - logs[0].created_at).total_seconds()
        check_interval_minutes = round(total_span / (len(logs) - 1) / 60, 2)

    total_downtime_minutes = round(failed_checks * check_interval_minutes, 2)

    # SLA 허용 다운타임 계산
    total_period_minutes = days * 24 * 60
    allowed_downtime_minutes = round(
        total_period_minutes * (1 - target_uptime / 100), 2
    )

    sla_met = achieved_uptime >= target_uptime

    # --- 일별 분석 ---
    daily_data = defaultdict(lambda: {
        "total": 0, "available": 0, "response_times": [], "incidents": 0
    })

    for log in logs:
        day_key = log.created_at.strftime("%Y-%m-%d")
        daily_data[day_key]["total"] += 1
        if log.is_available:
            daily_data[day_key]["available"] += 1
            if log.response_time:
                daily_data[day_key]["response_times"].append(
                    log.response_time * 1000
                )

    daily_breakdown = []
    current_date = period_start.date()
    end_date = period_end.date()

    while current_date <= end_date:
        day_key = current_date.strftime("%Y-%m-%d")
        data = daily_data.get(day_key)

        if data and data["total"] > 0:
            day_uptime = round(
                (data["available"] / data["total"]) * 100, 2
            )
            day_avg_rt = (
                round(
                    sum(data["response_times"]) / len(data["response_times"]), 2
                )
                if data["response_times"]
                else None
            )
            daily_breakdown.append(SLADailyEntry(
                date=day_key,
                total_checks=data["total"],
                available_checks=data["available"],
                uptime_percentage=day_uptime,
                avg_response_time=day_avg_rt,
                incidents_count=data["total"] - data["available"],
            ))
        else:
            # 데이터 없는 날은 100% 표시 (체크 없음)
            daily_breakdown.append(SLADailyEntry(
                date=day_key,
                total_checks=0,
                available_checks=0,
                uptime_percentage=100.0,
            ))

        current_date += timedelta(days=1)

    # --- 인시던트 탐지 (연속 실패 그룹) ---
    incidents = []
    incident_start = None
    incident_error = None

    for log in logs:
        if not log.is_available:
            if incident_start is None:
                incident_start = log.created_at
                incident_error = log.error_message
        else:
            if incident_start is not None:
                # 장애 종료: 현재 로그 시점에서 복구됨
                duration = (log.created_at - incident_start).total_seconds() / 60
                incidents.append(SLAIncident(
                    started_at=incident_start,
                    ended_at=log.created_at,
                    duration_minutes=round(duration, 2),
                    error_message=incident_error,
                ))
                incident_start = None
                incident_error = None

    # 아직 진행 중인 인시던트 처리
    if incident_start is not None:
        duration = (period_end - incident_start).total_seconds() / 60
        incidents.append(SLAIncident(
            started_at=incident_start,
            ended_at=None,  # 아직 진행 중
            duration_minutes=round(duration, 2),
            error_message=incident_error,
        ))

    # 일별 인시던트 카운트 업데이트
    for incident in incidents:
        day_key = incident.started_at.strftime("%Y-%m-%d")
        for entry in daily_breakdown:
            if entry.date == day_key:
                break

    # SLA 메트릭 구성
    metrics = SLAMetrics(
        target_uptime=target_uptime,
        achieved_uptime=achieved_uptime,
        sla_met=sla_met,
        total_checks=total_checks,
        available_checks=available_checks,
        failed_checks=failed_checks,
        total_downtime_minutes=total_downtime_minutes,
        allowed_downtime_minutes=allowed_downtime_minutes,
        incidents_count=len(incidents),
        avg_response_time=avg_rt,
        max_response_time=max_rt,
        min_response_time=min_rt,
        p95_response_time=p95_rt,
    )

    return SLAReport(
        project_id=project_id,
        project_title=project.title,
        project_url=str(project.url),
        period_start=period_start,
        period_end=period_end,
        period_days=days,
        metrics=metrics,
        daily_breakdown=daily_breakdown,
        incidents=incidents,
    )


@router.get("/reports/anomaly/{project_id}", response_model=AnomalyAnalysis)
def detect_anomalies(
    project_id: int,
    analysis_hours: int = Query(
        default=1, ge=1, le=24, description="분석 대상 기간 (시간)"
    ),
    baseline_hours: int = Query(
        default=168, ge=24, le=720, description="기준선 기간 (시간, 기본 7일)"
    ),
    sensitivity: float = Query(
        default=2.0, ge=1.0, le=5.0,
        description="민감도 (Z-score 임계값, 낮을수록 민감)"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모니터링 데이터의 이상 징후를 탐지합니다.

    기준선(baseline) 기간의 통계와 최근 분석 기간을 비교하여
    Z-score 기반으로 이상 패턴을 감지합니다.
    """
    import math

    # 프로젝트 확인
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    now = datetime.now(timezone.utc)

    # 기준선 기간 로그 (분석 기간 제외)
    baseline_start = now - timedelta(hours=baseline_hours)
    analysis_start = now - timedelta(hours=analysis_hours)

    baseline_logs = (
        db.query(MonitoringLog)
        .filter(
            MonitoringLog.project_id == project_id,
            MonitoringLog.created_at >= baseline_start,
            MonitoringLog.created_at < analysis_start,
        )
        .all()
    )

    # 분석 대상 기간 로그
    analysis_logs = (
        db.query(MonitoringLog)
        .filter(
            MonitoringLog.project_id == project_id,
            MonitoringLog.created_at >= analysis_start,
            MonitoringLog.created_at <= now,
        )
        .all()
    )

    anomalies = []

    # --- 기준선 통계 계산 ---
    baseline_rts = [
        log.response_time * 1000
        for log in baseline_logs
        if log.is_available and log.response_time
    ]
    baseline_total = len(baseline_logs)
    baseline_available = sum(1 for log in baseline_logs if log.is_available)

    baseline_avg_rt = (
        sum(baseline_rts) / len(baseline_rts) if baseline_rts else 0
    )
    baseline_std_rt = 0.0
    if len(baseline_rts) >= 2:
        variance = sum(
            (x - baseline_avg_rt) ** 2 for x in baseline_rts
        ) / len(baseline_rts)
        baseline_std_rt = math.sqrt(variance)

    baseline_avail_pct = (
        (baseline_available / baseline_total * 100)
        if baseline_total > 0 else 100.0
    )

    baseline_error_rate = (
        ((baseline_total - baseline_available) / baseline_total * 100)
        if baseline_total > 0 else 0.0
    )

    # --- 분석 기간 통계 ---
    analysis_rts = [
        log.response_time * 1000
        for log in analysis_logs
        if log.is_available and log.response_time
    ]
    analysis_total = len(analysis_logs)
    analysis_available = sum(1 for log in analysis_logs if log.is_available)

    analysis_avg_rt = (
        sum(analysis_rts) / len(analysis_rts) if analysis_rts else 0
    )

    analysis_avail_pct = (
        (analysis_available / analysis_total * 100)
        if analysis_total > 0 else 100.0
    )

    analysis_error_rate = (
        ((analysis_total - analysis_available) / analysis_total * 100)
        if analysis_total > 0 else 0.0
    )

    # --- 이상 탐지 1: 응답시간 급증 (Z-score) ---
    if baseline_std_rt > 0 and analysis_avg_rt > 0:
        z_score = (analysis_avg_rt - baseline_avg_rt) / baseline_std_rt
        if z_score > sensitivity:
            deviation = round(
                ((analysis_avg_rt - baseline_avg_rt) / baseline_avg_rt) * 100, 1
            ) if baseline_avg_rt > 0 else 0

            severity = "critical" if z_score > sensitivity * 2 else "warning"
            anomalies.append(AnomalyDetail(
                type="response_time_spike",
                severity=severity,
                message=(
                    f"응답시간이 평소보다 {deviation}% 증가했습니다 "
                    f"({round(baseline_avg_rt, 1)}ms → {round(analysis_avg_rt, 1)}ms)"
                ),
                detected_at=now,
                metric_name="avg_response_time",
                current_value=round(analysis_avg_rt, 2),
                baseline_value=round(baseline_avg_rt, 2),
                deviation_percent=round(deviation, 1),
            ))

    # --- 이상 탐지 2: 가용성 하락 ---
    if baseline_total > 0 and analysis_total > 0:
        avail_drop = baseline_avail_pct - analysis_avail_pct
        if avail_drop > (100 - baseline_avail_pct + 1):  # 기준선 대비 유의미한 하락
            severity = "critical" if analysis_avail_pct < 95 else "warning"
            anomalies.append(AnomalyDetail(
                type="availability_drop",
                severity=severity,
                message=(
                    f"가용성이 {round(baseline_avail_pct, 2)}%에서 "
                    f"{round(analysis_avail_pct, 2)}%로 하락했습니다"
                ),
                detected_at=now,
                metric_name="availability",
                current_value=round(analysis_avail_pct, 2),
                baseline_value=round(baseline_avail_pct, 2),
                deviation_percent=round(avail_drop, 1),
            ))

    # --- 이상 탐지 3: 에러율 증가 ---
    if baseline_total > 0 and analysis_total > 0:
        error_increase = analysis_error_rate - baseline_error_rate
        if error_increase > 5:  # 에러율 5% 이상 증가
            severity = "critical" if analysis_error_rate > 20 else "warning"
            anomalies.append(AnomalyDetail(
                type="error_rate_increase",
                severity=severity,
                message=(
                    f"에러율이 {round(baseline_error_rate, 1)}%에서 "
                    f"{round(analysis_error_rate, 1)}%로 증가했습니다"
                ),
                detected_at=now,
                metric_name="error_rate",
                current_value=round(analysis_error_rate, 2),
                baseline_value=round(baseline_error_rate, 2),
                deviation_percent=round(error_increase, 1),
            ))

    # --- 이상 탐지 4: 개별 응답시간 이상치 ---
    if baseline_std_rt > 0:
        upper_bound = baseline_avg_rt + (sensitivity * baseline_std_rt)
        outlier_count = sum(1 for rt in analysis_rts if rt > upper_bound)
        if len(analysis_rts) > 0:
            outlier_rate = (outlier_count / len(analysis_rts)) * 100
            if outlier_rate > 20:  # 이상치 비율 20% 이상
                anomalies.append(AnomalyDetail(
                    type="pattern_change",
                    severity="warning",
                    message=(
                        f"응답시간 이상치 비율이 {round(outlier_rate, 1)}%입니다 "
                        f"(기준: {round(upper_bound, 1)}ms 초과)"
                    ),
                    detected_at=now,
                    metric_name="outlier_rate",
                    current_value=round(outlier_rate, 2),
                    baseline_value=20.0,
                    deviation_percent=round(outlier_rate - 20, 1),
                ))

    # --- 이상 탐지 5: 데이터 없음 (모니터링 중단) ---
    if analysis_total == 0 and baseline_total > 0:
        anomalies.append(AnomalyDetail(
            type="pattern_change",
            severity="critical",
            message="분석 기간 동안 모니터링 데이터가 없습니다 (모니터링 중단 의심)",
            detected_at=now,
            metric_name="check_count",
            current_value=0,
            baseline_value=float(baseline_total),
            deviation_percent=100.0,
        ))

    # 심각도별 카운트
    critical_count = sum(1 for a in anomalies if a.severity == "critical")
    warning_count = sum(1 for a in anomalies if a.severity == "warning")
    info_count = sum(1 for a in anomalies if a.severity == "info")

    return AnomalyAnalysis(
        project_id=project_id,
        project_title=project.title,
        analysis_period_hours=analysis_hours,
        baseline_period_hours=baseline_hours,
        total_anomalies=len(anomalies),
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        anomalies=anomalies,
        baseline_stats={
            "total_checks": baseline_total,
            "available_checks": baseline_available,
            "availability_pct": round(baseline_avail_pct, 2),
            "avg_response_time_ms": round(baseline_avg_rt, 2),
            "std_response_time_ms": round(baseline_std_rt, 2),
            "error_rate_pct": round(baseline_error_rate, 2),
        },
        current_stats={
            "total_checks": analysis_total,
            "available_checks": analysis_available,
            "availability_pct": round(analysis_avail_pct, 2),
            "avg_response_time_ms": round(analysis_avg_rt, 2),
            "error_rate_pct": round(analysis_error_rate, 2),
        },
    )
