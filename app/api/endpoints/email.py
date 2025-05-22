"""
# Laravel 개발자를 위한 설명
# 이 파일은 이메일 관련 API 엔드포인트를 정의합니다.
# Laravel의 EmailController와 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 이메일 발송
# 2. 이메일 로그 조회
# 3. 프로젝트별 이메일 로그 조회
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.email import EmailCreate, EmailLogResponse
from app.services.email_service import EmailService

router = APIRouter()

@router.post("/send", response_model=EmailLogResponse)
async def send_email(
    email: EmailCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """이메일 발송"""
    email_service = EmailService(db)
    return email_service.send_email(
        user_id=current_user.id,
        email=email.email,
        subject=email.subject,
        body=email.body,
        project_id=email.project_id
    )

@router.get("/logs", response_model=List[EmailLogResponse])
async def get_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """이메일 로그 조회"""
    email_service = EmailService(db)
    return email_service.get_email_logs(current_user.id, skip=skip, limit=limit)

@router.get("/project/{project_id}/logs", response_model=List[EmailLogResponse])
async def get_project_email_logs(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """프로젝트별 이메일 로그 조회"""
    email_service = EmailService(db)
    return email_service.get_project_email_logs(project_id, current_user.id, skip=skip, limit=limit) 