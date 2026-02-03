"""
프로젝트 CRUD 관련 테스트

# Laravel 개발자를 위한 설명
# conftest.py의 fixture를 사용하여 테스트 환경을 설정합니다.
# client, auth_headers fixture를 통해 인증된 API 호출을 수행합니다.
"""

import pytest


class TestProjectCRUD:
    """프로젝트 CRUD 테스트"""

    def test_create_project(self, client, auth_headers):
        """프로젝트 생성 테스트"""
        response = client.post(
            "/api/v1/projects/",
            headers=auth_headers,
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
        assert "https://example.com" in data["url"]
        assert "id" in data

    def test_get_projects(self, client, auth_headers):
        """프로젝트 목록 조회 테스트"""
        response = client.get(
            "/api/v1/projects/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_project(self, client, auth_headers):
        """특정 프로젝트 조회 테스트"""
        # 먼저 프로젝트 생성
        create_response = client.post(
            "/api/v1/projects/",
            headers=auth_headers,
            json={
                "title": "Get Test Project",
                "url": "https://example.com",
                "host_name": "example.com"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]

        # 프로젝트 조회
        response = client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["title"] == "Get Test Project"

    def test_update_project(self, client, auth_headers):
        """프로젝트 업데이트 테스트"""
        # 먼저 프로젝트 생성
        create_response = client.post(
            "/api/v1/projects/",
            headers=auth_headers,
            json={
                "title": "Update Test Project",
                "url": "https://example.com",
                "host_name": "example.com"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]

        # 프로젝트 업데이트
        response = client.put(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
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

    def test_delete_project(self, client, auth_headers):
        """프로젝트 삭제 테스트 (소프트 삭제)"""
        # 먼저 프로젝트 생성
        create_response = client.post(
            "/api/v1/projects/",
            headers=auth_headers,
            json={
                "title": "Delete Test Project",
                "url": "https://example.com",
                "host_name": "example.com"
            }
        )
        assert create_response.status_code == 200
        project_id = create_response.json()["id"]

        # 프로젝트 삭제
        response = client.delete(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["is_active"] is False

    def test_invalid_project_access(self, client, auth_headers):
        """존재하지 않는 프로젝트 접근 테스트"""
        response = client.get(
            "/api/v1/projects/999999",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestProjectAuth:
    """프로젝트 인증 관련 테스트"""

    def test_unauthorized_access(self, client):
        """인증 없는 접근 테스트"""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """잘못된 토큰 테스트"""
        response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
