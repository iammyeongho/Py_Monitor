from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.schemas.monitoring import (
    MonitoringCheckRequest,
    MonitoringCheckResponse,
    MonitoringStatus,
    SSLStatus
)
from app.services.monitoring_service import MonitoringService
from urllib.parse import urlparse

router = APIRouter()

@router.post("/check", response_model=MonitoringCheckResponse)
async def check_website(
    request: MonitoringCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """웹사이트 상태 체크"""
    # URL에서 호스트네임 추출
    parsed_url = urlparse(str(request.url))
    hostname = parsed_url.netloc

    # 웹사이트 상태 체크
    status = await MonitoringService.check_website(
        str(request.url),
        timeout=request.timeout
    )

    # SSL 체크 (요청된 경우)
    ssl_status = None
    if request.check_ssl and parsed_url.scheme == 'https':
        ssl_status = MonitoringService.check_ssl(hostname)

    return MonitoringCheckResponse(
        status=status,
        ssl=ssl_status
    )

@router.get("/project/{project_id}/status", response_model=MonitoringCheckResponse)
async def check_project_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """프로젝트 상태 체크"""
    # 프로젝트 조회
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.url:
        raise HTTPException(status_code=400, detail="Project URL is not set")

    # 웹사이트 상태 체크
    status = await MonitoringService.check_website(
        project.url,
        timeout=30
    )

    # SSL 체크 (HTTPS인 경우)
    ssl_status = None
    if project.url.startswith('https://'):
        parsed_url = urlparse(project.url)
        ssl_status = MonitoringService.check_ssl(parsed_url.netloc)

    return MonitoringCheckResponse(
        status=status,
        ssl=ssl_status
    )
