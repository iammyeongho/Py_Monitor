"""
모니터링 Repository

모니터링 관련 엔티티(MonitoringLog, MonitoringAlert, MonitoringSetting)에 대한
데이터 접근 로직을 캡슐화합니다.

주요 기능:
- 모니터링 로그 CRUD
- 알림 관리
- 설정 관리
- 통계 조회
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringLog, MonitoringSetting
from app.repositories.base import BaseRepository


class MonitoringLogRepository(BaseRepository[MonitoringLog]):
    """모니터링 로그 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, MonitoringLog)

    def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[MonitoringLog]:
        """
        프로젝트의 모니터링 로그 조회

        Args:
            project_id: 프로젝트 ID
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            모니터링 로그 목록
        """
        return (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .order_by(MonitoringLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest_by_project(self, project_id: int) -> Optional[MonitoringLog]:
        """
        프로젝트의 최신 모니터링 로그 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            최신 모니터링 로그 또는 None
        """
        return (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .order_by(MonitoringLog.created_at.desc())
            .first()
        )

    def get_by_date_range(
        self,
        project_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[MonitoringLog]:
        """
        기간별 모니터링 로그 조회

        Args:
            project_id: 프로젝트 ID
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            모니터링 로그 목록
        """
        return (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .filter(MonitoringLog.created_at >= start_date)
            .filter(MonitoringLog.created_at <= end_date)
            .order_by(MonitoringLog.created_at.desc())
            .all()
        )

    def get_failed_logs(
        self,
        project_id: int,
        hours: int = 24
    ) -> List[MonitoringLog]:
        """
        실패한 모니터링 로그 조회

        Args:
            project_id: 프로젝트 ID
            hours: 조회할 시간 범위

        Returns:
            실패 로그 목록
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .filter(MonitoringLog.is_available == False)  # noqa: E712
            .filter(MonitoringLog.created_at >= since)
            .order_by(MonitoringLog.created_at.desc())
            .all()
        )

    def get_availability_stats(
        self,
        project_id: int,
        days: int = 7
    ) -> Tuple[int, int, float]:
        """
        가용성 통계 조회

        Args:
            project_id: 프로젝트 ID
            days: 조회할 일수

        Returns:
            (성공 횟수, 실패 횟수, 가용성 비율)
        """
        since = datetime.utcnow() - timedelta(days=days)

        total = (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .filter(MonitoringLog.created_at >= since)
            .count()
        )

        success = (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .filter(MonitoringLog.is_available == True)  # noqa: E712
            .filter(MonitoringLog.created_at >= since)
            .count()
        )

        failed = total - success
        availability = (success / total * 100) if total > 0 else 0.0

        return success, failed, availability

    def get_avg_response_time(
        self,
        project_id: int,
        days: int = 7
    ) -> Optional[float]:
        """
        평균 응답 시간 조회

        Args:
            project_id: 프로젝트 ID
            days: 조회할 일수

        Returns:
            평균 응답 시간 또는 None
        """
        since = datetime.utcnow() - timedelta(days=days)

        result = (
            self.db.query(func.avg(MonitoringLog.response_time))
            .filter(MonitoringLog.project_id == project_id)
            .filter(MonitoringLog.is_available == True)  # noqa: E712
            .filter(MonitoringLog.created_at >= since)
            .scalar()
        )

        return float(result) if result else None

    def delete_old_logs(self, days: int = 30) -> int:
        """
        오래된 로그 삭제

        Args:
            days: 보관 기간 (일)

        Returns:
            삭제된 로그 개수
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        deleted = (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.created_at < cutoff)
            .delete()
        )

        self.db.commit()
        return deleted

    def count_by_project(self, project_id: int) -> int:
        """
        프로젝트의 로그 개수 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            로그 개수
        """
        return (
            self.db.query(MonitoringLog)
            .filter(MonitoringLog.project_id == project_id)
            .count()
        )


class MonitoringAlertRepository(BaseRepository[MonitoringAlert]):
    """모니터링 알림 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, MonitoringAlert)

    def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        unresolved_only: bool = False
    ) -> List[MonitoringAlert]:
        """
        프로젝트의 알림 조회

        Args:
            project_id: 프로젝트 ID
            skip: 건너뛸 개수
            limit: 최대 조회 개수
            unresolved_only: 미해결 알림만 조회

        Returns:
            알림 목록
        """
        query = (
            self.db.query(MonitoringAlert)
            .filter(MonitoringAlert.project_id == project_id)
        )

        if unresolved_only:
            query = query.filter(MonitoringAlert.is_resolved == False)  # noqa: E712

        return (
            query
            .order_by(MonitoringAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unresolved_alerts(self) -> List[MonitoringAlert]:
        """
        모든 미해결 알림 조회

        Returns:
            미해결 알림 목록
        """
        return (
            self.db.query(MonitoringAlert)
            .filter(MonitoringAlert.is_resolved == False)  # noqa: E712
            .order_by(MonitoringAlert.created_at.desc())
            .all()
        )

    def resolve_alert(self, alert_id: int) -> Optional[MonitoringAlert]:
        """
        알림 해결 처리

        Args:
            alert_id: 알림 ID

        Returns:
            업데이트된 알림 또는 None
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_all_by_project(self, project_id: int) -> int:
        """
        프로젝트의 모든 알림 해결 처리

        Args:
            project_id: 프로젝트 ID

        Returns:
            해결된 알림 개수
        """
        now = datetime.utcnow()

        updated = (
            self.db.query(MonitoringAlert)
            .filter(MonitoringAlert.project_id == project_id)
            .filter(MonitoringAlert.is_resolved == False)  # noqa: E712
            .update({
                "is_resolved": True,
                "resolved_at": now,
                "updated_at": now
            })
        )

        self.db.commit()
        return updated

    def count_unresolved_by_project(self, project_id: int) -> int:
        """
        프로젝트의 미해결 알림 개수 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            미해결 알림 개수
        """
        return (
            self.db.query(MonitoringAlert)
            .filter(MonitoringAlert.project_id == project_id)
            .filter(MonitoringAlert.is_resolved == False)  # noqa: E712
            .count()
        )


class MonitoringSettingRepository(BaseRepository[MonitoringSetting]):
    """모니터링 설정 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, MonitoringSetting)

    def get_by_project(self, project_id: int) -> Optional[MonitoringSetting]:
        """
        프로젝트의 모니터링 설정 조회

        Args:
            project_id: 프로젝트 ID

        Returns:
            모니터링 설정 또는 None
        """
        return (
            self.db.query(MonitoringSetting)
            .filter(MonitoringSetting.project_id == project_id)
            .first()
        )

    def create_default(self, project_id: int) -> MonitoringSetting:
        """
        기본 모니터링 설정 생성

        Args:
            project_id: 프로젝트 ID

        Returns:
            생성된 설정
        """
        setting = MonitoringSetting(
            project_id=project_id,
            check_interval=300,  # 5분
            timeout=30,
            retry_count=3,
            alert_threshold=3,
            is_alert_enabled=True
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def get_or_create(self, project_id: int) -> MonitoringSetting:
        """
        모니터링 설정 조회 또는 생성

        Args:
            project_id: 프로젝트 ID

        Returns:
            모니터링 설정
        """
        setting = self.get_by_project(project_id)
        if not setting:
            setting = self.create_default(project_id)
        return setting

    def update_setting(
        self,
        project_id: int,
        settings: dict
    ) -> Optional[MonitoringSetting]:
        """
        모니터링 설정 업데이트

        Args:
            project_id: 프로젝트 ID
            settings: 업데이트할 설정

        Returns:
            업데이트된 설정 또는 None
        """
        setting = self.get_by_project(project_id)
        if not setting:
            return None

        for key, value in settings.items():
            if hasattr(setting, key):
                setattr(setting, key, value)

        setting.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(setting)
        return setting
