"""
# Laravel 개발자를 위한 설명
# 이 파일은 사용자 관련 API 엔드포인트를 정의합니다.
# Laravel의 UserController와 유사한 역할을 합니다.
#
# 주요 기능:
# 1. 사용자 CRUD
# 2. 인증
# 3. 권한 관리
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
):
    """사용자 생성"""
    user_service = UserService(db)
    db_user = user_service.get_user_by_email(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create_user(user)


@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(deps.get_current_user)):
    """현재 사용자 정보 조회"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """현재 사용자 정보 업데이트"""
    user_service = UserService(db)
    return user_service.update_user(current_user.id, user)


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
):
    """사용자 정보 조회"""
    user_service = UserService(db)
    db_user = user_service.get_user(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
):
    """사용자 목록 조회"""
    user_service = UserService(db)
    return user_service.get_users(skip=skip, limit=limit)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
):
    """사용자 정보 업데이트"""
    user_service = UserService(db)
    db_user = user_service.update_user(user_id, user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
):
    """사용자 삭제"""
    user_service = UserService(db)
    if not user_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/toggle-status", response_model=UserResponse)
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
):
    """사용자 활성화/비활성화"""
    user_service = UserService(db)
    db_user = user_service.toggle_user_status(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
