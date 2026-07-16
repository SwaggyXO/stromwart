import pytest

from stromwart.evals.tracer import AgentTracer


def test_end_span_uses_duration_ms() -> None:
    tracer = AgentTracer()
    tracer.start_trace()
    tracer.start_span("dispatch_detector", "detector")
    tracer.end_span("ok", duration_ms=2.5)
    trace = tracer.end_trace()
    assert trace is not None
    assert trace.spans[0].duration_ms == pytest.approx(2.5)
