"""
프로젝트 서비스

프로젝트 관련 비즈니스 로직을 구현합니다.
Laravel의 ProjectService와 유사한 역할을 합니다.

클린 아키텍처:
- Application Layer에 위치
- Repository를 통해 데이터 접근
- 비즈니스 규칙 적용
- 커스텀 예외 발생

주요 기능:
1. 프로젝트 CRUD
2. 프로젝트 상태 관리
3. 프로젝트 설정 관리
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project
from app.repositories import MonitoringSettingRepository, ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """프로젝트 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProjectRepository(db)
        self.setting_repository = MonitoringSettingRepository(db)

    def create_project(self, user_id: int, project: ProjectCreate) -> Project:
        """
        프로젝트 생성

        Args:
            user_id: 사용자 ID
            project: 생성할 프로젝트 정보

        Returns:
            생성된 프로젝트

        Raises:
            ConflictError: URL이 이미 등록된 경우
        """
        # URL 중복 검사
        existing = self.repository.get_by_url(project.url, user_id)
        if existing:
            raise ConflictError("이미 등록된 URL입니다", field="url")

        # 프로젝트 데이터 준비
        project_data = {
            "user_id": user_id,
            "title": project.title,
            "url": project.url,
            "host_name": project.host_name,
            "ip_address": project.ip_address,
            "description": getattr(project, "description", None),
            "is_active": True,
        }

        # 프로젝트 생성
        db_project = self.repository.create(project_data)

        # 기본 모니터링 설정 생성
        self.setting_repository.create_default(db_project.id)

        return db_project

    def get_project(self, project_id: int, user_id: int) -> Project:
        """
        프로젝트 조회

        Args:
            project_id: 프로젝트 ID
            user_id: 사용자 ID

        Returns:
            조회된 프로젝트

        Raises:
            NotFoundError: 프로젝트를 찾을 수 없는 경우
        """
        project = self.repository.get_by_user_and_id(project_id, user_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    def get_project_by_id(self, project_id: int) -> Project:
        """
        프로젝트 ID로 조회 (관리자용)

        Args:
            project_id: 프로젝트 ID

        Returns:
            조회된 프로젝트

        Raises:
            NotFoundError: 프로젝트를 찾을 수 없는 경우
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    def get_user_projects(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        사용자의 프로젝트 목록 조회

        Args:
            user_id: 사용자 ID
            skip: 건너뛸 개수
            limit: 최대 조회 개수

        Returns:
            프로젝트 목록
        """
        return self.repository.get_by_user(user_id, skip=skip, limit=limit)

    def get_active_projects(self, user_id: Optional[int] = None) -> List[Project]:
        """
        활성 프로젝트 목록 조회

        Args:
            user_id: 사용자 ID (None이면 전체)

        Returns:
            활성 프로젝트 목록
        """
        return self.repository.get_active_projects(user_id)

    def update_project(
        self,
        project_id: int,
        user_id: int,
        project: ProjectUpdate
    ) -> Project:
        """
        프로젝트 업데이트

        Args:
            project_id: 프로젝트 ID
            user_id: 사용자 ID
            project: 업데이트할 정보

        Returns:
            업데이트된 프로젝트

        Raises:
            NotFoundError: 프로젝트를 찾을 수 없는 경우
        """
        db_project = self.repository.get_by_user_and_id(project_id, user_id)
        if not db_project:
            raise NotFoundError("Project", project_id)

        update_data = project.dict(exclude_unset=True)
        return self.repository.update(db_project, update_data)

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """
        프로젝트 삭제 (소프트 삭제)

        Args:
            project_id: 프로젝트 ID
            user_id: 사용자 ID

        Returns:
            삭제 성공 여부

        Raises:
            NotFoundError: 프로젝트를 찾을 수 없는 경우
        """
        project = self.repository.get_by_user_and_id(project_id, user_id)
        if not project:
            raise NotFoundError("Project", project_id)

        return self.repository.soft_delete(project_id)

    def toggle_project_status(self, project_id: int, user_id: int) -> Project:
        """
        프로젝트 활성화/비활성화 토글

        Args:
            project_id: 프로젝트 ID
            user_id: 사용자 ID

        Returns:
            업데이트된 프로젝트

        Raises:
            NotFoundError: 프로젝트를 찾을 수 없는 경우
        """
        project = self.repository.toggle_active_status(project_id, user_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    def get_projects_for_monitoring(self) -> List[Project]:
        """
        모니터링 대상 프로젝트 목록 조회

        Returns:
            모니터링 대상 프로젝트 목록
        """
        return self.repository.get_all_active_for_monitoring()

    def update_snapshot(self, project_id: int, snapshot_path: str) -> Project:
        """
        프로젝트 스냅샷 업데이트

        Args:
            project_id: 프로젝트 ID
            snapshot_path: 스냅샷 파일 경로

        Returns:
            업데이트된 프로젝트

        Raises:
            NotFoundError: 프로젝트를 찾을 수 없는 경우
        """
        project = self.repository.update_snapshot(project_id, snapshot_path)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    def count_user_projects(self, user_id: int) -> int:
        """
        사용자의 프로젝트 개수 조회

        Args:
            user_id: 사용자 ID

        Returns:
            프로젝트 개수
        """
        return self.repository.count_by_user(user_id)
