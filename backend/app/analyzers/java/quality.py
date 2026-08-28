"""Java quality analyzer using configured PMD invocation."""
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


class JavaQualityAnalyzer(Analyzer):
    name = "java_quality"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._analysis_config = get_repository_config().load("analysis.json")
        self._severity_config = get_repository_config().load("severity.json")
        self._analyzer_config = get_repository_config().load("analyzers.json")

    def analyze(self, source: str, filename: str) -> tuple[list[Finding], dict[str, Any]]:
        """Run configured PMD rulesets."""
        logger.info("JavaQualityAnalyzer started for '%s'", filename)
        binary = str(self._analyzer_config.get("tool_binaries", {}).get("pmd"))
        if shutil.which(binary) is None:
            logger.warning("Configured PMD binary '%s' not found; skipping Java quality analysis", binary)
            return [], {}

        default_name = str(self._analysis_config.get("java_default_filename"))
        temp_path = write_temp_source(source, filename or default_name)
        findings: list[Finding] = []
        for ruleset in self._analyzer_config.get("java_quality", {}).get("pmd_rulesets", []):
            findings.extend(self._run_pmd(binary, temp_path, str(ruleset)))
        logger.info("JavaQualityAnalyzer finished for '%s' with %d findings", filename, len(findings))
        return findings, {}

    def _run_pmd(self, binary: str, temp_path: Any, ruleset: str) -> list[Finding]:
        pmd_options_str = self._settings.pmd_options or self._analyzer_config.get("tool_options", {}).get("pmd", "")
        options = render_command_options(
            self._settings.csv_list(pmd_options_str),
            {"source_path": str(temp_path), "source_dir": str(temp_path.parent), "ruleset": ruleset},
        )
        exit_codes = tuple(int(code) for code in self._analysis_config.get("tool_exit_codes", {}).get("pmd", [0, 1, 4]))
        try:
            output = run_command([binary, *options], cwd=str(temp_path.parent), ok_exit_codes=exit_codes, timeout=self._settings.analyzer_timeout)
            payload = json.loads(output or "{}")
        except (AnalyzerError, json.JSONDecodeError) as exc:
            logger.error("PMD failed or returned invalid output for ruleset '%s': %s", ruleset, exc)
            return []

        priority_map = self._severity_config.get("pmd_priority", {})
        findings: list[Finding] = []
        for file_entry in payload.get("files", []):
            for violation in file_entry.get("violations", []):
                rule = violation.get("rule") or "pmd-rule"
                ruleset_name = violation.get("ruleset") or ruleset
                description = violation.get("description") or rule
                priority = str(violation.get("priority") or "")
                findings.append(
                    build_finding(
                        rule_id=f"pmd-{rule}",
                        title=f"[{ruleset_name}] {rule}",
                        description=str(description),
                        severity=severity_from_config(priority_map.get(priority)),
                        category=str(self._analysis_config.get("quality_category")),
                        line=violation.get("beginline"),
                        column=violation.get("begincolumn"),
                        evidence=str(description),
                        tool_source=binary,
                        finding_metadata={"ruleset": ruleset_name, "priority": priority},
                    )
                )
        return findings
