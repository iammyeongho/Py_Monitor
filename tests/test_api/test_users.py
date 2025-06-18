import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate

def test_create_user(client, db: Session):
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data

def test_get_user(client, db: Session):
    # 테스트 사용자 생성
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.get(f"/api/v1/users/{user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user.email
    assert "password" not in data

def test_get_users(client, db: Session):
    # 테스트 사용자들 생성
    users = [
        User(email=f"test{i}@example.com", password_hash="hashed_password")
        for i in range(3)
    ]
    for user in users:
        db.add(user)
    db.commit()

    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    assert all("password" not in user for user in data)

def test_update_user(client, db: Session):
    # 테스트 사용자 생성
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123"
    }
    response = client.put(f"/api/v1/users/{user.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == update_data["email"]
    assert "password" not in data

def test_delete_user(client, db: Session):
    # 테스트 사용자 생성
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.delete(f"/api/v1/users/{user.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 삭제 확인
    response = client.get(f"/api/v1/users/{user.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND 