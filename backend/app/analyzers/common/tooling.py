"""Shared utilities for analyzers."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

from app.core.repository_config import get_repository_config
from app.models.finding import Finding
from app.models.severity import Severity
import time


class AnalyzerError(Exception):
    """Raised when a static-analysis tool fails or returns unparseable output."""

    def __init__(self, message: str, tool: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.tool = tool
        self.details = details or {}


def run_command(
    command: list[str],
    cwd: str | None = None,
    ok_exit_codes: tuple[int, ...] | None = None,
    timeout: Optional[int] = None,
) -> str:
    """Execute a configured analyzer command and return stdout."""
    if ok_exit_codes is None:
        configured = get_repository_config().load("analysis.json").get("tool_exit_codes", {}).get("default", [0, 1])
        ok_exit_codes = tuple(int(code) for code in configured)

    # Instrument analyzer runs with metrics
    start = time.time()
    tool_name = command[0] if command else "unknown"
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        # Record failure metric and latency
        try:
            from app.core import metrics as _metrics
            _metrics.analyzer_runs_total.labels(tool_name, "failure").inc()
            _metrics.analyzer_run_latency_seconds.labels(tool_name).observe(time.time() - start)
        except Exception:
            pass
        raise AnalyzerError(
            f"Tool timed out after {timeout}s",
            tool=command[0] if command else "unknown",
            details={"command": " ".join(command)},
        )
    if completed.returncode not in ok_exit_codes:
        try:
            from app.core import metrics as _metrics
            _metrics.analyzer_runs_total.labels(tool_name, "failure").inc()
            _metrics.analyzer_run_latency_seconds.labels(tool_name).observe(time.time() - start)
        except Exception:
            pass
        raise AnalyzerError(
            f"Tool exited with code {completed.returncode}",
            tool=command[0],
            details={"stdout": completed.stdout, "stderr": completed.stderr},
        )
    # Success path: record metrics
    try:
        from app.core import metrics as _metrics
        _metrics.analyzer_runs_total.labels(tool_name, "success").inc()
        _metrics.analyzer_run_latency_seconds.labels(tool_name).observe(time.time() - start)
    except Exception:
        pass
    return completed.stdout


def render_command_options(options: list[str], values: dict[str, str]) -> list[str]:
    """Render configured command option tokens."""
    return [option.format(**values) for option in options]


def write_temp_source(source: str, filename: str, directory: str | None = None) -> Path:
    """Write source to a temp file and return its path."""
    temp_dir = Path(directory or tempfile.gettempdir())
    temp_dir.mkdir(parents=True, exist_ok=True)
    import uuid
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    tmp_path = temp_dir / unique_name
    tmp_path.write_text(source, encoding="utf-8")
    return tmp_path


def severity_from_config(value: str | None, default: str | None = None) -> Severity:
    """Convert a configured severity string to the Severity enum."""
    configured_default = default or get_repository_config().load("analysis.json").get("default_severity")
    candidate = (value or configured_default or Severity.INFO.value).lower()
    try:
        return Severity(candidate)
    except ValueError:
        return Severity(configured_default or Severity.INFO.value)


def severity_from_score(score: int | float | None) -> Severity:
    """Map a numeric risk score to Severity using repository configuration."""
    if score is None:
        return Severity.INFO
    for item in get_repository_config().load("severity.json").get("numeric_thresholds", []):
        if score >= item.get("threshold", 0):
            return severity_from_config(item.get("severity"), Severity.INFO.value)
    return Severity.INFO


def severity_from_string(value: str | None) -> Severity:
    """Map a tool-reported severity string to the Severity enum."""
    if not value:
        return Severity.INFO
    mapped = get_repository_config().load("severity.json").get("string_map", {}).get(value.lower())
    return severity_from_config(mapped, get_repository_config().load("analysis.json").get("default_severity"))


def normalize_finding_severity(finding: Finding) -> Finding:
    """Apply configuration-driven rule overrides to a finding's severity.

    Static-analysis tools sometimes report a severity that is logically
    incorrect for the security impact of the rule (for example, Bandit reports
    hardcoded passwords as LOW even though exposed credentials can lead to
    unauthorized access). This function applies the project's security rules
    (configured in severity.json -> rule_overrides) to correct clearly
    incorrect or missing severities while preserving valid tool-provided
    severities for rules that are not overridden.
    """
    severity_config = get_repository_config().load("severity.json")
    overrides = severity_config.get("rule_overrides", {}) or {}
    if not overrides:
        return finding

    rule_id = finding.rule_id
    override = overrides.get(rule_id)
    if override is None:
        return finding

    corrected = severity_from_config(override)
    if corrected == finding.severity:
        return finding
    return finding.model_copy(update={"severity": corrected})


def normalize_findings(findings: list[Finding]) -> list[Finding]:
    """Normalize severity for every finding using configured rule overrides."""
    return [normalize_finding_severity(f) for f in findings]


def build_finding(
    *,
    rule_id: str,
    title: str,
    description: str,
    severity: Severity,
    category: str,
    line: int | None = None,
    column: int | None = None,
    evidence: str | None = None,
    remediation: str | None = None,
    tool_source: str | None = None,
    finding_metadata: dict[str, Any] | None = None,
) -> Finding:
    """Construct a Finding from parsed tool output."""
    location: str | None = None
    if line is not None:
        location = f"{line}:{column}" if column is not None else str(line)

    return Finding(
        rule_id=rule_id,
        title=title,
        description=description,
        severity=severity,
        category=category,
        location=location,
        evidence=evidence or description,
        remediation=remediation,
        tool_source=tool_source,
        finding_metadata=finding_metadata,
    )


def build_finding_from_tool_result(
    rule_id: str,
    message: str,
    severity: Severity,
    category: str,
    location: dict[str, Any] | None = None,
    evidence: str | None = None,
    tool_source: str | None = None,
) -> Finding:
    """Backward-compatible factory for older analyzer callers."""
    line = None
    column = None
    snippet = None
    if location:
        line = location.get("line")
        column = location.get("column")
        snippet = location.get("code") or location.get("snippet")
    return build_finding(
        rule_id=rule_id,
        title=message,
        description=message,
        severity=severity,
        category=category,
        line=line,
        column=column,
        evidence=snippet or evidence or message,
        tool_source=tool_source,
    )


def get_python_executable() -> str:
    """Return the interpreter running this process."""
    return sys.executable
