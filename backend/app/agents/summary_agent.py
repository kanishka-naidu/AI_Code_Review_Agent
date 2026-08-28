"""Summary Agent for AI explanations."""
from __future__ import annotations

import json
from typing import Any, Optional

from app.core.llm import BaseLLMClient, get_llm_client
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.core.template_loader import get_prompt_loader

logger = get_logger(__name__)


class SummaryAgent:
    """Generate an overall analysis explanation."""

    def __init__(self, llm: Optional[BaseLLMClient] = None) -> None:
        self._llm = llm or self._build_llm()
        self._prompt_loader = get_prompt_loader()
        self._repo_config = get_repository_config()

    async def summarize(self, report: dict[str, Any]) -> str:
        """Generate a comprehensive explanation from analysis data (async)."""
        if self._llm is not None:
            try:
                return await self._llm.agenerate(
                    self._prompt_loader.render("summary.txt", analysis_data=json.dumps(report, default=str, ensure_ascii=True)),
                    temperature=0.2,
                    max_tokens=500,
                )
            except Exception as exc:
                logger.warning("Summary generation failed: %s", exc)
        return self._derived_fallback(report)

    def _build_llm(self) -> BaseLLMClient | None:
        try:
            return get_llm_client()
        except Exception as exc:
            logger.warning("LLM client unavailable for SummaryAgent: %s", exc)
            return None

    def _derived_fallback(self, report: dict[str, Any]) -> str:
        findings = report.get("findings", [])
        lines = [
            f"filename: {report.get('filename')}",
            f"language: {report.get('language')}",
            f"quality_score: {report.get('quality_score')}",
            f"security_score: {report.get('security_score')}",
            f"total_findings: {len(findings)}",
        ]
        order = self._repo_config.load("severity.json").get("order_desc", [])
        for severity in order:
            rules = [
                finding.get("rule_id")
                for finding in findings
                if isinstance(finding, dict) and finding.get("severity") == severity
            ]
            if rules:
                lines.append(f"{severity.upper()}: {', '.join(str(rule) for rule in rules)}")
        return "\n".join(lines)
