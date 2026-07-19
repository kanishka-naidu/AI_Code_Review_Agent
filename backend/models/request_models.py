from typing import Optional
from pydantic import BaseModel


class CodeSubmission(BaseModel):
    code: str
    language: Optional[str] = None