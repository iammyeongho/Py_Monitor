"""
# Laravel 개발자를 위한 설명
# 이 파일은 웹사이트 스크린샷 캡처 서비스를 구현합니다.
# 외부 API를 사용하여 웹사이트의 썸네일 이미지를 생성합니다.
#
# 주요 기능:
# 1. 외부 스크린샷 API 호출
# 2. 이미지 저장 및 캐싱
# 3. 썸네일 URL 생성
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import aiohttp
from sqlalchemy.orm import Session

from app.models.project import Project


class ScreenshotService:
    """웹사이트 스크린샷 서비스"""

    # 무료 스크린샷 API 옵션들
    # 1. screenshot.screenshotlayer.com (무료 100/월)
    # 2. api.screenshotone.com (무료 100/월)
    # 3. api.apiflash.com (무료 100/월)
    # 4. 자체 URL 기반 (썸네일 서비스)

    SCREENSHOT_DIR = "frontend/screenshots"

    def __init__(self, db: Session):
        self.db = db
        # 스크린샷 저장 디렉토리 생성
        Path(self.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

    def get_screenshot_url(self, url: str, width: int = 1280, height: int = 800) -> str:
        """외부 스크린샷 API URL 생성 (무료 서비스 활용)"""
        encoded_url = quote_plus(url)

        # 옵션 1: microlink.io (무료, 제한적)
        # 가장 관대한 무료 티어 제공
        return f"https://api.microlink.io/?url={encoded_url}&screenshot=true&meta=false&embed=screenshot.url"

    def get_thumbnail_url(self, url: str) -> str:
        """Google PageSpeed 썸네일 URL (무료, 빠름)"""
        encoded_url = quote_plus(url)
        # Google의 무료 썸네일 서비스
        return f"https://www.google.com/s2/favicons?domain={url}&sz=128"

    def get_preview_url(self, url: str) -> str:
        """웹사이트 미리보기 URL 생성"""
        encoded_url = quote_plus(url)
        # 무료 스크린샷 서비스들
        # 1. Screenshot Machine (무료 100회/월)
        # 2. Thum.io (무료, 워터마크)
        # 3. PagePeeker (무료, 저해상도)
        return f"https://image.thum.io/get/width/400/crop/300/{url}"

    async def capture_screenshot(
        self,
        project_id: int,
        force: bool = False
    ) -> Optional[str]:
        """프로젝트 웹사이트 스크린샷 캡처"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 캐시 확인 (1시간 이내면 기존 이미지 사용)
        if not force and project.last_snapshot_at:
            time_diff = datetime.now(timezone.utc) - project.last_snapshot_at.replace(tzinfo=timezone.utc)
            if time_diff.total_seconds() < 3600:  # 1시간
                return project.snapshot_path

        url = str(project.url)
        filename = self._generate_filename(url)
        filepath = os.path.join(self.SCREENSHOT_DIR, filename)

        try:
            # Thum.io API 사용 (무료, 빠름)
            screenshot_url = f"https://image.thum.io/get/width/640/crop/400/{url}"

            async with aiohttp.ClientSession() as session:
                async with session.get(screenshot_url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(content)

                        # DB 업데이트
                        project.snapshot_path = f"/frontend/screenshots/{filename}"
                        project.last_snapshot_at = datetime.now(timezone.utc)
                        self.db.commit()

                        return project.snapshot_path

        except Exception as e:
            print(f"스크린샷 캡처 오류: {e}")
            return None

        return None

    def _generate_filename(self, url: str) -> str:
        """URL 기반 고유 파일명 생성"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"screenshot_{url_hash}.png"

    def get_cached_screenshot(self, project_id: int) -> Optional[str]:
        """캐시된 스크린샷 경로 반환"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project and project.snapshot_path:
            return project.snapshot_path
        return None
