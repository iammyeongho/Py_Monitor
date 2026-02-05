"""
Playwright 기반 심층 웹사이트 모니터링 서비스

HTTP 상태 코드만으로는 감지할 수 없는 문제들을 체크:
- JavaScript 에러
- DOM 로드 실패
- 페이지 성능 메트릭 (FCP, LCP 등)
- 리소스 로드 실패
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringLog
from app.models.project import Project
from app.schemas.monitoring import (
    SyntheticStepResult,
    SyntheticTestResponse,
)

logger = logging.getLogger(__name__)


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
                        body_exists = await page.evaluate(
                            '() => document.body !== null && document.body.innerHTML.length > 0'
                        )
                        metrics.is_dom_ready = body_exists
                    except Exception:
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

    async def run_synthetic_test(
        self,
        name: str,
        start_url: str,
        steps: list,
        timeout: int = 30000,
        viewport_width: int = 1280,
        viewport_height: int = 800,
    ) -> SyntheticTestResponse:
        """Synthetic 시나리오 테스트 실행

        사용자가 정의한 시나리오(스텝 목록)를 Playwright로 순차 실행합니다.
        각 스텝은 navigate, click, type, select, wait, assert 등의 액션을 수행합니다.
        """
        step_results = []
        total_start = time.time()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"]
                )
                context = await browser.new_context(
                    viewport={"width": viewport_width, "height": viewport_height},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36 PyMonitor/Synthetic"
                    ),
                )
                page = await context.new_page()
                page.set_default_timeout(timeout)

                # 시작 URL로 이동
                navigate_start = time.time()
                try:
                    await page.goto(start_url, wait_until="domcontentloaded")
                    step_results.append(SyntheticStepResult(
                        step_number=0,
                        action="navigate",
                        description=f"시작 URL: {start_url}",
                        passed=True,
                        duration_ms=round((time.time() - navigate_start) * 1000, 2),
                        current_url=page.url,
                    ))
                except Exception as e:
                    step_results.append(SyntheticStepResult(
                        step_number=0,
                        action="navigate",
                        description=f"시작 URL: {start_url}",
                        passed=False,
                        duration_ms=round((time.time() - navigate_start) * 1000, 2),
                        error_message=str(e),
                    ))
                    await browser.close()
                    return self._build_response(name, start_url, steps, step_results, total_start)

                # 각 스텝 순차 실행
                for i, step in enumerate(steps):
                    step_start = time.time()
                    step_num = i + 1
                    action = step.action
                    selector = step.selector
                    value = step.value
                    description = step.description or f"Step {step_num}: {action}"

                    try:
                        if action == "navigate":
                            await page.goto(value, wait_until="domcontentloaded")

                        elif action == "click":
                            await page.click(selector)
                            # 클릭 후 네비게이션 대기 (짧게)
                            try:
                                await page.wait_for_load_state("domcontentloaded", timeout=5000)
                            except Exception:
                                pass  # 페이지 전환이 아닌 클릭도 있음

                        elif action == "type":
                            await page.fill(selector, value or "")

                        elif action == "select":
                            await page.select_option(selector, value)

                        elif action == "wait":
                            wait_ms = int(value) if value else 1000
                            await page.wait_for_timeout(wait_ms)

                        elif action == "screenshot":
                            # 스크린샷은 응답에 경로만 포함 (실제 저장은 생략)
                            pass

                        elif action == "assert_text":
                            # 페이지에서 텍스트 존재 확인
                            content = await page.content()
                            if value not in content:
                                raise AssertionError(
                                    f"텍스트 '{value}'를 찾을 수 없습니다"
                                )

                        elif action == "assert_element":
                            # 요소 존재 확인
                            element = await page.query_selector(selector)
                            if not element:
                                raise AssertionError(
                                    f"요소 '{selector}'를 찾을 수 없습니다"
                                )

                        elif action == "assert_url":
                            current_url = page.url
                            if value not in current_url:
                                raise AssertionError(
                                    f"URL에 '{value}'가 포함되지 않습니다 (현재: {current_url})"
                                )

                        step_results.append(SyntheticStepResult(
                            step_number=step_num,
                            action=action,
                            description=description,
                            passed=True,
                            duration_ms=round((time.time() - step_start) * 1000, 2),
                            current_url=page.url,
                        ))

                    except Exception as e:
                        step_results.append(SyntheticStepResult(
                            step_number=step_num,
                            action=action,
                            description=description,
                            passed=False,
                            duration_ms=round((time.time() - step_start) * 1000, 2),
                            error_message=str(e),
                            current_url=page.url if page else None,
                        ))
                        # 스텝 실패 시 이후 스텝은 건너뜀
                        for j in range(i + 1, len(steps)):
                            remaining = steps[j]
                            step_results.append(SyntheticStepResult(
                                step_number=j + 1,
                                action=remaining.action,
                                description=remaining.description or f"Step {j + 1}: {remaining.action}",
                                passed=False,
                                error_message="이전 스텝 실패로 건너뜀",
                            ))
                        break

                await browser.close()

        except ImportError:
            return SyntheticTestResponse(
                name=name,
                start_url=start_url,
                total_steps=len(steps) + 1,
                passed_steps=0,
                failed_steps=len(steps) + 1,
                all_passed=False,
                total_duration_ms=round((time.time() - total_start) * 1000, 2),
                error_message="Playwright가 설치되지 않았습니다. 'pip install playwright && playwright install' 실행 필요",
            )
        except Exception as e:
            logger.error(f"Synthetic test error: {str(e)}")
            return SyntheticTestResponse(
                name=name,
                start_url=start_url,
                total_steps=len(steps) + 1,
                passed_steps=sum(1 for r in step_results if r.passed),
                failed_steps=len(steps) + 1 - sum(1 for r in step_results if r.passed),
                all_passed=False,
                total_duration_ms=round((time.time() - total_start) * 1000, 2),
                step_results=step_results,
                error_message=str(e),
            )

        return self._build_response(name, start_url, steps, step_results, total_start)

    def _build_response(
        self, name, start_url, steps, step_results, total_start
    ) -> SyntheticTestResponse:
        """Synthetic 테스트 결과 응답 구성"""
        passed = sum(1 for r in step_results if r.passed)
        total = len(steps) + 1  # 시작 navigate 포함
        failed = total - passed

        return SyntheticTestResponse(
            name=name,
            start_url=start_url,
            total_steps=total,
            passed_steps=passed,
            failed_steps=failed,
            all_passed=failed == 0,
            total_duration_ms=round((time.time() - total_start) * 1000, 2),
            step_results=step_results,
        )

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
