"""
# Laravel 개발자를 위한 설명
# 이 파일은 이메일 관련 비즈니스 로직을 구현합니다.
# Laravel의 Mail 클래스와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 이메일 발송
# 2. 이메일 템플릿 관리
# 3. 발송 로그 기록
"""

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import aiosmtplib
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_log import EmailLog


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    async def send_email(
        self,
        user_id: int,
        email: str,
        subject: str,
        body: str,
        project_id: Optional[int] = None,
    ) -> EmailLog:
        """이메일 발송"""
        # 이메일 로그 생성
        email_log = EmailLog(
            user_id=user_id,
            project_id=project_id,
            email=email,
            subject=subject,
            body=body,
            status="pending",
        )
        self.db.add(email_log)
        self.db.commit()
        self.db.refresh(email_log)

        try:
            # 이메일 메시지 생성
            message = MIMEMultipart()
            message["From"] = settings.SMTP_FROM
            message["To"] = email
            message["Subject"] = subject
            message.attach(MIMEText(body, "html"))

            # SMTP 서버 연결 및 이메일 발송
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=settings.SMTP_TLS,
            ) as smtp:
                await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                await smtp.send_message(message)

            # 로그 상태 업데이트
            email_log.status = "sent"
            email_log.updated_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            # 오류 발생 시 로그 업데이트
            email_log.status = "failed"
            email_log.error_message = str(e)
            email_log.updated_at = datetime.utcnow()
            self.db.commit()
            raise

        return email_log

    def get_email_logs(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[EmailLog]:
        """이메일 로그 조회"""
        return (
            self.db.query(EmailLog)
            .filter(EmailLog.user_id == user_id)
            .order_by(EmailLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_project_email_logs(
        self, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[EmailLog]:
        """프로젝트 관련 이메일 로그 조회"""
        return (
            self.db.query(EmailLog)
            .filter(EmailLog.project_id == project_id)
            .order_by(EmailLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
