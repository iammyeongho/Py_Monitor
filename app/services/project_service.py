"""
# Laravel 개발자를 위한 설명
# 이 파일은 프로젝트 관련 비즈니스 로직을 구현합니다.
# Laravel의 ProjectService와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 프로젝트 CRUD
# 2. 프로젝트 상태 관리
# 3. 프로젝트 설정 관리
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringSetting
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, user_id: int, project: ProjectCreate) -> Project:
        """프로젝트 생성"""
        db_project = Project(
            user_id=user_id,
            title=project.title,
            url=project.url,
            host_name=project.host_name,
            ip_address=project.ip_address,
            is_active=True,
        )
        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)

        # 기본 모니터링 설정 생성
        monitoring_setting = MonitoringSetting(
            project_id=db_project.id,
            check_interval=300,  # 5분
            timeout=30,
            retry_count=3,
            alert_threshold=3,
        )
        self.db.add(monitoring_setting)
        self.db.commit()

        return db_project

    def get_project(self, project_id: int, user_id: int) -> Optional[Project]:
        """프로젝트 조회"""
        return (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.user_id == user_id)
            .first()
        )

    def get_user_projects(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """사용자의 프로젝트 목록 조회"""
        return (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_project(
        self, project_id: int, user_id: int, project: ProjectUpdate
    ) -> Optional[Project]:
        """프로젝트 업데이트"""
        db_project = self.get_project(project_id, user_id)
        if not db_project:
            return None

        for key, value in project.dict(exclude_unset=True).items():
            setattr(db_project, key, value)

        db_project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """프로젝트 삭제"""
        db_project = self.get_project(project_id, user_id)
        if not db_project:
            return False

        db_project.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def toggle_project_status(self, project_id: int, user_id: int) -> Optional[Project]:
        """프로젝트 활성화/비활성화"""
        db_project = self.get_project(project_id, user_id)
        if not db_project:
            return None

        db_project.is_active = not db_project.is_active
        db_project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_project)
        return db_project
