from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.finding import Finding


class SeverityDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class AnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_id: str
    filename: str
    language: str
    summary: str
    quality_score: int
    security_score: int
    findings: List[Finding] = []
    recommendations: List[str] = []
    explanation: Optional[str] = None
    pr_summary: Optional[str] = None
    assistant_context: Optional[Dict[str, Any]] = None
    severity_distribution: Optional[SeverityDistribution] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Optional[Dict[str, Any]] = None
