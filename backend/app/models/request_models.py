from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    language: Optional[str] = None


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Optional[str] = None
    code: Optional[str] = None
    source_id: Optional[str] = None
    include_rag: bool = False


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(..., min_length=1, alias="message")
    context: Optional[str] = None
    source_id: Optional[str] = None
    report: Optional[dict] = Field(None, alias="report_context")
    conversation_id: Optional[str] = None
    assistant_detail_level: Optional[str] = Field(None, alias="assistant_detail_level")
