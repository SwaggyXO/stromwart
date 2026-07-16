from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from stromwart.application.dependencies import ContainerDep, UnitOfWorkDep
from stromwart.contracts.features import FeatureVector
from stromwart.contracts.modeling import (
    ForecastRequest,
    ForecastResult,
    ScoreRequest,
    ScoreResult,
)
from stromwart.errors import ModelUnavailableError
from stromwart.repositories.operations import OperationsRepository

router = APIRouter(prefix="/qoe", tags=["qoe"])


@router.post(
    "/score",
    response_model=ScoreResult,
    status_code=status.HTTP_200_OK,
    summary="Score session QoE",
    description="Compute QoE MOS estimate with conformal prediction interval for a session.",
)
async def score_qoe(
    request: ScoreRequest,
    container: ContainerDep,
) -> ScoreResult:
    model = container.models.qoe(request.model)
    if model is None:
        raise ModelUnavailableError(
            f"QoE model '{request.model.name}:{request.model.version}' is not registered"
        )

    features = await container.features.materialize(request.session_id)
    vector = FeatureVector.model_validate(features.values)
    result = await model.score(vector)

    async with container.database.transaction() as uow:
        ops = OperationsRepository(uow.session)
        await ops.record_prediction(
            entity_type="session",
            entity_id=str(request.session_id),
            prediction_type=result.prediction_type,
            value=result.value,
            lower_bound=result.lower_bound,
            upper_bound=result.upper_bound,
            confidence=result.confidence,
            model_name=request.model.name,
            model_version=request.model.version,
            feature_schema_version=request.model.feature_schema_version,
        )

    return result


@router.post(
    "/forecast",
    response_model=ForecastResult,
    status_code=status.HTTP_200_OK,
    summary="Forecast degradation risk",
    description="Produce P10/P50/P90 quantile forecast for a session metric over a given horizon.",
)
async def forecast_qoe(
    request: ForecastRequest,
    container: ContainerDep,
) -> ForecastResult:
    model = container.models.forecast(request.model)
    if model is None:
        raise ModelUnavailableError(
            f"Forecast model '{request.model.name}:{request.model.version}' is not registered"
        )

    features = await container.features.materialize(request.session_id)
    vector = FeatureVector.model_validate(features.values)
    result = await model.forecast(vector, request.metric_name, request.horizon_seconds)

    async with container.database.transaction() as uow:
        ops = OperationsRepository(uow.session)
        await ops.record_forecast(
            entity_type="session",
            entity_id=str(request.session_id),
            metric_name=request.metric_name,
            horizon_seconds=request.horizon_seconds,
            p10=result.p10,
            p50=result.p50,
            p90=result.p90,
            model_version=request.model.version,
        )

    return result


@router.get(
    "/predictions/{session_id}",
    response_model=list[dict[str, Any]],
    summary="Get prediction history",
    description="Retrieve all QoE predictions for a session, ordered by creation time.",
)
async def get_predictions(
    session_id: UUID,
    uow: UnitOfWorkDep,
) -> list[dict[str, Any]]:
    ops = OperationsRepository(uow.session)
    rows = await ops.predictions_for(str(session_id))
    return [
        {
            "id": row.id,
            "prediction_type": row.prediction_type,
            "value": row.value,
            "lower_bound": row.lower_bound,
            "upper_bound": row.upper_bound,
            "confidence": row.confidence,
            "model_name": row.model_name,
            "model_version": row.model_version,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
