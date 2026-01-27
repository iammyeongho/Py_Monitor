"""
프로젝트 Repository

프로젝트(Project) 엔티티에 대한 데이터 접근 로직을 캡슐화합니다.
Laravel의 Project Repository 패턴과 유사합니다.

주요 기능:
- 프로젝트 CRUD
- 사용자별 프로젝트 조회
- 활성 프로젝트 조회
- URL로 프로젝트 조회
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """프로젝트 Repository"""

    def __init__(self, db: Session):
        super().__init__(db, Project)

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Project]:
        """
        사용자의 프로젝트 목록 조회

        Args:
            user_id: 사용자 ID
            skip: 건너뛸 개수
            limit: 최대 조회 개수
            include_deleted: 삭제된 프로젝트 포함 여부

        Returns:
            프로젝트 목록
        """
        query = self.db.query(Project).filter(Project.user_id == user_id)

        if not include_deleted:
            query = query.filter(Project.deleted_at.is_(None))

        return (
            query
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user_and_id(
        self,
        project_id: int,
        user_id: int
    ) -> Optional[Project]:
        """
        사용자의 특정 프로젝트 조회

        Args:
            project_id: 프로젝트 ID
            user_id: 사용자 ID

        Returns:
            조회된 프로젝트 또는 None
        """
        return (
            self.db.query(Project)
            .filter(Project.id == project_id)
            .filter(Project.user_id == user_id)
            .filter(Project.deleted_at.is_(None))
            .first()
        )

    def get_by_url(self, url: str, user_id: int) -> Optional[Project]:
        """
        URL로 프로젝트 조회

        Args:
            url: 프로젝트 URL
            user_id: 사용자 ID

        Returns:
            조회된 프로젝트 또는 None
        """
        return (
            self.db.query(Project)
            .filter(Project.url == url)
            .filter(Project.user_id == user_id)
            .filter(Project.deleted_at.is_(None))
            .first()
        )

    def get_active_projects(self, user_id: Optional[int] = None) -> List[Project]:
        """
        활성 프로젝트 목록 조회

        Args:
            user_id: 사용자 ID (None이면 전체)

        Returns:
            활성 프로젝트 목록
        """
        query = (
            self.db.query(Project)
            .filter(Project.is_active == True)  # noqa: E712
            .filter(Project.deleted_at.is_(None))
        )

        if user_id:
            query = query.filter(Project.user_id == user_id)

        return query.order_by(Project.created_at.desc()).all()

    def get_all_active_for_monitoring(self) -> List[Project]:
        """
        모니터링 대상 활성 프로젝트 목록 조회
        (스케줄러에서 사용)

        Returns:
            모니터링 대상 프로젝트 목록
        """
        return (
            self.db.query(Project)
            .filter(Project.is_active == True)  # noqa: E712
            .filter(Project.status == True)  # noqa: E712
            .filter(Project.deleted_at.is_(None))
            .all()
        )

    def toggle_active_status(
        self,
        project_id: int,
        user_id: int
    ) -> Optional[Project]:
        """
        프로젝트 활성화 상태 토글

        Args:
            project_id: 프로젝트 ID
            user_id: 사용자 ID

        Returns:
            업데이트된 프로젝트 또는 None
        """
        project = self.get_by_user_and_id(project_id, user_id)
        if not project:
            return None

        project.is_active = not project.is_active
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def update_snapshot(
        self,
        project_id: int,
        snapshot_path: str
    ) -> Optional[Project]:
        """
        프로젝트 스냅샷 경로 업데이트

        Args:
            project_id: 프로젝트 ID
            snapshot_path: 스냅샷 파일 경로

        Returns:
            업데이트된 프로젝트 또는 None
        """
        project = self.get_by_id(project_id)
        if not project:
            return None

        project.snapshot_path = snapshot_path
        project.last_snapshot_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        return project

    def count_by_user(self, user_id: int) -> int:
        """
        사용자의 프로젝트 개수 조회

        Args:
            user_id: 사용자 ID

        Returns:
            프로젝트 개수
        """
        return (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .filter(Project.deleted_at.is_(None))
            .count()
        )
