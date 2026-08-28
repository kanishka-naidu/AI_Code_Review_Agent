from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query

from app.api.dependencies import get_upload_service
from app.core.config import get_settings
from app.core.repository_config import get_repository_config
from app.models.response_models import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
def upload_code(
    filename: str | None = Query(default=None),
    content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    if file is not None:
        filename = file.filename or filename
        content = file.file.read().decode("utf-8")
    if not filename:
        filename = get_settings().default_upload_filename
    if not content:
        detail = get_repository_config().load("reporting.json").get("content_required_message")
        raise HTTPException(status_code=400, detail=detail)

    source_id, language = upload_service.save_upload(filename, content, None)
    return UploadResponse(
        source_id=source_id,
        filename=filename,
        language=language,
        message=str(get_repository_config().load("reporting.json").get("upload_success_message")),
    )
