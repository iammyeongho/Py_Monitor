"""
# Laravel 개발자를 위한 설명
# 이 파일은 웹사이트 스크린샷 캡처 서비스를 구현합니다.
# Playwright를 사용하여 웹사이트의 스크린샷을 직접 캡처합니다.
#
# 주요 기능:
# 1. Playwright로 브라우저 스크린샷 캡처
# 2. 이미지 저장 및 캐싱
# 3. 썸네일 URL 생성
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.project import Project


class ScreenshotService:
    """웹사이트 스크린샷 서비스 (Playwright 기반)"""

    SCREENSHOT_DIR = "frontend/screenshots"

    def __init__(self, db: Session):
        self.db = db
        # 스크린샷 저장 디렉토리 생성
        Path(self.SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)

    def get_thumbnail_url(self, url: str) -> str:
        """Google Favicon URL (무료, 빠름)"""
        return f"https://www.google.com/s2/favicons?domain={url}&sz=128"

    def get_preview_url(self, url: str) -> str:
        """캐시된 스크린샷 경로 또는 placeholder 반환"""
        # 로컬 캐시 확인
        filename = self._generate_filename(url)
        filepath = os.path.join(self.SCREENSHOT_DIR, filename)

        if os.path.exists(filepath):
            return f"/{self.SCREENSHOT_DIR}/{filename}"

        # 캐시 없으면 placeholder
        return "/frontend/img/placeholder.svg"

    async def capture_screenshot(
        self,
        project_id: int,
        force: bool = False
    ) -> Optional[str]:
        """프로젝트 웹사이트 스크린샷 캡처 (Playwright 사용)"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 캐시 확인 (24시간 이내면 기존 이미지 사용)
        if not force and project.last_snapshot_at:
            time_diff = datetime.now(timezone.utc) - project.last_snapshot_at.replace(tzinfo=timezone.utc)
            if time_diff.total_seconds() < 86400:  # 24시간
                if project.snapshot_path and os.path.exists(project.snapshot_path.lstrip('/')):
                    return project.snapshot_path

        url = str(project.url)
        filename = self._generate_filename(url)
        filepath = os.path.join(self.SCREENSHOT_DIR, filename)

        try:
            # Playwright로 스크린샷 캡처
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )

                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    device_scale_factor=1
                )

                page = await context.new_page()

                try:
                    # 페이지 로드 (최대 30초)
                    await page.goto(url, wait_until='networkidle', timeout=30000)

                    # 약간의 대기 (동적 콘텐츠 로드)
                    await page.wait_for_timeout(1000)

                    # 스크린샷 캡처
                    await page.screenshot(
                        path=filepath,
                        type='png',
                        clip={'x': 0, 'y': 0, 'width': 1280, 'height': 800}
                    )

                except Exception as e:
                    print(f"페이지 로드 오류: {e}")
                    await browser.close()
                    return None

                await browser.close()

            # DB 업데이트
            project.snapshot_path = f"/{self.SCREENSHOT_DIR}/{filename}"
            project.last_snapshot_at = datetime.now(timezone.utc)
            self.db.commit()

            return project.snapshot_path

        except Exception as e:
            print(f"스크린샷 캡처 오류: {e}")
            return None

    def _generate_filename(self, url: str) -> str:
        """URL 기반 고유 파일명 생성"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"screenshot_{url_hash}.png"

    def get_cached_screenshot(self, project_id: int) -> Optional[str]:
        """캐시된 스크린샷 경로 반환"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project and project.snapshot_path:
            filepath = project.snapshot_path.lstrip('/')
            if os.path.exists(filepath):
                return project.snapshot_path
        return None

    def delete_screenshot(self, project_id: int) -> bool:
        """프로젝트 스크린샷 삭제"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project and project.snapshot_path:
            filepath = project.snapshot_path.lstrip('/')
            if os.path.exists(filepath):
                os.remove(filepath)
                project.snapshot_path = None
                project.last_snapshot_at = None
                self.db.commit()
                return True
        return False
