"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 EmailLog 모델과 유사한 역할을 합니다.
# SQLAlchemy ORM을 사용하여 email_logs 테이블을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. __tablename__ = "email_logs"  # Laravel의 protected $table = 'email_logs'와 동일
# 2. Column() = Laravel의 $fillable과 유사하지만, 타입과 제약조건을 직접 지정
# 3. relationship() = Laravel의 hasMany(), belongsTo()와 유사
# 4. func.now() = Laravel의 now()와 유사
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class EmailLog(Base):
    """이메일 로그 모델"""

    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # 관계 설정 (Laravel의 belongsTo와 유사)
    user = relationship("User", back_populates="email_logs")
