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

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.monitoring import MonitoringSetting
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    ContentCheckRequest,
    ContentCheckResponse,
    DNSLookupRequest,
    DNSLookupResponse,
    MonitoringAlertResponse,
    MonitoringLogResponse,
    MonitoringResponse,
    MonitoringSettingCreate,
    MonitoringSettingResponse,
    MonitoringSettingUpdate,
    SecurityHeadersRequest,
    SecurityHeadersResponse,
    SSLDomainStatusCreate,
    SSLDomainStatusResponse,
    SSLDomainStatusUpdate,
    TCPPortCheckRequest,
    TCPPortCheckResponse,
)
from app.services.monitoring import check_project_status, MonitoringService

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
