"""
프로젝트 CRUD 관련 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.models.project import Project
from app.db.session import SessionLocal

client = TestClient(app)

def get_test_token():
    """테스트용 토큰 획득"""
    # 사용자 생성
    client.post(
        "/api/v1/users/",
        json={
            "email": "project_test@example.com",
            "password": "testpassword123",
            "full_name": "Project Test User"
        }
    )
    
    # 로그인
    response = client.post(
        "/api/v1/users/login",
        data={
            "username": "project_test@example.com",
            "password": "testpassword123"
        }
    )
    return response.json()["access_token"]

def test_create_project():
    """프로젝트 생성 테스트"""
    token = get_test_token()
    
    response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Project",
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
    data = response.json()
    assert data["title"] == "Test Project"
    assert data["url"] == "https://example.com"
    assert "id" in data

def test_get_projects():
    """프로젝트 목록 조회 테스트"""
    token = get_test_token()
    
    response = client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "title" in data[0]

def test_get_project():
    """특정 프로젝트 조회 테스트"""
    token = get_test_token()
    
    # 먼저 프로젝트 생성
    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Get Test Project",
            "url": "https://example.com",
            "host_name": "example.com"
        }
    )
    project_id = create_response.json()["id"]
    
    # 프로젝트 조회
    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["title"] == "Get Test Project"

def test_update_project():
    """프로젝트 업데이트 테스트"""
    token = get_test_token()
    
    # 먼저 프로젝트 생성
    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Update Test Project",
            "url": "https://example.com",
            "host_name": "example.com"
        }
    )
    project_id = create_response.json()["id"]
    
    # 프로젝트 업데이트
    response = client.put(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Project Title",
            "url": "https://example.com",
            "host_name": "example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["title"] == "Updated Project Title"

def test_delete_project():
    """프로젝트 삭제 테스트"""
    token = get_test_token()
    
    # 먼저 프로젝트 생성
    create_response = client.post(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Delete Test Project",
            "url": "https://example.com",
            "host_name": "example.com"
        }
    )
    project_id = create_response.json()["id"]
    
    # 프로젝트 삭제
    response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["is_active"] == False

def test_invalid_project_access():
    """잘못된 프로젝트 접근 테스트"""
    token = get_test_token()
    
    response = client.get(
        "/api/v1/projects/999999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404 