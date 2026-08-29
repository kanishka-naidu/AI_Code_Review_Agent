"""
LangGraph Orchestrator.

Graph nodes (in execution order):
  1. validate       — validate submission language and code
  2. detect         — canonical language detection
  3. analyze        — run quality + security analyzers (independent, merged)
  4. rag_enrich     — enrich security findings with OWASP context via ChromaDB + Gemini
  5. remediate      — generate per-finding + report-level recommendations via Gemini
  6. summarize      — generate Gemini explanation and scores
  7. pr_summary     — generate structured PR summary via Gemini
  8. build_report   — assemble the final AnalysisReport

Each node receives and mutates a shared state dict.
Analyzer failures are caught independently and recorded in state["errors"].
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.assistant_agent import AssistantAgent
from app.agents.language_detection_agent import LanguageDetectionAgent
from app.agents.pr_summary_agent import PRSummaryAgent
from app.agents.rag_agent import RAGAgent
from app.agents.remediation_agent import RemediationAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.validation_agent import ValidationAgent
from app.analyzers.base.analyzer import Analyzer
from app.analyzers.common.scoring import compute_scores
from app.analyzers.common.tooling import AnalyzerError, normalize_findings
from app.analyzers.java.quality import JavaQualityAnalyzer
from app.analyzers.java.security import JavaSecurityAnalyzer
from app.analyzers.python.quality import PythonQualityAnalyzer
from app.analyzers.python.security import PythonSecurityAnalyzer
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.repository_config import get_repository_config
from app.models.finding import Finding
from app.models.report import AnalysisReport, SeverityDistribution
from app.models.submission import CodeSubmission

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline state
# ─────────────────────────────────────────────────────────────────────────────

class PipelineState(TypedDict, total=False):
    submission: CodeSubmission
    language: str
    validation: dict[str, Any]
    findings: list[Finding]
    quality_score: int
    security_score: int
    recommendations: list[str]
    summary: str
    pr_summary: str
    assistant_context: dict[str, Any]
    report: AnalysisReport
    errors: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Node functions (pure, dependency-injected via closures)
# ─────────────────────────────────────────────────────────────────────────────


def _node_validate(state: PipelineState) -> PipelineState:
    logger.info("[orchestrator] node=validate started")
    submission = state["submission"]
    result = ValidationAgent().validate(submission.language, submission.code)
    state["validation"] = result
    logger.info("[orchestrator] node=validate finished valid=%s", result.get("valid"))
    return state


def _node_detect(state: PipelineState) -> PipelineState:
    logger.info("[orchestrator] node=detect started")
    submission = state["submission"]
    settings = get_settings()
    detected = LanguageDetectionAgent().detect(
        submission.filename or settings.default_submitted_filename, submission.code
    )
    # Prefer the user-supplied language unless it's generic
    final = submission.language if submission.language not in ("text", "") else detected
    state["language"] = final
    logger.info("[orchestrator] node=detect language='%s'", final)
    return state


async def _node_analyze(
    state: PipelineState, analyzers: dict[str, dict[str, Analyzer]]
) -> PipelineState:
    logger.info("[orchestrator] node=analyze started")
    submission = state["submission"]
    language = state.get("language", submission.language)
    filename = submission.filename or get_settings().default_submitted_filename
    errors: list[str] = list(state.get("errors") or [])

    lang_analyzers = analyzers.get(language, {})
    if not lang_analyzers:
        msg = f"No analyzers registered for language '{language}'"
        logger.warning("[orchestrator] %s", msg)
        errors.append(msg)
        state["findings"] = []
        state["errors"] = errors
        return state

    import asyncio

    async def _run_single(name: str, analyzer: Analyzer) -> tuple[str, list[Finding], dict[str, Any]]:
        logger.info("[orchestrator] analyzer='%s' started", name)
        try:
            af, _ = await asyncio.to_thread(analyzer.analyze, submission.code, filename)
            logger.info("[orchestrator] analyzer='%s' finished findings=%d", name, len(af))
            return name, af, {}
        except AnalyzerError as exc:
            err = f"Analyzer '{name}' failed: {exc.message}"
            logger.error("[orchestrator] %s details=%s", err, exc.details)
            return name, [], {"status": "failure", "details": exc.details, "error": err}
        except Exception as exc:
            err = f"Analyzer '{name}' raised: {exc}"
            logger.error("[orchestrator] %s", err)
            return name, [], {"status": "failure", "details": {"exception": str(exc)}, "error": err}

    results = await asyncio.gather(*[_run_single(name, analyzer) for name, analyzer in lang_analyzers.items()])

    findings: list[Finding] = []
    analyzer_status: dict[str, dict] = {}
    for name, af, meta in results:
        findings.extend(af)
        if meta.get("status") == "failure":
            errors.append(meta["error"])
            analyzer_status[name] = meta
        else:
            analyzer_status[name] = {"status": "success", "findings": len(af)}

    # Normalize severity using the project's security rules so that clearly
    # incorrect tool-reported severities (e.g. hardcoded passwords reported as
    # LOW) are corrected before they reach scoring, reports, and the UI.
    findings = normalize_findings(findings)

    state["findings"] = findings
    state["errors"] = errors
    state["analyzer_status"] = analyzer_status

    from app.core.config import get_settings

    settings = get_settings()
    mode = getattr(settings, "analyzer_failure_mode", "partial")
    if errors and mode == "strict":
        logger.error("[orchestrator] analyzer errors and strict mode enabled — aborting pipeline")
        raise AnalyzerError("Analyzers failed", tool="analyzers", details={"errors": errors, "status": analyzer_status})

    logger.info("[orchestrator] node=analyze finished total_findings=%d", len(findings))
    return state


async def _node_rag_enrich(state: PipelineState, rag: RAGAgent) -> PipelineState:
    logger.info("[orchestrator] node=rag_enrich started")
    findings = state.get("findings") or []
    submission = state["submission"]

    if submission.metadata.get("include_rag") is False:
        logger.info("[orchestrator] node=rag_enrich skipped by request metadata")
        return state

    if not findings:
        logger.info("[orchestrator] node=rag_enrich: no findings to enrich")
        return state

    # All findings get RAG enrichment — security and quality both benefit.
    # Batch the entire list in one call to minimise LLM quota consumption.
    logger.info("[orchestrator] node=rag_enrich: enriching %d findings", len(findings))
    try:
        enriched = await rag.enrich_findings_batch(findings)
        state["findings"] = enriched
        logger.info("[orchestrator] node=rag_enrich finished enriched=%d", len(enriched))
    except Exception as exc:
        logger.warning("[orchestrator] RAG enrichment failed; continuing without RAG: %s", exc)
        # Keep original findings unchanged
    return state


async def _node_parallel_post_rag(
    state: PipelineState,
    remediation: RemediationAgent,
    summary: SummaryAgent,
    pr_summary: PRSummaryAgent,
) -> PipelineState:
    """
    Run remediation, summarization, and PR summary generation IN PARALLEL.

    These three stages only depend on findings and scores, not on each other.
    Running them concurrently cuts the critical path LLM calls from 3 to 1,
    reducing overall analysis time significantly.
    """
    logger.info("[orchestrator] parallel post-RAG stages started")

    findings = state.get("findings") or []
    submission = state["submission"]
    errors = state.get("errors") or []

    quality_score, security_score = compute_scores(findings)

    # If analyzers errored and produced no findings, avoid returning a misleading perfect score.
    if errors and not findings:
        logger.warning("[orchestrator] analyzer errors present with no findings; adjusting scores to reflect partial analysis")
        quality_score = 0
        security_score = 0

    report_dict: dict[str, Any] = {
        "filename": submission.filename or get_settings().default_submitted_filename,
        "language": state.get("language", submission.language),
        "quality_score": quality_score,
        "security_score": security_score,
        "findings": [f.model_dump() for f in findings],
    }

    # Launch all three independent LLM stages concurrently
    remediate_coro = _run_remediate(remediation, findings)
    summarize_coro = summary.summarize(report_dict)
    pr_summary_coro = pr_summary.generate_pr_summary(report_dict)

    remediation_results, summary_text, pr_text = await asyncio.gather(
        remediate_coro,
        summarize_coro,
        pr_summary_coro,
        return_exceptions=True,
    )

    # Handle remediation result
    if isinstance(remediation_results, Exception):
        logger.error("[orchestrator] remediation stage failed: %s", remediation_results)
        recommendations_result: list[str] = []
        updated_findings = findings
    else:
        per_recs, recommendations_result = remediation_results
        updated_findings = []
        for i, f in enumerate(findings):
            updates: dict[str, Any] = {}
            if not f.remediation and i < len(per_recs) and per_recs[i]:
                updates["remediation"] = per_recs[i]
            updated_findings.append(f.model_copy(update=updates) if updates else f)

    if isinstance(summary_text, Exception):
        logger.error("[orchestrator] summary stage failed: %s", summary_text)
        summary_text = ""

    if isinstance(pr_text, Exception):
        logger.error("[orchestrator] pr_summary stage failed: %s", pr_text)
        pr_text = ""

    state["findings"] = updated_findings
    state["recommendations"] = recommendations_result
    state["quality_score"] = quality_score
    state["security_score"] = security_score
    state["summary"] = summary_text or ""
    state["pr_summary"] = pr_text or ""

    logger.info(
        "[orchestrator] parallel post-RAG stages finished summary_len=%d pr_len=%d recs=%d",
        len(state["summary"]),
        len(state["pr_summary"]),
        len(state["recommendations"]),
    )
    return state


async def _run_remediate(
    agent: RemediationAgent, findings: list[Finding]
) -> tuple[list[str], list[str]]:
    """Run remediation agent, return (per-finding remediation, report recommendations)."""
    per_recs = await agent.suggest(findings)
    recommendations = await agent.generate_report_recommendations(findings)
    return per_recs, recommendations


async def _node_assistant_context(state: PipelineState, agent: AssistantAgent) -> PipelineState:
    logger.info("[orchestrator] node=assistant_context started")
    submission = state["submission"]
    findings = state.get("findings") or []
    report_data = {
        "filename": submission.filename or get_settings().default_submitted_filename,
        "language": state.get("language", submission.language),
        "quality_score": state.get("quality_score", 100),
        "security_score": state.get("security_score", 100),
        "findings": [finding.model_dump() for finding in findings],
        "recommendations": state.get("recommendations") or [],
        "summary": state.get("summary"),
        "pr_summary": state.get("pr_summary"),
    }
    # prepare_context is synchronous by design; keep as sync call
    state["assistant_context"] = agent.prepare_context(report_data, source_code=submission.code)
    logger.info("[orchestrator] node=assistant_context finished")
    return state


def _node_build_report(state: PipelineState) -> PipelineState:
    logger.info("[orchestrator] node=build_report started")
    submission = state["submission"]
    findings = state.get("findings") or []

    # Compute severity distribution
    dist = SeverityDistribution()
    for f in findings:
        sev = f.severity.value
        setattr(dist, sev, getattr(dist, sev, 0) + 1)

    report = AnalysisReport(
        report_id=str(uuid.uuid4()),
        filename=submission.filename or get_settings().default_submitted_filename,
        language=state.get("language", submission.language),
        summary=state.get("summary") or str(get_repository_config().load("reporting.json").get("empty_summary")),
        quality_score=max(0, min(100, state.get("quality_score", 100))),
        security_score=max(0, min(100, state.get("security_score", 100))),
        findings=findings,
        recommendations=state.get("recommendations") or [],
        explanation=state.get("summary"),
        pr_summary=state.get("pr_summary"),
        assistant_context=state.get("assistant_context"),
        severity_distribution=dist,
        metadata={
            "source_length": len(submission.code),
            "errors": state.get("errors") or [],
            **submission.metadata,
        },
    )
    state["report"] = report
    logger.info("[orchestrator] node=build_report finished report_id='%s'", report.report_id)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class Orchestrator:
    """
    LangGraph-based orchestration engine.

    - All agents and analyzers are singletons, created once in __init__.
    - The graph is compiled once and reused for every submission.
    - Adding new languages: add entry to self._analyzers, no graph changes needed.
    - Adding new nodes: add to _build_graph(), nothing else changes.
    """

    def __init__(self) -> None:
        # Language → category → analyzer registry
        self._analyzers: dict[str, dict[str, Analyzer]] = {
            "python": {
                "quality": PythonQualityAnalyzer(),
                "security": PythonSecurityAnalyzer(),
            },
            "java": {
                "quality": JavaQualityAnalyzer(),
                "security": JavaSecurityAnalyzer(),
            },
        }

        # Agent singletons
        try:
            self._rag = RAGAgent()
        except Exception as exc:
            logger.warning("RAGAgent unavailable at startup; RAG features will be disabled: %s", exc)
            class _NoopRAG:
                async def enrich_findings_batch(self, findings):
                    return findings

                async def answer(self, query, context=None):
                    reporting = get_repository_config().load("reporting.json")
                    return str(reporting.get("no_context_answer")), []

            self._rag = _NoopRAG()

        try:
            self._remediation = RemediationAgent()
        except Exception as exc:
            logger.warning("RemediationAgent unavailable at startup; using fallback: %s", exc)
            class _NoopRemediation:
                async def suggest(self, findings):
                    return [f.remediation for f in findings]

                async def enrich_missing_fields(self, findings):
                    return findings

                async def generate_report_recommendations(self, findings):
                    return []

            self._remediation = _NoopRemediation()

        try:
            self._summary = SummaryAgent()
        except Exception as exc:
            logger.warning("SummaryAgent unavailable at startup; using fallback: %s", exc)
            class _NoopSummary:
                async def summarize(self, report_dict):
                    return ""

            self._summary = _NoopSummary()

        try:
            self._pr_summary = PRSummaryAgent()
        except Exception as exc:
            logger.warning("PRSummaryAgent unavailable at startup; using fallback: %s", exc)
            class _NoopPRSummary:
                async def generate_pr_summary(self, report_dict):
                    return ""

            self._pr_summary = _NoopPRSummary()

        try:
            self._assistant = AssistantAgent(rag_agent=self._rag)
        except Exception as exc:
            logger.warning("AssistantAgent unavailable at startup; using fallback: %s", exc)
            class _NoopAssistant:
                def prepare_context(self, report_data, source_code=None):
                    return {}

                async def answer(self, query, context=None):
                    reporting = get_repository_config().load("reporting.json")
                    return str(reporting.get("no_context_answer")), []

            self._assistant = _NoopAssistant()

        # Compiled LangGraph
        self._graph = self._build_graph()
        logger.info("Orchestrator initialised — graph compiled")

    async def run(self, submission: CodeSubmission) -> AnalysisReport:
        """Execute the full LangGraph pipeline and return an AnalysisReport (async)."""
        from app.core import metrics as _metrics
        logger.info(
            "[orchestrator] pipeline started filename='%s' language='%s'",
            submission.filename or get_settings().default_paste_filename,
            submission.language,
        )
        # observe pipeline start time
        _metrics.pipeline_latency_seconds.labels("main").observe(0.0)
        import time
        _start = time.time()

        initial: PipelineState = {
            "submission": submission,
            "language": submission.language,
            "findings": [],
            "errors": [],
            "recommendations": [],
            "summary": "",
            "pr_summary": "",
        }

        # StateGraph compiled pipeline is async-capable; invoke via async API
        final = await self._graph.ainvoke(initial)
        report = final.get("report")
        if report is None:
            raise RuntimeError("Orchestrator pipeline did not produce a report")

        # record pipeline latency
        try:
            import time
            _dur = time.time() - _start
            from app.core import metrics as _metrics
            _metrics.pipeline_latency_seconds.labels("main").observe(_dur)
        except Exception:
            pass

        logger.info(
            "[orchestrator] pipeline finished report_id='%s' findings=%d quality=%d security=%d",
            report.report_id,
            len(report.findings),
            report.quality_score,
            report.security_score,
        )
        return report

    def _build_graph(self) -> Any:
        """Build and compile the LangGraph StateGraph."""
        # Capture singletons in closures — clean dependency injection
        analyzers = self._analyzers
        rag = self._rag
        remediation = self._remediation
        summary = self._summary
        pr_summary = self._pr_summary
        assistant = self._assistant

        def validate(s: PipelineState) -> PipelineState:
            return _node_validate(s)

        def detect(s: PipelineState) -> PipelineState:
            return _node_detect(s)

        async def analyze(s: PipelineState) -> PipelineState:
            return await _node_analyze(s, analyzers)

        async def rag_enrich(s: PipelineState) -> PipelineState:
            return await _node_rag_enrich(s, rag)

        async def parallel_post_rag(s: PipelineState) -> PipelineState:
            return await _node_parallel_post_rag(s, remediation, summary, pr_summary)

        async def assistant_context(s: PipelineState) -> PipelineState:
            return await _node_assistant_context(s, assistant)

        def build_report(s: PipelineState) -> PipelineState:
            return _node_build_report(s)

        builder = StateGraph(PipelineState)
        builder.add_node("validate", validate)
        builder.add_node("detect", detect)
        builder.add_node("analyze", analyze)
        builder.add_node("rag_enrich", rag_enrich)
        builder.add_node("parallel_post_rag", parallel_post_rag)
        builder.add_node("assistant_context", assistant_context)
        builder.add_node("build_report", build_report)

        builder.set_entry_point("validate")
        builder.add_edge("validate", "detect")
        builder.add_edge("detect", "analyze")
        builder.add_edge("analyze", "rag_enrich")
        builder.add_edge("rag_enrich", "parallel_post_rag")
        builder.add_edge("parallel_post_rag", "assistant_context")
        builder.add_edge("assistant_context", "build_report")
        builder.add_edge("build_report", END)

        return builder.compile()
