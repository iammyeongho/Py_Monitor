"""
API v1 라우터 설정

이 파일은 모든 API v1 엔드포인트를 통합하여 하나의 라우터로 관리합니다.
Laravel의 routes/api.php와 유사한 역할을 합니다.

라우터 등록 순서:
1. /auth - 사용자 인증 (로그인, 회원가입)
2. /projects - 프로젝트 CRUD
3. /monitoring - 모니터링 상태 조회
4. /notifications - 알림 관리
"""

from fastapi import APIRouter

from app.api.v1.endpoints import monitoring, notifications, projects, users

# API v1 라우터 생성
# 이 라우터는 main.py에서 /api/v1 prefix로 등록됩니다
api_router = APIRouter()

# 사용자 인증 라우터 등록
# 로그인, 회원가입, 토큰 갱신 등의 엔드포인트 포함
api_router.include_router(users.router, prefix="/auth", tags=["auth"])

# 프로젝트 라우터 등록
# 프로젝트 CRUD 및 관리 엔드포인트 포함
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# 모니터링 라우터 등록
# 프로젝트 상태 조회, 로그 조회 등의 엔드포인트 포함
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# 알림 라우터 등록
# 알림 조회, 읽음 처리 등의 엔드포인트 포함
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
