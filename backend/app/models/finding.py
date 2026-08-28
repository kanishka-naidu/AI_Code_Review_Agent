from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

from app.models.severity import Severity


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str
    title: str
    description: str
    severity: Severity
    category: str
    location: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    explanation: Optional[str] = None
    root_cause: Optional[str] = None
    corrected_code: Optional[str] = None
    secure_alternative: Optional[str] = None
    best_practice: Optional[str] = None
    prevention: Optional[str] = None
    maintainability_impact: Optional[str] = None
    owasp_reference: Optional[str] = None
    tool_source: Optional[str] = None
    finding_metadata: Optional[dict[str, Any]] = None
