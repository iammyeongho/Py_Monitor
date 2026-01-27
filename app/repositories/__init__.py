"""
Repository 패키지

데이터 접근 로직을 캡슐화하는 Repository 패턴을 구현합니다.
클린 아키텍처의 Infrastructure Layer에 해당합니다.

사용 예시:
    from app.repositories import UserRepository, ProjectRepository

    # Repository 인스턴스 생성
    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)

    # 데이터 조회
    user = user_repo.get_by_email("test@example.com")
    projects = project_repo.get_by_user(user.id)
"""

from app.repositories.base import BaseRepository
from app.repositories.monitoring_repository import (
    MonitoringAlertRepository,
    MonitoringLogRepository,
    MonitoringSettingRepository,
)
from app.repositories.notification_repository import NotificationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProjectRepository",
    "MonitoringLogRepository",
    "MonitoringAlertRepository",
    "MonitoringSettingRepository",
    "NotificationRepository",
]
