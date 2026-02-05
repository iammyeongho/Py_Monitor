"""
데이터베이스 연결 및 모델 관계 테스트
"""

import uuid
import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting
from sqlalchemy import text


def unique_email(prefix: str = "test") -> str:
    """고유한 이메일 생성"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def test_db_connection():
    """데이터베이스 연결 테스트"""
    db = SessionLocal()
    try:
        # 연결 테스트 (읽기 전용이므로 트랜잭션 롤백 불필요)
        db.execute(text("SELECT 1"))
        assert True
    except Exception as e:
        assert False, f"데이터베이스 연결 실패: {str(e)}"
    finally:
        db.close()


def test_model_relationships(db):
    """모델 관계 테스트 (db fixture 사용으로 자동 롤백)"""
    # 사용자 생성
    user = User(
        email=unique_email("dbtest"),
        hashed_password="test_password",
        full_name="Test User"
    )
    db.add(user)
    db.flush()
    db.refresh(user)

    # 프로젝트 생성
    project = Project(
        user_id=user.id,
        title="Test Project",
        url="http://test.com"
    )
    db.add(project)
    db.flush()
    db.refresh(project)

    # 모니터링 로그 생성
    log = MonitoringLog(
        project_id=project.id,
        status_code=200,
        response_time=0.5,
        is_available=True
    )
    db.add(log)
    db.flush()
    db.refresh(log)

    # 모니터링 알림 생성
    alert = MonitoringAlert(
        project_id=project.id,
        alert_type="error",
        message="Test alert"
    )
    db.add(alert)
    db.flush()
    db.refresh(alert)

    # 모니터링 설정 생성
    setting = MonitoringSetting(
        project_id=project.id,
        check_interval=300,
        timeout=30,
        retry_count=3,
        alert_threshold=3
    )
    db.add(setting)
    db.flush()
    db.refresh(setting)

    # 관계 검증
    assert project.user == user
    assert project.monitoring_logs[0] == log
    assert project.monitoring_alerts[0] == alert
    assert project.monitoring_settings == setting

    # 정리 불필요: db fixture의 트랜잭션 롤백으로 자동 정리됨
