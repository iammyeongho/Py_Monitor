"""
사용자 인증 관련 테스트

# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 Feature Test와 유사한 역할을 합니다.
# pytest를 사용하여 인증 관련 API를 테스트합니다.
"""

import uuid
from fastapi.testclient import TestClient


def test_create_user(client: TestClient):
    """사용자 생성 테스트"""
    unique_email = f"create_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/v1/auth/",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == unique_email
    assert data["full_name"] == "Test User"
    assert "id" in data


def test_login(client: TestClient, test_user):
    """로그인 테스트"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_current_user(client: TestClient, test_user, auth_headers):
    """현재 사용자 정보 조회 테스트"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email


def test_update_user(client: TestClient, test_user, auth_headers):
    """사용자 정보 업데이트 테스트"""
    response = client.put(
        "/api/v1/auth/me",
        headers=auth_headers,
        json={"full_name": "Updated Name", "email": test_user.email},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_invalid_login(client: TestClient):
    """잘못된 로그인 시도 테스트"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_invalid_token(client: TestClient):
    """잘못된 토큰으로 접근 시도 테스트"""
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
