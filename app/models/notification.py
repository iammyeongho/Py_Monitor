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
    recipient = Column(String(255))  # 이메일 주소 또는 웹훅 URL
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정
    project = relationship("Project", back_populates="notifications")
