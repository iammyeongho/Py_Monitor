"""
FastAPI 기반의 웹사이트 모니터링 시스템 메인 애플리케이션 파일
이 파일은 애플리케이션의 진입점으로, FastAPI 인스턴스를 생성하고
필요한 미들웨어와 라우터를 설정합니다.
"""

import app.core.logging_config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.router import api_router
from app.core.config import settings

# FastAPI 애플리케이션 생성
# title, description, version은 API 문서화에 사용됩니다.
app = FastAPI(
    title="Py_Monitor",
    description="웹사이트 모니터링 시스템",
    version="1.0.0"
)

# CORS 미들웨어 설정
# 프론트엔드와의 통신을 위한 CORS 정책을 설정합니다.
# 실제 운영 환경에서는 보안을 위해 특정 도메인만 허용하도록 수정해야 합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용하도록 수정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 제공 설정
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# API 라우터 등록
# /api/v1 경로 아래에 모든 API 엔드포인트를 등록합니다.
app.include_router(api_router, prefix="/api/v1")

# 헬스 체크 엔드포인트
# 시스템의 상태를 확인하기 위한 엔드포인트입니다.
@app.get("/health")
def health_check():
    return {"status": "healthy"}
