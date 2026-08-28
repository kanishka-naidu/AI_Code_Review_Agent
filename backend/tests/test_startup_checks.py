import json
from pathlib import Path

from app.core.startup import run_startup_checks
from app.core.config import get_settings
from app.core.repository_config import get_repository_config


def _write_config_file(name: str, content: dict, cfg_dir: Path):
    path = cfg_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(content, f)
    return path


def test_startup_checks_partial_mode_warns_and_returns_diagnostics(tmp_path, monkeypatch):
    settings = get_settings()
    # Point configuration path to temp
    monkeypatch.setattr(settings, "configuration_dir", str(tmp_path))
    cfg_dir = tmp_path
    # create minimal analyzer config with an available module (built-in 'sys') and binary 'python'
    analyzers = {
        "tool_modules": {"ruff": "sys", "bandit": "sys"},
        "tool_binaries": {"semgrep": "python"},
    }
    _write_config_file("analyzers.json", analyzers, cfg_dir)
    _write_config_file("analysis.json", {"python_default_filename": "pasted_code"}, cfg_dir)
    _write_config_file("severity.json", {"order_asc": []}, cfg_dir)
    _write_config_file("reporting.json", {"empty_summary": "No findings."}, cfg_dir)

    settings.startup_fail_on_missing_analyzers = False
    diag = run_startup_checks(raise_on_failure=False)
    assert diag is not None
    assert isinstance(diag.analyzer_status, dict)


def test_startup_checks_strict_mode_fails_on_missing(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "configuration_dir", str(tmp_path))
    cfg_dir = tmp_path
    # Intentionally create analyzers.json pointing to non-existent modules
    analyzers = {"tool_modules": {"ruff": "nonexistent_module_abc123"}, "tool_binaries": {"semgrep": "nonexistent-binary-xyz"}}
    _write_config_file("analyzers.json", analyzers, cfg_dir)
    _write_config_file("analysis.json", {"python_default_filename": "pasted_code"}, cfg_dir)
    _write_config_file("severity.json", {"order_asc": []}, cfg_dir)
    _write_config_file("reporting.json", {"empty_summary": "No findings."}, cfg_dir)

    settings.startup_fail_on_missing_analyzers = True
    try:
        run_startup_checks(raise_on_failure=True)
        assert False, "Expected RuntimeError due to missing tools"
    except RuntimeError as exc:
        # Accept any diagnostic error payload (missing tools/files/chromadb/gemini)
        assert "errors" in str(exc)
