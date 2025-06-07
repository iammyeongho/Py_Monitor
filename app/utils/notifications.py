"""
# Laravel 개발자를 위한 설명
# 이 파일은 알림 시스템을 구현합니다.
# Laravel의 Notification 시스템과 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 이메일 알림
# 2. 웹훅 알림
# 3. 알림 템플릿 관리
"""

import aiohttp
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from app.utils.email import send_email_alert

logger = logging.getLogger(__name__)

class NotificationService:
    """알림 서비스"""
    
    @staticmethod
    async def send_email_notification(
        email: str,
        subject: str,
        template: str,
        data: Dict[str, Any]
    ) -> bool:
        """이메일 알림 전송"""
        try:
            # 템플릿에 데이터 적용
            message = template.format(**data)
            
            # 이메일 전송
            await send_email_alert(
                email=email,
                subject=subject,
                message=message
            )
            return True
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    @staticmethod
    async def send_webhook_notification(
        webhook_url: str,
        data: Dict[str, Any]
    ) -> bool:
        """웹훅 알림 전송"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=data) as response:
                    if response.status == 200:
                        return True
                    logger.error(f"Webhook notification failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
            return False
    
    @staticmethod
    def get_alert_template(alert_type: str) -> str:
        """알림 템플릿 조회"""
        templates = {
            "status_error": """
                [모니터링 알림] 서비스 상태 오류
                프로젝트: {project_name}
                URL: {project_url}
                오류 메시지: {error_message}
                발생 시간: {created_at}
            """,
            "ssl_error": """
                [모니터링 알림] SSL 인증서 오류
                프로젝트: {project_name}
                도메인: {domain}
                오류 메시지: {error_message}
                발생 시간: {created_at}
            """,
            "domain_expiry": """
                [모니터링 알림] 도메인 만료 예정
                프로젝트: {project_name}
                도메인: {domain}
                만료일: {expiry_date}
                발생 시간: {created_at}
            """,
            "monitoring_error": """
                [모니터링 알림] 모니터링 시스템 오류
                프로젝트: {project_name}
                오류 메시지: {error_message}
                발생 시간: {created_at}
            """
        }
        return templates.get(alert_type, "알림 메시지: {message}") 