"""리포트 관련 스키마"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ReportFilter(BaseModel):
    """리포트 필터 조건"""
    project_ids: Optional[List[int]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_logs: bool = True
    include_alerts: bool = True
    include_ssl_status: bool = True


class ProjectSummary(BaseModel):
    """프로젝트 요약 정보"""
    project_id: int
    project_title: str
    url: str
    category: Optional[str] = None
    tags: Optional[str] = None
    total_checks: int
    available_checks: int
    availability_percentage: float
    avg_response_time: Optional[float] = None
    min_response_time: Optional[float] = None
    max_response_time: Optional[float] = None
    total_alerts: int
    unresolved_alerts: int


class ReportData(BaseModel):
    """리포트 데이터"""
    report_title: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_projects: int
    overall_availability: float
    overall_avg_response_time: Optional[float] = None
    projects: List[ProjectSummary]


class ExportRequest(BaseModel):
    """내보내기 요청"""
    format: str = Field(..., pattern="^(csv|pdf)$")
    project_ids: Optional[List[int]] = None
    days: int = Field(default=7, ge=1, le=365)
