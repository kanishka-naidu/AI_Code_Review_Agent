"""
Analyze endpoint.

Two explicit workflows:
  - Upload mode   (source_id provided): read from disk, ignore request.code
  - Paste mode    (code provided):      analyze request.code directly

The workflows are kept entirely separate — no mixing.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.agents.language_detection_agent import LanguageDetectionAgent
from app.analyzers.common.tooling import AnalyzerError
from app.api.dependencies import get_analysis_service, get_upload_service
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.models.request_models import AnalyzeRequest
from app.models.response_models import AnalysisResponse
from app.models.submission import CodeSubmission
from app.services.analysis_service import AnalysisService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = get_logger(__name__)

_language_agent = LanguageDetectionAgent()


@router.post("", response_model=AnalysisResponse)
async def analyze_code(
    request: AnalyzeRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    upload_service: UploadService = Depends(get_upload_service),
) -> AnalysisResponse:
    """
    Analyze a code submission.

    - If **source_id** is provided, the previously uploaded file is analyzed.
      `code` in the request body is ignored.
    - If **code** is provided, it is analyzed directly.
      `source_id` must not be present.
    """
    if request.source_id:
        submission = _build_upload_submission(request, upload_service)
    else:
        submission = _build_paste_submission(request)

    logger.info(
        "analyze_code: source_type='%s', language='%s', filename='%s'",
        submission.metadata.get("source_type"),
        submission.language,
        submission.filename,
    )

    try:
        report = await analysis_service.analyze_submission(submission)
    except AnalyzerError as exc:
        logger.error("AnalyzerError during analysis: %s", exc.message)
        raise HTTPException(
            status_code=500,
            detail={"tool": exc.tool, "message": exc.message, "details": exc.details},
        ) from exc
    except RuntimeError as exc:
        logger.error("Pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AnalysisResponse(report=report)


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _build_upload_submission(request: AnalyzeRequest, upload_service: UploadService) -> CodeSubmission:
    """
    Upload mode: resolve source_id → file on disk → CodeSubmission.

    The language is derived from the stored filename; request.language overrides.
    """
    upload_path = upload_service.settings.upload_path
    pattern = f"{request.source_id}_*"
    matches = list(upload_path.glob(pattern))

    if not matches:
        detail = get_repository_config().load("reporting.json").get("source_not_found_message")
        raise HTTPException(status_code=404, detail=str(detail).format(source_id=request.source_id))

    source_file = matches[0]
    code = source_file.read_text(encoding="utf-8")
    # Strip the UUID prefix to recover the original filename
    filename = source_file.name.split("_", 1)[1] if "_" in source_file.name else source_file.name

    # Language: explicit request.language > auto-detect from filename/content
    language = request.language or _language_agent.detect(filename, code)

    return CodeSubmission(
        language=language,
        code=code,
        filename=filename,
        source_id=request.source_id,
        metadata={
            "source_type": get_repository_config().load("reporting.json").get("source_type_upload"),
            "include_rag": request.include_rag,
        },
    )


def _build_paste_submission(request: AnalyzeRequest) -> CodeSubmission:
    """
    Paste mode: validate and wrap request.code in a CodeSubmission.
    """
    if not request.code:
        detail = get_repository_config().load("reporting.json").get("code_required_message")
        raise HTTPException(
            status_code=400,
            detail=detail,
        )
    if not request.language:
        detail = get_repository_config().load("reporting.json").get("language_required_message")
        raise HTTPException(
            status_code=400,
            detail=detail,
        )

    return CodeSubmission(
        language=request.language,
        code=request.code,
        filename=get_settings().default_paste_filename,
        metadata={
            "source_type": get_repository_config().load("reporting.json").get("source_type_paste"),
            "include_rag": request.include_rag,
        },
    )
