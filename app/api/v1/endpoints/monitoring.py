"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 MonitoringController와 유사한 역할을 합니다.
# FastAPI를 사용하여 모니터링 관련 엔드포인트를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. APIRouter = Laravel의 Route::controller()와 유사
# 2. Depends = Laravel의 dependency injection과 유사
# 3. HTTPException = Laravel의 abort()와 유사
"""

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringSetting
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    AvailabilityChartData,
    ChartDataPoint,
    ContentCheckRequest,
    ContentCheckResponse,
    DashboardChartData,
    DNSLookupRequest,
    DNSLookupResponse,
    MonitoringAlertResponse,
    MonitoringLogResponse,
    MonitoringResponse,
    MonitoringSettingCreate,
    MonitoringSettingResponse,
    MonitoringSettingUpdate,
    PlaywrightCheckResponse,
    PlaywrightHealth,
    PlaywrightMemory,
    PlaywrightNetwork,
    PlaywrightPerformance,
    PlaywrightResources,
    ResponseTimeChartData,
    SecurityHeadersRequest,
    SecurityHeadersResponse,
    SSLDomainStatusCreate,
    SSLDomainStatusResponse,
    SSLDomainStatusUpdate,
    TCPPortCheckRequest,
    TCPPortCheckResponse,
)
from app.services.monitoring import check_project_status, MonitoringService
from app.services.playwright_monitor import PlaywrightMonitorService

router = APIRouter()


# =====================
# 모니터링 상태 엔드포인트
# =====================


@router.get("/status/{project_id}", response_model=MonitoringResponse)
def get_project_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 현재 상태를 확인합니다."""
    db_project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
        )
        .first()
    )
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project_status = check_project_status(db_project)
    return project_status


@router.get("/status", response_model=List[MonitoringResponse])
def get_all_projects_status(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """현재 사용자의 모든 프로젝트 상태를 확인합니다."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.is_active.is_(True))
        .all()
    )
    statuses = [check_project_status(project) for project in projects]
    return statuses


# =====================
# 모니터링 설정 엔드포인트
# =====================


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


# =====================
# SSL 도메인 상태 엔드포인트
# =====================


@router.post("/ssl", response_model=SSLDomainStatusResponse)
def create_ssl_status(
    ssl_status: SSLDomainStatusCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """SSL 도메인 상태를 생성합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == ssl_status.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_ssl = SSLDomainStatus(**ssl_status.model_dump())
    db.add(db_ssl)
    db.commit()
    db.refresh(db_ssl)
    return db_ssl


@router.get("/ssl/{project_id}", response_model=List[SSLDomainStatusResponse])
def get_ssl_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 SSL 도메인 상태를 조회합니다."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ssl_statuses = (
        db.query(SSLDomainStatus)
        .filter(SSLDomainStatus.project_id == project_id)
        .all()
    )
    return ssl_statuses


@router.put("/ssl/{ssl_id}", response_model=SSLDomainStatusResponse)
def update_ssl_status(
    ssl_id: int,
    ssl_update: SSLDomainStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """SSL 도메인 상태를 업데이트합니다."""
    db_ssl = db.query(SSLDomainStatus).filter(SSLDomainStatus.id == ssl_id).first()
    if not db_ssl:
        raise HTTPException(status_code=404, detail="SSL status not found")

    # 프로젝트 소유권 확인
    project = (
        db.query(Project)
        .filter(Project.id == db_ssl.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = ssl_update.model_dump(exclude_unset=True)
    update_data["last_checked_at"] = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(db_ssl, key, value)

    db.commit()
    db.refresh(db_ssl)
    return db_ssl


@router.delete("/ssl/{ssl_id}", response_model=dict)
def delete_ssl_status(
    ssl_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """SSL 도메인 상태를 삭제합니다."""
    db_ssl = db.query(SSLDomainStatus).filter(SSLDomainStatus.id == ssl_id).first()
    if not db_ssl:
        raise HTTPException(status_code=404, detail="SSL status not found")

    # 프로젝트 소유권 확인
    project = (
        db.query(Project)
        .filter(Project.id == db_ssl.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_ssl)
    db.commit()
    return {"id": ssl_id, "message": "SSL status deleted"}


# =====================
# TCP 포트 체크 엔드포인트
# =====================


@router.post("/check/tcp", response_model=TCPPortCheckResponse)
async def check_tcp_port(
    request: TCPPortCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """TCP 포트 연결 가능 여부를 확인합니다."""
    service = MonitoringService(db)
    result = await service.check_tcp_port(
        host=request.host,
        port=request.port,
        timeout=request.timeout,
    )
    return result


# =====================
# DNS 조회 엔드포인트
# =====================


@router.post("/check/dns", response_model=DNSLookupResponse)
async def check_dns_lookup(
    request: DNSLookupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """DNS 레코드를 조회합니다."""
    service = MonitoringService(db)
    result = await service.check_dns_lookup(
        domain=request.domain,
        record_type=request.record_type,
    )
    return result


# =====================
# 콘텐츠 검증 엔드포인트
# =====================


@router.post("/check/content", response_model=ContentCheckResponse)
async def check_content(
    request: ContentCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """응답 콘텐츠에 특정 문자열이 포함되어 있는지 확인합니다."""
    service = MonitoringService(db)
    result = await service.check_content(
        url=request.url,
        expected_content=request.expected_content,
        timeout=request.timeout,
    )
    return result


# =====================
# 보안 헤더 체크 엔드포인트
# =====================


@router.post("/check/security-headers", response_model=SecurityHeadersResponse)
async def check_security_headers(
    request: SecurityHeadersRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """HTTP 보안 헤더를 확인합니다."""
    service = MonitoringService(db)
    result = await service.check_security_headers(
        url=request.url,
        timeout=request.timeout,
    )
    return result


# =====================
# 모니터링 로그 엔드포인트
# =====================


@router.get("/logs/{project_id}", response_model=List[MonitoringLogResponse])
def get_monitoring_logs(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 로그를 조회합니다."""
    from app.models.monitoring import MonitoringLog

    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = (
        db.query(MonitoringLog)
        .filter(MonitoringLog.project_id == project_id)
        .order_by(MonitoringLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs


# =====================
# 모니터링 알림 엔드포인트
# =====================


@router.get("/alerts/{project_id}", response_model=List[MonitoringAlertResponse])
def get_monitoring_alerts(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 모니터링 알림을 조회합니다."""
    from app.models.monitoring import MonitoringAlert

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


# =====================
# Playwright 심층 체크 엔드포인트
# =====================


@router.get("/check/deep/{project_id}", response_model=PlaywrightCheckResponse)
async def check_deep_monitoring(
    project_id: int,
    save_log: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Playwright를 사용한 심층 모니터링을 수행합니다.

    HTTP 상태 코드 외에도 다음을 체크합니다:
    - DOM 로드 상태
    - JavaScript 에러
    - 페이지 성능 메트릭 (FCP, LCP)
    - 리소스 로드 상태
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    service = PlaywrightMonitorService(db)
    metrics = await service.monitor_project(project_id, save_log=save_log)

    return PlaywrightCheckResponse(
        project_id=project_id,
        url=str(project.url),
        is_available=metrics.is_available,
        status_code=metrics.status_code,
        response_time=metrics.response_time,
        error_message=metrics.error_message,
        performance=PlaywrightPerformance(
            dom_content_loaded=metrics.dom_content_loaded,
            page_load_time=metrics.page_load_time,
            first_contentful_paint=metrics.first_contentful_paint,
            largest_contentful_paint=metrics.largest_contentful_paint,
            time_to_first_byte=metrics.time_to_first_byte,
            cumulative_layout_shift=metrics.cumulative_layout_shift,
            total_blocking_time=metrics.total_blocking_time
        ),
        health=PlaywrightHealth(
            is_dom_ready=metrics.is_dom_ready,
            is_js_healthy=metrics.is_js_healthy,
            js_errors=metrics.js_errors or [],
            console_errors=metrics.console_errors
        ),
        resources=PlaywrightResources(
            count=metrics.resource_count,
            size=metrics.resource_size,
            failed=metrics.failed_resources
        ),
        network=PlaywrightNetwork(
            redirect_count=metrics.redirect_count
        ),
        memory=PlaywrightMemory(
            js_heap_size=metrics.js_heap_size
        ),
        checked_at=datetime.now(timezone.utc)
    )


@router.get("/logs/{project_id}/latest", response_model=MonitoringLogResponse)
def get_latest_monitoring_log(
    project_id: int,
    check_type: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 최신 모니터링 로그를 조회합니다."""
    from app.models.monitoring import MonitoringLog

    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(MonitoringLog).filter(MonitoringLog.project_id == project_id)

    if check_type:
        query = query.filter(MonitoringLog.check_type == check_type)

    log = query.order_by(MonitoringLog.created_at.desc()).first()

    if not log:
        raise HTTPException(status_code=404, detail="No monitoring log found")

    return log


# =====================
# 스케줄러 엔드포인트
# =====================

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


# =====================
# 로그 정리 엔드포인트
# =====================


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


# =====================
# 차트 데이터 엔드포인트
# =====================


@router.get("/charts/dashboard", response_model=DashboardChartData)
def get_dashboard_chart_data(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """대시보드 차트 데이터를 조회합니다."""
    from app.models.monitoring import MonitoringLog

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
    from app.models.monitoring import MonitoringLog

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
    from app.models.monitoring import MonitoringLog

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
