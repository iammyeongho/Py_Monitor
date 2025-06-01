"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 관련 모델들을 정의합니다.
# SQLAlchemy ORM을 사용하여 monitoring_logs, monitoring_alerts, monitoring_settings 테이블을 정의합니다.
# 
# Laravel과의 주요 차이점:
# 1. 각 모델이 하나의 파일에 정의됨 (Laravel은 보통 각 모델을 별도 파일로 분리)
# 2. datetime.utcnow = Laravel의 now()와 유사하지만 UTC 기준
# 3. relationship() = Laravel의 hasMany(), belongsTo()와 유사
# 4. ondelete='CASCADE' = Laravel의 onDelete('cascade')와 유사
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class MonitoringLog(Base):
    """
    # 모니터링 로그 모델 (Laravel의 MonitoringLog 모델과 유사)
    # 
    # 주요 필드:
    # - project_id: 프로젝트 외래 키 (Laravel의 belongsTo('Project')와 유사)
    # - status_code: HTTP 상태 코드
    # - response_time: 응답 시간 (초)
    # - is_available: 서비스 가용성
    # - error_message: 오류 메시지
    # - created_at: 로그 생성 시간 (Laravel의 $timestamps와 유사)
    """
    __tablename__ = 'monitoring_logs'  # Laravel의 protected $table = 'monitoring_logs'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # Laravel의 foreign()와 유사
    status_code = Column(Integer)  # HTTP 상태 코드
    response_time = Column(Float)  # 응답 시간 (초)
    is_available = Column(Boolean)  # 서비스 가용성
    error_message = Column(Text)  # 오류 메시지
    created_at = Column(DateTime, default=datetime.utcnow)  # Laravel의 $timestamps

class MonitoringAlert(Base):
    """
    # 모니터링 알림 모델 (Laravel의 MonitoringAlert 모델과 유사)
    # 
    # 주요 필드:
    # - project_id: 프로젝트 외래 키 (Laravel의 belongsTo('Project')와 유사)
    # - alert_type: 알림 유형 (예: 'error', 'warning', 'info')
    # - message: 알림 메시지
    # - is_resolved: 해결 여부
    # - resolved_at: 해결 시간
    # - created_at, updated_at: 타임스탬프 (Laravel의 $timestamps와 유사)
    """
    __tablename__ = 'monitoring_alerts'  # Laravel의 protected $table = 'monitoring_alerts'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # Laravel의 foreign()와 유사
    alert_type = Column(String(50), nullable=False)  # 알림 유형
    message = Column(Text, nullable=False)  # 알림 메시지
    is_resolved = Column(Boolean, default=False)  # 해결 여부
    resolved_at = Column(DateTime)  # 해결 시간
    created_at = Column(DateTime, default=datetime.utcnow)  # Laravel의 $timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Laravel의 $timestamps

class MonitoringSetting(Base):
    """
    # 모니터링 설정 모델 (Laravel의 MonitoringSetting 모델과 유사)
    # 
    # 주요 필드:
    # - project_id: 프로젝트 외래 키 (Laravel의 belongsTo('Project')와 유사)
    # - check_interval: 체크 주기 (초)
    # - timeout: 타임아웃 (초)
    # - retry_count: 재시도 횟수
    # - alert_threshold: 알림 임계값
    # - created_at, updated_at: 타임스탬프 (Laravel의 $timestamps와 유사)
    """
    __tablename__ = 'monitoring_settings'  # Laravel의 protected $table = 'monitoring_settings'

    id = Column(Integer, primary_key=True, index=True)  # Laravel의 $primaryKey
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)  # Laravel의 foreign()와 유사
    check_interval = Column(Integer)  # 체크 주기 (초)
    timeout = Column(Integer)  # 타임아웃 (초)
    retry_count = Column(Integer)  # 재시도 횟수
    alert_threshold = Column(Integer)  # 알림 임계값
    created_at = Column(DateTime, default=datetime.utcnow)  # Laravel의 $timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Laravel의 $timestamps 