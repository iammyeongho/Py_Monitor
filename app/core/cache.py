"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 Cache 파사드와 유사한 역할을 합니다.
# Redis가 사용 가능하면 Redis를, 아니면 인메모리 캐시를 사용합니다.
#
# Laravel과의 주요 차이점:
# 1. Cache.get() = Laravel의 Cache::get()과 유사
# 2. Cache.set() = Laravel의 Cache::put()과 유사
# 3. Cache.delete() = Laravel의 Cache::forget()과 유사
# 4. Cache.clear() = Laravel의 Cache::flush()와 유사
#
# 주요 기능:
# 1. Redis 캐시 (REDIS_ENABLED=true일 때)
# 2. 인메모리 캐시 (Redis 미사용 시 폴백)
# 3. TTL 기반 자동 만료
# 4. JSON 직렬화/역직렬화
"""

import json
import logging
import time
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryCache:
    """인메모리 캐시 (Redis 폴백용)"""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._cleanup_interval = 100  # 매 100번 접근마다 만료 항목 정리
        self._access_count = 0

    def get(self, key: str) -> Optional[str]:
        """캐시 조회"""
        self._maybe_cleanup()
        item = self._store.get(key)
        if item is None:
            return None
        value, expire_at = item
        if expire_at and time.time() > expire_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        """캐시 저장"""
        expire_at = time.time() + ttl if ttl > 0 else 0
        self._store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        """캐시 삭제"""
        self._store.pop(key, None)

    def clear(self) -> None:
        """전체 캐시 삭제"""
        self._store.clear()

    def _maybe_cleanup(self):
        """만료된 항목 주기적 정리"""
        self._access_count += 1
        if self._access_count % self._cleanup_interval == 0:
            now = time.time()
            expired_keys = [
                k for k, (_, exp) in self._store.items()
                if exp and now > exp
            ]
            for k in expired_keys:
                del self._store[k]


class RedisCache:
    """Redis 기반 캐시"""

    def __init__(self):
        self._client = None
        self._connected = False

    def _get_client(self):
        """Redis 클라이언트 반환 (lazy 초기화)"""
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                # 연결 테스트
                self._client.ping()
                self._connected = True
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self._connected = False
                self._client = None
        return self._client

    def get(self, key: str) -> Optional[str]:
        """캐시 조회"""
        client = self._get_client()
        if not client:
            return None
        try:
            return client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        """캐시 저장"""
        client = self._get_client()
        if not client:
            return
        try:
            client.setex(key, ttl, value)
        except Exception:
            pass

    def delete(self, key: str) -> None:
        """캐시 삭제"""
        client = self._get_client()
        if not client:
            return
        try:
            client.delete(key)
        except Exception:
            pass

    def clear(self) -> None:
        """전체 캐시 삭제"""
        client = self._get_client()
        if not client:
            return
        try:
            client.flushdb()
        except Exception:
            pass

    @property
    def is_connected(self) -> bool:
        return self._connected


class CacheManager:
    """
    캐시 관리자 (Redis + InMemory 폴백)

    사용 예시:
        from app.core.cache import cache
        cache.set_json("status:1", {"uptime": 99.9}, ttl=60)
        data = cache.get_json("status:1")
    """

    def __init__(self):
        self._memory = InMemoryCache()
        self._redis: Optional[RedisCache] = None

        if settings.REDIS_ENABLED:
            self._redis = RedisCache()

    @property
    def _backend(self):
        """현재 사용 중인 캐시 백엔드"""
        if self._redis and self._redis.is_connected:
            return self._redis
        return self._memory

    def get(self, key: str) -> Optional[str]:
        """캐시에서 문자열 조회"""
        return self._backend.get(key)

    def set(self, key: str, value: str, ttl: int = None) -> None:
        """캐시에 문자열 저장"""
        if ttl is None:
            ttl = settings.CACHE_DEFAULT_TTL
        self._backend.set(key, value, ttl)

    def delete(self, key: str) -> None:
        """캐시 항목 삭제"""
        self._backend.delete(key)
        # Redis와 메모리 양쪽 모두 삭제
        if self._redis and self._backend != self._memory:
            self._memory.delete(key)

    def clear(self) -> None:
        """전체 캐시 삭제"""
        self._memory.clear()
        if self._redis:
            self._redis.clear()

    def get_json(self, key: str) -> Optional[Any]:
        """캐시에서 JSON 객체 조회"""
        raw = self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_json(self, key: str, value: Any, ttl: int = None) -> None:
        """캐시에 JSON 객체 저장"""
        try:
            raw = json.dumps(value, default=str)
            self.set(key, raw, ttl)
        except (TypeError, ValueError):
            pass

    @property
    def backend_name(self) -> str:
        """현재 백엔드 이름"""
        if self._redis and self._redis.is_connected:
            return "redis"
        return "memory"


# 글로벌 캐시 인스턴스
cache = CacheManager()
