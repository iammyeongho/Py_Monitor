"""
사용자 인증 관련 테스트

실제 API 라우터 경로: /api/v1/auth
"""

import uuid
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User


def unique_email(prefix: str = "test") -> str:
    """고유한 이메일 생성"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def test_create_user(client, db: Session):
    """사용자 생성 테스트"""
    email = unique_email("newuser")
    user_data = {
        "email": email,
        "password": "testpassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == email
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_user(client, db: Session):
    """사용자 등록 테스트"""
    email = unique_email("register")
    user_data = {
        "email": email,
        "password": "testpassword123",
        "full_name": "Register User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == email


def test_login(client, db: Session):
    """로그인 테스트"""
    email = unique_email("login")
    hashed = get_password_hash("testpassword123")
    user = User(
        email=email,
        hashed_password=hashed,
        full_name="Login User"
    )
    db.add(user)
    db.flush()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db: Session):
    """잘못된 비밀번호 로그인 테스트"""
    email = unique_email("wrongpw")
    hashed = get_password_hash("correctpassword")
    user = User(
        email=email,
        hashed_password=hashed
    )
    db.add(user)
    db.flush()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user(client, db: Session):
    """현재 사용자 조회 테스트"""
    email = unique_email("me")
    hashed = get_password_hash("testpassword123")
    user = User(
        email=email,
        hashed_password=hashed,
        full_name="Me User"
    )
    db.add(user)
    db.flush()

    # 로그인하여 토큰 획득
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]

    # 현재 사용자 조회
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == email


def test_update_current_user(client, db: Session):
    """현재 사용자 정보 수정 테스트"""
    email = unique_email("update")
    hashed = get_password_hash("testpassword123")
    user = User(
        email=email,
        hashed_password=hashed,
        full_name="Original Name"
    )
    db.add(user)
    db.flush()

    # 로그인
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "testpassword123"
        }
    )
    token = login_response.json()["access_token"]

    # 정보 수정
    response = client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_get_users(client, db: Session, superuser_headers: dict):
    """사용자 목록 조회 테스트 (관리자 전용)"""
    # 테스트 사용자들 생성
    created_emails = []
    for i in range(3):
        email = unique_email(f"list{i}")
        created_emails.append(email)
        user = User(
            email=email,
            hashed_password=get_password_hash("password")
        )
        db.add(user)
    db.flush()

    response = client.get("/api/v1/auth/", headers=superuser_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # 최소 3명 이상의 사용자가 있어야 함
    assert len(data) >= 3


def test_get_user_by_id(client, db: Session, superuser_headers: dict):
    """특정 사용자 조회 테스트 (관리자 전용)"""
    email = unique_email("specific")
    user = User(
        email=email,
        hashed_password=get_password_hash("password"),
        full_name="Specific User"
    )
    db.add(user)
    db.flush()
    db.refresh(user)

    response = client.get(f"/api/v1/auth/{user.id}", headers=superuser_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == email


def test_duplicate_email(client, db: Session):
    """중복 이메일 등록 테스트"""
    email = unique_email("duplicate")
    user = User(
        email=email,
        hashed_password=get_password_hash("password")
    )
    db.add(user)
    db.flush()

    response = client.post(
        "/api/v1/auth/",
        json={
            "email": email,
            "password": "newpassword123"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
