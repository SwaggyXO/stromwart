"""
Train QoE GBM + Quantile Forecaster models and save artifacts.

Uses a HYBRID data strategy:
  1. Primary: WaterlooSQoE-IV real-world data (peer-reviewed, 1350 sessions)
  2. Augmentation: Synthetic incident scenarios for operational robustness

Usage:
    cd backend
    uv run python scripts/download_waterloo.py   # (optional, real data)
    uv run python scripts/prepare_waterloo.py    # (optional, normalize)
    uv run python scripts/generate_synthetic_data.py  # synthetic augmentation
    uv run python scripts/train_models.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from mapie.regression import ConformalizedQuantileRegressor, SplitConformalRegressor
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from stromwart.models.conformal import conformalize, predict_interval
from stromwart.models.feature_matrix import FEATURE_COLUMNS, FORECAST_FEATURE_COLUMNS

DATA_DIR = Path(__file__).parents[1] / "data"
WATERLOO_PATH = DATA_DIR / "waterloo_normalized.csv"
SYNTHETIC_PATH = DATA_DIR / "synthetic_qoe_train.csv"
ARTIFACTS_DIR = Path(__file__).parents[1] / "artifacts"

FEATURE_COLS = FEATURE_COLUMNS


def train_qoe_model(df: pd.DataFrame) -> None:
    """Train QoE GBM with split conformal prediction intervals."""
    from stromwart.models.qoe_gbm import QoEGBMModel

    X = df[FEATURE_COLS]
    y = df["mos"].values

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.4, random_state=42
    )
    X_cal, X_test, y_cal, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )

    print(f"QoE Model — Train: {len(X_train)}, Cal: {len(X_cal)}, Test: {len(X_test)}")

    estimator = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
    )
    estimator.fit(X_train, y_train)

    # Split conformal prediction
    confidence_level = 0.9
    conformal = SplitConformalRegressor(
        estimator=estimator,
        confidence_level=confidence_level,
        prefit=True,
    )
    conformalize(conformal, X_cal, y_cal)

    # Evaluate
    points, intervals = predict_interval(conformal, X_test)
    coverage = np.mean(
        (y_test >= intervals[:, 0, 0]) & (y_test <= intervals[:, 1, 0])
    )
    avg_width = np.mean(intervals[:, 1, 0] - intervals[:, 0, 0])
    rmse = np.sqrt(np.mean((points - y_test) ** 2))

    print(f"  RMSE: {rmse:.4f}")
    print(f"  Coverage (target {confidence_level}): {coverage:.4f}")
    print(f"  Avg interval width: {avg_width:.4f}")

    model = QoEGBMModel(
        estimator=estimator,
        conformal=conformal,
        confidence_level=confidence_level,
    )
    output_path = ARTIFACTS_DIR / "qoe_gbm_v1.joblib"
    model.save(output_path)
    print(f"  Saved -> {output_path}")


def train_forecaster(df: pd.DataFrame) -> None:
    """Train quantile forecaster for risk prediction."""
    from stromwart.models.quantile_forecaster import QuantileForecasterModel

    X_base = df[FEATURE_COLS]
    # Create synthetic risk target: probability of bad QoE in next N seconds
    # Based on current features (stall_ratio, packet_loss, low buffer)
    stall_risk = (
        df["stall_ratio"] * 0.4
        + (df["latest_packet_loss_pct"] / 100) * 0.3
        + np.clip(1.0 - df["buffer_min_ms"] / 5000, 0, 1) * 0.3
    ).values
    noise = np.random.default_rng(42).normal(0, 0.05, len(stall_risk))
    stall_risk = np.clip(stall_risk + noise, 0, 1)

    # Add horizon as a feature (randomly sampled during training)
    rng = np.random.default_rng(42)
    horizons = rng.choice([30, 60, 120], size=len(X_base))
    # Longer horizon → slightly higher risk (more uncertainty)
    horizon_factor = 1.0 + (horizons - 30) / 300
    y = np.clip(stall_risk * horizon_factor, 0, 1)

    X_with_horizon = X_base.assign(horizon_seconds=horizons.astype(float))
    X_with_horizon = X_with_horizon[FORECAST_FEATURE_COLUMNS]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X_with_horizon, y, test_size=0.4, random_state=42
    )
    X_cal, X_test, y_cal, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )

    print(f"\nForecaster — Train: {len(X_train)}, Cal: {len(X_cal)}, Test: {len(X_test)}")

    params = {
        "objective": "quantile",
        "n_estimators": 250,
        "learning_rate": 0.04,
        "num_leaves": 47,
        "min_child_samples": 15,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "verbose": -1,
    }

    model_lower = LGBMRegressor(**params, alpha=0.05)
    model_median = LGBMRegressor(**params, alpha=0.5)
    model_upper = LGBMRegressor(**params, alpha=0.95)

    model_lower.fit(X_train, y_train)
    model_median.fit(X_train, y_train)
    model_upper.fit(X_train, y_train)

    # Conformalized Quantile Regression (CQR)
    # MAPIE expects [lower, upper, median] order with prefit=True
    cqr = ConformalizedQuantileRegressor(
        estimator=[model_lower, model_upper, model_median],
        confidence_level=0.8,
        prefit=True,
    )
    cqr.conformalize(X_cal, y_cal)

    # Evaluate on test set
    points, intervals = cqr.predict_interval(X_test)
    pred_lower = intervals[:, 0, 0]
    pred_upper = intervals[:, 1, 0]

    coverage = np.mean((y_test >= pred_lower) & (y_test <= pred_upper))
    avg_width = np.mean(pred_upper - pred_lower)
    median_mae = np.mean(np.abs(points - y_test))

    print(f"  CQR P10-P90 coverage: {coverage:.4f} (target ~0.80)")
    print(f"  Avg interval width: {avg_width:.4f}")
    print(f"  Median MAE: {median_mae:.4f}")

    raw_p10 = model_lower.predict(X_test)
    raw_p90 = model_upper.predict(X_test)
    raw_coverage = np.mean((y_test >= raw_p10) & (y_test <= raw_p90))
    print(f"  Raw (uncalibrated) coverage: {raw_coverage:.4f}")

    forecaster = QuantileForecasterModel(
        model_lower=model_lower,
        model_median=model_median,
        model_upper=model_upper,
        cqr=cqr,
        confidence_level=0.8,
    )
    output_path = ARTIFACTS_DIR / "quantile_forecaster_v2.joblib"
    forecaster.save(output_path)
    print(f"  Saved -> {output_path}")

    compat_path = ARTIFACTS_DIR / "quantile_forecaster_v1.joblib"
    forecaster.save(compat_path)
    print(f"  Saved (compat) -> {compat_path}")


def load_hybrid_data() -> pd.DataFrame:
    """Load hybrid dataset: real-world Waterloo + synthetic augmentation."""
    frames = []

    if WATERLOO_PATH.exists():
        waterloo = pd.read_csv(WATERLOO_PATH)
        waterloo["data_source"] = "waterloo_iv"
        frames.append(waterloo)
        print(f"Loaded {len(waterloo)} real-world samples from WaterlooSQoE-IV")
    else:
        print(
            "WARNING: Waterloo data not found. "
            "Run scripts/download_waterloo.py + prepare_waterloo.py"
        )
        print("         Proceeding with synthetic data only.\n")

    if SYNTHETIC_PATH.exists():
        synthetic = pd.read_csv(SYNTHETIC_PATH)
        synthetic["data_source"] = "synthetic"
        frames.append(synthetic)
        print(f"Loaded {len(synthetic)} synthetic augmentation samples")
    else:
        print("WARNING: Synthetic data not found. Run scripts/generate_synthetic_data.py")

    if not frames:
        print("ERROR: No training data available!")
        print("Run at minimum: uv run python scripts/generate_synthetic_data.py")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    print(f"\nCombined training set: {len(combined)} samples")
    if "data_source" in combined.columns:
        print(f"  Sources: {combined['data_source'].value_counts().to_dict()}")
    return combined


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_hybrid_data()
    print()

    train_qoe_model(df)
    train_forecaster(df)

    print("\nAll models trained and saved to artifacts/")


if __name__ == "__main__":
    main()
