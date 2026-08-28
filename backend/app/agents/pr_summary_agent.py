"""PR Summary Agent."""
from __future__ import annotations

import json
from typing import Any, Optional

from app.core.llm import BaseLLMClient, get_llm_client
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.core.template_loader import get_prompt_loader

logger = get_logger(__name__)


class PRSummaryAgent:
    """Generate a pull request summary from an analysis report."""

    def __init__(self, llm: Optional[BaseLLMClient] = None) -> None:
        from app.core.config import get_settings

        self._settings = get_settings()
        self._llm = llm or self._build_llm()
        self._prompt_loader = get_prompt_loader()
        self._repo_config = get_repository_config()

    async def generate_pr_summary(self, report_dict: dict[str, Any]) -> str:
        """Generate a markdown PR summary (async)."""
        filename = report_dict.get("filename") or ""
        if self._llm is not None:
            try:
                summary = await self._llm.agenerate(
                    self._prompt_loader.render("pr_summary.txt", analysis_data=json.dumps(report_dict, default=str, ensure_ascii=True)),
                    temperature=self._settings.llm_default_temperature,
                    max_tokens=700,
                )
                return self._correct_filename(summary, filename)
            except Exception as exc:
                logger.warning("PR summary generation failed: %s", exc)
        return self._fallback_summary(report_dict)

    @staticmethod
    def _correct_filename(summary: str, filename: str) -> str:
        """Replace an incorrect 'pasted_code' reference with the real filename.

        The LLM occasionally defaults to 'pasted_code' even when an actual file
        was uploaded. When the real filename is known and differs from the
        pasted-code fallback, correct any such references so the summary always
        reflects the actual analyzed file.
        """
        if not filename or not summary:
            return summary
        if filename == "pasted_code":
            return summary
        return summary.replace("pasted_code", filename)

    def _build_llm(self) -> BaseLLMClient | None:
        try:
            return get_llm_client()
        except Exception as exc:
            logger.warning("LLM client unavailable for PRSummaryAgent: %s", exc)
            return None

    def _fallback_summary(self, report: dict[str, Any]) -> str:
        findings = report.get("findings", [])
        severity_counts = {severity: 0 for severity in self._repo_config.load("severity.json").get("order_desc", [])}
        for finding in findings:
            if isinstance(finding, dict):
                severity = finding.get("severity")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        top_rules = [finding.get("rule_id") for finding in findings[:5] if isinstance(finding, dict)]
        severity_lines = [
            f"- {severity.upper()}: {count}"
            for severity, count in severity_counts.items()
            if count > 0
        ]
        return "\n".join(
            [
                f"# Pull Request Analysis - {report.get('filename')} ({report.get('language')})",
                "## Executive Summary",
                f"Findings: {len(findings)}; quality_score: {report.get('quality_score')}; security_score: {report.get('security_score')}.",
                "## Severity Breakdown",
                "\n".join(severity_lines) if severity_lines else "- No findings",
                "## Top Priority Fixes",
                ", ".join(str(rule) for rule in top_rules),
            ]
        )
