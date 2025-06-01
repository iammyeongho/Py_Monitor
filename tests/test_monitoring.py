import pytest
from fastapi import status
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting

@pytest.fixture
def test_project(db: Session):
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    project = Project(
        user_id=user.id,
        host_name="example.com",
        ip_address="192.168.1.1",
        url="https://example.com",
        title="Test Project"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def test_create_monitoring_log(client, db: Session, test_project):
    log_data = {
        "status_code": 200,
        "response_time": 0.5,
        "is_available": True,
        "error_message": None
    }
    response = client.post(f"/api/v1/projects/{test_project.id}/logs/", json=log_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status_code"] == log_data["status_code"]
    assert data["response_time"] == log_data["response_time"]

def test_get_project_logs(client, db: Session, test_project):
    # 테스트 로그 생성
    logs = [
        MonitoringLog(
            project_id=test_project.id,
            status_code=200,
            response_time=0.5,
            is_available=True
        ) for _ in range(3)
    ]
    for log in logs:
        db.add(log)
    db.commit()

    response = client.get(f"/api/v1/projects/{test_project.id}/logs/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3

def test_create_monitoring_alert(client, db: Session, test_project):
    alert_data = {
        "alert_type": "response_time",
        "message": "Response time exceeded threshold"
    }
    response = client.post(f"/api/v1/projects/{test_project.id}/alerts/", json=alert_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["alert_type"] == alert_data["alert_type"]
    assert data["message"] == alert_data["message"]
    assert data["is_resolved"] == False

def test_resolve_alert(client, db: Session, test_project):
    # 테스트 알림 생성
    alert = MonitoringAlert(
        project_id=test_project.id,
        alert_type="response_time",
        message="Response time exceeded threshold"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    response = client.put(f"/api/v1/alerts/{alert.id}/resolve")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_resolved"] == True
    assert data["resolved_at"] is not None

def test_update_monitoring_settings(client, db: Session, test_project):
    settings_data = {
        "check_interval": 300,
        "timeout": 30,
        "retry_count": 3,
        "alert_threshold": 1000
    }
    response = client.put(f"/api/v1/projects/{test_project.id}/settings/", json=settings_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["check_interval"] == settings_data["check_interval"]
    assert data["timeout"] == settings_data["timeout"]
    assert data["retry_count"] == settings_data["retry_count"]
    assert data["alert_threshold"] == settings_data["alert_threshold"]

def test_get_monitoring_settings(client, db: Session, test_project):
    # 테스트 설정 생성
    settings = MonitoringSetting(
        project_id=test_project.id,
        check_interval=300,
        timeout=30,
        retry_count=3,
        alert_threshold=1000
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)

    response = client.get(f"/api/v1/projects/{test_project.id}/settings/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["check_interval"] == settings.check_interval
    assert data["timeout"] == settings.timeout
    assert data["retry_count"] == settings.retry_count
    assert data["alert_threshold"] == settings.alert_threshold 