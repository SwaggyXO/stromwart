"""
QoE Gradient Boosted Model — LightGBM regressor for MOS estimation
with split conformal prediction intervals.
"""
from pathlib import Path

import joblib
from lightgbm import LGBMRegressor
from mapie.regression import SplitConformalRegressor

from stromwart.contracts.features import FeatureVector
from stromwart.contracts.modeling import ScoreResult
from stromwart.models.feature_matrix import FEATURE_COLUMNS, features_frame

# Re-export for callers that import from this module.
__all__ = ["FEATURE_COLUMNS", "QoEGBMModel"]


class QoEGBMModel:
    """Satisfies the QoEModel protocol."""

    def __init__(
        self,
        estimator: LGBMRegressor,
        conformal: SplitConformalRegressor | None = None,
        confidence_level: float = 0.9,
    ) -> None:
        self._estimator = estimator
        self._conformal = conformal
        self._confidence_level = confidence_level

    async def score(self, features: FeatureVector) -> ScoreResult:
        x = features_frame(features)

        if self._conformal is not None:
            point, intervals = self._conformal.predict_interval(x)
            value = float(max(1.0, min(5.0, point[0])))
            lower = float(max(1.0, min(5.0, intervals[0, 0, 0])))
            upper = float(max(1.0, min(5.0, intervals[0, 1, 0])))
        else:
            pred = self._estimator.predict(x)
            value = float(max(1.0, min(5.0, pred[0])))
            lower = None
            upper = None

        interval_width = (upper - lower) if (lower is not None and upper is not None) else None
        confidence = 1.0 - (interval_width / 4.0) if interval_width is not None else None

        return ScoreResult(
            prediction_type="mos_estimate",
            value=round(value, 3),
            lower_bound=round(lower, 3) if lower is not None else None,
            upper_bound=round(upper, 3) if upper is not None else None,
            confidence=round(confidence, 3) if confidence is not None else None,
        )

    def save(self, path: Path) -> None:
        joblib.dump(
            {
                "estimator": self._estimator,
                "conformal": self._conformal,
                "confidence_level": self._confidence_level,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path) -> "QoEGBMModel":
        data = joblib.load(path)
        return cls(
            estimator=data["estimator"],
            conformal=data["conformal"],
            confidence_level=data["confidence_level"],
        )
