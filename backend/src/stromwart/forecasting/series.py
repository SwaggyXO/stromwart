"""Event-scoped forecast time-series for the live dashboard chart."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import fmean
from uuid import UUID

from stromwart.application.container import Container
from stromwart.contracts.features import FeatureVector
from stromwart.contracts.modeling import ForecastSeriesPoint, ModelIdentity
from stromwart.errors import ModelUnavailableError, NotFoundError, ValidationError
from stromwart.models.contracts import ForecastModel
from stromwart.repositories.telemetry import TelemetryRepository

DEFAULT_FORECAST_MODEL = ModelIdentity(
    name="quantile_forecaster",
    version="v1",
    feature_schema_version="telemetry-v1",
)


async def build_event_forecast_series(
    container: Container,
    event_id: UUID,
    metric_name: str,
    horizon_minutes: int,
    step_seconds: int,
    session_limit: int,
    model: ModelIdentity,
) -> list[ForecastSeriesPoint]:
    """Aggregate per-session quantile forecasts into an event-level time series."""
    forecast_model: ForecastModel | None = container.models.forecast(model)
    if forecast_model is None:
        raise ModelUnavailableError(
            f"Forecast model '{model.name}:{model.version}' is not registered"
        )

    async with container.database.transaction() as uow:
        telemetry = TelemetryRepository(uow.session)
        await telemetry.get_event(event_id)
        sessions = await telemetry.sessions_for_event(str(event_id), limit=session_limit)

    vectors: list[FeatureVector] = []
    for session in sessions:
        try:
            snapshot = await container.features.materialize(UUID(session.id))
            vectors.append(FeatureVector.model_validate(snapshot.values))
        except (ValidationError, NotFoundError):
            continue

    if not vectors:
        return []

    now = datetime.now(UTC)
    num_steps = max(1, (horizon_minutes * 60) // step_seconds)
    series: list[ForecastSeriesPoint] = []

    for step in range(1, num_steps + 1):
        horizon_seconds = step * step_seconds
        p10_values: list[float] = []
        p50_values: list[float] = []
        p90_values: list[float] = []

        for vector in vectors:
            result = await forecast_model.forecast(vector, metric_name, horizon_seconds)
            p10_values.append(result.p10)
            p50_values.append(result.p50)
            p90_values.append(result.p90)

        series.append(
            ForecastSeriesPoint(
                timestamp=now + timedelta(seconds=horizon_seconds),
                p10=round(fmean(p10_values), 4),
                p50=round(fmean(p50_values), 4),
                p90=round(fmean(p90_values), 4),
            )
        )

    return series
