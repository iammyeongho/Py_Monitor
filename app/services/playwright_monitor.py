"""
Playwright 기반 심층 웹사이트 모니터링 서비스

HTTP 상태 코드만으로는 감지할 수 없는 문제들을 체크:
- JavaScript 에러
- DOM 로드 실패
- 페이지 성능 메트릭 (FCP, LCP 등)
- 리소스 로드 실패
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringLog
from app.models.project import Project


@dataclass
class PlaywrightMetrics:
    """Playwright 모니터링 결과"""
    is_available: bool = False
    status_code: Optional[int] = None
    response_time: float = 0.0
    error_message: Optional[str] = None

    # 성능 메트릭
    dom_content_loaded: Optional[float] = None  # ms
    page_load_time: Optional[float] = None  # ms
    first_contentful_paint: Optional[float] = None  # ms
    largest_contentful_paint: Optional[float] = None  # ms
    time_to_first_byte: Optional[float] = None  # ms (TTFB)
    cumulative_layout_shift: Optional[float] = None  # CLS
    total_blocking_time: Optional[float] = None  # ms (TBT)

    # JavaScript 건강 상태
    js_errors: List[str] = None
    console_errors: int = 0
    is_js_healthy: bool = True

    # 리소스 정보
    resource_count: int = 0
    resource_size: int = 0  # bytes
    failed_resources: int = 0  # 로드 실패한 리소스 개수

    # 네트워크 정보
    redirect_count: int = 0  # 리다이렉트 횟수

    # 메모리 정보
    js_heap_size: Optional[int] = None  # bytes

    # DOM 상태
    is_dom_ready: bool = False

    def __post_init__(self):
        if self.js_errors is None:
            self.js_errors = []


class PlaywrightMonitorService:
    """Playwright 기반 심층 모니터링 서비스"""

    def __init__(self, db: Session):
        self.db = db

    async def check_website(self, url: str, timeout: int = 30000) -> PlaywrightMetrics:
        """웹사이트 심층 체크"""
        metrics = PlaywrightMetrics()
        start_time = time.time()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )

                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='PyMonitor/1.0 (Playwright Health Check)'
                )

                page = await context.new_page()

                # JavaScript 에러 수집
                js_errors = []
                page.on('pageerror', lambda error: js_errors.append(str(error)))

                # 콘솔 에러 수집
                console_errors = []
                page.on('console', lambda msg: console_errors.append(msg) if msg.type == 'error' else None)

                # 리소스 추적
                resources = []
                failed_resources = []

                def track_response(response):
                    resources.append({
                        'url': response.url,
                        'status': response.status,
                        'size': 0
                    })
                    # 실패한 리소스 추적 (4xx, 5xx)
                    if response.status >= 400:
                        failed_resources.append({
                            'url': response.url,
                            'status': response.status
                        })

                page.on('response', track_response)

                # 리다이렉트 추적
                redirect_chain = []
                page.on('request', lambda req: redirect_chain.append(req.url) if req.redirected_from else None)

                try:
                    # 페이지 로드
                    response = await page.goto(
                        url,
                        wait_until='networkidle',
                        timeout=timeout
                    )

                    if response:
                        metrics.status_code = response.status
                        metrics.is_available = 200 <= response.status < 400

                    # 응답 시간 계산
                    metrics.response_time = time.time() - start_time

                    # Performance 메트릭 수집
                    try:
                        performance = await page.evaluate('''() => {
                            const timing = performance.timing;
                            const paintEntries = performance.getEntriesByType('paint');
                            const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                            const layoutShiftEntries = performance.getEntriesByType('layout-shift');

                            let fcp = null;
                            let lcp = null;
                            let cls = 0;

                            for (const entry of paintEntries) {
                                if (entry.name === 'first-contentful-paint') {
                                    fcp = entry.startTime;
                                }
                            }

                            if (lcpEntries.length > 0) {
                                lcp = lcpEntries[lcpEntries.length - 1].startTime;
                            }

                            // CLS 계산 (hadRecentInput이 false인 것만)
                            for (const entry of layoutShiftEntries) {
                                if (!entry.hadRecentInput) {
                                    cls += entry.value;
                                }
                            }

                            // TTFB 계산
                            const ttfb = timing.responseStart - timing.requestStart;

                            return {
                                domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                                pageLoadTime: timing.loadEventEnd - timing.navigationStart,
                                fcp: fcp,
                                lcp: lcp,
                                ttfb: ttfb,
                                cls: cls
                            };
                        }''')

                        metrics.dom_content_loaded = performance.get('domContentLoaded')
                        metrics.page_load_time = performance.get('pageLoadTime')
                        metrics.first_contentful_paint = performance.get('fcp')
                        metrics.largest_contentful_paint = performance.get('lcp')
                        metrics.time_to_first_byte = performance.get('ttfb')
                        metrics.cumulative_layout_shift = performance.get('cls')

                    except Exception as perf_error:
                        print(f"Performance 메트릭 수집 실패: {perf_error}")

                    # 메모리 사용량 수집
                    try:
                        memory_info = await page.evaluate('''() => {
                            if (performance.memory) {
                                return {
                                    jsHeapSize: performance.memory.usedJSHeapSize
                                };
                            }
                            return null;
                        }''')
                        if memory_info:
                            metrics.js_heap_size = memory_info.get('jsHeapSize')
                    except Exception as mem_error:
                        print(f"메모리 정보 수집 실패: {mem_error}")

                    # DOM 상태 확인 (body 존재 여부)
                    try:
                        body_exists = await page.evaluate('() => document.body !== null && document.body.innerHTML.length > 0')
                        metrics.is_dom_ready = body_exists
                    except:
                        metrics.is_dom_ready = False

                    # JavaScript 에러 정리
                    metrics.js_errors = js_errors
                    metrics.console_errors = len(console_errors)
                    metrics.is_js_healthy = len(js_errors) == 0

                    # 리소스 정보
                    metrics.resource_count = len(resources)
                    metrics.failed_resources = len(failed_resources)

                    # 리다이렉트 횟수
                    metrics.redirect_count = len(redirect_chain)

                    # 전체 가용성 판단 (HTTP OK + DOM Ready + JS Healthy)
                    if metrics.is_available:
                        if not metrics.is_dom_ready:
                            metrics.is_available = False
                            metrics.error_message = "DOM이 정상적으로 로드되지 않았습니다"
                        elif not metrics.is_js_healthy:
                            # JS 에러가 있어도 페이지는 사용 가능할 수 있음
                            # 하지만 경고 표시
                            metrics.error_message = f"JavaScript 에러 {len(js_errors)}개 감지"

                except Exception as page_error:
                    metrics.is_available = False
                    metrics.error_message = str(page_error)
                    metrics.response_time = time.time() - start_time

                await browser.close()

        except Exception as e:
            metrics.is_available = False
            metrics.error_message = f"Playwright 실행 오류: {str(e)}"
            metrics.response_time = time.time() - start_time

        return metrics

    async def monitor_project(self, project_id: int, save_log: bool = True) -> PlaywrightMetrics:
        """프로젝트 모니터링 실행"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return PlaywrightMetrics(
                is_available=False,
                error_message="프로젝트를 찾을 수 없습니다"
            )

        url = str(project.url)
        metrics = await self.check_website(url)

        if save_log:
            self._save_log(project_id, metrics)

        return metrics

    def _save_log(self, project_id: int, metrics: PlaywrightMetrics):
        """모니터링 결과를 DB에 저장"""
        log = MonitoringLog(
            project_id=project_id,
            check_type="playwright",
            status_code=metrics.status_code,
            response_time=metrics.response_time,
            is_available=metrics.is_available,
            error_message=metrics.error_message,
            dom_content_loaded=metrics.dom_content_loaded,
            page_load_time=metrics.page_load_time,
            first_contentful_paint=metrics.first_contentful_paint,
            largest_contentful_paint=metrics.largest_contentful_paint,
            time_to_first_byte=metrics.time_to_first_byte,
            cumulative_layout_shift=metrics.cumulative_layout_shift,
            total_blocking_time=metrics.total_blocking_time,
            js_errors=json.dumps(metrics.js_errors) if metrics.js_errors else None,
            console_errors=metrics.console_errors,
            resource_count=metrics.resource_count,
            resource_size=metrics.resource_size,
            failed_resources=metrics.failed_resources,
            redirect_count=metrics.redirect_count,
            js_heap_size=metrics.js_heap_size,
            is_dom_ready=metrics.is_dom_ready,
            is_js_healthy=metrics.is_js_healthy,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(log)
        self.db.commit()

    async def close(self):
        """서비스 종료 (리소스 정리)"""
        # Playwright는 매 호출시 브라우저를 열고 닫으므로 별도 정리 불필요
        pass

    def get_metrics_dict(self, metrics: PlaywrightMetrics) -> dict:
        """메트릭을 딕셔너리로 변환"""
        return {
            "is_available": metrics.is_available,
            "status_code": metrics.status_code,
            "response_time": round(metrics.response_time, 3),
            "error_message": metrics.error_message,
            "performance": {
                "dom_content_loaded": metrics.dom_content_loaded,
                "page_load_time": metrics.page_load_time,
                "first_contentful_paint": metrics.first_contentful_paint,
                "largest_contentful_paint": metrics.largest_contentful_paint,
                "time_to_first_byte": metrics.time_to_first_byte,
                "cumulative_layout_shift": metrics.cumulative_layout_shift,
                "total_blocking_time": metrics.total_blocking_time
            },
            "health": {
                "is_dom_ready": metrics.is_dom_ready,
                "is_js_healthy": metrics.is_js_healthy,
                "js_errors": metrics.js_errors,
                "console_errors": metrics.console_errors
            },
            "resources": {
                "count": metrics.resource_count,
                "size": metrics.resource_size,
                "failed": metrics.failed_resources
            },
            "network": {
                "redirect_count": metrics.redirect_count
            },
            "memory": {
                "js_heap_size": metrics.js_heap_size
            }
        }
