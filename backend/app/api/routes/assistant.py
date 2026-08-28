from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_assistant_service
from app.models.request_models import AssistantRequest
from app.models.response_models import AssistantResponse
from app.services.assistant_service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("", response_model=AssistantResponse)
async def assistant(
    request: AssistantRequest,
    assistant_service: AssistantService = Depends(get_assistant_service),
) -> AssistantResponse:
    """Answer a free-form code review question."""
    try:
        return await assistant_service.answer(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
