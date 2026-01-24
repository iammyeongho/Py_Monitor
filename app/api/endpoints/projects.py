"""
# Laravel 개발자를 위한 설명
# 이 파일은 프로젝트 관련 API 엔드포인트를 정의합니다.
# Laravel의 ProjectController와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 프로젝트 CRUD
# 2. 프로젝트 상태 관리
# 3. 프로젝트 설정 관리
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """프로젝트 생성"""
    project_service = ProjectService(db)
    return project_service.create_project(current_user.id, project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def read_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """프로젝트 정보 조회"""
    project_service = ProjectService(db)
    db_project = project_service.get_project(project_id, current_user.id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.get("/", response_model=List[ProjectResponse])
async def read_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """프로젝트 목록 조회"""
    project_service = ProjectService(db)
    return project_service.get_user_projects(current_user.id, skip=skip, limit=limit)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """프로젝트 정보 업데이트"""
    project_service = ProjectService(db)
    db_project = project_service.update_project(project_id, current_user.id, project)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """프로젝트 삭제"""
    project_service = ProjectService(db)
    if not project_service.delete_project(project_id, current_user.id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/toggle-status", response_model=ProjectResponse)
async def toggle_project_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """프로젝트 활성화/비활성화"""
    project_service = ProjectService(db)
    db_project = project_service.toggle_project_status(project_id, current_user.id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project
