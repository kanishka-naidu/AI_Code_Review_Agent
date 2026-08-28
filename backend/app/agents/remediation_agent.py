"""Gemini-powered remediation and report recommendations."""
from __future__ import annotations

import json
from typing import Any, Optional

from app.core.llm import BaseLLMClient, get_llm_client
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.core.template_loader import get_prompt_loader
from app.models.finding import Finding

logger = get_logger(__name__)


class RemediationAgent:
    """Generate per-finding remediation and report-level recommendations."""

    def __init__(self, llm: Optional[BaseLLMClient] = None) -> None:
        from app.core.config import get_settings

        self._settings = get_settings()
        self._llm = llm or self._build_llm()
        self._prompt_loader = get_prompt_loader()
        self._repo_config = get_repository_config()

    async def suggest(self, findings: list[Finding]) -> list[str]:
        """Return one remediation string per finding (async)."""
        if not findings:
            return []
        result: list[Optional[str]] = [finding.remediation for finding in findings]
        pending = [(index, finding) for index, finding in enumerate(findings) if not finding.remediation]
        if pending and self._llm is not None:
            generated = await self._batch_remediate([finding for _, finding in pending])
            for (index, _finding), remediation in zip(pending, generated):
                result[index] = remediation
        return [value or self._derive_from_finding(findings[index]) for index, value in enumerate(result)]

    async def enrich_missing_fields(self, findings: list[Finding]) -> list[Finding]:
        """Populate missing structured remediation fields from generated remediation text (async)."""
        remediations = await self.suggest(findings)
        enriched: list[Finding] = []
        for finding, remediation in zip(findings, remediations):
            updates: dict[str, Any] = {}
            if remediation and not finding.remediation:
                updates["remediation"] = remediation
            enriched.append(finding.model_copy(update=updates) if updates else finding)
        return enriched

    async def generate_report_recommendations(self, findings: list[Finding]) -> list[str]:
        """Generate prioritized recommendations from findings (async)."""
        if not findings:
            return await self._no_findings_recommendations()
        sorted_findings = self._sort_by_configured_severity(findings)[:5]
        formatted = "\n".join(
            json.dumps(
                {
                    "rule_id": finding.rule_id,
                    "severity": finding.severity.value,
                    "category": finding.category,
                    "description": finding.description,
                    "owasp_reference": finding.owasp_reference,
                },
                ensure_ascii=True,
            )
            for finding in sorted_findings
        )
        categories = sorted({finding.category for finding in findings})
        severities = sorted({finding.severity.value for finding in findings})
        if self._llm is None:
            return self._fallback_recommendations(findings)
        try:
            raw = await self._llm.agenerate(
                self._prompt_loader.render(
                    "report_recommendations.txt",
                    categories=", ".join(categories),
                    severities=", ".join(severities),
                    total_findings=len(findings),
                    top_findings=formatted,
                ),
                temperature=self._settings.llm_default_temperature,
                max_tokens=min(600, self._settings.llm_default_max_tokens),
            )
            parsed = self._parse_numbered_list(raw)
            return parsed or self._fallback_recommendations(findings)
        except Exception as exc:
            logger.warning("Report recommendation generation failed: %s", exc)
            return self._fallback_recommendations(findings)

    def _build_llm(self) -> BaseLLMClient | None:
        try:
            return get_llm_client()
        except Exception as exc:
            logger.warning("LLM client unavailable for RemediationAgent: %s", exc)
            return None

    async def _batch_remediate(self, findings: list[Finding]) -> list[str]:
        finding_lines = "\n".join(json.dumps(finding.model_dump(), default=str, ensure_ascii=True) for finding in findings)
        try:
            raw = await (self._llm.agenerate(
                self._prompt_loader.render("remediation_batch.txt", findings=finding_lines),
                temperature=self._settings.llm_default_temperature,
                max_tokens=min(1200, self._settings.llm_default_max_tokens),
            ) if self._llm else "")
            parsed = self._parse_json_array(raw)
            return [self._format_remediation(parsed.get(index + 1, {}), findings[index]) for index in range(len(findings))]
        except Exception as exc:
            logger.warning("Batch remediation failed: %s", exc)
            return [self._derive_from_finding(finding) for finding in findings]

    @staticmethod
    def _parse_json_array(raw: str) -> dict[int, dict[str, Any]]:
        text = raw.strip()
        if text.startswith("```"):
            text = "\n".join(line for line in text.splitlines() if not line.strip().startswith("```")).strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, list):
            return {}
        return {int(item.get("index", index + 1)): item for index, item in enumerate(parsed) if isinstance(item, dict)}

    @staticmethod
    def _format_remediation(entry: dict[str, Any], finding: Finding) -> str:
        """Build a plain-English remediation explanation from structured LLM output."""
        parts: list[str] = []

        root_cause = entry.get("root_cause")
        if root_cause:
            parts.append(f"Why this happens: {root_cause}")

        steps = entry.get("steps")
        if isinstance(steps, list) and steps:
            clean_steps = [str(step).strip() for step in steps if str(step).strip()]
            if clean_steps:
                parts.append("What to do:")
                parts.extend(f"  {index + 1}. {step}" for index, step in enumerate(clean_steps))

        best_practice = entry.get("best_practice")
        if best_practice:
            parts.append(f"Best practice: {best_practice}")

        prevention = entry.get("prevention")
        if prevention:
            parts.append(f"How to prevent it in the future: {prevention}")

        if parts:
            return "\n".join(parts)

        # Fall back to a clean human-readable sentence
        title = finding.title or "This issue"
        description = finding.description or ""
        return f"{title}. {description}".strip()

    def _fallback_recommendations(self, findings: list[Finding]) -> list[str]:
        recommendations: list[str] = []
        for finding in self._sort_by_configured_severity(findings)[:5]:
            title = finding.title or "A code issue"
            severity = finding.severity.label
            category = finding.category or "code"
            description = finding.description or ""
            if description and description.lower() != title.lower():
                recommendations.append(
                    f"{title}. This is a {severity} severity {category} issue. {description} Fix it by applying the suggested remediation."
                )
            else:
                recommendations.append(
                    f"{title}. This is a {severity} severity {category} issue. Fix it by applying the suggested remediation."
                )
        return recommendations

    async def _no_findings_recommendations(self) -> list[str]:
        if self._llm is None:
            return []
        try:
            raw = await self._llm.agenerate(
                self._prompt_loader.render("no_findings_recommendations.txt", language="", metadata={}),
                temperature=0.15,
                max_tokens=200,
            )
            return [line.strip("- ").strip() for line in raw.splitlines() if line.strip()]
        except Exception as exc:
            logger.warning("No-findings recommendation generation failed: %s", exc)
            return []

    def _derive_from_finding(self, finding: Finding) -> str:
        return self._derive_static_from_metadata(finding)

    @staticmethod
    def _derive_static_from_metadata(finding: Finding) -> str:
        """Build a plain-English fallback explanation for a finding."""
        title = finding.title or "This code issue"
        severity = finding.severity.label
        category = finding.category or "code"
        description = finding.description or ""
        location = f"line {finding.location}" if finding.location else "the reported location"

        parts = [
            f"What is wrong: {title}.",
        ]
        if description and description.lower() != title.lower():
            parts.append(f" {description}")
        parts.append(
            f" This is a {severity} severity {category} issue located at {location}."
        )
        parts.append(
            " Fix it by reviewing the code at that location and applying the recommended remediation."
        )
        return " ".join(parts)

    def _sort_by_configured_severity(self, findings: list[Finding]) -> list[Finding]:
        order = self._repo_config.load("severity.json").get("order_desc", [])
        return sorted(findings, key=lambda finding: order.index(finding.severity.value) if finding.severity.value in order else len(order))

    @staticmethod
    def _parse_numbered_list(raw: str) -> list[str]:
        items: list[str] = []
        current: list[str] = []
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped and stripped[0].isdigit() and ". " in stripped[:5]:
                if current:
                    items.append(" ".join(current).strip())
                current = [stripped.split(". ", 1)[1]]
            elif current and stripped:
                current.append(stripped)
        if current:
            items.append(" ".join(current).strip())
        return items
