"""Tests for GET /v1/modeling/forecast event-scoped series."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from stromwart.app import create_app
from stromwart.contracts.common import SourceType
from stromwart.contracts.telemetry import ObservationCreate


def _observation(session_id: str, sequence: int) -> dict[str, object]:
    return ObservationCreate(
        session_id=session_id,
        observed_at=datetime.now(UTC),
        sequence=sequence,
        duration_ms=2_000,
        bitrate_kbps=3_000 + sequence * 100,
        buffer_level_ms=5_000 - sequence * 50,
        rebuffer_duration_ms=100 * sequence,
        throughput_kbps=4_000,
        packet_loss_pct=0.5 + sequence * 0.1,
        source_type=SourceType.REPLAY,
    ).model_dump(mode="json")


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_event_forecast_series_returns_quantile_points(client: TestClient) -> None:
    event_resp = client.post(
        "/v1/events",
        json={
            "name": "forecast-chart-event",
            "content_type": "live",
            "starts_at": "2026-07-14T00:00:00Z",
            "metadata": {},
        },
    )
    assert event_resp.status_code == 201, event_resp.text
    event_id = event_resp.json()["id"]

    session_resp = client.post(
        "/v1/sessions",
        json={
            "event_id": event_id,
            "external_id": f"fc-{uuid4()}",
            "client_type": "web",
            "source_type": "replay",
            "started_at": "2026-07-14T00:00:00Z",
        },
    )
    assert session_resp.status_code == 201, session_resp.text
    session_id = session_resp.json()["id"]

    for seq in range(5):
        obs_resp = client.post(
            "/v1/telemetry/observations",
            json=_observation(session_id, seq),
        )
        assert obs_resp.status_code == 201, obs_resp.text

    forecast_resp = client.get(
        "/v1/modeling/forecast",
        params={
            "event_id": event_id,
            "metric_name": "stall_risk",
            "horizon_minutes": 10,
            "step_seconds": 60,
        },
    )
    assert forecast_resp.status_code == 200, forecast_resp.text
    series = forecast_resp.json()
    assert isinstance(series, list)
    assert len(series) == 10

    for point in series:
        assert "timestamp" in point
        assert point["p10"] <= point["p50"] <= point["p90"]
        assert 0.0 <= point["p10"] <= 1.0
        assert 0.0 <= point["p90"] <= 1.0


def test_event_forecast_series_empty_without_sessions(client: TestClient) -> None:
    event_resp = client.post(
        "/v1/events",
        json={
            "name": "empty-forecast-event",
            "content_type": "live",
            "starts_at": "2026-07-14T00:00:00Z",
            "metadata": {},
        },
    )
    assert event_resp.status_code == 201
    event_id = event_resp.json()["id"]

    forecast_resp = client.get(
        "/v1/modeling/forecast",
        params={"event_id": event_id},
    )
    assert forecast_resp.status_code == 200
    assert forecast_resp.json() == []
