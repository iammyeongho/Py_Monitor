"""
# 모니터링 스케줄러
# HTTP 체크와 Playwright 심층 모니터링을 통합하여 실행합니다.
#
# 주요 기능:
# 1. 프로젝트 모니터링 작업 스케줄링
# 2. HTTP + Playwright 통합 모니터링
# 3. 연속 실패 추적 및 알림 생성
# 4. 복구 알림
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringLog, MonitoringSetting
from app.models.project import Project
from app.services.monitoring import MonitoringService
from app.services.playwright_monitor import PlaywrightMonitorService

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """HTTP + Playwright 통합 모니터링 스케줄러"""

    def __init__(self, db: Session):
        self.db = db
        self.tasks: Dict[int, asyncio.Task] = {}
        self.monitoring_service = MonitoringService(db)
        self.playwright_service: Optional[PlaywrightMonitorService] = None
        self.consecutive_failures: Dict[int, int] = {}  # 프로젝트별 연속 실패 횟수
        self.is_running = False
        self._lock = asyncio.Lock()

    async def _get_playwright_service(self) -> PlaywrightMonitorService:
        """Playwright 서비스 인스턴스 반환 (지연 초기화)"""
        if self.playwright_service is None:
            self.playwright_service = PlaywrightMonitorService()
        return self.playwright_service

    async def start(self):
        """스케줄러 시작"""
        async with self._lock:
            if self.is_running:
                logger.warning("Scheduler is already running")
                return

            logger.info("Starting monitoring scheduler...")
            self.is_running = True

            # 활성화된 모든 프로젝트의 모니터링 시작
            projects = self.db.query(Project).filter(Project.is_active.is_(True)).all()
            for project in projects:
                await self.start_monitoring(project.id)

            logger.info(f"Monitoring scheduler started with {len(projects)} projects")

    async def stop(self):
        """스케줄러 중지"""
        async with self._lock:
            if not self.is_running:
                logger.warning("Scheduler is not running")
                return

            logger.info("Stopping monitoring scheduler...")

            # 모든 모니터링 작업 중지
            for project_id in list(self.tasks.keys()):
                await self.stop_monitoring(project_id)

            # Playwright 서비스 정리
            if self.playwright_service:
                await self.playwright_service.close()
                self.playwright_service = None

            self.is_running = False
            logger.info("Monitoring scheduler stopped successfully")

    async def start_monitoring(self, project_id: int):
        """프로젝트 모니터링 시작"""
        if project_id in self.tasks:
            await self.stop_monitoring(project_id)

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return

        # 모니터링 설정 조회
        setting = self.db.query(MonitoringSetting).filter(
            MonitoringSetting.project_id == project_id
        ).first()

        interval = setting.check_interval if setting else (project.status_interval or 300)

        logger.info(f"Starting monitoring for project {project_id} (interval: {interval}s)")
        self.consecutive_failures[project_id] = 0
        self.tasks[project_id] = asyncio.create_task(
            self._monitor_project(project_id, interval)
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
            self.consecutive_failures.pop(project_id, None)

    async def _monitor_project(self, project_id: int, interval: int):
        """프로젝트 모니터링 작업 (HTTP + Playwright 통합)"""
        while True:
            try:
                project = self.db.query(Project).filter(Project.id == project_id).first()
                if not project or not project.is_active:
                    logger.info(f"Project {project_id} is inactive, stopping monitoring")
                    break

                # 모니터링 설정 조회
                setting = self.db.query(MonitoringSetting).filter(
                    MonitoringSetting.project_id == project_id
                ).first()
                alert_threshold = setting.alert_threshold if setting else 3

                # 1. HTTP 기본 체크 실행
                http_status = await self.monitoring_service.check_project_status(project_id)

                # 2. Playwright 심층 체크 실행 (URL이 있는 경우)
                playwright_result = None
                if project.url:
                    try:
                        pw_service = await self._get_playwright_service()
                        playwright_result = await pw_service.deep_check(
                            project_id=project_id,
                            url=project.url
                        )
                    except Exception as e:
                        logger.warning(f"Playwright check failed for project {project_id}: {e}")

                # 3. 결과 통합 및 로그 생성
                log = self._create_monitoring_log(
                    project_id=project_id,
                    http_status=http_status,
                    playwright_result=playwright_result
                )
                self.db.add(log)

                # 4. 가용성 판단 (HTTP와 Playwright 모두 고려)
                is_available = http_status.is_available
                if playwright_result:
                    is_available = is_available and playwright_result.is_available

                # 5. 연속 실패 추적 및 알림
                await self._handle_failure_tracking(
                    project_id=project_id,
                    is_available=is_available,
                    http_status=http_status,
                    playwright_result=playwright_result,
                    alert_threshold=alert_threshold
                )

                self.db.commit()

                # 다음 모니터링까지 대기
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info(f"Monitoring task for project {project_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error monitoring project {project_id}: {str(e)}")
                self.db.rollback()
                await asyncio.sleep(interval)

    def _create_monitoring_log(self, project_id: int, http_status, playwright_result) -> MonitoringLog:
        """모니터링 로그 생성"""
        log = MonitoringLog(
            project_id=project_id,
            check_type="playwright" if playwright_result else "http",
            is_available=http_status.is_available,
            response_time=http_status.response_time,
            status_code=http_status.status_code,
            error_message=http_status.error_message,
        )

        # Playwright 결과가 있으면 심층 메트릭 추가
        if playwright_result:
            # 성능 메트릭
            if playwright_result.performance:
                log.dom_content_loaded = playwright_result.performance.dom_content_loaded
                log.page_load_time = playwright_result.performance.page_load_time
                log.first_contentful_paint = playwright_result.performance.first_contentful_paint
                log.largest_contentful_paint = playwright_result.performance.largest_contentful_paint
                log.time_to_first_byte = playwright_result.performance.time_to_first_byte
                log.cumulative_layout_shift = playwright_result.performance.cumulative_layout_shift
                log.total_blocking_time = playwright_result.performance.total_blocking_time

            # 건강 상태
            if playwright_result.health:
                log.is_dom_ready = playwright_result.health.is_dom_ready
                log.is_js_healthy = playwright_result.health.is_js_healthy
                log.console_errors = playwright_result.health.console_errors
                if playwright_result.health.js_errors:
                    log.js_errors = json.dumps(playwright_result.health.js_errors)

            # 리소스 정보
            if playwright_result.resources:
                log.resource_count = playwright_result.resources.count
                log.resource_size = playwright_result.resources.size
                log.failed_resources = playwright_result.resources.failed

            # 네트워크 정보
            if playwright_result.network:
                log.redirect_count = playwright_result.network.redirect_count

            # 메모리 정보
            if playwright_result.memory:
                log.js_heap_size = playwright_result.memory.js_heap_size

            # Playwright 응답 시간 우선 사용
            if playwright_result.response_time:
                log.response_time = playwright_result.response_time

        return log

    async def _handle_failure_tracking(
        self,
        project_id: int,
        is_available: bool,
        http_status,
        playwright_result,
        alert_threshold: int
    ):
        """연속 실패 추적 및 알림 처리"""
        if not is_available:
            self.consecutive_failures[project_id] = self.consecutive_failures.get(project_id, 0) + 1
            failures = self.consecutive_failures[project_id]

            logger.warning(
                f"Project {project_id} check failed ({failures}/{alert_threshold})"
            )

            # 임계값 도달 시 알림 생성
            if failures == alert_threshold:
                error_details = []
                if http_status.error_message:
                    error_details.append(f"HTTP: {http_status.error_message}")
                if playwright_result and playwright_result.error_message:
                    error_details.append(f"Playwright: {playwright_result.error_message}")

                alert = MonitoringAlert(
                    project_id=project_id,
                    alert_type="availability",
                    message=f"서비스 연속 {failures}회 실패. " + "; ".join(error_details) if error_details else f"서비스 연속 {failures}회 실패",
                )
                self.db.add(alert)
                logger.error(f"Alert created for project {project_id}: {failures} consecutive failures")

        else:
            # 복구 시 알림 생성 (이전에 실패한 경우에만)
            if self.consecutive_failures.get(project_id, 0) >= alert_threshold:
                alert = MonitoringAlert(
                    project_id=project_id,
                    alert_type="recovery",
                    message=f"서비스가 복구되었습니다. (응답 시간: {http_status.response_time:.2f}s)",
                )
                self.db.add(alert)
                logger.info(f"Recovery alert created for project {project_id}")

            self.consecutive_failures[project_id] = 0

    async def check_now(self, project_id: int) -> Optional[MonitoringLog]:
        """즉시 모니터링 체크 실행 (수동 트리거)"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return None

        try:
            # HTTP 체크
            http_status = await self.monitoring_service.check_project_status(project_id)

            # Playwright 심층 체크
            playwright_result = None
            if project.url:
                try:
                    pw_service = await self._get_playwright_service()
                    playwright_result = await pw_service.deep_check(
                        project_id=project_id,
                        url=project.url
                    )
                except Exception as e:
                    logger.warning(f"Playwright check failed: {e}")

            # 로그 생성 및 저장
            log = self._create_monitoring_log(
                project_id=project_id,
                http_status=http_status,
                playwright_result=playwright_result
            )
            self.db.add(log)
            self.db.commit()

            return log

        except Exception as e:
            logger.error(f"Manual check failed for project {project_id}: {e}")
            self.db.rollback()
            return None

    def get_status(self) -> dict:
        """스케줄러 상태 반환"""
        return {
            "is_running": self.is_running,
            "active_projects": list(self.tasks.keys()),
            "project_count": len(self.tasks),
            "consecutive_failures": dict(self.consecutive_failures),
        }

    def get_project_status(self, project_id: int) -> dict:
        """특정 프로젝트의 모니터링 상태 반환"""
        return {
            "project_id": project_id,
            "is_monitoring": project_id in self.tasks,
            "consecutive_failures": self.consecutive_failures.get(project_id, 0),
        }
