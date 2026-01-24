"""
알림(Notification) 엔드포인트 모듈

이 파일은 FastAPI를 사용하여 알림 관련 API 엔드포인트를 정의합니다.
Laravel의 NotificationController와 유사한 역할을 합니다.

주요 기능:
1. 알림 생성/조회/수정/삭제 (CRUD)
2. 읽지 않은 알림 조회
3. 모든 알림 읽음 처리

Laravel과의 주요 차이점:
1. APIRouter = Laravel의 Route::controller()와 유사
2. Depends = Laravel의 dependency injection과 유사
3. HTTPException = Laravel의 abort()와 유사
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.notification import Notification
from app.models.project import Project
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)

router = APIRouter()


@router.post("/", response_model=NotificationResponse)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """새로운 알림을 생성합니다."""
    project = db.query(Project).filter(Project.id == notification.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    notif = Notification(**notification.model_dump())
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@router.get("/project/{project_id}", response_model=List[NotificationResponse])
def get_notifications_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 프로젝트의 모든 알림을 조회합니다."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    notifs = (
        db.query(Notification)
        .filter(Notification.project_id == project_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return notifs


@router.get("/unread", response_model=List[NotificationResponse])
def get_unread_notifications(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """현재 사용자의 읽지 않은 모든 알림을 조회합니다."""
    notifs = (
        db.query(Notification)
        .join(Project)
        .filter(Project.user_id == current_user.id, Notification.is_read.is_(False))
        .order_by(Notification.created_at.desc())
        .all()
    )
    return notifs


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 알림을 조회합니다."""
    notif = (
        db.query(Notification)
        .join(Project)
        .filter(Notification.id == notification_id, Project.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: int,
    notification: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """알림 정보를 업데이트합니다."""
    notif = (
        db.query(Notification)
        .join(Project)
        .filter(Notification.id == notification_id, Project.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    update_data = notification.model_dump(exclude_unset=True)

    # 읽음 처리 시 read_at 자동 설정
    if update_data.get("is_read") is True and notif.is_read is False:
        update_data["read_at"] = datetime.now(timezone.utc)

    for key, value in update_data.items():
        setattr(notif, key, value)

    db.commit()
    db.refresh(notif)
    return notif


@router.delete("/{notification_id}", response_model=dict)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """알림을 삭제합니다."""
    notif = (
        db.query(Notification)
        .join(Project)
        .filter(Notification.id == notification_id, Project.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()
    return {"id": notification_id, "message": "Notification deleted"}


@router.put("/mark-all-read", response_model=dict)
def mark_all_as_read(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """현재 사용자의 모든 알림을 읽음 처리합니다."""
    now = datetime.now(timezone.utc)
    notifs = (
        db.query(Notification)
        .join(Project)
        .filter(Project.user_id == current_user.id, Notification.is_read.is_(False))
        .all()
    )
    count = len(notifs)
    for notif in notifs:
        notif.is_read = True
        notif.read_at = now
    db.commit()
    return {"message": f"{count} notifications marked as read"}
