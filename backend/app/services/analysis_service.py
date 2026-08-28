"""
Analysis Service.

Thin application-layer facade over the Orchestrator.
Business logic lives in the orchestrator and its nodes — not here.
"""
from __future__ import annotations

from app.agents.orchestrator import Orchestrator
from app.core.logging import get_logger
from app.core.config import get_settings
from app.models.report import AnalysisReport
from app.models.submission import CodeSubmission
from app.services.report_service import ReportService

logger = get_logger(__name__)


class AnalysisService:
    """Coordinates the analysis pipeline via the Orchestrator."""

    def __init__(self) -> None:
        logger.info("AnalysisService initialising Orchestrator")
        self._orchestrator = Orchestrator()
        # concurrency guard for orchestrations
        settings = get_settings()
        import asyncio

        self._concurrency = asyncio.Semaphore(max(1, int(settings.orchestrator_concurrency_limit)))

    async def analyze_submission(self, submission: CodeSubmission) -> AnalysisReport:
        """
        Run the full analysis pipeline for a CodeSubmission.

        Raises RuntimeError if the pipeline fails to produce a report.
        """
        logger.info(
            "AnalysisService.analyze_submission: filename='%s', language='%s', source_type='%s'",
            submission.filename,
            submission.language,
            submission.metadata.get("source_type", "unknown"),
        )
        # Acquire concurrency semaphore to limit simultaneous pipeline runs
        async with self._concurrency:
            report = await self._orchestrator.run(submission)

            report_id = ReportService.save(report)

            report.report_id = report_id

            return report
