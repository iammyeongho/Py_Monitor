"""
# Laravel 개발자를 위한 설명
# 이 파일은 이메일 로그 관련 모델을 정의합니다.
# SQLAlchemy ORM을 사용하여 email_logs 테이블을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. ForeignKey() = Laravel의 foreign()와 유사
# 2. relationship() = Laravel의 belongsTo()와 유사
# 3. ondelete="CASCADE" = Laravel의 onDelete('cascade')와 유사
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class EmailLog(Base):
    """
    # 이메일 로그 모델
    #
    # 주요 필드:
    # - id: 기본 키
    # - user_id: 사용자 외래 키
    # - project_id: 프로젝트 외래 키
    # - email: 수신자 이메일
    # - status: 발송 상태
    # - body: 이메일 내용
    # - error_message: 오류 메시지
    # - created_at: 생성 시간
    """

    __tablename__ = "email_logs"  # Laravel의 protected $table = 'email_logs'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    email = Column(String(255))  # 수신자 이메일
    status = Column(Boolean)  # 발송 상태
    body = Column(Text)  # 이메일 내용
    error_message = Column(Text)  # 오류 메시지
    created_at = Column(DateTime, default=func.now())  # Laravel의 $timestamps

    # 관계 설정 (Laravel의 belongsTo와 유사)
    user = relationship("User", back_populates="email_logs")
    project = relationship("Project", back_populates="email_logs")
