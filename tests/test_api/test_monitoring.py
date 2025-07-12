"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 서비스의 테스트를 구현합니다.
# Laravel의 PHPUnit 테스트와 유사한 역할을 합니다.
# 
# 주요 테스트:
# 1. 프로젝트 상태 확인
# 2. SSL 인증서 확인
# 3. 도메인 만료일 확인
# 4. 알림 생성
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import ssl
from fastapi.testclient import TestClient
from main import app
from app.models.project import Project
from app.db.session import SessionLocal

from app.models.user import User
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting
from app.schemas.monitoring import MonitoringStatus
from app.services.monitoring import MonitoringService

client = TestClient(app)

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

@pytest.fixture
def mock_db():
    """테스트용 DB 세션"""
    return Mock()

@pytest.fixture
def mock_project():
    """테스트용 프로젝트"""
    return Project(
        id=1,
        title="Test Project",
        url="https://example.com",
        user_id=1,
        is_active=True
    )

@pytest.fixture
def monitoring_service(mock_db):
    """테스트용 모니터링 서비스"""
    return MonitoringService(mock_db)

@pytest.mark.asyncio
async def test_check_project_status_success(monitoring_service, mock_project):
    """프로젝트 상태 확인 성공 테스트"""
    mock_db = monitoring_service.db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        status = await monitoring_service.check_project_status(1)
        
        assert status.is_available == True
        assert status.status_code == 200
        assert status.error_message is None

@pytest.mark.asyncio
async def test_check_project_status_failure(monitoring_service, mock_project):
    """프로젝트 상태 확인 실패 테스트"""
    mock_db = monitoring_service.db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__.return_value.get.side_effect = Exception("Connection error")
        
        status = await monitoring_service.check_project_status(1)
        
        assert status.is_available == False
        assert status.status_code is None
        assert "Connection error" in status.error_message

@pytest.mark.asyncio
async def test_check_ssl_status_success(monitoring_service, mock_project):
    """SSL 인증서 확인 성공 테스트"""
    with patch("ssl.create_default_context") as mock_context, \
         patch("socket.create_connection") as mock_connection:
        
        mock_ssl_socket = Mock()
        mock_ssl_socket.getpeercert.return_value = {
            "notAfter": "Dec 31 23:59:59 2025 GMT"
        }
        mock_context.return_value.wrap_socket.return_value = mock_ssl_socket
        
        result = await monitoring_service.check_ssl_status(mock_project)
        
        assert result["is_valid"] == True
        assert isinstance(result["expiry_date"], datetime)
        assert result["error_message"] is None

@pytest.mark.asyncio
async def test_check_ssl_status_failure(monitoring_service, mock_project):
    """SSL 인증서 확인 실패 테스트"""
    with patch("ssl.create_default_context") as mock_context:
        mock_context.return_value.wrap_socket.side_effect = ssl.SSLError("SSL error")
        
        result = await monitoring_service.check_ssl_status(mock_project)
        
        assert result["is_valid"] == False
        assert result["expiry_date"] is None
        assert "SSL error" in result["error_message"]

@pytest.mark.asyncio
async def test_create_alert(monitoring_service, mock_project):
    """알림 생성 테스트"""
    mock_db = monitoring_service.db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project
    
    with patch.object(monitoring_service.notification_service, "send_email_notification") as mock_email, \
         patch.object(monitoring_service.notification_service, "send_webhook_notification") as mock_webhook:
        
        alert = await monitoring_service.create_alert(
            project_id=1,
            alert_type="status_error",
            message="Test alert"
        )
        
        assert alert.project_id == 1
        assert alert.alert_type == "status_error"
        assert alert.message == "Test alert"
        
        mock_email.assert_called_once()
        mock_webhook.assert_called_once()

@pytest.mark.asyncio
async def test_monitoring_task(monitoring_service, mock_project):
    """모니터링 작업 테스트"""
    mock_db = monitoring_service.db
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project
    
    with patch.object(monitoring_service, "check_project_status") as mock_status, \
         patch.object(monitoring_service, "check_ssl_status") as mock_ssl, \
         patch.object(monitoring_service, "create_alert") as mock_alert:
        
        mock_status.return_value = MonitoringStatus(
            is_available=True,
            response_time=0.1,
            status_code=200,
            error_message=None
        )
        
        mock_ssl.return_value = {
            "is_valid": True,
            "expiry_date": datetime.now() + timedelta(days=30),
            "error_message": None
        }
        
        await monitoring_service.start_monitoring(1)
        await asyncio.sleep(0.1)  # 작업이 실행될 시간을 줌
        await monitoring_service.stop_monitoring(1)
        
        mock_status.assert_called()
        mock_ssl.assert_called()
        mock_alert.assert_not_called()  # 정상 상태이므로 알림이 생성되지 않아야 함 

def get_test_token():
    """테스트용 토큰 획득"""
    # 사용자 생성
    client.post(
        "/api/v1/users/",
        json={
            "email": "monitoring_test@example.com",
            "password": "testpassword123",
            "full_name": "Monitoring Test User"
        }
    )
    
    # 로그인
    response = client.post(
        "/api/v1/users/login",
        data={
            "username": "monitoring_test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]

def create_test_project(token: str) -> int:
    """테스트용 프로젝트 생성"""
    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Monitoring Test Project",
            "url": "https://example.com",
            "host_name": "example.com",
            "ip_address": "93.184.216.34",
            "status_interval": 300,
            "expiry_d_day": 30,
            "expiry_interval": 7,
            "time_limit": 5,
            "time_limit_interval": 15
        }
    )
    return response.json()["id"]

def test_check_project_status():
    """프로젝트 상태 확인 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.get(
        f"/api/v1/monitoring/status/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data
    assert "status" in data
    assert "ssl" in data
    assert "checked_at" in data

def test_get_monitoring_logs():
    """모니터링 로그 조회 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.get(
        f"/api/v1/monitoring/logs/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_monitoring_alerts():
    """모니터링 알림 조회 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.get(
        f"/api/v1/monitoring/alerts/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_alert_status():
    """알림 상태 업데이트 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    # 먼저 알림 생성
    alert_response = client.post(
        f"/api/v1/monitoring/alerts/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "alert_type": "test_alert",
            "message": "Test alert message"
        }
    )
    alert_id = alert_response.json()["id"]
    
    # 알림 상태 업데이트
    response = client.put(
        f"/api/v1/monitoring/alerts/{alert_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_resolved": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_resolved"] == True

def test_get_monitoring_settings():
    """모니터링 설정 조회 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.get(
        f"/api/v1/monitoring/settings/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "check_interval" in data
    assert "timeout" in data
    assert "retry_count" in data
    assert "alert_threshold" in data

def test_update_monitoring_settings():
    """모니터링 설정 업데이트 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.put(
        f"/api/v1/monitoring/settings/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "check_interval": 600,
            "timeout": 60,
            "retry_count": 5,
            "alert_threshold": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["check_interval"] == 600
    assert data["timeout"] == 60
    assert data["retry_count"] == 5
    assert data["alert_threshold"] == 5

def test_start_monitoring():
    """모니터링 시작 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.post(
        f"/api/v1/monitoring/projects/{project_id}/monitoring/start",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Monitoring started"

def test_stop_monitoring():
    """모니터링 중지 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.post(
        f"/api/v1/monitoring/projects/{project_id}/monitoring/stop",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Monitoring stopped" 