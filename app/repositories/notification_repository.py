"""
알림 Repository

알림(Notification) 엔티티에 대한 데이터 접근 로직을 캡슐화합니다.

주요 기능:
- 알림 CRUD
- 읽지 않은 알림 조회
- 알림 읽음 처리
- 심각도별 알림 조회
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """알림 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, Notification)

    def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        프로젝트의 알림 조회

        Args:
            project_id: 프로젝트 ID
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            알림 목록
        """
        return (
            self.db.query(Notification)
            .filter(Notification.project_id == project_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unread(
        self,
        project_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        읽지 않은 알림 조회

        Args:
            project_id: 프로젝트 ID (None이면 전체)
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            읽지 않은 알림 목록
        """
        query = (
            self.db.query(Notification)
            .filter(Notification.is_read == False)  # noqa: E712
        )

        if project_id:
            query = query.filter(Notification.project_id == project_id)

        return (
            query
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_severity(
        self,
        severity: str,
        project_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        심각도별 알림 조회

        Args:
            severity: 심각도 (info, warning, error, critical)
            project_id: 프로젝트 ID (None이면 전체)
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            알림 목록
        """
        query = (
            self.db.query(Notification)
            .filter(Notification.severity == severity)
        )

        if project_id:
            query = query.filter(Notification.project_id == project_id)

        return (
            query
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        """
        알림을 읽음으로 표시

        Args:
            notification_id: 알림 ID

        Returns:
            업데이트된 알림 또는 None
        """
        notification = self.get_by_id(notification_id)
        if not notification:
            return None

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, project_id: Optional[int] = None) -> int:
        """
        모든 알림을 읽음으로 표시

        Args:
            project_id: 프로젝트 ID (None이면 전체)

        Returns:
            업데이트된 알림 개수
        """
        now = datetime.utcnow()
        query = (
            self.db.query(Notification)
            .filter(Notification.is_read == False)  # noqa: E712
        )

        if project_id:
            query = query.filter(Notification.project_id == project_id)

        updated = query.update({
            "is_read": True,
            "read_at": now
        })

        self.db.commit()
        return updated

    def mark_as_sent(self, notification_id: int) -> Optional[Notification]:
        """
        알림을 발송됨으로 표시

        Args:
            notification_id: 알림 ID

        Returns:
            업데이트된 알림 또는 None
        """
        notification = self.get_by_id(notification_id)
        if not notification:
            return None

        notification.is_sent = True
        notification.sent_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_unsent(self, limit: int = 100) -> List[Notification]:
        """
        발송되지 않은 알림 조회

        Args:
            limit: 최대 조회 개수

        Returns:
            발송되지 않은 알림 목록
        """
        return (
            self.db.query(Notification)
            .filter(Notification.is_sent == False)  # noqa: E712
            .order_by(Notification.created_at.asc())
            .limit(limit)
            .all()
        )

    def count_unread(self, project_id: Optional[int] = None) -> int:
        """
        읽지 않은 알림 개수 조회

        Args:
            project_id: 프로젝트 ID (None이면 전체)

        Returns:
            읽지 않은 알림 개수
        """
        query = (
            self.db.query(Notification)
            .filter(Notification.is_read == False)  # noqa: E712
        )

        if project_id:
            query = query.filter(Notification.project_id == project_id)

        return query.count()

    def delete_old_notifications(self, days: int = 30) -> int:
        """
        오래된 알림 삭제

        Args:
            days: 보관 기간 (일)

        Returns:
            삭제된 알림 개수
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # 읽은 알림만 삭제
        deleted = (
            self.db.query(Notification)
            .filter(Notification.is_read == True)  # noqa: E712
            .filter(Notification.created_at < cutoff)
            .delete()
        )

        self.db.commit()
        return deleted

    def get_recent(
        self,
        hours: int = 24,
        project_id: Optional[int] = None
    ) -> List[Notification]:
        """
        최근 알림 조회

        Args:
            hours: 조회할 시간 범위
            project_id: 프로젝트 ID (None이면 전체)

        Returns:
            최근 알림 목록
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = (
            self.db.query(Notification)
            .filter(Notification.created_at >= since)
        )

        if project_id:
            query = query.filter(Notification.project_id == project_id)

        return query.order_by(Notification.created_at.desc()).all()
