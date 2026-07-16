"""Split conformal prediction helpers for QoE regression."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from mapie.regression import SplitConformalRegressor
from sklearn.base import RegressorMixin

type FeatureMatrix = pd.DataFrame | np.ndarray

_SKLEARN_FEATURE_NAME_WARNING = (
    "X does not have valid feature names, but LGBMRegressor was fitted with feature names"
)


def build_split_conformal(
    estimator: RegressorMixin,
    confidence_level: float = 0.9,
) -> SplitConformalRegressor:
    """Wrap a pre-fitted regressor with split conformal intervals."""
    return SplitConformalRegressor(
        estimator=estimator,
        confidence_level=confidence_level,
        prefit=True,
    )


def conformalize(
    conformal: SplitConformalRegressor,
    x_cal: FeatureMatrix,
    y_cal: np.ndarray | pd.Series,
) -> SplitConformalRegressor:
    """Compute conformity scores on the calibration set."""
    # MAPIE converts inputs to NumPy internally during conformalize; suppress the
    # resulting sklearn feature-name warning when the base estimator was trained
    # on a named DataFrame.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_SKLEARN_FEATURE_NAME_WARNING,
            category=UserWarning,
        )
        return conformal.conformalize(x_cal, y_cal)


def predict_interval(
    conformal: SplitConformalRegressor,
    x: FeatureMatrix,
) -> tuple[np.ndarray, np.ndarray]:
    """Return point predictions and (n_samples, 2, 1) interval bounds."""
    points, intervals = conformal.predict_interval(x)
    return points, intervals


__all__ = [
    "LGBMRegressor",
    "SplitConformalRegressor",
    "build_split_conformal",
    "conformalize",
    "predict_interval",
]
