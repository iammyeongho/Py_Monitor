"""
알림 모델 정의
"""

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
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
