"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 ThrottleRequests 미들웨어와 유사한 역할을 합니다.
# 인메모리 슬라이딩 윈도우 방식으로 API 요청 속도를 제한합니다.
#
# Laravel과의 주요 차이점:
# 1. Starlette BaseHTTPMiddleware 사용 (Laravel의 Middleware 클래스와 유사)
# 2. 인메모리 딕셔너리 기반 (Laravel은 캐시 드라이버 사용)
# 3. X-RateLimit 헤더로 남은 요청 수 전달
#
# 주요 기능:
# 1. IP 기반 Rate Limiting (슬라이딩 윈도우)
# 2. 엔드포인트별 차등 제한 (로그인 등 민감 API는 더 엄격)
# 3. 정적 파일/health check 제외
# 4. 429 Too Many Requests 응답 반환
"""

import time
import logging
from collections import defaultdict
from threading import Lock

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 요청 속도 제한 미들웨어

    슬라이딩 윈도우 방식으로 IP별 요청 횟수를 제한합니다.
    """

    # Rate Limiting 제외 경로
    EXCLUDED_PREFIXES = (
        "/frontend/",
        "/health",
        "/favicon.ico",
        "/test_frontend/",
    )

    # 엔드포인트별 제한 설정 (window_seconds, max_requests)
    STRICT_ENDPOINTS = {
        "/api/v1/auth/login": (60, 10),       # 로그인: 분당 10회
        "/api/v1/auth/register": (60, 5),      # 회원가입: 분당 5회
        "/api/v1/auth/me/password": (60, 5),   # 비밀번호 변경: 분당 5회
    }

    # 기본 제한: 60초에 120회
    DEFAULT_WINDOW = 60
    DEFAULT_MAX_REQUESTS = 120

    def __init__(self, app):
        super().__init__(app)
        # IP별 요청 타임스탬프 저장 {ip: {endpoint_key: [timestamps]}}
        self._requests = defaultdict(lambda: defaultdict(list))
        self._lock = Lock()
        # 주기적 정리를 위한 카운터
        self._cleanup_counter = 0

    def _get_client_ip(self, request) -> str:
        """클라이언트 IP 추출 (프록시 헤더 포함)"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_rate_limit(self, path: str) -> tuple:
        """경로에 따른 Rate Limit 설정 반환"""
        for endpoint, limits in self.STRICT_ENDPOINTS.items():
            if path == endpoint:
                return limits
        return (self.DEFAULT_WINDOW, self.DEFAULT_MAX_REQUESTS)

    def _cleanup_old_entries(self, now: float):
        """오래된 요청 기록 정리 (메모리 누수 방지)"""
        max_window = max(
            self.DEFAULT_WINDOW,
            max((w for w, _ in self.STRICT_ENDPOINTS.values()), default=60),
        )
        cutoff = now - max_window - 10

        keys_to_delete = []
        for ip, endpoints in self._requests.items():
            endpoint_keys_to_delete = []
            for endpoint_key, timestamps in endpoints.items():
                # 오래된 타임스탬프 제거
                endpoints[endpoint_key] = [t for t in timestamps if t > cutoff]
                if not endpoints[endpoint_key]:
                    endpoint_keys_to_delete.append(endpoint_key)
            for ek in endpoint_keys_to_delete:
                del endpoints[ek]
            if not endpoints:
                keys_to_delete.append(ip)
        for ip in keys_to_delete:
            del self._requests[ip]

    async def dispatch(self, request, call_next):
        path = request.url.path

        # 제외 경로 체크
        if path.startswith(self.EXCLUDED_PREFIXES):
            return await call_next(request)

        # GET 이외의 API 경로만 체크 (GET은 더 관대하게)
        # 모든 API 요청에 적용
        if not path.startswith("/api/"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        window_seconds, max_requests = self._get_rate_limit(path)
        now = time.time()

        # 엔드포인트 그룹 키 결정
        # 엄격한 엔드포인트는 개별 추적, 나머지는 "default"로 통합
        endpoint_key = path if path in self.STRICT_ENDPOINTS else "default"

        with self._lock:
            # 주기적 정리 (1000 요청마다)
            self._cleanup_counter += 1
            if self._cleanup_counter >= 1000:
                self._cleanup_old_entries(now)
                self._cleanup_counter = 0

            timestamps = self._requests[client_ip][endpoint_key]

            # 윈도우 밖의 오래된 요청 제거
            cutoff = now - window_seconds
            self._requests[client_ip][endpoint_key] = [
                t for t in timestamps if t > cutoff
            ]
            current_count = len(self._requests[client_ip][endpoint_key])

            if current_count >= max_requests:
                # Rate Limit 초과
                retry_after = int(
                    window_seconds - (now - self._requests[client_ip][endpoint_key][0])
                )
                retry_after = max(1, retry_after)

                logger.warning(
                    f"Rate limit exceeded: {client_ip} on {path} "
                    f"({current_count}/{max_requests} in {window_seconds}s)"
                )

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + retry_after)),
                    },
                )

            # 요청 기록 추가
            self._requests[client_ip][endpoint_key].append(now)
            remaining = max_requests - current_count - 1

        # 정상 요청 처리
        response = await call_next(request)

        # Rate Limit 헤더 추가
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + window_seconds))

        return response
