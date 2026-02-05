"""
알림(Notification) API 테스트

# Laravel 개발자를 위한 설명
# conftest.py의 fixture를 사용하여 테스트 환경을 설정합니다.
# client, auth_headers fixture를 통해 인증된 API 호출을 수행합니다.
#
# 주요 테스트:
# 1. 알림 CRUD (생성/조회/수정/삭제)
# 2. 읽지 않은 알림 조회
# 3. 모든 알림 읽음 처리
# 4. 이메일/웹훅 알림 전송 (단위 테스트)
# 5. 알림 템플릿 관리
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.utils.notifications import NotificationService
from app.models.project import Project
from app.models.notification import Notification


# =====================
# Fixture 정의
# =====================

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


@pytest.fixture
def test_project(client, auth_headers, db):
    """테스트용 프로젝트 생성 (API를 통해)"""
    response = client.post(
        "/api/v1/projects/",
        headers=auth_headers,
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
    assert response.status_code == 200
    return response.json()


def _create_notification(client, auth_headers, project_id, message="Test notification message"):
    """알림 생성 헬퍼 함수"""
    response = client.post(
        "/api/v1/notifications/",
        headers=auth_headers,
        json={
            "project_id": project_id,
            "type": "email",
            "recipient": "test@example.com",
            "message": message
        }
    )
    assert response.status_code == 200
    return response.json()


# =====================
# 알림 CRUD 테스트
# =====================

def test_create_notification(client, auth_headers, test_project):
    """알림 생성 테스트"""
    project_id = test_project["id"]

    response = client.post(
        "/api/v1/notifications/",
        headers=auth_headers,
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


def test_get_notifications(client, auth_headers, test_project):
    """알림 목록 조회 테스트"""
    project_id = test_project["id"]

    # 알림 생성
    _create_notification(client, auth_headers, project_id)

    response = client.get(
        f"/api/v1/notifications/project/{project_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_update_notification(client, auth_headers, test_project):
    """알림 업데이트 테스트"""
    project_id = test_project["id"]

    # 알림 생성
    notification = _create_notification(client, auth_headers, project_id)
    notification_id = notification["id"]

    # 알림 업데이트
    response = client.put(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers,
        json={
            "is_read": True,
            "message": "Updated notification message"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] is True
    assert data["message"] == "Updated notification message"


def test_delete_notification(client, auth_headers, test_project):
    """알림 삭제 테스트"""
    project_id = test_project["id"]

    # 알림 생성
    notification = _create_notification(client, auth_headers, project_id)
    notification_id = notification["id"]

    # 알림 삭제
    response = client.delete(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers
    )
    assert response.status_code == 200

    # 삭제 확인
    get_response = client.get(
        f"/api/v1/notifications/{notification_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


def test_get_unread_notifications(client, auth_headers, test_project):
    """읽지 않은 알림 조회 테스트"""
    project_id = test_project["id"]

    # 읽지 않은 알림 생성
    _create_notification(client, auth_headers, project_id, "Unread notification")

    response = client.get(
        "/api/v1/notifications/unread",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(not notification["is_read"] for notification in data)


def test_mark_all_as_read(client, auth_headers, test_project):
    """모든 알림을 읽음으로 표시 테스트"""
    project_id = test_project["id"]

    # 여러 알림 생성
    for i in range(3):
        _create_notification(client, auth_headers, project_id, f"Test notification {i}")

    # 모든 알림을 읽음으로 표시
    response = client.put(
        "/api/v1/notifications/mark-all-read",
        headers=auth_headers
    )
    assert response.status_code == 200

    # 확인
    get_response = client.get(
        "/api/v1/notifications/unread",
        headers=auth_headers
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert len(data) == 0


# =====================
# 알림 전송 단위 테스트
# =====================

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

        assert result is True
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

        assert result is False


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

        assert result is True


@pytest.mark.asyncio
async def test_send_webhook_notification_failure(notification_service, test_alert_data):
    """웹훅 알림 전송 실패 테스트"""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__.return_value.post.side_effect = Exception("Webhook sending failed")

        result = await notification_service.send_webhook_notification(
            webhook_url="https://webhook.example.com",
            data=test_alert_data
        )

        assert result is False


# =====================
# 알림 템플릿 테스트
# =====================

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
