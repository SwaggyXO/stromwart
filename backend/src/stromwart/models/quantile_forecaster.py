"""Quantile forecaster with Conformalized Quantile Regression."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from stromwart.contracts.features import FeatureVector
from stromwart.contracts.modeling import ForecastResult
from stromwart.models.feature_matrix import (
    FEATURE_COLUMNS,
    FORECAST_FEATURE_COLUMNS,
    forecast_features_frame,
)

__all__ = ["FEATURE_COLUMNS", "FORECAST_FEATURE_COLUMNS", "QuantileForecasterModel"]

SUPPORTED_METRICS = {"stall_risk", "mos_degradation", "buffer_risk"}


class QuantileForecasterModel:
    """Risk quantile forecaster with conformal calibration.

    Uses three LightGBM quantile regressors (lower/median/upper)
    wrapped in MAPIE ConformalizedQuantileRegressor for guaranteed coverage.
    """

    def __init__(
        self,
        model_lower: Any | None = None,
        model_median: Any | None = None,
        model_upper: Any | None = None,
        cqr: Any | None = None,
        confidence_level: float = 0.8,
        model_p10: Any | None = None,
        model_p50: Any | None = None,
        model_p90: Any | None = None,
    ) -> None:
        self._model_lower = model_lower or model_p10
        self._model_median = model_median or model_p50
        self._model_upper = model_upper or model_p90
        self._cqr = cqr
        self._confidence_level = confidence_level

    @classmethod
    def load(cls, path: Path) -> QuantileForecasterModel:
        data = joblib.load(path)
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            return cls(
                model_lower=data.get("model_lower") or data.get("model_p10"),
                model_median=data.get("model_median") or data.get("model_p50"),
                model_upper=data.get("model_upper") or data.get("model_p90"),
                cqr=data.get("cqr"),
                confidence_level=data.get("confidence_level", 0.8),
            )
        raise ValueError(f"Cannot load forecaster from {path}")

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    async def forecast(
        self,
        features: FeatureVector,
        metric_name: str,
        horizon_seconds: int,
    ) -> ForecastResult:
        """Produce P10/P50/P90 forecast with conformal guarantees."""
        del metric_name  # metric selection reserved for future use
        x = forecast_features_frame(features, horizon_seconds)

        if self._cqr is not None:
            points, intervals = self._cqr.predict_interval(x)
            p50 = float(points[0])
            p10 = float(intervals[0, 0, 0])
            p90 = float(intervals[0, 1, 0])
        else:
            if (
                self._model_lower is None
                or self._model_median is None
                or self._model_upper is None
            ):
                raise RuntimeError("Forecaster has no CQR or quantile models loaded")
            p10 = float(self._model_lower.predict(x)[0])
            p50 = float(self._model_median.predict(x)[0])
            p90 = float(self._model_upper.predict(x)[0])

        p10, p50, p90 = sorted([p10, p50, p90])
        p10 = float(np.clip(p10, 0.0, 1.0))
        p50 = float(np.clip(p50, 0.0, 1.0))
        p90 = float(np.clip(p90, 0.0, 1.0))

        return ForecastResult(
            p10=round(p10, 4),
            p50=round(p50, 4),
            p90=round(p90, 4),
        )
