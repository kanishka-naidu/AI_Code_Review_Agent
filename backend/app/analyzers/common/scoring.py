"""Centralised, configuration-driven scoring strategy."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.repository_config import get_repository_config
from app.models.finding import Finding


def compute_scores(findings: list[Finding]) -> tuple[int, int]:
    """Return quality and security scores derived from findings and settings."""
    settings = get_settings()
    analysis_config = get_repository_config().load("analysis.json")
    weights = settings.severity_weights()

    quality_findings = [f for f in findings if f.category == analysis_config.get("quality_category")]
    security_findings = [f for f in findings if f.category == analysis_config.get("security_category")]
    quality_severity_total = sum(weights.get(f.severity.value, 0) for f in quality_findings)
    security_severity_total = sum(weights.get(f.severity.value, 0) for f in security_findings)

    quality_score = max(
        0,
        100
        - len(quality_findings) * settings.quality_penalty_per_finding
        - min(quality_severity_total // settings.quality_severity_divisor, settings.max_quality_severity_penalty),
    )
    security_score = max(
        0,
        100
        - len(security_findings) * settings.security_penalty_per_finding
        - min(security_severity_total // settings.security_severity_divisor, settings.max_security_severity_penalty),
    )

    return min(100, quality_score), min(100, security_score)
