from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.pdf_service import PDFReportService
from app.services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["reports"])


@router.get("/{report_id}")
def get_report(report_id: str):
    try:
        return ReportService.load(report_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )


@router.get("/{report_id}/pdf")
def download_report_pdf(report_id: str):
    """Download the analysis report as a professional PDF."""
    try:
        report = ReportService.load(report_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    pdf_bytes = PDFReportService.generate(report)

    filename = f"analysis-report-{report_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )