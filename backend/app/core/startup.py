from __future__ import annotations

import importlib
import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import get_settings
from app.core.repository_config import get_repository_config

logger = logging.getLogger(__name__)


@dataclass
class StartupDiagnostics:
    missing_files: List[str]
    missing_tools: Dict[str, str]
    analyzer_status: Dict[str, Any]
    chromadb_ok: bool
    gemini_ok: bool
    details: Dict[str, Any]


def _check_config_files(required: List[str]) -> List[str]:
    repo = get_repository_config()
    missing: List[str] = []
    for filename in required:
        try:
            repo.load(filename)
        except FileNotFoundError:
            missing.append(filename)
        except Exception as exc:
            # Corrupt file or parsing error — treat as missing but record detail
            logger.error("Configuration file '%s' could not be loaded: %s", filename, exc)
            missing.append(filename)
    return missing


def _check_tool_module(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        # fallback: see if module_name is an executable available on PATH
        return shutil.which(module_name) is not None


def _check_tool_binary(binary: str) -> bool:
    # Do not treat empty strings as available
    if not binary:
        return False
    return shutil.which(binary) is not None


def _check_chromadb(vector_db_path: Path) -> bool:
    try:
        import chromadb
        # Try creating a temporary client; do not seed or modify state here
        vector_db_path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(vector_db_path))
        # Basic call
        _ = client.list_collections()
        return True
    except Exception as exc:
        logger.warning("ChromaDB check failed: %s", exc)
        return False


def _check_gemini(settings) -> bool:
    # Basic validation: provider/gemini + api key presence + model string validated by settings
    try:
        provider = (settings.llm_provider or "").strip().lower()
        if provider != "gemini":
            return True
        if not settings.llm_api_key:
            logger.warning("Gemini provider configured but LLM_API_KEY is not set")
            return False
        # get_settings() already validates model naming when API key is set
        # so if we reach here the model is considered valid by Settings
        return True
    except Exception as exc:
        logger.error("Gemini configuration check failed: %s", exc)
        return False


def run_startup_checks(raise_on_failure: bool | None = None) -> StartupDiagnostics:
    """Run startup checks and return diagnostics.

    If raise_on_failure is None, consult settings.startup_fail_on_missing_analyzers.
    """
    settings = get_settings()
    repo = get_repository_config()

    if raise_on_failure is None:
        raise_on_failure = bool(getattr(settings, "startup_fail_on_missing_analyzers", False))

    required_files = ["analysis.json", "analyzers.json", "severity.json", "reporting.json"]
    missing_files = _check_config_files(required_files)

    analyzer_status: Dict[str, Any] = {}
    missing_tools: Dict[str, str] = {}

    # Try to load analyzer configuration if present
    try:
        analyzer_conf = repo.load("analyzers.json")
    except Exception:
        analyzer_conf = {}

    tool_modules = analyzer_conf.get("tool_modules", {}) or {}
    tool_binaries = analyzer_conf.get("tool_binaries", {}) or {}

    # Check python module-style tools (ruff, bandit, radon, etc.)
    for name, module in tool_modules.items():
        ok = False
        if module:
            ok = _check_tool_module(str(module))
        analyzer_status[name] = {"type": "module", "module": module, "available": ok}
        if not ok:
            missing_tools[f"module:{name}"] = str(module)

    # Check binary-style tools (semgrep, pmd)
    for name, binary in tool_binaries.items():
        ok = False
        if binary:
            ok = _check_tool_binary(str(binary))
        analyzer_status[name] = {"type": "binary", "binary": binary, "available": ok}
        if not ok:
            missing_tools[f"binary:{name}"] = str(binary)

    # Verify PMD only if Java is enabled in settings
    java_ok = True
    if "java" in settings.supported_languages_list:
        pmd_binary = tool_binaries.get("pmd")
        if pmd_binary:
            java_ok = _check_tool_binary(str(pmd_binary))
            if not java_ok:
                missing_tools["binary:pmd"] = str(pmd_binary)

    # verify chromadb accessibility
    chroma_ok = _check_chromadb(settings.vector_db_path)

    gemini_ok = _check_gemini(settings)

    details: Dict[str, Any] = {"missing_files": missing_files, "missing_tools": missing_tools}

    diagnostics = StartupDiagnostics(
        missing_files=missing_files,
        missing_tools=missing_tools,
        analyzer_status=analyzer_status,
        chromadb_ok=chroma_ok,
        gemini_ok=gemini_ok,
        details=details,
    )

    # Decide whether to fail startup
    if raise_on_failure:
        errors: List[str] = []
        if missing_files:
            errors.append(f"Missing configuration files: {missing_files}")
        if missing_tools:
            errors.append(f"Missing tools or modules: {list(missing_tools.keys())}")
        if not chroma_ok:
            errors.append("ChromaDB is not available or misconfigured")
        if not gemini_ok:
            errors.append("Gemini LLM configuration invalid or credentials missing")
        if errors:
            # raise a RuntimeError with diagnostic info to abort app startup
            raise RuntimeError(json.dumps({"errors": errors, "details": details}))

    # Otherwise just log warnings and continue
    if missing_files:
        logger.warning("Startup check: missing configuration files: %s", missing_files)
    if missing_tools:
        logger.warning("Startup check: missing tools/modules: %s", missing_tools)
    if not chroma_ok:
        logger.warning("Startup check: chromadb not fully available or misconfigured")
    if not gemini_ok:
        logger.warning("Startup check: gemini configuration incomplete or missing LLM_API_KEY")

    return diagnostics
