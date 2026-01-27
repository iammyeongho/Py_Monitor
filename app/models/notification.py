"""
알림(Notification) 모델

이 파일은 알림 정보를 저장하는 모델을 정의합니다.
Laravel의 Notification 모델과 유사한 역할을 합니다.

주요 필드:
- project_id: 연관된 프로젝트
- type: 알림 유형 (email, webhook 등)
- recipient: 수신자 (이메일 주소 또는 웹훅 URL)
- message: 알림 내용
- is_read: 읽음 여부
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Notification(Base):
    """알림 모델"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    type = Column(String(50))  # email, webhook 등
    title = Column(String(255), nullable=True)  # 알림 제목
    severity = Column(String(20), default="info")  # 심각도: info, warning, error, critical
    recipient = Column(String(255))  # 이메일 주소 또는 웹훅 URL
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # 발송 여부
    sent_at = Column(DateTime(timezone=True), nullable=True)  # 발송 시간
    created_at = Column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정
    project = relationship("Project", back_populates="notifications")

    # ==================== 비즈니스 메서드 ====================

    @property
    def is_critical(self) -> bool:
        """심각한 알림 여부"""
        return self.severity in ("error", "critical")

    @property
    def is_pending(self) -> bool:
        """발송 대기 중 여부"""
        return not self.is_sent

    @property
    def age_hours(self) -> float:
        """알림 생성 후 경과 시간 (시간)"""
        if not self.created_at:
            return 0
        delta = datetime.utcnow() - self.created_at.replace(tzinfo=None)
        return delta.total_seconds() / 3600

    @property
    def is_email_type(self) -> bool:
        """이메일 알림 여부"""
        return self.type == "email"

    @property
    def is_webhook_type(self) -> bool:
        """웹훅 알림 여부"""
        return self.type == "webhook"

    def can_resend(self, hours: int = 1) -> bool:
        """재발송 가능 여부 (발송 후 일정 시간 경과)"""
        if not self.is_sent or not self.sent_at:
            return True
        delta = datetime.utcnow() - self.sent_at.replace(tzinfo=None)
        return delta.total_seconds() > (hours * 3600)

    def get_severity_level(self) -> int:
        """심각도 레벨 (정렬용)"""
        levels = {"info": 0, "warning": 1, "error": 2, "critical": 3}
        return levels.get(self.severity, 0)
