"""
커스텀 예외 클래스 패키지

애플리케이션 전용 예외 클래스를 정의합니다.
클린 아키텍처 원칙에 따라 비즈니스 로직에서 발생하는 예외를
HTTP 예외와 분리하여 관리합니다.

사용 예시:
    from app.core.exceptions import NotFoundError, ValidationError

    if not user:
        raise NotFoundError("User", user_id)
"""

from app.core.exceptions.base import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "AppException",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "BusinessRuleError",
    "ExternalServiceError",
]
