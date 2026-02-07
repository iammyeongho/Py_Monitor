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
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.services.notification_service import NotificationService
from app.models.project import Project
from app.models.notification import Notification


# =====================
# Fixture 정의
# =====================

@pytest.fixture
def notification_service(db):
    """테스트용 알림 서비스"""
    return NotificationService(db)


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
# NotificationService 단위 테스트
# =====================

def test_notification_service_create(notification_service, test_project, db):
    """NotificationService 알림 생성 테스트"""
    project_id = test_project["id"]

    notification = notification_service.create_notification(
        project_id=project_id,
        notification_type="email",
        message="Test notification",
        title="Test Title",
        severity="info",
        recipient="test@example.com"
    )

    assert notification.project_id == project_id
    assert notification.type == "email"
    assert notification.message == "Test notification"
    assert notification.is_read is False


def test_notification_service_mark_as_read(notification_service, test_project, db):
    """NotificationService 읽음 처리 테스트"""
    project_id = test_project["id"]

    # 알림 생성
    notification = notification_service.create_notification(
        project_id=project_id,
        notification_type="system",
        message="Test notification"
    )

    assert notification.is_read is False

    # 읽음 처리
    updated = notification_service.mark_as_read(notification.id)
    assert updated.is_read is True


def test_notification_service_get_unread_count(notification_service, test_project, db):
    """NotificationService 읽지 않은 알림 개수 테스트"""
    project_id = test_project["id"]

    # 알림 3개 생성
    for i in range(3):
        notification_service.create_notification(
            project_id=project_id,
            notification_type="system",
            message=f"Test notification {i}"
        )

    count = notification_service.get_unread_count(project_id=project_id)
    assert count >= 3
