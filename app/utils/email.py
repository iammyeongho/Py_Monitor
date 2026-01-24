"""
# Laravel 개발자를 위한 설명
# 이 파일은 이메일 발송 기능을 구현합니다.
# Laravel의 Mail 클래스와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 이메일 발송
# 2. HTML 템플릿 지원
# 3. 첨부 파일 지원
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_log import EmailLog


async def send_email_alert(
    email_to: str,
    subject: str,
    body: str,
    db: Session = None,
    project_id: int = None,
    user_id: int = None,
) -> bool:
    """
    모니터링 알림 이메일 발송

    Args:
        email_to: 수신자 이메일
        subject: 이메일 제목
        body: 이메일 내용
        db: 데이터베이스 세션
        project_id: 프로젝트 ID
        user_id: 사용자 ID

    Returns:
        bool: 발송 성공 여부
    """
    try:
        # 이메일 메시지 생성
        message = MIMEMultipart()
        message["From"] = settings.SMTP_USERNAME
        message["To"] = email_to
        message["Subject"] = subject

        # HTML 본문 추가
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ padding: 20px; }}
                    .alert {{
                        background-color: #f8d7da;
                        border: 1px solid #f5c6cb;
                        border-radius: 4px;
                        padding: 15px;
                        margin-bottom: 20px;
                    }}
                    .footer {{
                        color: #6c757d;
                        font-size: 12px;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert">
                        {body}
                    </div>
                    <div class="footer">
                        This is an automated message from Py Monitor.
                        Please do not reply to this email.
                    </div>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(html_content, "html"))

        # SMTP 서버 연결 및 이메일 발송
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_TLS,
        ) as smtp:
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(message)

        # 이메일 로그 저장
        if db and project_id and user_id:
            email_log = EmailLog(
                user_id=user_id,
                project_id=project_id,
                email=email_to,
                status=True,
                body=body,
            )
            db.add(email_log)
            db.commit()

        return True

    except Exception as e:
        # 오류 로그 저장
        if db and project_id and user_id:
            email_log = EmailLog(
                user_id=user_id,
                project_id=project_id,
                email=email_to,
                status=False,
                body=body,
                error_message=str(e),
            )
            db.add(email_log)
            db.commit()

        return False
