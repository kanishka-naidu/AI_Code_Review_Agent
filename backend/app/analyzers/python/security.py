"""Python security analyzer using configured Bandit and Semgrep invocations."""
from __future__ import annotations

import json
import re
import shutil
from typing import Any

from app.analyzers.base.analyzer import Analyzer
from app.analyzers.common.tooling import (
    AnalyzerError,
    build_finding,
    get_python_executable,
    render_command_options,
    run_command,
    severity_from_config,
    write_temp_source,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.models.finding import Finding
from app.models.severity import Severity

logger = get_logger(__name__)

_HARDCODED_SECRET_PATTERN = re.compile(
    r"^(?P<assign>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"](?P<value>.+?)['\"]\s*$",
    re.MULTILINE,
)

_HARDCODED_SECRET_KEYWORDS = {
    "api_key",
    "apikey",
    "secret_key",
    "password",
    "passwd",
    "pwd",
    "token",
    "auth_token",
    "access_token",
    "private_key",
    "client_secret",
}


class PythonSecurityAnalyzer(Analyzer):
    name = "python_security"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._analysis_config = get_repository_config().load("analysis.json")
        self._severity_config = get_repository_config().load("severity.json")
        self._analyzer_config = get_repository_config().load("analyzers.json")

    def analyze(self, source: str, filename: str) -> tuple[list[Finding], dict[str, Any]]:
        """Run configured Python security tools and merge findings."""
        logger.info("PythonSecurityAnalyzer started for '%s'", filename)
        default_name = str(self._analysis_config.get("python_default_filename"))
        temp_path = write_temp_source(source, filename or default_name)
        findings = self._run_bandit(temp_path)
        if len(source.strip().splitlines()) >= 30:
            findings += self._run_semgrep(temp_path)
        findings += self._run_hardcoded_secret_detection(source)
        logger.info("PythonSecurityAnalyzer finished for '%s' with %d findings", filename, len(findings))
        return findings, {}

    def _run_hardcoded_secret_detection(self, source: str) -> list[Finding]:
        """Detect hardcoded secrets via simple assignment pattern matching."""
        findings: list[Finding] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            stripped = line.strip()
            match = _HARDCODED_SECRET_PATTERN.match(stripped)
            if not match:
                continue
            key = match.group("assign").lower()
            if key not in _HARDCODED_SECRET_KEYWORDS:
                continue
            findings.append(
                build_finding(
                    rule_id="hardcoded_secret",
                    title=f"Hardcoded secret: {match.group('assign')}",
                    description=f"Hardcoded secret detected in assignment to '{match.group('assign')}'.",
                    severity=Severity.HIGH,
                    category=str(self._analysis_config.get("security_category")),
                    line=line_number,
                    evidence=stripped,
                    tool_source="python_security",
                    finding_metadata={"key": match.group("assign")},
                )
            )
        return findings

    def _run_bandit(self, temp_path: Any) -> list[Finding]:
        python = get_python_executable()
        module = self._analyzer_config.get("tool_modules", {}).get("bandit")
        # Prefer explicit settings; if empty, fall back to repository analyzer configuration
        bandit_options_str = self._settings.bandit_options or self._analyzer_config.get("tool_options", {}).get("bandit", "")
        options = render_command_options(
            self._settings.csv_list(bandit_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent)},
        )
        try:
            output = run_command([python, "-m", str(module), *options], cwd=str(temp_path.parent), timeout=self._settings.analyzer_timeout)
        except AnalyzerError as exc:
            logger.error("Bandit failed: %s; stderr=%s", exc.message, exc.details.get("stderr", ""))
            return []

        try:
            payload = json.loads(output or "{}")
        except json.JSONDecodeError as exc:
            logger.error("Bandit returned invalid JSON: %s", exc)
            return []

        severity_map = self._severity_config.get("bandit", {})
        findings: list[Finding] = []
        for issue in payload.get("results", []):
            test_id = issue.get("test_id") or module
            test_name = issue.get("test_name") or test_id
            issue_text = issue.get("issue_text") or test_name
            raw_sev = str(issue.get("issue_severity") or "").upper()
            line_number = issue.get("line_number")
            if line_number is None:
                line_range = issue.get("line_range") or []
                line_number = line_range[0] if line_range else None
            findings.append(
                build_finding(
                    rule_id=str(test_id),
                    title=f"{test_name}: {str(issue_text)[:120]}",
                    description=str(issue_text),
                    severity=severity_from_config(severity_map.get(raw_sev)),
                    category=str(self._analysis_config.get("security_category")),
                    line=line_number,
                    evidence=(issue.get("code") or issue_text),
                    tool_source=str(module),
                    finding_metadata={
                        "confidence": issue.get("issue_confidence") or "",
                        "test_name": test_name,
                        "more_info": issue.get("more_info") or "",
                    },
                )
            )
        return findings

    def _run_semgrep(self, temp_path: Any) -> list[Finding]:
        binary = str(self._analyzer_config.get("tool_binaries", {}).get("semgrep"))
        if not shutil.which(binary):
            logger.info("Configured Semgrep binary '%s' not found; skipping", binary)
            return []

        semgrep_options_str = self._settings.semgrep_options or self._analyzer_config.get("tool_options", {}).get("semgrep", "")
        options = render_command_options(
            self._settings.csv_list(semgrep_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent)},
        )
        timeout = self._settings.semgrep_timeout or None
        try:
            output = run_command([binary, *options], cwd=str(temp_path.parent), timeout=timeout)
        except AnalyzerError as exc:
            logger.error("Semgrep failed: %s; stderr=%s", exc.message, exc.details.get("stderr", ""))
            return []

        try:
            payload = json.loads(output or "{}")
        except json.JSONDecodeError as exc:
            logger.error("Semgrep returned invalid JSON: %s", exc)
            return []

        severity_map = self._severity_config.get("semgrep", {})
        findings: list[Finding] = []
        for result in payload.get("results", []):
            check_id = result.get("check_id") or binary
            extra = result.get("extra") or {}
            message = extra.get("message") or check_id
            raw_sev = str(extra.get("severity") or "").upper()
            start = result.get("start") or {}
            meta = extra.get("metadata") or {}
            owasp_refs = meta.get("owasp") or meta.get("references") or []
            finding = build_finding(
                rule_id=str(check_id),
                title=str(message)[:120],
                description=str(message),
                severity=severity_from_config(severity_map.get(raw_sev)),
                category=str(self._analysis_config.get("security_category")),
                line=start.get("line"),
                column=start.get("col"),
                evidence=extra.get("lines") or message,
                tool_source=binary,
                finding_metadata={"check_id": check_id, "metadata": meta},
            )
            if owasp_refs:
                finding = finding.model_copy(update={"owasp_reference": owasp_refs[0]})
            findings.append(finding)
        return findings
