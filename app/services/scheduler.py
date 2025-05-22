"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 작업을 스케줄링하는 서비스를 구현합니다.
# Laravel의 Task Scheduling과 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 모니터링 작업 스케줄링
# 2. 주기적인 상태 확인
# 3. 알림 발송
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.monitoring import MonitoringService

class MonitoringScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.monitoring_service = MonitoringService(db)
        self._scheduled_tasks: Dict[int, asyncio.Task] = {}
        self._running = False

    async def start(self):
        """스케줄러 시작"""
        if self._running:
            return
        
        self._running = True
        # 모든 활성화된 프로젝트의 모니터링 시작
        projects = self.db.query(Project).filter(Project.is_active == True).all()
        for project in projects:
            await self.schedule_project(project.id)

    async def stop(self):
        """스케줄러 중지"""
        if not self._running:
            return
        
        self._running = False
        # 모든 모니터링 작업 중지
        for task in self._scheduled_tasks.values():
            task.cancel()
        self._scheduled_tasks.clear()

    async def schedule_project(self, project_id: int):
        """프로젝트 모니터링 스케줄링"""
        if project_id in self._scheduled_tasks:
            return
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.is_active:
            return
        
        async def monitoring_task():
            while self._running:
                try:
                    # 프로젝트 상태 확인
                    status = await self.monitoring_service.check_project_status(project)
                    if not status["status"]:
                        await self.monitoring_service.create_alert(
                            project_id=project_id,
                            alert_type="status_error",
                            message=f"프로젝트 상태 오류: {status['error_message']}"
                        )
                    
                    # SSL 상태 확인
                    ssl_status = await self.monitoring_service.check_ssl_status(project)
                    if not ssl_status["is_valid"]:
                        await self.monitoring_service.create_alert(
                            project_id=project_id,
                            alert_type="ssl_error",
                            message=f"SSL 인증서 만료: {ssl_status['error_message']}"
                        )
                    
                    # 도메인 만료일 확인
                    domain_expiry = await self.monitoring_service.check_domain_expiry(project)
                    if domain_expiry and (domain_expiry - datetime.now()).days <= 30:
                        await self.monitoring_service.create_alert(
                            project_id=project_id,
                            alert_type="domain_expiry",
                            message=f"도메인 만료 예정: {domain_expiry.strftime('%Y-%m-%d')}"
                        )
                    
                    # 다음 체크까지 대기
                    settings = await self.monitoring_service.get_monitoring_settings(project_id)
                    await asyncio.sleep(settings.check_interval if settings else 300)  # 기본 5분
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    await self.monitoring_service.create_alert(
                        project_id=project_id,
                        alert_type="monitoring_error",
                        message=f"모니터링 오류: {str(e)}"
                    )
                    await asyncio.sleep(60)  # 오류 발생 시 1분 대기
        
        self._scheduled_tasks[project_id] = asyncio.create_task(monitoring_task())

    async def unschedule_project(self, project_id: int):
        """프로젝트 모니터링 스케줄링 해제"""
        if project_id in self._scheduled_tasks:
            self._scheduled_tasks[project_id].cancel()
            del self._scheduled_tasks[project_id]

    async def reschedule_project(self, project_id: int):
        """프로젝트 모니터링 재스케줄링"""
        await self.unschedule_project(project_id)
        await self.schedule_project(project_id) 