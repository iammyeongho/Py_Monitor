"""
# Laravel 개발자를 위한 설명
# 이 파일은 프로젝트 로그 관련 모델을 정의합니다.
# SQLAlchemy ORM을 사용하여 project_logs 테이블을 정의합니다.
# 
# Laravel과의 주요 차이점:
# 1. ForeignKey() = Laravel의 foreign()와 유사
# 2. relationship() = Laravel의 belongsTo()와 유사
# 3. ondelete="CASCADE" = Laravel의 onDelete('cascade')와 유사
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base

class ProjectLog(Base):
    """
    # 프로젝트 로그 모델
    # 
    # 주요 필드:
    # - id: 기본 키
    # - project_id: 프로젝트 외래 키
    # - status: 모니터링 상태
    # - response_time: 응답 시간
    # - http_code: HTTP 상태 코드
    # - response_body: 응답 본문
    # - response_headers: 응답 헤더
    # - response_error: 오류 메시지
    # - created_at: 생성 시간
    """
    __tablename__ = "project_logs"  # Laravel의 protected $table = 'project_logs'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)  # Laravel의 foreign()와 유사
    status = Column(Boolean)  # 모니터링 상태
    response_time = Column(Float)  # 응답 시간
    http_code = Column(Integer)  # HTTP 상태 코드
    response_body = Column(Text)  # 응답 본문
    response_headers = Column(Text)  # 응답 헤더
    response_error = Column(Text)  # 오류 메시지
    created_at = Column(DateTime, default=func.now())  # Laravel의 $timestamps

    # 관계 설정 (Laravel의 belongsTo와 유사)
    project = relationship("Project", back_populates="project_logs")

