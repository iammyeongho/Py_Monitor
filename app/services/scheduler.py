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
import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringLog, MonitoringSetting
from app.models.project import Project
from app.services.cleanup_service import CleanupService
from app.services.monitoring import MonitoringService
from app.services.notification_service import NotificationService
from app.services.playwright_monitor import PlaywrightMonitorService

# WebSocket 알림 함수 (지연 임포트로 순환 참조 방지)
_ws_notify_update = None
_ws_notify_alert = None


def _get_ws_functions():
    """WebSocket 함수 지연 로드"""
    global _ws_notify_update, _ws_notify_alert
    if _ws_notify_update is None:
        try:
            from app.api.v1.endpoints.websocket import (
                notify_monitoring_update,
                notify_alert
            )
            _ws_notify_update = notify_monitoring_update
            _ws_notify_alert = notify_alert
        except ImportError:
            pass
    return _ws_notify_update, _ws_notify_alert


logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """HTTP + Playwright 통합 모니터링 스케줄러"""

    def __init__(self, db: Session):
        self.db = db
        self.tasks: Dict[int, asyncio.Task] = {}
        self.monitoring_service = MonitoringService(db)
        self.notification_service = NotificationService(db)
        self.playwright_service: Optional[PlaywrightMonitorService] = None
        self.consecutive_failures: Dict[int, int] = {}  # 프로젝트별 연속 실패 횟수
        self.last_slow_alert: Dict[int, datetime] = {}  # 프로젝트별 마지막 느린 응답 알림 시간
        self.last_ssl_check: Dict[int, datetime] = {}  # 프로젝트별 마지막 SSL 체크 시간
        self.ssl_check_task: Optional[asyncio.Task] = None  # SSL/도메인 만료 체크 태스크
        self.cleanup_task: Optional[asyncio.Task] = None  # 로그 정리 태스크
        self.cleanup_service = CleanupService(db)
        self.is_running = False
        self._lock = asyncio.Lock()

    async def _get_playwright_service(self) -> PlaywrightMonitorService:
        """Playwright 서비스 인스턴스 반환 (지연 초기화)"""
        if self.playwright_service is None:
            self.playwright_service = PlaywrightMonitorService(self.db)
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

            # SSL/도메인 만료 체크 태스크 시작 (매일 1회)
            self.ssl_check_task = asyncio.create_task(self._ssl_expiry_check_loop())

            # 로그 자동 정리 태스크 시작 (매일 1회, 새벽 3시)
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

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

            # SSL 체크 태스크 중지
            if self.ssl_check_task:
                self.ssl_check_task.cancel()
                self.ssl_check_task = None

            # 로그 정리 태스크 중지
            if self.cleanup_task:
                self.cleanup_task.cancel()
                self.cleanup_task = None

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

                # 6. 성능 임계값 체크 (응답 시간 초과 알림)
                if is_available and http_status.response_time:
                    await self._handle_performance_alert(
                        project=project,
                        response_time=http_status.response_time
                    )

                # 7. 콘텐츠 변경 감지 및 키워드 모니터링
                if is_available and setting and http_status.content:
                    await self._handle_content_monitoring(
                        project=project,
                        setting=setting,
                        content=http_status.content
                    )

                self.db.commit()

                # 7. WebSocket으로 실시간 업데이트 전송
                await self._send_websocket_update(project, log)

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

                if error_details:
                    alert_message = f"서비스 연속 {failures}회 실패. " + "; ".join(error_details)
                else:
                    alert_message = f"서비스 연속 {failures}회 실패"

                alert = MonitoringAlert(
                    project_id=project_id,
                    alert_type="availability",
                    message=alert_message,
                )
                self.db.add(alert)
                logger.error(f"Alert created for project {project_id}: {failures} consecutive failures")

                # 이메일/웹훅 알림 발송
                try:
                    await self.notification_service.send_alert_notification(
                        project_id=project_id,
                        alert_type="availability",
                        message=alert_message,
                        details={
                            "연속 실패 횟수": failures,
                            "HTTP 상태 코드": http_status.status_code,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")

        else:
            # 복구 시 알림 생성 (이전에 실패한 경우에만)
            if self.consecutive_failures.get(project_id, 0) >= alert_threshold:
                recovery_message = f"서비스가 복구되었습니다. (응답 시간: {http_status.response_time:.2f}s)"

                alert = MonitoringAlert(
                    project_id=project_id,
                    alert_type="recovery",
                    message=recovery_message,
                )
                self.db.add(alert)
                logger.info(f"Recovery alert created for project {project_id}")

                # 복구 알림 발송
                try:
                    await self.notification_service.send_alert_notification(
                        project_id=project_id,
                        alert_type="recovery",
                        message=recovery_message,
                        details={
                            "응답 시간": f"{http_status.response_time:.2f}s",
                            "HTTP 상태 코드": http_status.status_code,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send recovery notification: {e}")

            self.consecutive_failures[project_id] = 0

    async def _handle_performance_alert(
        self,
        project: Project,
        response_time: float
    ):
        """성능 임계값 초과 시 알림 처리"""
        project_id = project.id
        time_limit = project.time_limit or 5  # 기본 5초
        time_limit_interval = project.time_limit_interval or 15  # 기본 15분

        # 응답 시간이 임계값을 초과하지 않으면 무시
        if response_time <= time_limit:
            return

        # 마지막 알림으로부터 충분한 시간이 지났는지 확인
        last_alert_time = self.last_slow_alert.get(project_id)
        if last_alert_time:
            elapsed_minutes = (datetime.now() - last_alert_time).total_seconds() / 60
            if elapsed_minutes < time_limit_interval:
                logger.debug(
                    f"Skipping slow response alert for project {project_id}: "
                    f"last alert was {elapsed_minutes:.1f} minutes ago"
                )
                return

        # 성능 임계값 초과 알림 생성
        alert_message = (
            f"응답 시간이 임계값을 초과했습니다. "
            f"(현재: {response_time:.2f}초, 임계값: {time_limit}초)"
        )

        alert = MonitoringAlert(
            project_id=project_id,
            alert_type="slow_response",
            message=alert_message,
        )
        self.db.add(alert)
        self.last_slow_alert[project_id] = datetime.now()

        logger.warning(f"Slow response alert for project {project_id}: {response_time:.2f}s > {time_limit}s")

        # 알림 발송
        try:
            await self.notification_service.send_alert_notification(
                project_id=project_id,
                alert_type="slow_response",
                message=alert_message,
                details={
                    "응답 시간": f"{response_time:.2f}초",
                    "임계값": f"{time_limit}초",
                    "초과량": f"{response_time - time_limit:.2f}초",
                }
            )
        except Exception as e:
            logger.error(f"Failed to send slow response notification: {e}")

    async def _handle_content_monitoring(
        self,
        project: Project,
        setting: MonitoringSetting,
        content: str
    ):
        """콘텐츠 변경 감지 및 키워드 모니터링 처리"""
        # 1. 콘텐츠 변경 감지
        if setting.content_change_detection:
            await self._check_content_change(project, setting, content)

        # 2. 키워드 모니터링
        if setting.keyword_monitoring and setting.keywords:
            await self._check_keywords(project, setting, content)

    async def _check_content_change(
        self,
        project: Project,
        setting: MonitoringSetting,
        content: str
    ):
        """콘텐츠 변경 감지"""
        project_id = project.id

        # 특정 CSS 셀렉터가 지정된 경우 해당 부분만 추출 (간단한 구현)
        # 실제로는 BeautifulSoup 등을 사용해야 하지만 여기서는 전체 콘텐츠 사용
        target_content = content
        if setting.content_selector:
            # 간단한 정규식으로 특정 태그 내용 추출 시도
            pattern = rf'<{setting.content_selector}[^>]*>(.*?)</{setting.content_selector}>'
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                target_content = ' '.join(matches)

        # 콘텐츠 해시 계산 (공백 정규화)
        normalized_content = ' '.join(target_content.split())
        current_hash = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()

        # 이전 해시와 비교
        previous_hash = setting.content_hash

        if previous_hash and previous_hash != current_hash:
            # 콘텐츠 변경 감지됨
            alert_message = "웹사이트 콘텐츠가 변경되었습니다."
            if setting.content_selector:
                alert_message += f" (감시 영역: {setting.content_selector})"

            alert = MonitoringAlert(
                project_id=project_id,
                alert_type="content_change",
                message=alert_message,
            )
            self.db.add(alert)

            logger.info(f"Content change detected for project {project_id}")

            # 알림 발송
            try:
                await self.notification_service.send_alert_notification(
                    project_id=project_id,
                    alert_type="content_change",
                    message=alert_message,
                    details={
                        "이전 해시": previous_hash[:16] + "...",
                        "현재 해시": current_hash[:16] + "...",
                        "감시 영역": setting.content_selector or "전체 페이지",
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send content change notification: {e}")

        # 해시 업데이트
        setting.content_hash = current_hash
        setting.last_content_check_at = datetime.utcnow()

    async def _check_keywords(
        self,
        project: Project,
        setting: MonitoringSetting,
        content: str
    ):
        """키워드 모니터링"""
        project_id = project.id

        try:
            keywords: List[str] = json.loads(setting.keywords)
        except (json.JSONDecodeError, TypeError):
            # 쉼표 구분 문자열로 처리
            keywords = [k.strip() for k in (setting.keywords or "").split(",") if k.strip()]

        if not keywords:
            return

        # 키워드 검색
        content_lower = content.lower()
        found_keywords = [kw for kw in keywords if kw.lower() in content_lower]
        missing_keywords = [kw for kw in keywords if kw.lower() not in content_lower]

        # 알림 조건 확인
        should_alert = False
        alert_message = ""

        if setting.keyword_alert_on_found and found_keywords:
            # 키워드가 발견되면 알림
            should_alert = True
            alert_message = f"모니터링 키워드가 발견되었습니다: {', '.join(found_keywords)}"
        elif not setting.keyword_alert_on_found and missing_keywords:
            # 키워드가 없으면 알림
            should_alert = True
            alert_message = f"필수 키워드가 누락되었습니다: {', '.join(missing_keywords)}"

        if should_alert:
            alert = MonitoringAlert(
                project_id=project_id,
                alert_type="keyword_alert",
                message=alert_message,
            )
            self.db.add(alert)

            logger.info(f"Keyword alert for project {project_id}: {alert_message}")

            # 알림 발송
            try:
                await self.notification_service.send_alert_notification(
                    project_id=project_id,
                    alert_type="keyword_alert",
                    message=alert_message,
                    details={
                        "발견된 키워드": ', '.join(found_keywords) if found_keywords else "없음",
                        "누락된 키워드": ', '.join(missing_keywords) if missing_keywords else "없음",
                        "전체 키워드": ', '.join(keywords),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send keyword alert notification: {e}")

    async def _send_websocket_update(self, project: Project, log: MonitoringLog):
        """WebSocket으로 모니터링 업데이트 전송"""
        try:
            notify_update, _ = _get_ws_functions()
            if notify_update:
                await notify_update(
                    user_id=project.user_id,
                    project_id=project.id,
                    log=log
                )
        except Exception as e:
            logger.debug(f"WebSocket update failed (non-critical): {e}")

    async def _ssl_expiry_check_loop(self):
        """SSL/도메인 만료 체크 루프 (24시간마다 실행)"""
        CHECK_INTERVAL = 24 * 60 * 60  # 24시간
        WARNING_DAYS = [30, 14, 7, 3, 1]  # 알림을 보낼 D-day

        while self.is_running:
            try:
                logger.info("Starting SSL/Domain expiry check...")
                projects = self.db.query(Project).filter(
                    Project.is_active.is_(True),
                    Project.deleted_at.is_(None)
                ).all()

                for project in projects:
                    if not project.url or not project.is_https:
                        continue

                    await self._check_ssl_expiry(project, WARNING_DAYS)
                    await self._check_domain_expiry(project, WARNING_DAYS)

                logger.info(f"SSL/Domain expiry check completed for {len(projects)} projects")
                await asyncio.sleep(CHECK_INTERVAL)

            except asyncio.CancelledError:
                logger.info("SSL expiry check task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in SSL expiry check loop: {e}")
                await asyncio.sleep(3600)  # 오류 시 1시간 후 재시도

    async def _check_ssl_expiry(self, project: Project, warning_days: list):
        """SSL 인증서 만료 체크 및 알림"""
        try:
            ssl_result = await self.monitoring_service.check_ssl_status(project)

            if not ssl_result.get("is_valid") or not ssl_result.get("expiry_date"):
                return

            expiry_date = ssl_result["expiry_date"]
            days_remaining = (expiry_date - datetime.now()).days

            # 이미 만료된 경우
            if days_remaining < 0:
                await self._send_expiry_alert(
                    project=project,
                    alert_type="ssl_expired",
                    message=f"SSL 인증서가 만료되었습니다! (만료일: {expiry_date.strftime('%Y-%m-%d')})",
                    days_remaining=days_remaining
                )
                return

            # 경고 일수에 해당하는 경우 알림
            if days_remaining in warning_days:
                await self._send_expiry_alert(
                    project=project,
                    alert_type="ssl_expiring",
                    message=f"SSL 인증서가 {days_remaining}일 후 만료됩니다. (만료일: {expiry_date.strftime('%Y-%m-%d')})",
                    days_remaining=days_remaining
                )

        except Exception as e:
            logger.error(f"Error checking SSL expiry for project {project.id}: {e}")

    async def _check_domain_expiry(self, project: Project, warning_days: list):
        """도메인 만료 체크 및 알림"""
        try:
            expiry_result = await self.monitoring_service.check_domain_expiry(project)

            if not expiry_result:
                return

            # whois 결과가 리스트인 경우 첫 번째 값 사용
            expiry_date = expiry_result[0] if isinstance(expiry_result, list) else expiry_result
            if not expiry_date:
                return

            days_remaining = (expiry_date - datetime.now()).days

            # 이미 만료된 경우
            if days_remaining < 0:
                await self._send_expiry_alert(
                    project=project,
                    alert_type="domain_expired",
                    message=f"도메인이 만료되었습니다! (만료일: {expiry_date.strftime('%Y-%m-%d')})",
                    days_remaining=days_remaining
                )
                return

            # 경고 일수에 해당하는 경우 알림
            if days_remaining in warning_days:
                await self._send_expiry_alert(
                    project=project,
                    alert_type="domain_expiring",
                    message=f"도메인이 {days_remaining}일 후 만료됩니다. (만료일: {expiry_date.strftime('%Y-%m-%d')})",
                    days_remaining=days_remaining
                )

        except Exception as e:
            logger.error(f"Error checking domain expiry for project {project.id}: {e}")

    async def _send_expiry_alert(
        self,
        project: Project,
        alert_type: str,
        message: str,
        days_remaining: int
    ):
        """SSL/도메인 만료 알림 발송"""
        project_id = project.id

        # 알림 생성
        alert = MonitoringAlert(
            project_id=project_id,
            alert_type=alert_type,
            message=message,
        )
        self.db.add(alert)
        self.db.commit()

        logger.warning(f"{alert_type} alert for project {project_id}: {message}")

        # 알림 발송
        try:
            severity = "critical" if days_remaining <= 7 else "warning"
            await self.notification_service.send_alert_notification(
                project_id=project_id,
                alert_type=alert_type,
                message=message,
                details={
                    "프로젝트": project.title,
                    "URL": project.url,
                    "남은 일수": f"{days_remaining}일",
                    "심각도": severity,
                }
            )
        except Exception as e:
            logger.error(f"Failed to send {alert_type} notification: {e}")

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

    async def _cleanup_loop(self):
        """로그 자동 정리 루프 (매일 새벽 3시 실행)

        보관 기간:
        - 모니터링 로그: 30일
        - 알림 기록: 90일
        - 이메일 로그: 30일
        """
        while self.is_running:
            try:
                # 다음 새벽 3시까지 대기 시간 계산
                now = datetime.now()
                next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                if now >= next_run:
                    # 이미 3시가 지났으면 내일 3시로
                    from datetime import timedelta
                    next_run = next_run + timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Next cleanup scheduled at {next_run} (in {wait_seconds/3600:.1f} hours)")
                await asyncio.sleep(wait_seconds)

                # 정리 실행
                logger.info("Starting scheduled log cleanup...")
                result = self.cleanup_service.cleanup_all()
                logger.info(
                    f"Cleanup completed: "
                    f"logs={result['monitoring_logs_deleted']}, "
                    f"alerts={result['alerts_deleted']}, "
                    f"emails={result['email_logs_deleted']}"
                )

            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # 오류 시 1시간 후 재시도
                await asyncio.sleep(3600)

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
