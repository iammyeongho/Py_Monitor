"""리포트 생성 서비스"""

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.monitoring import MonitoringLog, MonitoringAlert
from app.schemas.report import ProjectSummary, ReportData


class ReportService:
    """리포트 생성 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def generate_report_data(
        self,
        user_id: int,
        project_ids: Optional[List[int]] = None,
        days: int = 7
    ) -> ReportData:
        """리포트 데이터 생성"""
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=days)

        # 프로젝트 조회
        query = self.db.query(Project).filter(
            Project.user_id == user_id,
            Project.is_active.is_(True),
            Project.deleted_at.is_(None)
        )

        if project_ids:
            query = query.filter(Project.id.in_(project_ids))

        projects = query.all()

        # 프로젝트별 요약 생성
        project_summaries = []
        total_available = 0
        total_checks = 0
        all_response_times = []

        for project in projects:
            summary = self._generate_project_summary(
                project, period_start, period_end
            )
            project_summaries.append(summary)

            total_available += summary.available_checks
            total_checks += summary.total_checks
            if summary.avg_response_time:
                all_response_times.append(summary.avg_response_time)

        # 전체 통계 계산
        overall_availability = (
            (total_available / total_checks * 100) if total_checks > 0 else 100.0
        )
        overall_avg_response_time = (
            sum(all_response_times) / len(all_response_times)
            if all_response_times else None
        )

        return ReportData(
            report_title=f"모니터링 리포트 ({days}일간)",
            generated_at=datetime.now(timezone.utc),
            period_start=period_start,
            period_end=period_end,
            total_projects=len(projects),
            overall_availability=round(overall_availability, 2),
            overall_avg_response_time=(
                round(overall_avg_response_time, 2) if overall_avg_response_time else None
            ),
            projects=project_summaries
        )

    def _generate_project_summary(
        self,
        project: Project,
        period_start: datetime,
        period_end: datetime
    ) -> ProjectSummary:
        """프로젝트 요약 생성"""
        # 로그 조회
        logs = (
            self.db.query(MonitoringLog)
            .filter(
                MonitoringLog.project_id == project.id,
                MonitoringLog.created_at >= period_start,
                MonitoringLog.created_at <= period_end,
            )
            .all()
        )

        total_checks = len(logs)
        available_checks = sum(1 for log in logs if log.is_available)
        availability_pct = (
            (available_checks / total_checks * 100) if total_checks > 0 else 0
        )

        # 응답 시간 통계
        response_times = [
            log.response_time * 1000 for log in logs if log.response_time
        ]
        avg_rt = sum(response_times) / len(response_times) if response_times else None
        min_rt = min(response_times) if response_times else None
        max_rt = max(response_times) if response_times else None

        # 알림 통계
        total_alerts = (
            self.db.query(MonitoringAlert)
            .filter(
                MonitoringAlert.project_id == project.id,
                MonitoringAlert.created_at >= period_start,
                MonitoringAlert.created_at <= period_end,
            )
            .count()
        )
        unresolved_alerts = (
            self.db.query(MonitoringAlert)
            .filter(
                MonitoringAlert.project_id == project.id,
                MonitoringAlert.is_resolved.is_(False),
            )
            .count()
        )

        return ProjectSummary(
            project_id=project.id,
            project_title=project.title,
            url=project.url,
            category=project.category,
            tags=project.tags,
            total_checks=total_checks,
            available_checks=available_checks,
            availability_percentage=round(availability_pct, 2),
            avg_response_time=round(avg_rt, 2) if avg_rt else None,
            min_response_time=round(min_rt, 2) if min_rt else None,
            max_response_time=round(max_rt, 2) if max_rt else None,
            total_alerts=total_alerts,
            unresolved_alerts=unresolved_alerts,
        )

    def export_to_csv(self, report_data: ReportData) -> str:
        """CSV 형식으로 내보내기"""
        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow([
            "프로젝트 ID",
            "프로젝트명",
            "URL",
            "카테고리",
            "태그",
            "총 체크 수",
            "가용 체크 수",
            "가용률 (%)",
            "평균 응답시간 (ms)",
            "최소 응답시간 (ms)",
            "최대 응답시간 (ms)",
            "총 알림 수",
            "미해결 알림 수"
        ])

        # 데이터 행
        for project in report_data.projects:
            writer.writerow([
                project.project_id,
                project.project_title,
                project.url,
                project.category or "",
                project.tags or "",
                project.total_checks,
                project.available_checks,
                project.availability_percentage,
                project.avg_response_time or "",
                project.min_response_time or "",
                project.max_response_time or "",
                project.total_alerts,
                project.unresolved_alerts
            ])

        # 요약 행
        writer.writerow([])
        writer.writerow(["=== 요약 ==="])
        writer.writerow(["리포트 제목", report_data.report_title])
        writer.writerow(["생성 시간", report_data.generated_at.isoformat()])
        writer.writerow(["기간", f"{report_data.period_start.date()} ~ {report_data.period_end.date()}"])
        writer.writerow(["총 프로젝트 수", report_data.total_projects])
        writer.writerow(["전체 가용률 (%)", report_data.overall_availability])
        writer.writerow(["전체 평균 응답시간 (ms)", report_data.overall_avg_response_time or "N/A"])

        return output.getvalue()

    def export_to_pdf_html(self, report_data: ReportData) -> str:
        """PDF용 HTML 생성 (클라이언트에서 PDF 변환)"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report_data.report_title}</title>
    <style>
        body {{ font-family: 'Noto Sans KR', Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #1f2937; margin-top: 30px; }}
        .summary {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .summary-item {{ display: inline-block; margin-right: 40px; }}
        .summary-label {{ color: #6b7280; font-size: 12px; }}
        .summary-value {{ font-size: 24px; font-weight: bold; color: #1f2937; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; font-weight: 600; color: #374151; }}
        tr:hover {{ background: #f9fafb; }}
        .good {{ color: #059669; }}
        .warning {{ color: #d97706; }}
        .bad {{ color: #dc2626; }}
        .footer {{ margin-top: 40px; text-align: center; color: #9ca3af; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>{report_data.report_title}</h1>

    <div class="summary">
        <div class="summary-item">
            <div class="summary-label">기간</div>
            <div class="summary-value">{report_data.period_start.strftime('%Y-%m-%d')} ~ {report_data.period_end.strftime('%Y-%m-%d')}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">총 프로젝트</div>
            <div class="summary-value">{report_data.total_projects}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">전체 가용률</div>
            <div class="summary-value {'good' if report_data.overall_availability >= 99 else 'warning' if report_data.overall_availability >= 95 else 'bad'}">{report_data.overall_availability}%</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">평균 응답시간</div>
            <div class="summary-value">{report_data.overall_avg_response_time or 'N/A'} ms</div>
        </div>
    </div>

    <h2>프로젝트별 상세</h2>
    <table>
        <thead>
            <tr>
                <th>프로젝트</th>
                <th>URL</th>
                <th>가용률</th>
                <th>평균 응답시간</th>
                <th>체크 수</th>
                <th>알림</th>
            </tr>
        </thead>
        <tbody>
"""

        for project in report_data.projects:
            availability_class = (
                "good" if project.availability_percentage >= 99
                else "warning" if project.availability_percentage >= 95
                else "bad"
            )
            html += f"""
            <tr>
                <td><strong>{project.project_title}</strong></td>
                <td>{project.url}</td>
                <td class="{availability_class}">{project.availability_percentage}%</td>
                <td>{project.avg_response_time or 'N/A'} ms</td>
                <td>{project.available_checks}/{project.total_checks}</td>
                <td>{project.unresolved_alerts}/{project.total_alerts}</td>
            </tr>
"""

        html += f"""
        </tbody>
    </table>

    <div class="footer">
        PyMonitor - 생성일시: {report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
    </div>
</body>
</html>
"""
        return html
