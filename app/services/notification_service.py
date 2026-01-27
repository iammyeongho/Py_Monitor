"""
# 알림 서비스
# 이메일 및 웹훅 알림을 처리합니다.
#
# 주요 기능:
# 1. 장애 알림 발송
# 2. 복구 알림 발송
# 3. 웹훅 발송 (Slack, Discord 등)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringSetting
from app.models.project import Project
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    """알림 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService(db)

    async def send_alert_notification(
        self,
        project_id: int,
        alert_type: str,
        message: str,
        details: Optional[dict] = None
    ) -> bool:
        """알림 발송 (이메일 + 웹훅)"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return False

        setting = self.db.query(MonitoringSetting).filter(
            MonitoringSetting.project_id == project_id
        ).first()

        if not setting or not setting.is_alert_enabled:
            logger.info(f"Alerts disabled for project {project_id}")
            return False

        success = True
        tasks = []

        # 이메일 알림
        if setting.alert_email:
            tasks.append(self._send_email_alert(
                project=project,
                email=setting.alert_email,
                alert_type=alert_type,
                message=message,
                details=details
            ))

        # 웹훅 알림
        if setting.webhook_url:
            tasks.append(self._send_webhook_alert(
                project=project,
                webhook_url=setting.webhook_url,
                alert_type=alert_type,
                message=message,
                details=details
            ))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Notification error: {result}")
                    success = False

        return success

    async def _send_email_alert(
        self,
        project: Project,
        email: str,
        alert_type: str,
        message: str,
        details: Optional[dict] = None
    ):
        """이메일 알림 발송"""
        try:
            if alert_type == "availability":
                subject = f"[PyMonitor] 장애 알림 - {project.title}"
                body = self._create_alert_email_body(project, message, details)
            elif alert_type == "recovery":
                subject = f"[PyMonitor] 복구 알림 - {project.title}"
                body = self._create_recovery_email_body(project, message, details)
            else:
                subject = f"[PyMonitor] 알림 - {project.title}"
                body = self._create_general_email_body(project, message, details)

            await self.email_service.send_email(
                user_id=project.user_id,
                email=email,
                subject=subject,
                body=body,
                project_id=project.id
            )
            logger.info(f"Email alert sent to {email} for project {project.id}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            raise

    async def _send_webhook_alert(
        self,
        project: Project,
        webhook_url: str,
        alert_type: str,
        message: str,
        details: Optional[dict] = None
    ):
        """웹훅 알림 발송"""
        try:
            # 웹훅 타입 감지 (Slack, Discord 등)
            payload = self._create_webhook_payload(
                webhook_url=webhook_url,
                project=project,
                alert_type=alert_type,
                message=message,
                details=details
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

            logger.info(f"Webhook alert sent for project {project.id}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            raise

    def _create_webhook_payload(
        self,
        webhook_url: str,
        project: Project,
        alert_type: str,
        message: str,
        details: Optional[dict] = None
    ) -> dict:
        """웹훅 페이로드 생성 (Slack/Discord 자동 감지)"""

        # 색상 결정
        if alert_type == "availability":
            color = "#ef6253"  # 빨강
            emoji = ":x:"
            title = "장애 알림"
        elif alert_type == "recovery":
            color = "#31b46e"  # 녹색
            emoji = ":white_check_mark:"
            title = "복구 알림"
        else:
            color = "#f5a623"  # 주황
            emoji = ":warning:"
            title = "알림"

        timestamp = datetime.utcnow().isoformat()

        # Discord 웹훅
        if "discord.com" in webhook_url or "discordapp.com" in webhook_url:
            return {
                "embeds": [{
                    "title": f"{emoji} {title} - {project.title}",
                    "description": message,
                    "color": int(color.replace("#", ""), 16),
                    "fields": [
                        {"name": "프로젝트", "value": project.title, "inline": True},
                        {"name": "URL", "value": str(project.url), "inline": True},
                    ],
                    "timestamp": timestamp,
                    "footer": {"text": "PyMonitor"}
                }]
            }

        # Slack 웹훅 (기본)
        return {
            "attachments": [{
                "color": color,
                "title": f"{emoji} {title} - {project.title}",
                "text": message,
                "fields": [
                    {"title": "프로젝트", "value": project.title, "short": True},
                    {"title": "URL", "value": str(project.url), "short": True},
                ],
                "footer": "PyMonitor",
                "ts": int(datetime.utcnow().timestamp())
            }]
        }

    def _create_alert_email_body(
        self,
        project: Project,
        message: str,
        details: Optional[dict] = None
    ) -> str:
        """장애 알림 이메일 본문 생성"""
        details_html = ""
        if details:
            details_html = "<ul>"
            for key, value in details.items():
                details_html += f"<li><strong>{key}:</strong> {value}</li>"
            details_html += "</ul>"

        return f"""
        <html>
        <body style="font-family: 'Noto Sans KR', sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #fff; border-radius: 12px; overflow: hidden;">
                <div style="background-color: #ef6253; color: #fff; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">장애 알림</h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #222; margin-top: 0;">{project.title}</h2>
                    <p style="color: #666; font-size: 14px;">
                        <strong>URL:</strong> <a href="{project.url}" style="color: #222;">{project.url}</a>
                    </p>
                    <div style="background-color: #fdecea; border-left: 4px solid #ef6253; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #333;">{message}</p>
                    </div>
                    {details_html}
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        발생 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                    </p>
                </div>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; color: #999; font-size: 12px;">
                    PyMonitor 자동 알림
                </div>
            </div>
        </body>
        </html>
        """

    def _create_recovery_email_body(
        self,
        project: Project,
        message: str,
        details: Optional[dict] = None
    ) -> str:
        """복구 알림 이메일 본문 생성"""
        details_html = ""
        if details:
            details_html = "<ul>"
            for key, value in details.items():
                details_html += f"<li><strong>{key}:</strong> {value}</li>"
            details_html += "</ul>"

        return f"""
        <html>
        <body style="font-family: 'Noto Sans KR', sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #fff; border-radius: 12px; overflow: hidden;">
                <div style="background-color: #31b46e; color: #fff; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">복구 알림</h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #222; margin-top: 0;">{project.title}</h2>
                    <p style="color: #666; font-size: 14px;">
                        <strong>URL:</strong> <a href="{project.url}" style="color: #222;">{project.url}</a>
                    </p>
                    <div style="background-color: #e8f8ef; border-left: 4px solid #31b46e; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #333;">{message}</p>
                    </div>
                    {details_html}
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        복구 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                    </p>
                </div>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; color: #999; font-size: 12px;">
                    PyMonitor 자동 알림
                </div>
            </div>
        </body>
        </html>
        """

    def _create_general_email_body(
        self,
        project: Project,
        message: str,
        details: Optional[dict] = None
    ) -> str:
        """일반 알림 이메일 본문 생성"""
        return f"""
        <html>
        <body style="font-family: 'Noto Sans KR', sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #fff; border-radius: 12px; overflow: hidden;">
                <div style="background-color: #222; color: #fff; padding: 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px;">모니터링 알림</h1>
                </div>
                <div style="padding: 30px;">
                    <h2 style="color: #222; margin-top: 0;">{project.title}</h2>
                    <p style="color: #666; font-size: 14px;">
                        <strong>URL:</strong> <a href="{project.url}" style="color: #222;">{project.url}</a>
                    </p>
                    <p style="color: #333; margin: 20px 0;">{message}</p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        알림 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                    </p>
                </div>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; color: #999; font-size: 12px;">
                    PyMonitor 자동 알림
                </div>
            </div>
        </body>
        </html>
        """


async def send_test_notification(
    db: Session,
    project_id: int,
    notification_type: str = "email"
) -> bool:
    """테스트 알림 발송"""
    service = NotificationService(db)
    return await service.send_alert_notification(
        project_id=project_id,
        alert_type="test",
        message="테스트 알림입니다. 이 알림은 정상적으로 수신되었음을 확인하기 위한 것입니다.",
        details={"테스트 유형": notification_type}
    )
