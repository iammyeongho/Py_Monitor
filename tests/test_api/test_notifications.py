"""
# Laravel 개발자를 위한 설명
# 이 파일은 알림 시스템의 테스트를 구현합니다.
# Laravel의 PHPUnit 테스트와 유사한 역할을 합니다.
# 
# 주요 테스트:
# 1. 이메일 알림 전송
# 2. 웹훅 알림 전송
# 3. 알림 템플릿 관리
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.utils.notifications import NotificationService
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.models.project import Project
from app.models.notification import Notification
from app.db.session import SessionLocal
from datetime import datetime, timedelta

@pytest.fixture
def notification_service():
    """테스트용 알림 서비스"""
    return NotificationService()

@pytest.fixture
def test_alert_data():
    """테스트용 알림 데이터"""
    return {
        "project_name": "Test Project",
        "project_url": "https://example.com",
        "error_message": "Test error message",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

client = TestClient(app)

def get_test_token():
    """테스트용 토큰 획득"""
    # 사용자 생성
    client.post(
        "/api/v1/users/",
        json={
            "email": "notification_test@example.com",
            "password": "testpassword123",
            "full_name": "Notification Test User"
        }
    )
    
    # 로그인
    response = client.post(
        "/api/v1/users/login",
        data={
            "username": "notification_test@example.com",
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
            "title": "Notification Test Project",
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

def test_create_notification():
    """알림 생성 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    response = client.post(
        f"/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "type": "email",
            "recipient": "test@example.com",
            "message": "Test notification message"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id
    assert data["type"] == "email"
    assert data["recipient"] == "test@example.com"
    assert data["message"] == "Test notification message"

def test_get_notifications():
    """알림 목록 조회 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    # 알림 생성
    client.post(
        f"/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "type": "email",
            "recipient": "test@example.com",
            "message": "Test notification message"
        }
    )
    
    response = client.get(
        f"/api/v1/notifications/project/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_update_notification():
    """알림 업데이트 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    # 알림 생성
    create_response = client.post(
        f"/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "type": "email",
            "recipient": "test@example.com",
            "message": "Test notification message"
        }
    )
    notification_id = create_response.json()["id"]
    
    # 알림 업데이트
    response = client.put(
        f"/api/v1/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "is_read": True,
            "message": "Updated notification message"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] == True
    assert data["message"] == "Updated notification message"

def test_delete_notification():
    """알림 삭제 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    # 알림 생성
    create_response = client.post(
        f"/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "type": "email",
            "recipient": "test@example.com",
            "message": "Test notification message"
        }
    )
    notification_id = create_response.json()["id"]
    
    # 알림 삭제
    response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # 삭제 확인
    get_response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404

def test_get_unread_notifications():
    """읽지 않은 알림 조회 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    # 읽지 않은 알림 생성
    client.post(
        f"/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "type": "email",
            "recipient": "test@example.com",
            "message": "Unread notification message"
        }
    )
    
    response = client.get(
        f"/api/v1/notifications/unread",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(not notification["is_read"] for notification in data)

def test_mark_all_as_read():
    """모든 알림을 읽음으로 표시 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)
    
    # 여러 알림 생성
    for i in range(3):
        client.post(
            f"/api/v1/notifications/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": project_id,
                "type": "email",
                "recipient": "test@example.com",
                "message": f"Test notification {i}"
            }
        )
    
    # 모든 알림을 읽음으로 표시
    response = client.put(
        f"/api/v1/notifications/mark-all-read",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # 확인
    get_response = client.get(
        f"/api/v1/notifications/unread",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert len(data) == 0

@pytest.mark.asyncio
async def test_send_email_notification_success(notification_service, test_alert_data):
    """이메일 알림 전송 성공 테스트"""
    with patch("app.utils.email.send_email_alert") as mock_send_email:
        mock_send_email.return_value = True
        
        result = await notification_service.send_email_notification(
            email="test@example.com",
            subject="Test Alert",
            template="Test template: {project_name}",
            data=test_alert_data
        )
        
        assert result == True
        mock_send_email.assert_called_once()

@pytest.mark.asyncio
async def test_send_email_notification_failure(notification_service, test_alert_data):
    """이메일 알림 전송 실패 테스트"""
    with patch("app.utils.email.send_email_alert") as mock_send_email:
        mock_send_email.side_effect = Exception("Email sending failed")
        
        result = await notification_service.send_email_notification(
            email="test@example.com",
            subject="Test Alert",
            template="Test template: {project_name}",
            data=test_alert_data
        )
        
        assert result == False

@pytest.mark.asyncio
async def test_send_webhook_notification_success(notification_service, test_alert_data):
    """웹훅 알림 전송 성공 테스트"""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        result = await notification_service.send_webhook_notification(
            webhook_url="https://webhook.example.com",
            data=test_alert_data
        )
        
        assert result == True

@pytest.mark.asyncio
async def test_send_webhook_notification_failure(notification_service, test_alert_data):
    """웹훅 알림 전송 실패 테스트"""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__.return_value.post.side_effect = Exception("Webhook sending failed")
        
        result = await notification_service.send_webhook_notification(
            webhook_url="https://webhook.example.com",
            data=test_alert_data
        )
        
        assert result == False

def test_get_alert_template(notification_service):
    """알림 템플릿 조회 테스트"""
    # 상태 오류 템플릿
    status_template = notification_service.get_alert_template("status_error")
    assert "프로젝트:" in status_template
    assert "URL:" in status_template
    assert "오류 메시지:" in status_template
    
    # SSL 오류 템플릿
    ssl_template = notification_service.get_alert_template("ssl_error")
    assert "SSL 인증서 오류" in ssl_template
    assert "도메인:" in ssl_template
    
    # 도메인 만료 템플릿
    domain_template = notification_service.get_alert_template("domain_expiry")
    assert "도메인 만료 예정" in domain_template
    assert "만료일:" in domain_template
    
    # 모니터링 오류 템플릿
    monitoring_template = notification_service.get_alert_template("monitoring_error")
    assert "모니터링 시스템 오류" in monitoring_template
    
    # 알 수 없는 타입
    unknown_template = notification_service.get_alert_template("unknown_type")
    assert unknown_template == "알림 메시지: {message}"

def test_alert_template_formatting(notification_service, test_alert_data):
    """알림 템플릿 포맷팅 테스트"""
    template = notification_service.get_alert_template("status_error")
    formatted_message = template.format(**test_alert_data)
    
    assert test_alert_data["project_name"] in formatted_message
    assert test_alert_data["project_url"] in formatted_message
    assert test_alert_data["error_message"] in formatted_message
    assert test_alert_data["created_at"] in formatted_message 