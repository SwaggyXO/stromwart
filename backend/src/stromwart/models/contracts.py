from typing import Protocol

from stromwart.contracts.features import FeatureVector
from stromwart.contracts.modeling import ForecastResult, ScoreResult


class QoEModel(Protocol):
    async def score(self, features: FeatureVector) -> ScoreResult: ...


class ForecastModel(Protocol):
    async def forecast(
        self,
        features: FeatureVector,
        metric_name: str,
        horizon_seconds: int,
    ) -> ForecastResult: ...
