from __future__ import annotations

import json
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.models.report import AnalysisReport


_REPORT_CACHE: dict[str, dict] = {}


class ReportService:
    @staticmethod
    def save(report: AnalysisReport) -> str:
        settings = get_settings()

        reports_dir = settings.reports_path
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_id = str(uuid.uuid4())

        # Update the report's id BEFORE serializing so the persisted JSON
        # matches the filename. Previously the file was written with the old
        # orchestrator-generated id, causing report_id mismatches when the
        # saved report was later loaded and its PDF was requested.
        report.report_id = report_id

        report_file = reports_dir / f"{report_id}.json"

        payload = report.model_dump()

        report_file.write_text(
            json.dumps(
                payload,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        _REPORT_CACHE[report_id] = json.loads(json.dumps(payload, default=str))

        return report_id

    @staticmethod
    def load(report_id: str) -> dict:
        if report_id in _REPORT_CACHE:
            return _REPORT_CACHE[report_id]

        settings = get_settings()

        report_file = settings.reports_path / f"{report_id}.json"

        if not report_file.exists():
            raise FileNotFoundError(report_id)

        data = json.loads(report_file.read_text(encoding="utf-8"))
        _REPORT_CACHE[report_id] = data
        return data