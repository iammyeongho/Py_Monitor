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