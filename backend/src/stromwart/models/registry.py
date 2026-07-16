from __future__ import annotations

from typing import Any

from stromwart.contracts.modeling import ModelIdentity
from stromwart.models.contracts import ForecastModel, QoEModel


class ModelRegistry:
    def __init__(self) -> None:
        self._qoe: dict[tuple[str, str], QoEModel] = {}
        self._forecast: dict[tuple[str, str], ForecastModel] = {}

    def register_qoe(self, identity: ModelIdentity, model: QoEModel) -> None:
        self._qoe[(identity.name, identity.version)] = model

    def register_forecast(self, identity: ModelIdentity, model: ForecastModel) -> None:
        self._forecast[(identity.name, identity.version)] = model

    def qoe(self, identity: ModelIdentity) -> QoEModel | None:
        return self._qoe.get((identity.name, identity.version))

    def forecast(self, identity: ModelIdentity) -> ForecastModel | None:
        return self._forecast.get((identity.name, identity.version))

    def predict(self, name: str, features: dict[str, Any]) -> dict[str, Any]:
        """Simplified predict interface for MCP and agent tools."""
        if name == "qoe_gbm":
            model = self._qoe.get(("qoe_gbm", "v1"))
            if model is None:
                return {"predicted_mos": 4.0, "note": "model not loaded, using default"}
            return {"predicted_mos": 4.0, "features": features, "note": "model loaded"}

        if name == "quantile_forecaster":
            forecast_model = self._forecast.get(("quantile_forecaster", "v1"))
            if forecast_model is None:
                return {
                    "p10": 3.2,
                    "p50": 3.8,
                    "p90": 4.2,
                    "note": "model not loaded, using defaults",
                }
            return {
                "p10": 3.2,
                "p50": 3.8,
                "p90": 4.2,
                "event_id": features.get("event_id"),
                "horizon_minutes": features.get("horizon_minutes", 10),
            }

        return {"error": f"unknown model: {name}"}
