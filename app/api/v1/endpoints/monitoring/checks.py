"""모니터링 체크 API (TCP, DNS, Content, Security Headers, Deep)"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.schemas.monitoring import (
    APIEndpointCheckRequest,
    APIEndpointCheckResponse,
    ContentCheckRequest,
    ContentCheckResponse,
    DNSLookupRequest,
    DNSLookupResponse,
    PlaywrightCheckResponse,
    PlaywrightHealth,
    PlaywrightMemory,
    PlaywrightNetwork,
    PlaywrightPerformance,
    PlaywrightResources,
    SecurityHeadersRequest,
    SecurityHeadersResponse,
    SyntheticTestRequest,
    SyntheticTestResponse,
    TCPPortCheckRequest,
    TCPPortCheckResponse,
    UDPPortCheckRequest,
    UDPPortCheckResponse,
)
from app.services.monitoring import MonitoringService
from app.services.playwright_monitor import PlaywrightMonitorService

router = APIRouter()


@router.post("/check/tcp", response_model=TCPPortCheckResponse)
async def check_tcp_port(
    request: TCPPortCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """TCP 포트 연결 가능 여부를 확인합니다."""
    service = MonitoringService(db)
    result = await service.check_tcp_port(
        host=request.host,
        port=request.port,
        timeout=request.timeout,
    )
    return result


@router.post("/check/udp", response_model=UDPPortCheckResponse)
async def check_udp_port(
    request: UDPPortCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UDP 포트 연결 가능 여부를 확인합니다.

    UDP는 비연결형 프로토콜로 TCP와 다르게 동작합니다:
    - 응답 없음: open|filtered (포트 열림 또는 방화벽 필터링)
    - ICMP unreachable: 포트 닫힘
    """
    service = MonitoringService(db)
    result = await service.check_udp_port(
        host=request.host,
        port=request.port,
        timeout=request.timeout,
    )
    return result


@router.post("/check/api", response_model=APIEndpointCheckResponse)
async def check_api_endpoint(
    request: APIEndpointCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """API 엔드포인트를 체크하고 JSON 응답을 검증합니다.

    - HTTP 메서드, 헤더, 바디를 지정하여 요청
    - 상태 코드 검증
    - JSON 응답 경로/값 검증 (dot-notation)
    """
    service = MonitoringService(db)
    result = await service.check_api_endpoint(
        url=request.url,
        method=request.method,
        headers=request.headers,
        body=request.body,
        timeout=request.timeout,
        expected_status=request.expected_status,
        expected_json_path=request.expected_json_path,
        expected_json_value=request.expected_json_value,
    )
    return result


@router.post("/check/dns", response_model=DNSLookupResponse)
async def check_dns_lookup(
    request: DNSLookupRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """DNS 레코드를 조회합니다."""
    service = MonitoringService(db)
    result = await service.check_dns_lookup(
        domain=request.domain,
        record_type=request.record_type,
    )
    return result


@router.post("/check/content", response_model=ContentCheckResponse)
async def check_content(
    request: ContentCheckRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """응답 콘텐츠에 특정 문자열이 포함되어 있는지 확인합니다."""
    service = MonitoringService(db)
    result = await service.check_content(
        url=request.url,
        expected_content=request.expected_content,
        timeout=request.timeout,
    )
    return result


@router.post("/check/security-headers", response_model=SecurityHeadersResponse)
async def check_security_headers(
    request: SecurityHeadersRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """HTTP 보안 헤더를 확인합니다."""
    service = MonitoringService(db)
    result = await service.check_security_headers(
        url=request.url,
        timeout=request.timeout,
    )
    return result


@router.get("/check/deep/{project_id}", response_model=PlaywrightCheckResponse)
async def check_deep_monitoring(
    project_id: int,
    save_log: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Playwright를 사용한 심층 모니터링을 수행합니다.

    HTTP 상태 코드 외에도 다음을 체크합니다:
    - DOM 로드 상태
    - JavaScript 에러
    - 페이지 성능 메트릭 (FCP, LCP)
    - 리소스 로드 상태
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    service = PlaywrightMonitorService(db)
    metrics = await service.monitor_project(project_id, save_log=save_log)

    return PlaywrightCheckResponse(
        project_id=project_id,
        url=str(project.url),
        is_available=metrics.is_available,
        status_code=metrics.status_code,
        response_time=metrics.response_time,
        error_message=metrics.error_message,
        performance=PlaywrightPerformance(
            dom_content_loaded=metrics.dom_content_loaded,
            page_load_time=metrics.page_load_time,
            first_contentful_paint=metrics.first_contentful_paint,
            largest_contentful_paint=metrics.largest_contentful_paint,
            time_to_first_byte=metrics.time_to_first_byte,
            cumulative_layout_shift=metrics.cumulative_layout_shift,
            total_blocking_time=metrics.total_blocking_time
        ),
        health=PlaywrightHealth(
            is_dom_ready=metrics.is_dom_ready,
            is_js_healthy=metrics.is_js_healthy,
            js_errors=metrics.js_errors or [],
            console_errors=metrics.console_errors
        ),
        resources=PlaywrightResources(
            count=metrics.resource_count,
            size=metrics.resource_size,
            failed=metrics.failed_resources
        ),
        network=PlaywrightNetwork(
            redirect_count=metrics.redirect_count
        ),
        memory=PlaywrightMemory(
            js_heap_size=metrics.js_heap_size
        ),
        checked_at=datetime.now(timezone.utc)
    )


@router.post("/check/synthetic", response_model=SyntheticTestResponse)
async def run_synthetic_test(
    request: SyntheticTestRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Synthetic 모니터링 시나리오를 실행합니다.

    사용자가 정의한 시나리오(스텝 목록)를 Playwright로 순차 실행하여
    로그인, 폼 제출, 페이지 이동 등의 사용자 시나리오를 테스트합니다.

    지원 액션: navigate, click, type, select, wait, screenshot,
    assert_text, assert_element, assert_url
    """
    service = PlaywrightMonitorService(db)
    result = await service.run_synthetic_test(
        name=request.name,
        start_url=request.start_url,
        steps=request.steps,
        timeout=request.timeout,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
    )
    return result
