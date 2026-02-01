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

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_non_viewer_user
from app.core.security import get_current_user
from app.models.project import Project
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.screenshot import ScreenshotService

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_non_viewer_user),
):
    """새로운 프로젝트를 생성합니다."""
    project_data = project.model_dump()
    # HttpUrl을 문자열로 변환
    if "url" in project_data:
        project_data["url"] = str(project_data["url"])
    db_project = Project(**project_data, user_id=current_user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectResponse])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """현재 사용자의 모든 프로젝트를 조회합니다.

    Args:
        skip: 건너뛸 항목 수
        limit: 반환할 최대 항목 수
        category: 카테고리로 필터링
        tag: 태그로 필터링 (부분 일치)
    """
    query = (
        db.query(Project)
        .filter(Project.user_id == current_user.id, Project.is_active.is_(True))
    )

    # 카테고리 필터링
    if category:
        query = query.filter(Project.category == category)

    # 태그 필터링 (부분 일치)
    if tag:
        query = query.filter(Project.tags.ilike(f"%{tag}%"))

    projects = (
        query
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects


@router.get("/categories", response_model=List[str])
def get_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """사용자의 프로젝트 카테고리 목록을 조회합니다."""
    categories = (
        db.query(Project.category)
        .filter(
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
            Project.category.isnot(None),
            Project.category != ""
        )
        .distinct()
        .all()
    )
    return [c[0] for c in categories if c[0]]


@router.get("/tags", response_model=List[str])
def get_tags(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """사용자의 프로젝트에서 사용된 모든 태그를 조회합니다."""
    projects = (
        db.query(Project.tags)
        .filter(
            Project.user_id == current_user.id,
            Project.is_active.is_(True),
            Project.tags.isnot(None),
            Project.tags != ""
        )
        .all()
    )

    # 모든 태그 수집 (중복 제거)
    all_tags = set()
    for (tags_str,) in projects:
        if tags_str:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

    return sorted(list(all_tags))


@router.get("/{project_id}", response_model=ProjectResponse)
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


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project: ProjectUpdate,
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

    update_data = project.model_dump(exclude_unset=True)
    # HttpUrl을 문자열로 변환
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])

    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)
    return db_project


@router.delete("/{project_id}", response_model=ProjectResponse)
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


# =====================
# 스크린샷 엔드포인트
# =====================


@router.get("/{project_id}/screenshot")
async def get_project_screenshot(
    project_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트 웹사이트의 스크린샷을 가져옵니다."""
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

    service = ScreenshotService(db)

    # 캐시된 스크린샷이 있으면 반환
    if not force and db_project.snapshot_path:
        return {
            "screenshot_url": db_project.snapshot_path,
            "thumbnail_url": service.get_preview_url(str(db_project.url)),
            "last_captured_at": db_project.last_snapshot_at,
            "cached": True
        }

    # 새로 캡처
    screenshot_path = await service.capture_screenshot(project_id, force=force)

    if screenshot_path:
        return {
            "screenshot_url": screenshot_path,
            "thumbnail_url": service.get_preview_url(str(db_project.url)),
            "last_captured_at": db_project.last_snapshot_at,
            "cached": False
        }

    # 캡처 실패 시 외부 URL 반환
    return {
        "screenshot_url": None,
        "thumbnail_url": service.get_preview_url(str(db_project.url)),
        "last_captured_at": None,
        "cached": False
    }


@router.get("/{project_id}/thumbnail")
def get_project_thumbnail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """프로젝트의 썸네일 URL을 반환합니다 (외부 서비스 이용)."""
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

    service = ScreenshotService(db)
    url = str(db_project.url)

    return {
        "project_id": project_id,
        "url": url,
        "thumbnail_url": service.get_preview_url(url),
        "favicon_url": service.get_thumbnail_url(url),
        "cached_screenshot": db_project.snapshot_path
    }
