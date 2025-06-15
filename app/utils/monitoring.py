"""
# Laravel 개발자를 위한 설명
# 이 파일은 모니터링 관련 유틸리티 함수들을 포함합니다.
# Laravel의 Helpers 디렉토리와 유사한 역할을 합니다.
"""

import aiohttp
import ssl
import socket
import whois
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

async def check_website_availability(url: str, timeout: int = 30) -> Tuple[bool, float, Optional[int], Optional[str]]:
    """
    웹사이트 가용성을 확인합니다.
    
    Args:
        url (str): 확인할 URL
        timeout (int): 타임아웃 시간 (초)
        
    Returns:
        Tuple[bool, float, Optional[int], Optional[str]]: 
            - 가용성 상태
            - 응답 시간
            - HTTP 상태 코드
            - 오류 메시지
    """
    start_time = datetime.now()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response_time = (datetime.now() - start_time).total_seconds()
                return True, response_time, response.status, None
    except aiohttp.ClientError as e:
        response_time = (datetime.now() - start_time).total_seconds()
        return False, response_time, None, str(e)
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        return False, response_time, None, str(e)

def check_ssl_certificate(domain: str) -> Dict:
    """
    SSL 인증서 상태를 확인합니다.
    
    Args:
        domain (str): 확인할 도메인
        
    Returns:
        Dict: SSL 인증서 정보
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                # 인증서 만료일 계산
                expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (expire_date - datetime.now()).days
                
                return {
                    'valid': True,
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'subject': dict(x[0] for x in cert['subject']),
                    'version': cert['version'],
                    'not_before': cert['notBefore'],
                    'not_after': cert['notAfter'],
                    'days_until_expiry': days_until_expiry
                }
    except Exception as e:
        logger.error(f"SSL 인증서 확인 중 오류 발생: {str(e)}")
        return {
            'valid': False,
            'error': str(e)
        }

def check_domain_expiry(domain: str) -> Dict:
    """
    도메인 만료일을 확인합니다.
    
    Args:
        domain (str): 확인할 도메인
        
    Returns:
        Dict: 도메인 정보
    """
    try:
        domain_info = whois.whois(domain)
        expiry_date = domain_info.expiration_date
        
        # 만약 만료일이 리스트인 경우 (여러 날짜가 있는 경우)
        if isinstance(expiry_date, list):
            expiry_date = expiry_date[0]
            
        days_until_expiry = (expiry_date - datetime.now()).days
        
        return {
            'valid': True,
            'registrar': domain_info.registrar,
            'creation_date': domain_info.creation_date,
            'expiration_date': expiry_date,
            'days_until_expiry': days_until_expiry
        }
    except Exception as e:
        logger.error(f"도메인 만료일 확인 중 오류 발생: {str(e)}")
        return {
            'valid': False,
            'error': str(e)
        }

def calculate_next_check_time(interval: int) -> datetime:
    """
    다음 체크 시간을 계산합니다.
    
    Args:
        interval (int): 체크 간격 (초)
        
    Returns:
        datetime: 다음 체크 시간
    """
    return datetime.now() + timedelta(seconds=interval)

def format_response_time(response_time: float) -> str:
    """
    응답 시간을 포맷팅합니다.
    
    Args:
        response_time (float): 응답 시간 (초)
        
    Returns:
        str: 포맷팅된 응답 시간
    """
    if response_time < 1:
        return f"{response_time * 1000:.0f}ms"
    return f"{response_time:.1f}s"
