"""Java security analyzer using configured Semgrep invocation."""
from __future__ import annotations

import json
import shutil
from typing import Any

from app.analyzers.base.analyzer import Analyzer
from app.analyzers.common.tooling import AnalyzerError, build_finding, render_command_options, run_command, severity_from_config, write_temp_source
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.models.finding import Finding

logger = get_logger(__name__)


class JavaSecurityAnalyzer(Analyzer):
    name = "java_security"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._analysis_config = get_repository_config().load("analysis.json")
        self._severity_config = get_repository_config().load("severity.json")
        self._analyzer_config = get_repository_config().load("analyzers.json")

    def analyze(self, source: str, filename: str) -> tuple[list[Finding], dict[str, Any]]:
        """Run configured Java security analysis."""
        logger.info("JavaSecurityAnalyzer started for '%s'", filename)
        binary = str(self._analyzer_config.get("tool_binaries", {}).get("semgrep"))
        if not shutil.which(binary):
            logger.warning("Configured Semgrep binary '%s' not found; skipping Java security analysis", binary)
            return [], {}

        default_name = str(self._analysis_config.get("java_default_filename"))
        safe_filename = filename or default_name
        if not safe_filename.endswith(".java"):
            safe_filename = f"{safe_filename}.java"
        temp_path = write_temp_source(source, safe_filename)
        semgrep_options_str = self._settings.semgrep_options or self._analyzer_config.get("tool_options", {}).get("semgrep", "")
        options = render_command_options(
            self._settings.csv_list(semgrep_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent)},
        )
        try:
            output = run_command([binary, *options], cwd=str(temp_path.parent), timeout=self._settings.semgrep_timeout or None)
            logger.info("Java Semgrep raw output[:500]: %r", output[:500])
            payload = json.loads(output or "{}")
        except (AnalyzerError, json.JSONDecodeError) as exc:
            logger.error("Java Semgrep failed or returned invalid output: %s", exc)
            return [], {}

        severity_map = self._severity_config.get("semgrep", {})
        findings: list[Finding] = []
        for result in payload.get("results", []):
            check_id = result.get("check_id") or binary
            extra = result.get("extra") or {}
            message = extra.get("message") or check_id
            start = result.get("start") or {}
            meta = extra.get("metadata") or {}
            owasp_refs = meta.get("owasp") or meta.get("references") or []
            finding = build_finding(
                rule_id=str(check_id),
                title=str(message)[:120],
                description=str(message),
                severity=severity_from_config(severity_map.get(str(extra.get("severity") or "").upper())),
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
        return findings, {}
