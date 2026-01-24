"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 ProjectController와 유사한 역할을 합니다.
# FastAPI를 사용하여 프로젝트 관련 엔드포인트를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. APIRouter = Laravel의 Route::controller()와 유사
# 2. Depends = Laravel의 dependency injection과 유사
# 3. HTTPException = Laravel의 abort()와 유사
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.project import Project
from app.schemas.project import Project as ProjectSchema
from app.schemas.project import ProjectCreate
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=ProjectSchema)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """새로운 프로젝트를 생성합니다."""
    db_project = Project(**project.dict(), user_id=current_user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectSchema])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """현재 사용자의 모든 프로젝트를 조회합니다."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.is_active.is_(True))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectSchema)
def read_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """특정 프로젝트를 조회합니다."""
    db_project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
        )
        .first()
    )
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return db_project


@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트 정보를 업데이트합니다."""
    db_project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
        )
        .first()
    )
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    for key, value in project.dict().items():
        setattr(db_project, key, value)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/{project_id}", response_model=ProjectSchema)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트를 삭제합니다."""
    db_project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
        )
        .first()
    )
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    db_project.is_active = False
    db.commit()
    db.refresh(db_project)
    return db_project
