"""
# Laravel 개발자를 위한 설명
# 이 파일은 이메일 로그 모델을 정의합니다.
# Laravel의 EmailLog 모델과 유사한 역할을 합니다.
# 
# 주요 기능:
# 1. 이메일 발송 로그 기록
# 2. 이메일 상태 추적
# 3. 오류 메시지 저장
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    user = relationship("User", back_populates="email_logs")
    project = relationship("Project", back_populates="email_logs")
