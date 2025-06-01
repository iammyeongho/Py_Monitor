import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project

@pytest.fixture
def test_user(db: Session):
    user = User(
        email="test@example.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_create_project(client, db: Session, test_user):
    project_data = {
        "host_name": "example.com",
        "ip_address": "192.168.1.1",
        "url": "https://example.com",
        "title": "Test Project",
        "status_interval": 300,
        "expiry_d_day": 30,
        "expiry_interval": 86400,
        "time_limit": 3600,
        "time_limit_interval": 300
    }
    response = client.post(f"/api/v1/users/{test_user.id}/projects/", json=project_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == project_data["title"]
    assert data["host_name"] == project_data["host_name"]

def test_get_project(client, db: Session, test_user):
    # 테스트 프로젝트 생성
    project = Project(
        user_id=test_user.id,
        host_name="example.com",
        ip_address="192.168.1.1",
        url="https://example.com",
        title="Test Project"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    response = client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == project.title
    assert data["host_name"] == project.host_name

def test_get_user_projects(client, db: Session, test_user):
    # 테스트 프로젝트들 생성
    projects = [
        Project(
            user_id=test_user.id,
            host_name=f"example{i}.com",
            ip_address=f"192.168.1.{i}",
            url=f"https://example{i}.com",
            title=f"Test Project {i}"
        )
        for i in range(3)
    ]
    for project in projects:
        db.add(project)
    db.commit()

    response = client.get(f"/api/v1/users/{test_user.id}/projects/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3

def test_update_project(client, db: Session, test_user):
    # 테스트 프로젝트 생성
    project = Project(
        user_id=test_user.id,
        host_name="example.com",
        ip_address="192.168.1.1",
        url="https://example.com",
        title="Test Project"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    update_data = {
        "title": "Updated Project",
        "host_name": "updated.com",
        "status_interval": 600
    }
    response = client.put(f"/api/v1/projects/{project.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["host_name"] == update_data["host_name"]

def test_delete_project(client, db: Session, test_user):
    # 테스트 프로젝트 생성
    project = Project(
        user_id=test_user.id,
        host_name="example.com",
        ip_address="192.168.1.1",
        url="https://example.com",
        title="Test Project"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    response = client.delete(f"/api/v1/projects/{project.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 삭제 확인
    response = client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND 