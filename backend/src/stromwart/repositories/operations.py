from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stromwart.persistence import AuditRow, ForecastRow, PredictionRow


class OperationsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_prediction(
        self,
        entity_type: str,
        entity_id: str,
        prediction_type: str,
        value: float,
        lower_bound: float | None,
        upper_bound: float | None,
        confidence: float | None,
        model_name: str,
        model_version: str,
        feature_schema_version: str,
    ) -> PredictionRow:
        row = PredictionRow(
            entity_type=entity_type,
            entity_id=entity_id,
            prediction_type=prediction_type,
            value=value,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence=confidence,
            model_name=model_name,
            model_version=model_version,
            feature_schema_version=feature_schema_version,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def record_forecast(
        self,
        entity_type: str,
        entity_id: str,
        metric_name: str,
        horizon_seconds: int,
        p10: float,
        p50: float,
        p90: float,
        model_version: str,
    ) -> ForecastRow:
        row = ForecastRow(
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            horizon_seconds=horizon_seconds,
            p10=p10,
            p50=p50,
            p90=p90,
            model_version=model_version,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def predictions_for(self, entity_id: str) -> list[PredictionRow]:
        result = await self._session.execute(
            select(PredictionRow)
            .where(PredictionRow.entity_id == entity_id)
            .order_by(PredictionRow.created_at.desc())
        )
        return list(result.scalars().all())

    async def audit_for_artifact(
        self,
        artifact_id: str,
        limit: int = 100,
    ) -> list[AuditRow]:
        statement = (
            select(AuditRow)
            .where(AuditRow.artifact_id == artifact_id)
            .order_by(AuditRow.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())
