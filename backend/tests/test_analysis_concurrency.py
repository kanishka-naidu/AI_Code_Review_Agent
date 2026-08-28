import importlib
import sys

import app.core.config as config_mod
from app.services.analysis_service import AnalysisService


def test_analysis_service_concurrency_setting(monkeypatch):
    class S:
        orchestrator_concurrency_limit = 3
        app_name = "test"
        app_version = "0"
        log_level = "INFO"
        startup_fail_on_missing_analyzers = False

    monkeypatch.setattr(config_mod, "get_settings", lambda: S())
    # reload module to pick up patched settings when AnalysisService constructed
    importlib.reload(sys.modules["app.services.analysis_service"])
    from app.services.analysis_service import AnalysisService as AS

    svc = AS()
    # internal semaphore should be initialized with the configured value
    assert hasattr(svc, "_concurrency")
    sem = svc._concurrency
    # _value is internal but indicative of initial permits remaining
    assert getattr(sem, "_value", None) == 3
