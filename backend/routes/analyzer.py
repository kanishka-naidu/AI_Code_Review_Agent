from fastapi import APIRouter

from backend.models.request_models import CodeSubmission
from backend.services.analyzer_service import analyze_code

router = APIRouter()


@router.post("/analyze")
def analyze(data: CodeSubmission):

    return analyze_code(data.code)