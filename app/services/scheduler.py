"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 작업을 스케줄링하는 서비스를 구현합니다.
# Laravel의 Task Scheduling과 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 모니터링 작업 스케줄링
# 2. 주기적인 상태 확인
# 3. 알림 발송
# 4. 로깅
# 5. 예외 처리
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Set
from sqlalchemy.orm import Session
import traceback

from app.models.project import Project
from app.services.monitoring import MonitoringService

# 로거 설정
logger = logging.getLogger(__name__)

class MonitoringScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.monitoring_service = MonitoringService(db)
        self._scheduled_tasks: Dict[int, asyncio.Task] = {}
        self._running = False
        logger.info("MonitoringScheduler initialized")

    async def start(self):
        """스케줄러 시작"""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            logger.info("Starting scheduler...")
            self._running = True
            # 모든 활성화된 프로젝트의 모니터링 시작
            projects = self.db.query(Project).filter(Project.is_active == True).all()
            logger.info(f"Found {len(projects)} active projects")
            for project in projects:
                await self.schedule_project(project.id)
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def stop(self):
        """스케줄러 중지"""
        if not self._running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            logger.info("Stopping scheduler...")
            self._running = False
            # 모든 모니터링 작업 중지
            for project_id, task in self._scheduled_tasks.items():
                logger.info(f"Cancelling task for project {project_id}")
                task.cancel()
            self._scheduled_tasks.clear()
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def schedule_project(self, project_id: int):
        """프로젝트 모니터링 스케줄링"""
        if project_id in self._scheduled_tasks:
            logger.warning(f"Project {project_id} is already scheduled")
            return
        
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                logger.error(f"Project {project_id} not found")
                return
            if not project.is_active:
                logger.warning(f"Project {project_id} is not active")
                return
            
            logger.info(f"Scheduling monitoring for project {project_id}")
            
            async def monitoring_task():
                while self._running:
                    try:
                        logger.debug(f"Checking status for project {project_id}")
                        # 프로젝트 상태 확인
                        status = await self.monitoring_service.check_project_status(project)
                        if not status["status"]:
                            logger.warning(f"Status error for project {project_id}: {status['error_message']}")
                            await self.monitoring_service.create_alert(
                                project_id=project_id,
                                alert_type="status_error",
                                message=f"프로젝트 상태 오류: {status['error_message']}"
                            )
                        
                        # SSL 상태 확인
                        ssl_status = await self.monitoring_service.check_ssl_status(project)
                        if not ssl_status["is_valid"]:
                            logger.warning(f"SSL error for project {project_id}: {ssl_status['error_message']}")
                            await self.monitoring_service.create_alert(
                                project_id=project_id,
                                alert_type="ssl_error",
                                message=f"SSL 인증서 만료: {ssl_status['error_message']}"
                            )
                        
                        # 도메인 만료일 확인
                        domain_expiry = await self.monitoring_service.check_domain_expiry(project)
                        if domain_expiry and (domain_expiry - datetime.now()).days <= 30:
                            logger.warning(f"Domain expiry warning for project {project_id}: {domain_expiry}")
                            await self.monitoring_service.create_alert(
                                project_id=project_id,
                                alert_type="domain_expiry",
                                message=f"도메인 만료 예정: {domain_expiry.strftime('%Y-%m-%d')}"
                            )
                        
                        # 다음 체크까지 대기
                        settings = await self.monitoring_service.get_monitoring_settings(project_id)
                        wait_time = settings.check_interval if settings else 300  # 기본 5분
                        logger.debug(f"Waiting {wait_time} seconds before next check for project {project_id}")
                        await asyncio.sleep(wait_time)
                    except asyncio.CancelledError:
                        logger.info(f"Monitoring task for project {project_id} cancelled")
                        break
                    except Exception as e:
                        logger.error(f"Error in monitoring task for project {project_id}: {str(e)}")
                        logger.error(traceback.format_exc())
                        await self.monitoring_service.create_alert(
                            project_id=project_id,
                            alert_type="monitoring_error",
                            message=f"모니터링 오류: {str(e)}"
                        )
                        await asyncio.sleep(60)  # 오류 발생 시 1분 대기
            
            self._scheduled_tasks[project_id] = asyncio.create_task(monitoring_task())
            logger.info(f"Monitoring task for project {project_id} scheduled successfully")
        except Exception as e:
            logger.error(f"Error scheduling project {project_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def unschedule_project(self, project_id: int):
        """프로젝트 모니터링 스케줄링 해제"""
        try:
            if project_id in self._scheduled_tasks:
                logger.info(f"Unscheduling project {project_id}")
                self._scheduled_tasks[project_id].cancel()
                del self._scheduled_tasks[project_id]
                logger.info(f"Project {project_id} unscheduled successfully")
            else:
                logger.warning(f"Project {project_id} is not scheduled")
        except Exception as e:
            logger.error(f"Error unscheduling project {project_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def reschedule_project(self, project_id: int):
        """프로젝트 모니터링 재스케줄링"""
        try:
            logger.info(f"Rescheduling project {project_id}")
            await self.unschedule_project(project_id)
            await self.schedule_project(project_id)
            logger.info(f"Project {project_id} rescheduled successfully")
        except Exception as e:
            logger.error(f"Error rescheduling project {project_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise 