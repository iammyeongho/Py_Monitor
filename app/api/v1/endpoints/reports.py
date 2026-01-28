"""리포트 엔드포인트"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.schemas.report import ReportData, ExportRequest
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/", response_model=ReportData)
def get_report(
    project_ids: Optional[List[int]] = Query(None),
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """모니터링 리포트 데이터를 조회합니다."""
    service = ReportService(db)
    return service.generate_report_data(
        user_id=current_user.id,
        project_ids=project_ids,
        days=days
    )


@router.get("/export/csv")
def export_csv(
    project_ids: Optional[List[int]] = Query(None),
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """CSV 형식으로 리포트를 내보냅니다."""
    service = ReportService(db)
    report_data = service.generate_report_data(
        user_id=current_user.id,
        project_ids=project_ids,
        days=days
    )

    csv_content = service.export_to_csv(report_data)

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=monitoring_report_{days}days.csv"
        }
    )


@router.get("/export/pdf")
def export_pdf_html(
    project_ids: Optional[List[int]] = Query(None),
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """PDF용 HTML을 반환합니다. (클라이언트에서 PDF로 변환)"""
    service = ReportService(db)
    report_data = service.generate_report_data(
        user_id=current_user.id,
        project_ids=project_ids,
        days=days
    )

    html_content = service.export_to_pdf_html(report_data)

    return Response(
        content=html_content,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=monitoring_report_{days}days.html"
        }
    )
