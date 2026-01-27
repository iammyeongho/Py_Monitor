"""
모니터링 API 모듈

각 기능별로 분리된 엔드포인트:
- status: 모니터링 상태 조회
- settings: 모니터링 설정
- ssl: SSL 도메인 상태
- checks: TCP, DNS, 콘텐츠, 보안 헤더, 심층 체크
- logs: 모니터링 로그
- alerts: 모니터링 알림
- scheduler: 스케줄러 제어
- cleanup: 로그 정리
- charts: 차트 데이터
"""

from fastapi import APIRouter

from app.api.v1.endpoints.monitoring.status import router as status_router
from app.api.v1.endpoints.monitoring.settings import router as settings_router
from app.api.v1.endpoints.monitoring.ssl import router as ssl_router
from app.api.v1.endpoints.monitoring.checks import router as checks_router
from app.api.v1.endpoints.monitoring.logs import router as logs_router
from app.api.v1.endpoints.monitoring.alerts import router as alerts_router
from app.api.v1.endpoints.monitoring.scheduler import router as scheduler_router
from app.api.v1.endpoints.monitoring.cleanup import router as cleanup_router
from app.api.v1.endpoints.monitoring.charts import router as charts_router

router = APIRouter()

# 각 하위 라우터 등록
router.include_router(status_router, tags=["monitoring-status"])
router.include_router(settings_router, tags=["monitoring-settings"])
router.include_router(ssl_router, tags=["monitoring-ssl"])
router.include_router(checks_router, tags=["monitoring-checks"])
router.include_router(logs_router, tags=["monitoring-logs"])
router.include_router(alerts_router, tags=["monitoring-alerts"])
router.include_router(scheduler_router, tags=["monitoring-scheduler"])
router.include_router(cleanup_router, tags=["monitoring-cleanup"])
router.include_router(charts_router, tags=["monitoring-charts"])
