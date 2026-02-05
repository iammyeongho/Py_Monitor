"""
# Laravel 개발자를 위한 설명
# 이 파일은 Laravel의 MonitoringService와 유사한 역할을 합니다.
# FastAPI를 사용하여 모니터링 서비스를 정의합니다.
#
# Laravel과의 주요 차이점:
# 1. async/await = Laravel의 비동기 처리와 유사
# 2. aiohttp = Laravel의 HTTP 클라이언트와 유사
# 3. ssl = Laravel의 SSL 검증과 유사
#
# 추가 기능:
# 4. TCP 포트 체크 - 특정 포트 연결 가능 여부 확인
# 5. DNS 조회 - 도메인 DNS 레코드 확인
# 6. 콘텐츠 검증 - 응답에 특정 문자열 포함 여부 확인
# 7. 보안 헤더 체크 - HTTP 보안 헤더 존재 여부 확인
"""

import asyncio
import dns.resolver
import json
import logging
import socket
import ssl
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
import whois
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.monitoring import MonitoringAlert, MonitoringLog, MonitoringSetting
from app.models.project import Project
from app.models.ssl_domain import SSLDomainStatus
from app.schemas.monitoring import (
    APIEndpointCheckResponse,
    APIEndpointValidation,
    ContentCheckResponse,
    DNSLookupResponse,
    DNSRecord,
    MonitoringAlertCreate,
    MonitoringLogCreate,
    MonitoringResponse,
    MonitoringSettingCreate,
    MonitoringSettingUpdate,
    MonitoringStatus,
    SecurityHeader,
    SecurityHeadersResponse,
    SSLDomainStatusCreate,
    SSLStatus,
    TCPPortCheckResponse,
    UDPPortCheckResponse,
)
from app.utils.notifications import NotificationService

logger = logging.getLogger(__name__)


def create_monitoring_log(db: Session, log: MonitoringLogCreate) -> MonitoringLog:
    """모니터링 로그 생성"""
    db_log = MonitoringLog(
        project_id=log.project_id,
        status_code=log.status_code,
        response_time=log.response_time,
        is_available=log.is_available,
        error_message=log.error_message,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_monitoring_logs(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> List[MonitoringLog]:
    """프로젝트의 모니터링 로그 조회"""
    return (
        db.query(MonitoringLog)
        .filter(MonitoringLog.project_id == project_id)
        .order_by(MonitoringLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_monitoring_alert(
    db: Session, alert: MonitoringAlertCreate
) -> MonitoringAlert:
    """모니터링 알림 생성"""
    db_alert = MonitoringAlert(
        project_id=alert.project_id,
        alert_type=alert.alert_type,
        message=alert.message,
        is_resolved=False,
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_monitoring_alerts(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> List[MonitoringAlert]:
    """프로젝트의 모니터링 알림 조회"""
    return (
        db.query(MonitoringAlert)
        .filter(MonitoringAlert.project_id == project_id)
        .order_by(MonitoringAlert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_monitoring_alert(
    db: Session, alert_id: int, alert: MonitoringAlertCreate
) -> Optional[MonitoringAlert]:
    """모니터링 알림 업데이트"""
    db_alert = db.query(MonitoringAlert).filter(MonitoringAlert.id == alert_id).first()
    if not db_alert:
        return None

    for key, value in alert.dict().items():
        setattr(db_alert, key, value)

    db_alert.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_alert)
    return db_alert


def create_monitoring_setting(
    db: Session, setting: MonitoringSettingCreate
) -> MonitoringSetting:
    """모니터링 설정 생성"""
    db_setting = MonitoringSetting(
        project_id=setting.project_id,
        check_interval=setting.check_interval,
        timeout=setting.timeout,
        retry_count=setting.retry_count,
        alert_threshold=setting.alert_threshold,
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


def get_monitoring_setting(db: Session, project_id: int) -> Optional[MonitoringSetting]:
    """프로젝트의 모니터링 설정 조회"""
    return (
        db.query(MonitoringSetting)
        .filter(MonitoringSetting.project_id == project_id)
        .first()
    )


def update_monitoring_setting(
    db: Session, setting_id: int, setting: MonitoringSettingCreate
) -> Optional[MonitoringSetting]:
    """모니터링 설정 업데이트"""
    db_setting = (
        db.query(MonitoringSetting).filter(MonitoringSetting.id == setting_id).first()
    )
    if not db_setting:
        return None

    for key, value in setting.dict().items():
        setattr(db_setting, key, value)

    db_setting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_setting)
    return db_setting


class MonitoringService:
    """모니터링 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self._monitoring_tasks: Dict[int, asyncio.Task] = {}
        self.notification_service = NotificationService()

    async def check_project_status(self, project_id: int) -> MonitoringStatus:
        """프로젝트 상태 확인"""
        import json

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 커스텀 헤더 파싱
        headers = {}
        if project.custom_headers:
            try:
                headers = json.loads(project.custom_headers)
            except json.JSONDecodeError:
                logger.warning(f"Invalid custom headers JSON for project {project_id}")

        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                async with session.get(
                    project.url, timeout=30, headers=headers
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()

                    # 콘텐츠 변경 감지를 위해 본문 읽기
                    content = None
                    try:
                        content = await response.text()
                    except Exception:
                        pass  # 콘텐츠 읽기 실패는 무시

                    return MonitoringStatus(
                        is_available=True,
                        response_time=response_time,
                        status_code=response.status,
                        error_message=None,
                        content=content,
                    )
        except Exception as e:
            logger.error(f"Error checking project {project_id}: {str(e)}")
            return MonitoringStatus(
                is_available=False,
                response_time=None,
                status_code=None,
                error_message=str(e),
                content=None,
            )

    async def check_ssl_status(self, project: Project) -> dict:
        """SSL 인증서 상태 확인"""
        try:
            hostname = project.url.split("//")[-1].split("/")[0]
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    expiry_date = datetime.strptime(
                        cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
                    )

                    return {
                        "is_valid": True,
                        "expiry_date": expiry_date,
                        "error_message": None,
                    }
        except Exception as e:
            logger.error(f"Error checking SSL for project {project.id}: {str(e)}")
            return {"is_valid": False, "expiry_date": None, "error_message": str(e)}

    async def check_domain_expiry(self, project: Project) -> Optional[datetime]:
        """도메인 만료일 확인

        Returns:
            만료일 datetime 또는 None (오류/정보 없음)
        """
        try:
            domain = project.url.split("//")[-1].split("/")[0]
            w = whois.whois(domain)
            expiry = w.expiration_date

            if expiry is None:
                return None

            # python-whois는 리스트로 반환하는 경우가 있음
            if isinstance(expiry, list):
                expiry = expiry[0] if expiry else None

            return expiry
        except Exception as e:
            logger.error(
                f"Error checking domain expiry for project {project.id}: {str(e)}"
            )
            return None

    async def check_tcp_port(
        self, host: str, port: int, timeout: int = 5
    ) -> TCPPortCheckResponse:
        """TCP 포트 연결 가능 여부 확인"""
        start_time = datetime.now()
        try:
            # 비동기로 소켓 연결 시도
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            await loop.run_in_executor(None, sock.connect, (host, port))
            response_time = (datetime.now() - start_time).total_seconds()
            sock.close()

            return TCPPortCheckResponse(
                host=host,
                port=port,
                is_open=True,
                response_time=response_time,
            )
        except socket.timeout:
            return TCPPortCheckResponse(
                host=host,
                port=port,
                is_open=False,
                error_message="Connection timed out",
            )
        except ConnectionRefusedError:
            return TCPPortCheckResponse(
                host=host,
                port=port,
                is_open=False,
                error_message="Connection refused",
            )
        except Exception as e:
            logger.error(f"Error checking TCP port {host}:{port}: {str(e)}")
            return TCPPortCheckResponse(
                host=host,
                port=port,
                is_open=False,
                error_message=str(e),
            )

    async def check_udp_port(
        self, host: str, port: int, timeout: int = 5
    ) -> UDPPortCheckResponse:
        """UDP 포트 연결 가능 여부 확인

        UDP는 비연결형 프로토콜이므로 TCP와 다르게 동작합니다:
        - ICMP Port Unreachable 응답: 포트 닫힘 (확실)
        - 응답 없음: 포트 열림 또는 필터링됨 (open|filtered)
        - 데이터 응답: 포트 열림 (확실)
        """
        start_time = datetime.now()
        try:
            loop = asyncio.get_event_loop()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)

            # UDP 패킷 전송
            await loop.run_in_executor(
                None, sock.sendto, b'\x00', (host, port)
            )

            # 응답 대기
            try:
                await loop.run_in_executor(None, sock.recv, 1024)
                response_time = (datetime.now() - start_time).total_seconds()
                sock.close()
                # 응답이 있으면 포트가 열려있음
                return UDPPortCheckResponse(
                    host=host,
                    port=port,
                    is_open=True,
                    is_filtered=False,
                    response_time=response_time,
                )
            except socket.timeout:
                response_time = (datetime.now() - start_time).total_seconds()
                sock.close()
                # 타임아웃 = 응답 없음 = open|filtered
                return UDPPortCheckResponse(
                    host=host,
                    port=port,
                    is_open=True,
                    is_filtered=True,
                    response_time=response_time,
                    error_message="open|filtered (응답 없음)",
                )
        except ConnectionRefusedError:
            # ICMP Port Unreachable = 포트 닫힘
            return UDPPortCheckResponse(
                host=host,
                port=port,
                is_open=False,
                is_filtered=False,
                error_message="Port closed (ICMP unreachable)",
            )
        except Exception as e:
            logger.error(f"Error checking UDP port {host}:{port}: {str(e)}")
            return UDPPortCheckResponse(
                host=host,
                port=port,
                is_open=False,
                error_message=str(e),
            )

    async def check_dns_lookup(
        self, domain: str, record_type: str = "A"
    ) -> DNSLookupResponse:
        """DNS 레코드 조회"""
        try:
            loop = asyncio.get_event_loop()
            resolver = dns.resolver.Resolver()
            resolver.timeout = 10
            resolver.lifetime = 10

            # 비동기로 DNS 조회 실행
            answers = await loop.run_in_executor(
                None, lambda: resolver.resolve(domain, record_type)
            )

            records = []
            for rdata in answers:
                records.append(
                    DNSRecord(
                        record_type=record_type,
                        value=str(rdata),
                        ttl=answers.ttl,
                    )
                )

            return DNSLookupResponse(
                domain=domain,
                records=records,
                is_resolved=True,
            )
        except dns.resolver.NXDOMAIN:
            return DNSLookupResponse(
                domain=domain,
                records=[],
                is_resolved=False,
                error_message="Domain does not exist (NXDOMAIN)",
            )
        except dns.resolver.NoAnswer:
            return DNSLookupResponse(
                domain=domain,
                records=[],
                is_resolved=False,
                error_message=f"No {record_type} records found",
            )
        except dns.resolver.Timeout:
            return DNSLookupResponse(
                domain=domain,
                records=[],
                is_resolved=False,
                error_message="DNS query timed out",
            )
        except Exception as e:
            logger.error(f"Error checking DNS for {domain}: {str(e)}")
            return DNSLookupResponse(
                domain=domain,
                records=[],
                is_resolved=False,
                error_message=str(e),
            )

    async def check_content(
        self, url: str, expected_content: str, timeout: int = 30
    ) -> ContentCheckResponse:
        """응답 콘텐츠에 특정 문자열 포함 여부 확인"""
        start_time = datetime.now()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    content = await response.text()

                    # 대소문자 구분 없이 검색
                    is_found = expected_content.lower() in content.lower()

                    return ContentCheckResponse(
                        url=url,
                        expected_content=expected_content,
                        is_found=is_found,
                        response_time=response_time,
                        status_code=response.status,
                    )
        except asyncio.TimeoutError:
            return ContentCheckResponse(
                url=url,
                expected_content=expected_content,
                is_found=False,
                error_message="Request timed out",
            )
        except Exception as e:
            logger.error(f"Error checking content for {url}: {str(e)}")
            return ContentCheckResponse(
                url=url,
                expected_content=expected_content,
                is_found=False,
                error_message=str(e),
            )

    async def check_security_headers(
        self, url: str, timeout: int = 30
    ) -> SecurityHeadersResponse:
        """HTTP 보안 헤더 체크"""
        # 체크할 보안 헤더 목록 및 설명
        security_headers_config = [
            {
                "name": "Strict-Transport-Security",
                "description": "HTTPS 강제 (HSTS)",
                "is_recommended": True,
            },
            {
                "name": "Content-Security-Policy",
                "description": "XSS 및 데이터 삽입 공격 방지",
                "is_recommended": True,
            },
            {
                "name": "X-Content-Type-Options",
                "description": "MIME 타입 스니핑 방지",
                "is_recommended": True,
            },
            {
                "name": "X-Frame-Options",
                "description": "클릭재킹 방지",
                "is_recommended": True,
            },
            {
                "name": "X-XSS-Protection",
                "description": "XSS 필터 활성화 (레거시)",
                "is_recommended": False,
            },
            {
                "name": "Referrer-Policy",
                "description": "리퍼러 정보 제어",
                "is_recommended": True,
            },
            {
                "name": "Permissions-Policy",
                "description": "브라우저 기능 권한 제어",
                "is_recommended": True,
            },
            {
                "name": "Cache-Control",
                "description": "캐시 동작 제어",
                "is_recommended": False,
            },
        ]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    headers_result = []
                    score = 0
                    max_score = 0

                    for header_config in security_headers_config:
                        header_name = header_config["name"]
                        header_value = response.headers.get(header_name)
                        is_present = header_value is not None

                        headers_result.append(
                            SecurityHeader(
                                name=header_name,
                                value=header_value,
                                is_present=is_present,
                                is_recommended=header_config["is_recommended"],
                                description=header_config["description"],
                            )
                        )

                        # 권장 헤더만 점수 계산에 포함
                        if header_config["is_recommended"]:
                            max_score += 1
                            if is_present:
                                score += 1

                    # 0-100 점수로 변환
                    final_score = int((score / max_score) * 100) if max_score > 0 else 0

                    return SecurityHeadersResponse(
                        url=url,
                        headers=headers_result,
                        score=final_score,
                        status_code=response.status,
                    )
        except asyncio.TimeoutError:
            return SecurityHeadersResponse(
                url=url,
                headers=[],
                score=0,
                error_message="Request timed out",
            )
        except Exception as e:
            logger.error(f"Error checking security headers for {url}: {str(e)}")
            return SecurityHeadersResponse(
                url=url,
                headers=[],
                score=0,
                error_message=str(e),
            )

    async def check_api_endpoint(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        body: Optional[str] = None,
        timeout: int = 30,
        expected_status: Optional[int] = None,
        expected_json_path: Optional[str] = None,
        expected_json_value: Optional[str] = None,
    ) -> APIEndpointCheckResponse:
        """API 엔드포인트 체크 (JSON 응답 검증 포함)

        HTTP 요청을 보내고 상태 코드, 응답 시간, JSON 응답을 검증합니다.
        JSONPath 형식으로 중첩된 JSON 값을 검증할 수 있습니다 (예: "data.user.id").
        """
        validations = []
        start_time = time.time()

        try:
            # 요청 헤더 구성
            request_headers = {"Accept": "application/json"}
            if headers:
                request_headers.update(headers)

            # 요청 바디 파싱 (JSON 문자열 → dict)
            request_body = None
            if body:
                try:
                    request_body = json.loads(body)
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "application/json"
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 문자열 그대로 전송
                    request_body = body

            client_timeout = aiohttp.ClientTimeout(total=timeout)

            async with aiohttp.ClientSession(
                timeout=client_timeout
            ) as session:
                # HTTP 메서드별 요청 발송
                request_kwargs = {"headers": request_headers, "ssl": False}
                if request_body and method in ("POST", "PUT", "PATCH"):
                    if isinstance(request_body, dict):
                        request_kwargs["json"] = request_body
                    else:
                        request_kwargs["data"] = request_body

                async with session.request(
                    method, url, **request_kwargs
                ) as response:
                    response_time = round(
                        (time.time() - start_time) * 1000, 2
                    )
                    status_code = response.status
                    content_type = response.headers.get(
                        "Content-Type", ""
                    )

                    # 응답 본문 읽기 (최대 10KB)
                    raw_body = await response.read()
                    response_text = raw_body[:10240].decode(
                        "utf-8", errors="replace"
                    )
                    # 표시용은 1000자까지
                    display_body = (
                        response_text[:1000] + "..."
                        if len(response_text) > 1000
                        else response_text
                    )

                    # JSON 여부 판별
                    is_json = False
                    json_data = None
                    if "application/json" in content_type:
                        try:
                            json_data = json.loads(response_text)
                            is_json = True
                        except json.JSONDecodeError:
                            pass

                    # 검증 1: 상태 코드
                    if expected_status is not None:
                        validations.append(
                            APIEndpointValidation(
                                field="status_code",
                                expected=str(expected_status),
                                actual=str(status_code),
                                passed=status_code == expected_status,
                            )
                        )

                    # 검증 2: JSON 경로 값 검증
                    if (
                        expected_json_path
                        and expected_json_value is not None
                    ):
                        actual_value = self._resolve_json_path(
                            json_data, expected_json_path
                        )
                        actual_str = (
                            str(actual_value)
                            if actual_value is not None
                            else "null"
                        )
                        validations.append(
                            APIEndpointValidation(
                                field=f"json:{expected_json_path}",
                                expected=expected_json_value,
                                actual=actual_str,
                                passed=actual_str
                                == expected_json_value,
                            )
                        )

                    # 모든 검증 통과 여부
                    all_passed = (
                        all(v.passed for v in validations)
                        if validations
                        else True
                    )

                    return APIEndpointCheckResponse(
                        url=url,
                        method=method,
                        status_code=status_code,
                        response_time=response_time,
                        response_body=display_body,
                        content_type=content_type,
                        is_json=is_json,
                        validations=validations,
                        all_passed=all_passed,
                    )

        except asyncio.TimeoutError:
            response_time = round((time.time() - start_time) * 1000, 2)
            return APIEndpointCheckResponse(
                url=url,
                method=method,
                response_time=response_time,
                error_message="요청 시간이 초과되었습니다",
            )
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"API endpoint check error for {url}: {str(e)}"
            )
            return APIEndpointCheckResponse(
                url=url,
                method=method,
                response_time=response_time,
                error_message=str(e),
            )

    def _resolve_json_path(self, data: dict, path: str):
        """JSON 경로를 따라 값을 추출합니다.

        "data.user.id" 같은 dot-notation 경로를 지원합니다.
        배열 인덱스는 "data.items.0.name" 형식으로 접근합니다.
        """
        if data is None:
            return None

        keys = path.split(".")
        current = data

        for key in keys:
            if current is None:
                return None

            # 배열 인덱스 처리
            if isinstance(current, list):
                try:
                    index = int(key)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    return None
            elif isinstance(current, dict):
                current = current.get(key)
            else:
                return None

        return current

    async def create_alert(
        self, project_id: int, alert_type: str, message: str
    ) -> MonitoringAlert:
        """알림 생성"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 알림 생성
        alert = MonitoringAlert(
            project_id=project_id, alert_type=alert_type, message=message
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        # 알림 데이터 준비
        alert_data = {
            "project_name": project.title,
            "project_url": project.url,
            "error_message": message,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 이메일 알림 전송
        if project.user.email:
            template = self.notification_service.get_alert_template(alert_type)
            await self.notification_service.send_email_notification(
                email=project.user.email,
                subject=f"[모니터링 알림] {project.title}",
                template=template,
                data=alert_data,
            )

        # 웹훅 알림 전송
        if project.webhook_url:
            await self.notification_service.send_webhook_notification(
                webhook_url=project.webhook_url,
                data={
                    "type": alert_type,
                    "project": project.title,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        return alert

    async def create_log(self, log_data: MonitoringLogCreate) -> MonitoringLog:
        """모니터링 로그 생성"""
        log = MonitoringLog(**log_data.dict())
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    async def create_monitoring_alert(
        self, alert_data: MonitoringAlertCreate
    ) -> MonitoringAlert:
        """모니터링 알림 생성"""
        alert = MonitoringAlert(**alert_data.dict())
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        # 이메일 알림 전송
        project = self.db.query(Project).filter(Project.id == alert.project_id).first()
        if project and project.user.email:
            await self.notification_service.send_email_notification(
                email=project.user.email,
                subject=f"모니터링 알림: {project.title}",
                template=self.notification_service.get_alert_template(alert.alert_type),
                data={
                    "project_name": project.title,
                    "project_url": project.url,
                    "error_message": alert.message,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

        return alert

    async def update_ssl_status(
        self, ssl_data: SSLDomainStatusCreate
    ) -> SSLDomainStatus:
        """SSL 도메인 상태 업데이트"""
        existing = (
            self.db.query(SSLDomainStatus)
            .filter(
                and_(
                    SSLDomainStatus.project_id == ssl_data.project_id,
                    SSLDomainStatus.domain == ssl_data.domain,
                )
            )
            .first()
        )

        if existing:
            for key, value in ssl_data.dict().items():
                if value is not None:
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            ssl_status = SSLDomainStatus(**ssl_data.dict())
            self.db.add(ssl_status)
            self.db.commit()
            self.db.refresh(ssl_status)
            return ssl_status

    async def get_monitoring_settings(
        self, project_id: int
    ) -> Optional[MonitoringSetting]:
        """모니터링 설정 조회"""
        return (
            self.db.query(MonitoringSetting)
            .filter(MonitoringSetting.project_id == project_id)
            .first()
        )

    async def update_monitoring_settings(
        self, project_id: int, settings: MonitoringSettingUpdate
    ) -> MonitoringSetting:
        """모니터링 설정 업데이트"""
        existing = await self.get_monitoring_settings(project_id)
        if existing:
            for key, value in settings.dict(exclude_unset=True).items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            new_settings = MonitoringSetting(
                project_id=project_id, **settings.dict(exclude_unset=True)
            )
            self.db.add(new_settings)
            self.db.commit()
            self.db.refresh(new_settings)
            return new_settings

    async def start_monitoring(self, project_id: int) -> None:
        """프로젝트 모니터링 시작"""
        if project_id in self._monitoring_tasks:
            return

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        settings = await self.get_monitoring_settings(project_id)
        if not settings:
            settings = await self.update_monitoring_settings(
                project_id, MonitoringSettingCreate(project_id=project_id)
            )

        async def monitor_task():
            while True:
                try:
                    # 상태 확인
                    status = await self.check_project_status(project_id)
                    if not status.is_available:
                        await self.create_alert(
                            project_id, "status_error", status.error_message
                        )

                    # SSL 상태 확인
                    ssl_status = await self.check_ssl_status(project)
                    if not ssl_status["is_valid"]:
                        await self.create_alert(
                            project_id, "ssl_error", ssl_status["error_message"]
                        )

                    # 도메인 만료일 확인
                    domain_expiry = await self.check_domain_expiry(project)
                    if domain_expiry and (domain_expiry - datetime.now()).days <= 30:
                        await self.create_alert(
                            project_id,
                            "domain_expiry",
                            f"도메인 만료 예정: {domain_expiry.strftime('%Y-%m-%d')}",
                        )

                    await asyncio.sleep(settings.check_interval)
                except Exception as e:
                    await self.create_alert(
                        project_id, "monitoring_error", f"모니터링 오류: {str(e)}"
                    )
                    await asyncio.sleep(60)  # 오류 발생 시 1분 대기

        self._monitoring_tasks[project_id] = asyncio.create_task(monitor_task())

    async def stop_monitoring(self, project_id: int) -> None:
        """프로젝트 모니터링 중지"""
        if project_id in self._monitoring_tasks:
            self._monitoring_tasks[project_id].cancel()
            del self._monitoring_tasks[project_id]


async def check_website(url: str, timeout: int = 30) -> MonitoringStatus:
    """웹사이트 상태를 확인합니다. (비동기 버전)"""
    start_time = datetime.now()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                return MonitoringStatus(
                    is_available=True, response_time=response_time, status_code=response.status
                )
    except Exception as e:
        return MonitoringStatus(is_available=False, error_message=str(e))


def check_website_sync(url: str, timeout: int = 30) -> MonitoringStatus:
    """웹사이트 상태를 확인합니다. (동기 버전)"""
    import requests

    start_time = datetime.now()
    try:
        response = requests.get(url, timeout=timeout)
        response_time = (datetime.now() - start_time).total_seconds()
        return MonitoringStatus(
            is_available=True, response_time=response_time, status_code=response.status_code
        )
    except Exception as e:
        return MonitoringStatus(is_available=False, error_message=str(e))


def check_ssl(hostname: str) -> SSLStatus:
    """SSL 인증서 상태를 확인합니다."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                issuer = dict(x[0] for x in cert["issuer"])
                not_before = datetime.strptime(
                    cert["notBefore"], "%b %d %H:%M:%S %Y %Z"
                )
                not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                days_remaining = (not_after - datetime.now()).days
                return SSLStatus(
                    is_valid=True,
                    issuer=issuer.get("organizationName"),
                    valid_from=not_before,
                    valid_until=not_after,
                    days_remaining=days_remaining,
                )
    except Exception as e:
        return SSLStatus(is_valid=False, error_message=str(e))


def check_project_status(project: Project) -> MonitoringResponse:
    """프로젝트의 상태를 확인합니다."""
    # URL에서 호스트네임 추출
    parsed_url = urlparse(str(project.url))
    hostname = parsed_url.netloc

    # 웹사이트 상태 체크 (동기 버전 사용)
    status = check_website_sync(str(project.url))

    # SSL 체크 (HTTPS인 경우)
    ssl_status = None
    if parsed_url.scheme == "https":
        ssl_status = check_ssl(hostname)

    return MonitoringResponse(
        project_id=project.id,
        project_title=project.title,
        url=str(project.url),
        status=status,
        ssl=ssl_status,
    )
