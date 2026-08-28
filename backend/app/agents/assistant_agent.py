"""Conversational code assistant grounded in analysis and RAG context."""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from app.agents.rag_agent import RAGAgent
from app.core.llm import BaseLLMClient, get_llm_client
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.core.template_loader import get_prompt_loader

logger = get_logger(__name__)


class AssistantAgent:
    """Answer free-form developer questions using supplied project context."""

    def __init__(self, rag_agent: RAGAgent | None = None, llm: Optional[BaseLLMClient] = None) -> None:
        from app.core.config import get_settings

        self._settings = get_settings()
        self._rag = rag_agent or RAGAgent()
        self._llm = llm or self._build_llm()
        self._prompt_loader = get_prompt_loader()
        self._reporting = get_repository_config().load("reporting.json")

    def prepare_context(self, report_data: dict[str, Any], source_code: str | None = None) -> dict[str, Any]:
        """Build compact assistant context from a report and optional source code."""
        findings = report_data.get("findings", [])
        # If explicit source_code is not provided, fall back to the source code
        # embedded in the report's assistant_context (if present).
        if source_code is None:
            assistant_ctx = report_data.get("assistant_context") or {}
            if isinstance(assistant_ctx, dict):
                source_code = assistant_ctx.get("source_code")
        return {
            "report_id": report_data.get("report_id"),
            "filename": report_data.get("filename"),
            "language": report_data.get("language"),
            "quality_score": report_data.get("quality_score"),
            "security_score": report_data.get("security_score"),
            "severity_distribution": report_data.get("severity_distribution"),
            "finding_count": len(findings) if isinstance(findings, list) else 0,
            "findings": findings,
            "recommendations": report_data.get("recommendations", []),
            "summary": report_data.get("summary") or report_data.get("explanation"),
            "pr_summary": report_data.get("pr_summary"),
            "source_code": source_code,
        }

    async def answer(
        self,
        question: str,
        *,
        analysis_context: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list[str]]:
        """Answer a free-form question grounded in available context (async)."""
        context_text = json.dumps(analysis_context or {}, default=str, ensure_ascii=True)
        history_text = json.dumps(conversation_history or [], ensure_ascii=True)
        retrieval_query = f"{question}\n{context_text[:2000]}"
        retrieved = self._rag.retrieve_context(retrieval_query)
        sources = retrieved.get("sources", [])
        retrieved_context = "\n\n".join(retrieved.get("chunks", []))

        if self._llm is None:
            return str(self._reporting.get("no_context_answer")), sources

        prompt = self._prompt_loader.render(
            "assistant.txt",
            conversation_history=history_text,
            analysis_context=context_text,
            retrieved_context=retrieved_context,
            question=question,
        )
        answer = await self._llm.agenerate(prompt, temperature=self._settings.llm_default_temperature, max_tokens=self._settings.llm_default_max_tokens)
        return answer, sources

    @staticmethod
    def new_conversation_id() -> str:
        """Create a conversation identifier."""
        return str(uuid.uuid4())

    def _build_llm(self) -> BaseLLMClient | None:
        try:
            return get_llm_client()
        except Exception as exc:
            logger.warning("LLM client unavailable for AssistantAgent: %s", exc)
            return None
