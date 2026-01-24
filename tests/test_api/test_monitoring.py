"""
모니터링 서비스 테스트

실제 API 라우터 경로: /api/v1/monitoring
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from fastapi.testclient import TestClient
from main import app

from app.core.security import get_password_hash
from app.models.user import User
from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert, MonitoringSetting
from app.schemas.monitoring import MonitoringStatus
from app.services.monitoring import MonitoringService

client = TestClient(app)


def get_test_token():
    """테스트용 토큰 획득"""
    # 사용자 생성
    client.post(
        "/api/v1/auth/",
        json={
            "email": "monitoring_test@example.com",
            "password": "testpassword123",
            "full_name": "Monitoring Test User"
        }
    )

    # 로그인
    response = client.post(
        "/api/v1/auth/login",
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
    assert "checked_at" in data


def test_get_all_projects_status():
    """전체 프로젝트 상태 확인 테스트"""
    token = get_test_token()

    response = client.get(
        "/api/v1/monitoring/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_monitoring_setting():
    """모니터링 설정 생성 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)

    response = client.post(
        "/api/v1/monitoring/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "check_interval": 300,
            "timeout": 30,
            "retry_count": 3,
            "alert_threshold": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id
    assert data["check_interval"] == 300


def test_get_monitoring_setting():
    """모니터링 설정 조회 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)

    # 먼저 설정 생성
    client.post(
        "/api/v1/monitoring/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "check_interval": 300,
            "timeout": 30,
            "retry_count": 3,
            "alert_threshold": 3
        }
    )

    response = client.get(
        f"/api/v1/monitoring/settings/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "check_interval" in data


def test_update_monitoring_setting():
    """모니터링 설정 업데이트 테스트"""
    token = get_test_token()
    project_id = create_test_project(token)

    # 먼저 설정 생성
    client.post(
        "/api/v1/monitoring/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "check_interval": 300,
            "timeout": 30,
            "retry_count": 3,
            "alert_threshold": 3
        }
    )

    response = client.put(
        f"/api/v1/monitoring/settings/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "check_interval": 600,
            "timeout": 60
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["check_interval"] == 600
    assert data["timeout"] == 60


def test_tcp_port_check():
    """TCP 포트 체크 테스트"""
    token = get_test_token()

    response = client.post(
        "/api/v1/monitoring/check/tcp",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "host": "google.com",
            "port": 80,
            "timeout": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "host" in data
    assert "port" in data
    assert "is_open" in data


def test_dns_lookup():
    """DNS 조회 테스트"""
    token = get_test_token()

    response = client.post(
        "/api/v1/monitoring/check/dns",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "domain": "google.com",
            "record_type": "A"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "domain" in data
    assert "is_resolved" in data
    assert "records" in data


def test_content_check():
    """콘텐츠 검증 테스트"""
    token = get_test_token()

    response = client.post(
        "/api/v1/monitoring/check/content",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://www.google.com",
            "expected_content": "Google",
            "timeout": 30
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "is_found" in data


def test_security_headers_check():
    """보안 헤더 체크 테스트"""
    token = get_test_token()

    response = client.post(
        "/api/v1/monitoring/check/security-headers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "url": "https://www.google.com",
            "timeout": 30
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "headers" in data
    assert "score" in data


# MonitoringService 단위 테스트
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
async def test_check_tcp_port_open(monitoring_service):
    """TCP 포트 열림 테스트"""
    with patch("socket.socket") as mock_socket:
        mock_sock_instance = Mock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None

        result = await monitoring_service.check_tcp_port("localhost", 80)

        assert result.is_open == True
        assert result.host == "localhost"
        assert result.port == 80


@pytest.mark.asyncio
async def test_check_dns_lookup_success(monitoring_service):
    """DNS 조회 성공 테스트"""
    with patch("dns.resolver.Resolver") as mock_resolver:
        mock_answer = Mock()
        mock_answer.ttl = 300
        mock_answer.__iter__ = lambda self: iter([Mock(__str__=lambda self: "1.2.3.4")])
        mock_resolver.return_value.resolve.return_value = mock_answer

        result = await monitoring_service.check_dns_lookup("example.com", "A")

        assert result.is_resolved == True
        assert result.domain == "example.com"
