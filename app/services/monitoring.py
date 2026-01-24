"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 MonitoringService와 유사한 역할을 합니다.
# FastAPI를 사용하여 모니터링 서비스를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. async/await = Laravel의 비동기 처리와 유사
# 2. aiohttp = Laravel의 HTTP 클라이언트와 유사
# 3. ssl = Laravel의 SSL 검증과 유사
"""

from sqlalchemy.orm import Session
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting
from app.schemas.monitoring import (
    MonitoringLogCreate,
    MonitoringAlertCreate,
    MonitoringSettingCreate,
    MonitoringSettingUpdate,
    SSLDomainStatusCreate,
    MonitoringStatus,
    SSLStatus,
    MonitoringResponse,
)
from datetime import datetime
from typing import List, Optional, Dict
import asyncio
import aiohttp
import ssl
import socket
import whois
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.utils.notifications import NotificationService
from sqlalchemy import and_
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def create_monitoring_log(db: Session, log: MonitoringLogCreate) -> MonitoringLog:
    """모니터링 로그 생성"""
    db_log = MonitoringLog(
        project_id=log.project_id,
        status_code=log.status_code,
        response_time=log.response_time,
        is_available=log.is_available,
        error_message=log.error_message,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_monitoring_logs(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> List[MonitoringLog]:
    """프로젝트의 모니터링 로그 조회"""
    return (
        db.query(MonitoringLog)
        .filter(MonitoringLog.project_id == project_id)
        .order_by(MonitoringLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_monitoring_alert(
    db: Session, alert: MonitoringAlertCreate
) -> MonitoringAlert:
    """모니터링 알림 생성"""
    db_alert = MonitoringAlert(
        project_id=alert.project_id,
        alert_type=alert.alert_type,
        message=alert.message,
        is_resolved=False,
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_monitoring_alerts(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> List[MonitoringAlert]:
    """프로젝트의 모니터링 알림 조회"""
    return (
        db.query(MonitoringAlert)
        .filter(MonitoringAlert.project_id == project_id)
        .order_by(MonitoringAlert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_monitoring_alert(
    db: Session, alert_id: int, alert: MonitoringAlertCreate
) -> Optional[MonitoringAlert]:
    """모니터링 알림 업데이트"""
    db_alert = db.query(MonitoringAlert).filter(MonitoringAlert.id == alert_id).first()
    if not db_alert:
        return None

    for key, value in alert.dict().items():
        setattr(db_alert, key, value)

    db_alert.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_alert)
    return db_alert


def create_monitoring_setting(
    db: Session, setting: MonitoringSettingCreate
) -> MonitoringSetting:
    """모니터링 설정 생성"""
    db_setting = MonitoringSetting(
        project_id=setting.project_id,
        check_interval=setting.check_interval,
        timeout=setting.timeout,
        retry_count=setting.retry_count,
        alert_threshold=setting.alert_threshold,
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


def get_monitoring_setting(db: Session, project_id: int) -> Optional[MonitoringSetting]:
    """프로젝트의 모니터링 설정 조회"""
    return (
        db.query(MonitoringSetting)
        .filter(MonitoringSetting.project_id == project_id)
        .first()
    )


def update_monitoring_setting(
    db: Session, setting_id: int, setting: MonitoringSettingCreate
) -> Optional[MonitoringSetting]:
    """모니터링 설정 업데이트"""
    db_setting = (
        db.query(MonitoringSetting).filter(MonitoringSetting.id == setting_id).first()
    )
    if not db_setting:
        return None

    for key, value in setting.dict().items():
        setattr(db_setting, key, value)

    db_setting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_setting)
    return db_setting


class MonitoringService:
    """모니터링 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self._monitoring_tasks: Dict[int, asyncio.Task] = {}
        self.notification_service = NotificationService()

    async def check_project_status(self, project_id: int) -> MonitoringStatus:
        """프로젝트 상태 확인"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                async with session.get(project.url, timeout=30) as response:
                    response_time = (datetime.now() - start_time).total_seconds()

                    return MonitoringStatus(
                        is_available=True,
                        response_time=response_time,
                        status_code=response.status,
                        error_message=None,
                    )
        except Exception as e:
            logger.error(f"Error checking project {project_id}: {str(e)}")
            return MonitoringStatus(
                is_available=False,
                response_time=None,
                status_code=None,
                error_message=str(e),
            )

    async def check_ssl_status(self, project: Project) -> dict:
        """SSL 인증서 상태 확인"""
        try:
            hostname = project.url.split("//")[-1].split("/")[0]
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    expiry_date = datetime.strptime(
                        cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                    )

                    return {
                        "is_valid": True,
                        "expiry_date": expiry_date,
                        "error_message": None,
                    }
        except Exception as e:
            logger.error(f"Error checking SSL for project {project.id}: {str(e)}")
            return {"is_valid": False, "expiry_date": None, "error_message": str(e)}

    async def check_domain_expiry(self, project: Project) -> Optional[datetime]:
        """도메인 만료일 확인"""
        try:
            domain = project.url.split("//")[-1].split("/")[0]
            w = whois.whois(domain)
            return w.expiration_date
        except Exception as e:
            logger.error(
                f"Error checking domain expiry for project {project.id}: {str(e)}"
            )
            return None

    async def create_alert(
        self, project_id: int, alert_type: str, message: str
    ) -> MonitoringAlert:
        """알림 생성"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 알림 생성
        alert = MonitoringAlert(
            project_id=project_id, alert_type=alert_type, message=message
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        # 알림 데이터 준비
        alert_data = {
            "project_name": project.title,
            "project_url": project.url,
            "error_message": message,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 이메일 알림 전송
        if project.user.email:
            template = self.notification_service.get_alert_template(alert_type)
            await self.notification_service.send_email_notification(
                email=project.user.email,
                subject=f"[모니터링 알림] {project.title}",
                template=template,
                data=alert_data,
            )

        # 웹훅 알림 전송
        if project.webhook_url:
            await self.notification_service.send_webhook_notification(
                webhook_url=project.webhook_url,
                data={
                    "type": alert_type,
                    "project": project.title,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        return alert

    async def create_log(self, log_data: MonitoringLogCreate) -> MonitoringLog:
        """모니터링 로그 생성"""
        log = MonitoringLog(**log_data.dict())
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    async def create_monitoring_alert(
        self, alert_data: MonitoringAlertCreate
    ) -> MonitoringAlert:
        """모니터링 알림 생성"""
        alert = MonitoringAlert(**alert_data.dict())
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        # 이메일 알림 전송
        project = self.db.query(Project).filter(Project.id == alert.project_id).first()
        if project and project.user.email:
            await self.notification_service.send_email_notification(
                email=project.user.email,
                subject=f"모니터링 알림: {project.title}",
                template=self.notification_service.get_alert_template(alert.alert_type),
                data={
                    "project_name": project.title,
                    "project_url": project.url,
                    "error_message": alert.message,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

        return alert

    async def update_ssl_status(
        self, ssl_data: SSLDomainStatusCreate
    ) -> SSLDomainStatus:
        """SSL 도메인 상태 업데이트"""
        existing = (
            self.db.query(SSLDomainStatus)
            .filter(
                and_(
                    SSLDomainStatus.project_id == ssl_data.project_id,
                    SSLDomainStatus.domain == ssl_data.domain,
                )
            )
            .first()
        )

        if existing:
            for key, value in ssl_data.dict().items():
                if value is not None:
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            ssl_status = SSLDomainStatus(**ssl_data.dict())
            self.db.add(ssl_status)
            self.db.commit()
            self.db.refresh(ssl_status)
            return ssl_status

    async def get_monitoring_settings(
        self, project_id: int
    ) -> Optional[MonitoringSetting]:
        """모니터링 설정 조회"""
        return (
            self.db.query(MonitoringSetting)
            .filter(MonitoringSetting.project_id == project_id)
            .first()
        )

    async def update_monitoring_settings(
        self, project_id: int, settings: MonitoringSettingUpdate
    ) -> MonitoringSetting:
        """모니터링 설정 업데이트"""
        existing = await self.get_monitoring_settings(project_id)
        if existing:
            for key, value in settings.dict(exclude_unset=True).items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            new_settings = MonitoringSetting(
                project_id=project_id, **settings.dict(exclude_unset=True)
            )
            self.db.add(new_settings)
            self.db.commit()
            self.db.refresh(new_settings)
            return new_settings

    async def start_monitoring(self, project_id: int) -> None:
        """프로젝트 모니터링 시작"""
        if project_id in self._monitoring_tasks:
            return

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        settings = await self.get_monitoring_settings(project_id)
        if not settings:
            settings = await self.update_monitoring_settings(
                project_id, MonitoringSettingCreate(project_id=project_id)
            )

        async def monitor_task():
            while True:
                try:
                    # 상태 확인
                    status = await self.check_project_status(project_id)
                    if not status.is_available:
                        await self.create_alert(
                            project_id, "status_error", status.error_message
                        )

                    # SSL 상태 확인
                    ssl_status = await self.check_ssl_status(project)
                    if not ssl_status["is_valid"]:
                        await self.create_alert(
                            project_id, "ssl_error", ssl_status["error_message"]
                        )

                    # 도메인 만료일 확인
                    domain_expiry = await self.check_domain_expiry(project)
                    if domain_expiry and (domain_expiry - datetime.now()).days <= 30:
                        await self.create_alert(
                            project_id,
                            "domain_expiry",
                            f"도메인 만료 예정: {domain_expiry.strftime('%Y-%m-%d')}",
                        )

                    await asyncio.sleep(settings.check_interval)
                except Exception as e:
                    await self.create_alert(
                        project_id, "monitoring_error", f"모니터링 오류: {str(e)}"
                    )
                    await asyncio.sleep(60)  # 오류 발생 시 1분 대기

        self._monitoring_tasks[project_id] = asyncio.create_task(monitor_task())

    async def stop_monitoring(self, project_id: int) -> None:
        """프로젝트 모니터링 중지"""
        if project_id in self._monitoring_tasks:
            self._monitoring_tasks[project_id].cancel()
            del self._monitoring_tasks[project_id]


async def check_website(url: str, timeout: int = 30) -> MonitoringStatus:
    """웹사이트 상태를 확인합니다."""
    start_time = datetime.now()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                return MonitoringStatus(
                    is_up=True, response_time=response_time, status_code=response.status
                )
    except Exception as e:
        return MonitoringStatus(is_up=False, error_message=str(e))


def check_ssl(hostname: str) -> SSLStatus:
    """SSL 인증서 상태를 확인합니다."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert["issuer"])
                not_before = datetime.strptime(
                    cert["notBefore"], "%b %d %H:%M:%S %Y %Z"
                )
                not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                days_remaining = (not_after - datetime.now()).days
                return SSLStatus(
                    is_valid=True,
                    issuer=issuer.get("organizationName"),
                    valid_from=not_before,
                    valid_until=not_after,
                    days_remaining=days_remaining,
                )
    except Exception as e:
        return SSLStatus(is_valid=False, error_message=str(e))


def check_project_status(project: Project) -> MonitoringResponse:
    """프로젝트의 상태를 확인합니다."""
    # URL에서 호스트네임 추출
    parsed_url = urlparse(str(project.url))
    hostname = parsed_url.netloc

    # 웹사이트 상태 체크
    status = check_website(project.url)

    # SSL 체크 (HTTPS인 경우)
    ssl_status = None
    if parsed_url.scheme == "https":
        ssl_status = check_ssl(hostname)

    return MonitoringResponse(
        project_id=project.id,
        project_title=project.title,
        url=str(project.url),
        status=status,
        ssl=ssl_status,
    )
