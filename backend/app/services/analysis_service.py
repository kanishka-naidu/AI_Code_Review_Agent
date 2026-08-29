"""
Analysis Service.

Thin application-layer facade over the Orchestrator.
Business logic lives in the orchestrator and its nodes — not here.
"""
from __future__ import annotations

import asyncio

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
        self._orchestrator: Orchestrator | None = None
        self._init_lock = asyncio.Lock()
        settings = get_settings()
        self._concurrency = asyncio.Semaphore(max(1, int(settings.orchestrator_concurrency_limit)))

    async def _ensure_initialised(self) -> None:
        if self._orchestrator is not None:
            return
        async with self._init_lock:
            if self._orchestrator is None:
                logger.info("AnalysisService: lazily creating Orchestrator")
                self._orchestrator = Orchestrator()
                logger.info("AnalysisService: Orchestrator ready")

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
        await self._ensure_initialised()
        assert self._orchestrator is not None
        async with self._concurrency:
            report = await self._orchestrator.run(submission)

            report_id = ReportService.save(report)

            report.report_id = report_id

            return report
