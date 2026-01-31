"""
# Laravel 개발자를 위한 설명
# 이 파일은 Uptime 배지 API 엔드포인트를 정의합니다.
# shields.io 스타일의 SVG 배지를 생성하여 반환합니다.
# 인증 없이 접근 가능한 공개 API입니다.
#
# 주요 기능:
# 1. 프로젝트별 uptime 퍼센트 배지 (SVG)
# 2. 프로젝트별 현재 상태 배지 (SVG)
# 3. 프로젝트별 응답 시간 배지 (SVG)
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.monitoring import MonitoringLog
from app.models.project import Project

router = APIRouter()

# SVG 배지 캐시 헤더 (5분)
BADGE_CACHE_SECONDS = 300


def _make_badge_svg(label: str, value: str, color: str) -> str:
    """shields.io 스타일 SVG 배지 생성"""
    # 텍스트 너비 근사 계산 (문자당 약 6.5px, 한글은 약 12px)
    def _text_width(text):
        width = 0
        for ch in text:
            if ord(ch) > 127:
                width += 12
            else:
                width += 6.5
        return width + 10  # 좌우 패딩

    label_width = _text_width(label)
    value_width = _text_width(value)
    total_width = label_width + value_width

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="{label_width / 2}" y="14" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="13">{label}</text>
    <text x="{label_width + value_width / 2}" y="14" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="13">{value}</text>
  </g>
</svg>'''


def _get_public_project(db: Session, project_id: int):
    """공개 프로젝트 조회"""
    return (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.is_public == True,  # noqa: E712
            Project.is_active == True,  # noqa: E712
            Project.deleted_at.is_(None),
        )
        .first()
    )


def _calculate_uptime(db: Session, project_id: int, hours: int) -> float:
    """특정 기간 동안의 uptime 퍼센트 계산"""
    since = datetime.utcnow() - timedelta(hours=hours)

    total = db.query(func.count(MonitoringLog.id)).filter(
        MonitoringLog.project_id == project_id,
        MonitoringLog.created_at >= since,
    ).scalar() or 0

    if total == 0:
        return 100.0

    available = db.query(func.count(MonitoringLog.id)).filter(
        MonitoringLog.project_id == project_id,
        MonitoringLog.created_at >= since,
        MonitoringLog.is_available == True,  # noqa: E712
    ).scalar() or 0

    return round((available / total) * 100, 1)


def _uptime_color(uptime: float) -> str:
    """uptime 퍼센트에 따른 배지 색상"""
    if uptime >= 99.9:
        return "#4c1"       # 밝은 녹색
    if uptime >= 99.0:
        return "#97CA00"    # 연두
    if uptime >= 95.0:
        return "#dfb317"    # 노랑
    if uptime >= 90.0:
        return "#fe7d37"    # 주황
    return "#e05d44"        # 빨강


def _svg_response(svg: str) -> Response:
    """SVG 응답 생성 (캐시 헤더 포함)"""
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": f"max-age={BADGE_CACHE_SECONDS}, s-maxage={BADGE_CACHE_SECONDS}",
            "Expires": (datetime.utcnow() + timedelta(seconds=BADGE_CACHE_SECONDS)).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            ),
        },
    )


def _not_found_badge(label: str = "uptime") -> Response:
    """프로젝트를 찾을 수 없을 때 반환하는 배지"""
    svg = _make_badge_svg(label, "not found", "#9f9f9f")
    return _svg_response(svg)


# ==================== API 엔드포인트 ====================

@router.get("/{project_id}/uptime")
def get_uptime_badge(
    project_id: int,
    period: str = Query("30d", pattern="^(24h|7d|30d|90d)$", description="기간: 24h, 7d, 30d, 90d"),
    label: str = Query("uptime", description="배지 라벨"),
    db: Session = Depends(get_db),
):
    """
    프로젝트 uptime 퍼센트 배지 (SVG)
    인증 없이 접근 가능합니다. 공개 프로젝트만 조회됩니다.

    사용 예시:
    ![uptime](https://your-domain/api/v1/badge/1/uptime?period=30d)
    """
    project = _get_public_project(db, project_id)
    if not project:
        return _not_found_badge(label)

    period_hours = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160}
    hours = period_hours.get(period, 720)

    uptime = _calculate_uptime(db, project_id, hours)
    color = _uptime_color(uptime)
    value = f"{uptime}%"

    svg = _make_badge_svg(label, value, color)
    return _svg_response(svg)


@router.get("/{project_id}/status")
def get_status_badge(
    project_id: int,
    label: str = Query("status", description="배지 라벨"),
    db: Session = Depends(get_db),
):
    """
    프로젝트 현재 상태 배지 (SVG)
    인증 없이 접근 가능합니다. 공개 프로젝트만 조회됩니다.

    사용 예시:
    ![status](https://your-domain/api/v1/badge/1/status)
    """
    project = _get_public_project(db, project_id)
    if not project:
        return _not_found_badge(label)

    # 최신 로그 조회
    latest = (
        db.query(MonitoringLog)
        .filter(MonitoringLog.project_id == project_id)
        .order_by(MonitoringLog.created_at.desc())
        .first()
    )

    if not latest:
        svg = _make_badge_svg(label, "unknown", "#9f9f9f")
    elif latest.is_available:
        svg = _make_badge_svg(label, "up", "#4c1")
    else:
        svg = _make_badge_svg(label, "down", "#e05d44")

    return _svg_response(svg)


@router.get("/{project_id}/response-time")
def get_response_time_badge(
    project_id: int,
    label: str = Query("response time", description="배지 라벨"),
    db: Session = Depends(get_db),
):
    """
    프로젝트 평균 응답 시간 배지 (SVG)
    인증 없이 접근 가능합니다. 공개 프로젝트만 조회됩니다.

    사용 예시:
    ![response time](https://your-domain/api/v1/badge/1/response-time)
    """
    project = _get_public_project(db, project_id)
    if not project:
        return _not_found_badge(label)

    # 최근 24시간 평균 응답 시간
    since = datetime.utcnow() - timedelta(hours=24)
    avg_time = db.query(func.avg(MonitoringLog.response_time)).filter(
        MonitoringLog.project_id == project_id,
        MonitoringLog.created_at >= since,
        MonitoringLog.is_available == True,  # noqa: E712
    ).scalar()

    if avg_time is None:
        svg = _make_badge_svg(label, "N/A", "#9f9f9f")
    else:
        ms = avg_time * 1000
        value = f"{ms:.0f}ms"
        # 응답 시간에 따른 색상
        if ms < 200:
            color = "#4c1"
        elif ms < 500:
            color = "#97CA00"
        elif ms < 1000:
            color = "#dfb317"
        elif ms < 3000:
            color = "#fe7d37"
        else:
            color = "#e05d44"

        svg = _make_badge_svg(label, value, color)

    return _svg_response(svg)
