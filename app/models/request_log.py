"""
# Laravel 개발자를 위한 설명
# 이 파일은 요청 로그 관련 모델을 정의합니다.
# SQLAlchemy ORM을 사용하여 request_logs 테이블을 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. ForeignKey() = Laravel의 foreign()와 유사
# 2. relationship() = Laravel의 belongsTo()와 유사
# 3. ondelete="CASCADE" = Laravel의 onDelete('cascade')와 유사
"""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class RequestLog(Base):
    """
    # 요청 로그 모델
    #
    # 주요 필드:
    # - id: 기본 키
    # - project_id: 프로젝트 외래 키
    # - request_url: 요청 URL
    # - request_method: 요청 메서드
    # - request_headers: 요청 헤더
    # - request_body: 요청 본문
    # - response_code: 응답 코드
    # - response_time: 응답 시간
    # - response_body: 응답 본문
    # - response_headers: 응답 헤더
    # - created_at: 생성 시간
    """

    __tablename__ = "request_logs"  # Laravel의 protected $table = 'request_logs'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )  # Laravel의 foreign()와 유사
    request_url = Column(String(255), nullable=False)  # 요청 URL
    request_method = Column(String(10), nullable=False)  # 요청 메서드
    request_headers = Column(Text)  # 요청 헤더
    request_body = Column(Text)  # 요청 본문
    response_code = Column(Integer)  # 응답 코드
    response_time = Column(Float)  # 응답 시간
    response_body = Column(Text)  # 응답 본문
    response_headers = Column(Text)  # 응답 헤더
    created_at = Column(DateTime, default=func.now())  # Laravel의 $timestamps

    # 관계 설정 (Laravel의 belongsTo와 유사)
    project = relationship("Project", back_populates="request_logs")
