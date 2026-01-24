"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 스케줄러를 구현합니다.
# Laravel의 Task Scheduling과 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 프로젝트 모니터링 작업 스케줄링
# 2. 모니터링 작업 실행
# 3. 알림 생성
# 4. 로그 기록
"""

import asyncio
import logging
from typing import Dict

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringLog
from app.models.project import Project
from app.services.monitoring import MonitoringService

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """모니터링 스케줄러"""

    def __init__(self, db: Session):
        self.db = db
        self.tasks: Dict[int, asyncio.Task] = {}
        self.monitoring_service = MonitoringService(db)

    async def start(self):
        """스케줄러 시작"""
        logger.info("Starting monitoring scheduler...")
        # 활성화된 모든 프로젝트의 모니터링 시작
        projects = self.db.query(Project).filter(Project.is_active.is_(True)).all()
        for project in projects:
            await self.start_monitoring(project.id)
        logger.info("Monitoring scheduler started successfully")

    async def stop(self):
        """스케줄러 중지"""
        logger.info("Stopping monitoring scheduler...")
        # 모든 모니터링 작업 중지
        for project_id in list(self.tasks.keys()):
            await self.stop_monitoring(project_id)
        logger.info("Monitoring scheduler stopped successfully")

    async def start_monitoring(self, project_id: int):
        """프로젝트 모니터링 시작"""
        if project_id in self.tasks:
            await self.stop_monitoring(project_id)

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return

        logger.info(f"Starting monitoring for project {project_id}")
        self.tasks[project_id] = asyncio.create_task(
            self._monitor_project(project_id, project.status_interval or 300)
        )

    async def stop_monitoring(self, project_id: int):
        """프로젝트 모니터링 중지"""
        if project_id in self.tasks:
            logger.info(f"Stopping monitoring for project {project_id}")
            self.tasks[project_id].cancel()
            try:
                await self.tasks[project_id]
            except asyncio.CancelledError:
                pass
            del self.tasks[project_id]

    async def _monitor_project(self, project_id: int, interval: int):
        """프로젝트 모니터링 작업"""
        while True:
            try:
                # 모니터링 실행
                status = await self.monitoring_service.check_project_status(project_id)

                # 로그 기록
                log = MonitoringLog(
                    project_id=project_id,
                    is_available=status.is_available,
                    response_time=status.response_time,
                    status_code=status.status_code,
                    error_message=status.error_message,
                )
                self.db.add(log)

                # 알림 생성
                if not status.is_available:
                    alert = MonitoringAlert(
                        project_id=project_id,
                        alert_type="availability",
                        message=f"서비스가 응답하지 않습니다. (상태 코드: {status.status_code})",
                    )
                    self.db.add(alert)

                self.db.commit()

                # 다음 모니터링까지 대기
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info(f"Monitoring task for project {project_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error monitoring project {project_id}: {str(e)}")
                await asyncio.sleep(interval)  # 에러 발생 시에도 다음 모니터링까지 대기
