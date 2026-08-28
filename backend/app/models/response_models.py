from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.models.report import AnalysisReport


class UploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    filename: str
    language: str
    message: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report: AnalysisReport


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    sources: List[str] = []
    conversation_id: Optional[str] = None
