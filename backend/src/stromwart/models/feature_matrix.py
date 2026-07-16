"""Shared feature column names and DataFrame builders for ML models."""

from __future__ import annotations

import pandas as pd

from stromwart.contracts.features import FeatureVector

FEATURE_COLUMNS = [
    "observation_count",
    "throughput_mean_kbps",
    "throughput_std_kbps",
    "buffer_mean_ms",
    "buffer_min_ms",
    "rebuffer_total_ms",
    "stall_ratio",
    "downswitch_count",
    "latest_bitrate_kbps",
    "latest_packet_loss_pct",
]

FORECAST_FEATURE_COLUMNS = [*FEATURE_COLUMNS, "horizon_seconds"]


def feature_row(features: FeatureVector) -> dict[str, float]:
    return {
        "observation_count": float(features.observation_count),
        "throughput_mean_kbps": float(features.throughput_mean_kbps),
        "throughput_std_kbps": float(features.throughput_std_kbps),
        "buffer_mean_ms": float(features.buffer_mean_ms),
        "buffer_min_ms": float(features.buffer_min_ms),
        "rebuffer_total_ms": float(features.rebuffer_total_ms),
        "stall_ratio": float(features.stall_ratio),
        "downswitch_count": float(features.downswitch_count),
        "latest_bitrate_kbps": float(features.latest_bitrate_kbps),
        "latest_packet_loss_pct": (
            float(features.latest_packet_loss_pct)
            if features.latest_packet_loss_pct is not None
            else 0.0
        ),
    }


def features_frame(features: FeatureVector) -> pd.DataFrame:
    return pd.DataFrame([feature_row(features)], columns=FEATURE_COLUMNS)


def forecast_features_frame(
    features: FeatureVector,
    horizon_seconds: int,
) -> pd.DataFrame:
    row = feature_row(features)
    row["horizon_seconds"] = float(horizon_seconds)
    return pd.DataFrame([row], columns=FORECAST_FEATURE_COLUMNS)
