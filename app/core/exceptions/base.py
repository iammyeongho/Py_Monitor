"""
커스텀 예외 베이스 클래스

애플리케이션 전용 예외 클래스를 정의합니다.
HTTP 상태 코드와 에러 메시지를 포함하여
API 계층에서 일관된 에러 응답을 생성할 수 있습니다.

클린 아키텍처 원칙:
- 비즈니스 로직 예외를 HTTP 예외와 분리
- Service 계층에서 도메인 예외 발생
- API 계층에서 HTTP 응답으로 변환
"""

from typing import Any, Optional


class AppException(Exception):
    """
    애플리케이션 기본 예외 클래스

    모든 커스텀 예외의 베이스 클래스입니다.
    HTTP 상태 코드와 상세 정보를 포함합니다.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None
    ):
        """
        예외 초기화

        Args:
            message: 에러 메시지
            status_code: HTTP 상태 코드
            detail: 추가 상세 정보
        """
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """예외 정보를 딕셔너리로 변환"""
        result = {
            "message": self.message,
            "status_code": self.status_code
        }
        if self.detail:
            result["detail"] = self.detail
        return result


class NotFoundError(AppException):
    """
    리소스를 찾을 수 없을 때 발생하는 예외

    사용 예시:
        raise NotFoundError("User", user_id)
        raise NotFoundError("Project", project_id, "해당 프로젝트가 존재하지 않습니다")
    """

    def __init__(
        self,
        resource: str,
        resource_id: Optional[Any] = None,
        message: Optional[str] = None
    ):
        if message is None:
            if resource_id:
                message = f"{resource}(을)를 찾을 수 없습니다: {resource_id}"
            else:
                message = f"{resource}(을)를 찾을 수 없습니다"

        super().__init__(
            message=message,
            status_code=404,
            detail={"resource": resource, "resource_id": resource_id}
        )


class ValidationError(AppException):
    """
    데이터 검증 실패 시 발생하는 예외

    사용 예시:
        raise ValidationError("이메일 형식이 올바르지 않습니다")
        raise ValidationError("비밀번호는 8자 이상이어야 합니다", field="password")
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        errors: Optional[list] = None
    ):
        detail = {}
        if field:
            detail["field"] = field
        if errors:
            detail["errors"] = errors

        super().__init__(
            message=message,
            status_code=400,
            detail=detail if detail else None
        )


class AuthenticationError(AppException):
    """
    인증 실패 시 발생하는 예외

    사용 예시:
        raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")
        raise AuthenticationError("토큰이 만료되었습니다")
    """

    def __init__(self, message: str = "인증에 실패했습니다"):
        super().__init__(
            message=message,
            status_code=401,
            detail={"type": "authentication_error"}
        )


class AuthorizationError(AppException):
    """
    권한 부족 시 발생하는 예외

    사용 예시:
        raise AuthorizationError("이 작업을 수행할 권한이 없습니다")
        raise AuthorizationError("관리자만 접근할 수 있습니다")
    """

    def __init__(self, message: str = "권한이 없습니다"):
        super().__init__(
            message=message,
            status_code=403,
            detail={"type": "authorization_error"}
        )


class ConflictError(AppException):
    """
    리소스 충돌 시 발생하는 예외

    사용 예시:
        raise ConflictError("이미 등록된 이메일입니다")
        raise ConflictError("해당 URL은 이미 등록되어 있습니다", field="url")
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None
    ):
        detail = {"type": "conflict_error"}
        if field:
            detail["field"] = field

        super().__init__(
            message=message,
            status_code=409,
            detail=detail
        )


class BusinessRuleError(AppException):
    """
    비즈니스 규칙 위반 시 발생하는 예외

    사용 예시:
        raise BusinessRuleError("프로젝트 생성 한도를 초과했습니다")
        raise BusinessRuleError("비활성 사용자는 프로젝트를 생성할 수 없습니다")
    """

    def __init__(self, message: str, rule: Optional[str] = None):
        detail = {"type": "business_rule_error"}
        if rule:
            detail["rule"] = rule

        super().__init__(
            message=message,
            status_code=422,
            detail=detail
        )


class ExternalServiceError(AppException):
    """
    외부 서비스 오류 시 발생하는 예외

    사용 예시:
        raise ExternalServiceError("이메일 발송에 실패했습니다", service="smtp")
        raise ExternalServiceError("모니터링 대상에 연결할 수 없습니다", service="http")
    """

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        detail = {"type": "external_service_error"}
        if service:
            detail["service"] = service
        if original_error:
            detail["original_error"] = str(original_error)

        super().__init__(
            message=message,
            status_code=502,
            detail=detail
        )
