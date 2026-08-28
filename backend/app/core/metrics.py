"""Prometheus metrics for observability.

Expose common counters and histograms used across the application.
"""
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _PROM_AVAILABLE = False


class _NoopMetric:
    def __init__(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self

    def inc(self, amount=1):
        return None

    def dec(self, amount=1):
        return None

    def observe(self, value):
        return None


if _PROM_AVAILABLE:
    # LLM metrics
    llm_requests_total = Counter("llm_requests_total", "Total LLM requests", ["model"])
    llm_retries_total = Counter("llm_retries_total", "Total LLM retries", ["model"])
    llm_request_latency_seconds = Histogram("llm_request_latency_seconds", "LLM request latency seconds", ["model"])
    llm_inprogress = Gauge("llm_inprogress", "Number of in-progress LLM requests", ["model"])

    # Analyzer metrics
    analyzer_runs_total = Counter("analyzer_runs_total", "Static analyzer runs", ["tool", "status"])  # status: success/failure
    analyzer_run_latency_seconds = Histogram("analyzer_run_latency_seconds", "Analyzer run latency seconds", ["tool"]) 

    # Pipeline / stage metrics
    pipeline_latency_seconds = Histogram("pipeline_latency_seconds", "Orchestrator pipeline latency seconds", ["pipeline"])
    stage_latency_seconds = Histogram("stage_latency_seconds", "Orchestrator stage latency seconds", ["stage"])

    # Helper to expose metrics in HTTP handler
    def metrics_export() -> tuple[bytes, str]:
        data = generate_latest()
        return data, CONTENT_TYPE_LATEST
else:
    # Provide noop metrics so app can run without prometheus_client installed
    llm_requests_total = _NoopMetric()
    llm_retries_total = _NoopMetric()
    llm_request_latency_seconds = _NoopMetric()
    llm_inprogress = _NoopMetric()
    analyzer_runs_total = _NoopMetric()
    analyzer_run_latency_seconds = _NoopMetric()
    pipeline_latency_seconds = _NoopMetric()
    stage_latency_seconds = _NoopMetric()

    def metrics_export() -> tuple[bytes, str]:
        return (b"", "text/plain; version=0.0.4")
