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


@router.post("/pdf")
def generate_pdf_report(request: dict):
    """Generate a PDF from report data sent directly by the frontend.

    The frontend already has the complete report object from POST /analyze,
    so it sends it directly to avoid server-side storage dependencies.
    This works on Render's FREE plan without persistent disk.
    """
    if not request:
        raise HTTPException(status_code=400, detail="Report data is required")

    try:
        pdf_bytes = PDFReportService.generate(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    filename = f"analysis-report-{request.get('report_id', 'unknown')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{report_id}/pdf")
def download_report_pdf(report_id: str):
    """Download the analysis report as a professional PDF.

    NOTE: This endpoint requires server-side storage and will return 404
    if the report was lost due to a Render worker restart. Use POST /pdf
    for reliable PDF generation.
    """
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