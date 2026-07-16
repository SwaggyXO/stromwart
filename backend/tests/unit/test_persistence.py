from stromwart.database import Base
from stromwart.persistence import control, operations, telemetry


def test_required_tables_are_registered() -> None:
    expected = {
        "events",
        "sessions",
        "observations",
        "feature_snapshots",
        "predictions",
        "forecasts",
        "alerts",
        "incidents",
        "action_proposals",
        "action_executions",
        "agent_runs",
        "audit_events",
    }

    assert expected == set(Base.metadata.tables)


def test_idempotency_index_is_registered() -> None:
    indexes = {
        index.name
        for index in Base.metadata.tables["observations"].indexes
    }

    assert "uq_observations_session_sequence" in indexes


def test_active_incident_unique_index_is_registered() -> None:
    indexes = {
        index.name
        for index in Base.metadata.tables["incidents"].indexes
    }

    assert "uq_incidents_active_key" in indexes