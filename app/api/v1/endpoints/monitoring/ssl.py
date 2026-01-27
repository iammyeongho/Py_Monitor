"""SSL 도메인 상태 API"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    SSLDomainStatusCreate,
    SSLDomainStatusResponse,
    SSLDomainStatusUpdate,
)

router = APIRouter()


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
