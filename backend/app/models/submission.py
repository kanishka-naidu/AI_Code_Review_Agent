from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CodeSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    filename: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = {}
