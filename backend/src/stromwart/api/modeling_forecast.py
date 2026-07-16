"""Forecast series API for event-level dashboard charts."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from stromwart.application.dependencies import ContainerDep
from stromwart.contracts.modeling import ForecastSeriesPoint, ModelIdentity
from stromwart.forecasting.series import DEFAULT_FORECAST_MODEL, build_event_forecast_series

router = APIRouter(prefix="/modeling", tags=["modeling"])


@router.get(
    "/forecast",
    response_model=list[ForecastSeriesPoint],
    status_code=status.HTTP_200_OK,
    summary="Event forecast time series",
    description=(
        "Return event-scoped degradation-risk quantiles (p10/p50/p90) over a forward "
        "horizon. Samples up to `session_limit` sessions with telemetry, runs the "
        "quantile forecaster at each step, and averages quantiles across sessions."
    ),
)
async def get_event_forecast_series(
    container: ContainerDep,
    event_id: UUID = Query(description="Live event UUID"),
    metric_name: str = Query(
        default="stall_risk",
        min_length=1,
        max_length=100,
        description="Risk metric to forecast",
    ),
    horizon_minutes: int = Query(
        default=10,
        ge=1,
        le=60,
        description="Forward forecast window in minutes",
    ),
    step_seconds: int = Query(
        default=60,
        ge=30,
        le=300,
        description="Seconds between series points",
    ),
    session_limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Max sessions to sample for event aggregation",
    ),
    model_name: str = Query(default=DEFAULT_FORECAST_MODEL.name),
    model_version: str = Query(default=DEFAULT_FORECAST_MODEL.version),
    feature_schema_version: str = Query(
        default=DEFAULT_FORECAST_MODEL.feature_schema_version,
    ),
) -> list[ForecastSeriesPoint]:
    model = ModelIdentity(
        name=model_name,
        version=model_version,
        feature_schema_version=feature_schema_version,
    )
    return await build_event_forecast_series(
        container=container,
        event_id=event_id,
        metric_name=metric_name,
        horizon_minutes=horizon_minutes,
        step_seconds=step_seconds,
        session_limit=session_limit,
        model=model,
    )
