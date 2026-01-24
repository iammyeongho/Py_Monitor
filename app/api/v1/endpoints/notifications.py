"""
알림(Notification) 관련 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_user
from app.models.notification import Notification
from app.models.project import Project

router = APIRouter()


@router.post("/", response_model=dict)
def create_notification(
    notification: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == notification["project_id"]).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    notif = Notification(**notification)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif.__dict__


@router.get("/project/{project_id}", response_model=List[dict])
def get_notifications_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    notifs = db.query(Notification).filter(Notification.project_id == project_id).all()
    return [n.__dict__ for n in notifs]


@router.get("/unread", response_model=List[dict])
def get_unread_notifications(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    notifs = (
        db.query(Notification)
        .join(Project)
        .filter(Project.user_id == current_user.id, Notification.is_read.is_(False))
        .all()
    )
    return [n.__dict__ for n in notifs]


@router.get("/{notification_id}", response_model=dict)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notif = (
        db.query(Notification)
        .join(Project)
        .filter(Notification.id == notification_id, Project.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif.__dict__


@router.put("/{notification_id}", response_model=dict)
def update_notification(
    notification_id: int,
    notification: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notif = (
        db.query(Notification)
        .join(Project)
        .filter(Notification.id == notification_id, Project.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    for key, value in notification.items():
        setattr(notif, key, value)
    db.commit()
    db.refresh(notif)
    return notif.__dict__


@router.delete("/{notification_id}", response_model=dict)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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
    return {"id": notification_id}


@router.put("/mark-all-read", response_model=dict)
def mark_all_as_read(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    notifs = (
        db.query(Notification)
        .join(Project)
        .filter(Project.user_id == current_user.id, Notification.is_read.is_(False))
        .all()
    )
    for notif in notifs:
        notif.is_read = True
        notif.read_at = None
    db.commit()
    return {"message": "All notifications marked as read"}
