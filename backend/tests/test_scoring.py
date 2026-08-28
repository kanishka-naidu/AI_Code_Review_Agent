"""Unit tests for category-aware score computation."""

from app.analyzers.common.scoring import compute_scores
from app.models.finding import Finding
from app.models.severity import Severity


def _finding(*, category: str, severity: Severity) -> Finding:
    return Finding(
        rule_id="test-rule",
        title="Test finding",
        description="Test description",
        severity=severity,
        category=category,
    )


def test_security_findings_do_not_penalize_quality_severity():
    """Quality score must ignore security finding severities."""
    findings = [
        _finding(category="security", severity=Severity.CRITICAL),
        _finding(category="security", severity=Severity.CRITICAL),
    ]

    quality_score, security_score = compute_scores(findings)

    assert quality_score == 100
    assert security_score < 100


def test_quality_findings_do_not_penalize_security_severity():
    """Security score must ignore quality finding severities."""
    findings = [
        _finding(category="quality", severity=Severity.HIGH),
        _finding(category="quality", severity=Severity.HIGH),
    ]

    quality_score, security_score = compute_scores(findings)

    assert quality_score < 100
    assert security_score == 100
