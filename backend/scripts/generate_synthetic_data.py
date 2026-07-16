"""
Generate synthetic QoE training data mimicking WaterlooSQoE-IV feature distributions.

Output: backend/data/synthetic_qoe_train.csv
Features match the FeatureVector schema; labels are synthetic MOS (1-5).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

SEED = 42
N_SAMPLES = 2000
OUTPUT_DIR = Path(__file__).parents[1] / "data"


def _compute_mos(df: pd.DataFrame) -> pd.Series:
    """Synthetic MOS (inspired by ITU-T P.1203 degradation model)."""
    bitrate_norm = np.log1p(df["latest_bitrate_kbps"]) / np.log1p(8000)
    stall_penalty = df["stall_ratio"] * 3.0
    loss_penalty = (df["latest_packet_loss_pct"] / 100) * 1.5
    buffer_bonus = np.clip((df["buffer_min_ms"] - 500) / 10000, 0, 0.5)
    mos_raw = 1.0 + 3.5 * bitrate_norm - stall_penalty - loss_penalty + buffer_bonus
    return mos_raw


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    throughput_mean = rng.lognormal(mean=8.5, sigma=0.6, size=N_SAMPLES)  # ~4000-8000 kbps
    throughput_std = rng.exponential(scale=500, size=N_SAMPLES)
    buffer_mean = rng.uniform(1000, 15000, size=N_SAMPLES)
    buffer_min = np.clip(buffer_mean - rng.exponential(2000, size=N_SAMPLES), 0, None).astype(int)
    rebuffer_total = rng.exponential(scale=800, size=N_SAMPLES).astype(int)
    observation_count = rng.integers(10, 60, size=N_SAMPLES)
    duration_total = observation_count * 2000  # ~2s chunks
    stall_ratio = np.clip(rebuffer_total / duration_total, 0, 1)
    downswitch_count = rng.poisson(lam=1.5, size=N_SAMPLES)
    latest_bitrate = rng.choice(
        [720, 1500, 3000, 5000, 8000], size=N_SAMPLES, p=[0.05, 0.15, 0.35, 0.30, 0.15]
    )
    latest_packet_loss = rng.exponential(scale=1.5, size=N_SAMPLES)
    latest_packet_loss = np.clip(latest_packet_loss, 0, 100)

    df = pd.DataFrame(
        {
            "observation_count": observation_count,
            "throughput_mean_kbps": throughput_mean.round(1),
            "throughput_std_kbps": throughput_std.round(1),
            "buffer_mean_ms": buffer_mean.round(1),
            "buffer_min_ms": buffer_min,
            "rebuffer_total_ms": rebuffer_total,
            "stall_ratio": stall_ratio.round(6),
            "downswitch_count": downswitch_count,
            "latest_bitrate_kbps": latest_bitrate,
            "latest_packet_loss_pct": latest_packet_loss.round(2),
        }
    )
    mos = np.clip(_compute_mos(df) + rng.normal(0, 0.2, size=N_SAMPLES), 1.0, 5.0)
    df["mos"] = mos.round(3)

    return df


def generate_tail_cases(n: int = 500, seed: int = 99) -> pd.DataFrame:
    """Generate extreme degradation scenarios for tail coverage."""
    rng = np.random.default_rng(seed)

    severe = pd.DataFrame(
        {
            "throughput_mean_kbps": rng.uniform(200, 1500, n // 2),
            "throughput_std_kbps": rng.uniform(300, 800, n // 2),
            "buffer_mean_ms": rng.uniform(500, 2000, n // 2),
            "buffer_min_ms": rng.uniform(0, 500, n // 2),
            "rebuffer_total_ms": rng.uniform(2000, 8000, n // 2),
            "stall_ratio": rng.uniform(0.1, 0.4, n // 2),
            "downswitch_count": rng.integers(3, 10, n // 2).astype(float),
            "latest_bitrate_kbps": rng.uniform(500, 2000, n // 2),
            "latest_packet_loss_pct": rng.uniform(3.0, 15.0, n // 2),
            "observation_count": rng.integers(5, 30, n // 2).astype(float),
        }
    )

    perfect = pd.DataFrame(
        {
            "throughput_mean_kbps": rng.uniform(8000, 15000, n // 2),
            "throughput_std_kbps": rng.uniform(50, 200, n // 2),
            "buffer_mean_ms": rng.uniform(10000, 20000, n // 2),
            "buffer_min_ms": rng.uniform(5000, 12000, n // 2),
            "rebuffer_total_ms": rng.uniform(0, 50, n // 2),
            "stall_ratio": rng.uniform(0.0, 0.005, n // 2),
            "downswitch_count": rng.integers(0, 1, n // 2).astype(float),
            "latest_bitrate_kbps": rng.uniform(6000, 12000, n // 2),
            "latest_packet_loss_pct": rng.uniform(0.0, 0.2, n // 2),
            "observation_count": rng.integers(10, 50, n // 2).astype(float),
        }
    )

    combined = pd.concat([severe, perfect], ignore_index=True)
    combined["mos"] = np.clip(_compute_mos(combined), 1.0, 5.0).round(3)
    return combined


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_df = generate()
    tail_df = generate_tail_cases()
    df = pd.concat([base_df, tail_df], ignore_index=True)
    output_path = OUTPUT_DIR / "synthetic_qoe_train.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} samples -> {output_path}")
    print(f"  Base: {len(base_df)}, Tail cases: {len(tail_df)}")
    print(f"MOS distribution: mean={df['mos'].mean():.2f}, std={df['mos'].std():.2f}")
    print(f"  min={df['mos'].min():.2f}, max={df['mos'].max():.2f}")
