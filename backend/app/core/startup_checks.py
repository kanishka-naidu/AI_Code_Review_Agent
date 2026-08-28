"""Startup checks for analyzer binaries and environment readiness.

Provides a small utility to verify required analyzer executables are present in PATH.
"""
from __future__ import annotations

import shutil
from typing import Dict

from app.core.logging import get_logger

logger = get_logger(__name__)

REQUIRED_ANALYZERS = ["ruff", "bandit", "semgrep", "pmd"]


def check_analyzer_binaries() -> Dict[str, bool]:
    """Return a map of analyzer->present(bool). Logs warnings for missing analyzers."""
    results: Dict[str, bool] = {}
    for tool in REQUIRED_ANALYZERS:
        found = shutil.which(tool) is not None
        results[tool] = found
        if not found:
            logger.warning("Analyzer binary not found in PATH: %s", tool)
    return results
