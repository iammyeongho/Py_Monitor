"""
예외 핸들러

FastAPI 애플리케이션의 전역 예외 핸들러를 정의합니다.
커스텀 예외를 HTTP 응답으로 변환합니다.

사용 방법:
    from app.core.exceptions.handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
"""

import logging
from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions.base import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException
) -> JSONResponse:
    """
    애플리케이션 예외 핸들러

    커스텀 예외를 JSON 응답으로 변환합니다.
    """
    logger.warning(
        f"AppException: {exc.message} | "
        f"Status: {exc.status_code} | "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        }
    )


async def not_found_handler(
    request: Request,
    exc: NotFoundError
) -> JSONResponse:
    """NotFoundError 핸들러"""
    logger.info(f"NotFound: {exc.message} | Path: {request.url.path}")

    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        }
    )


async def validation_error_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """ValidationError 핸들러"""
    logger.warning(f"Validation: {exc.message} | Path: {request.url.path}")

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        }
    )


async def authentication_error_handler(
    request: Request,
    exc: AuthenticationError
) -> JSONResponse:
    """AuthenticationError 핸들러"""
    logger.warning(f"Auth: {exc.message} | Path: {request.url.path}")

    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        },
        headers={"WWW-Authenticate": "Bearer"}
    )


async def authorization_error_handler(
    request: Request,
    exc: AuthorizationError
) -> JSONResponse:
    """AuthorizationError 핸들러"""
    logger.warning(f"Forbidden: {exc.message} | Path: {request.url.path}")

    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        }
    )


async def conflict_error_handler(
    request: Request,
    exc: ConflictError
) -> JSONResponse:
    """ConflictError 핸들러"""
    logger.warning(f"Conflict: {exc.message} | Path: {request.url.path}")

    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "message": exc.message,
            "detail": exc.detail,
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    일반 예외 핸들러

    처리되지 않은 예외를 500 에러로 변환합니다.
    프로덕션 환경에서는 상세 정보를 숨깁니다.
    """
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)} | "
        f"Path: {request.url.path}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "서버 내부 오류가 발생했습니다",
            "detail": None,
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    예외 핸들러 등록

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # 커스텀 예외 핸들러 등록
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(ConflictError, conflict_error_handler)

    # 기본 AppException 핸들러
    app.add_exception_handler(AppException, app_exception_handler)

    # 처리되지 않은 예외 핸들러 (선택적)
    # app.add_exception_handler(Exception, generic_exception_handler)
