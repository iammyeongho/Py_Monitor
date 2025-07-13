"""
사용자 인증 관련 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.core.security import get_password_hash
from app.models.user import User
from app.db.session import SessionLocal

client = TestClient(app)

def test_create_user():
    """사용자 생성 테스트"""
    response = client.post(
        "/api/v1/auth/",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data

def test_login():
    """로그인 테스트"""
    # 먼저 사용자 생성
    client.post(
        "/api/v1/auth/",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
            "full_name": "Login Test User"
        }
    )
    
    # 로그인 시도
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user():
    """현재 사용자 정보 조회 테스트"""
    # 로그인하여 토큰 획득
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 현재 사용자 정보 조회
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "login@example.com"

def test_update_user():
    """사용자 정보 업데이트 테스트"""
    # 로그인하여 토큰 획득
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login@example.com",
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 사용자 정보 업데이트
    response = client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Updated Name",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"

def test_invalid_login():
    """잘못된 로그인 시도 테스트"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_invalid_token():
    """잘못된 토큰으로 접근 시도 테스트"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401 