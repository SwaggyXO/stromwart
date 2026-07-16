"""
Download WaterlooSQoE-IV processed features from the research repository.
Falls back to generating a realistic proxy if network is unavailable.
"""

import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parents[1] / "data"
RAW_DIR = DATA_DIR / "raw" / "waterloo_iv"
REPO_URL = "https://github.com/Leo-rojo/Quality_of_Experience_in_Video_Streaming_Status_Quo_Pitfalls_and_Guidelines.git"


def download() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    clone_target = RAW_DIR / "repo"
    if clone_target.exists():
        print(f"Repository already cloned at {clone_target}")
        return

    print("Cloning Waterloo-IV research repository...")
    result = subprocess.run(
        [
            "git",
            "clone",
            "--depth=1",
            "--filter=blob:none",
            "--sparse",
            REPO_URL,
            str(clone_target),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: git clone failed: {result.stderr}")
        print("Falling back to synthetic data generation.")
        sys.exit(1)

    # Sparse checkout only the data we need
    subprocess.run(
        ["git", "sparse-checkout", "set", "allfeat_allscores_WIV"],
        cwd=str(clone_target),
        capture_output=True,
    )
    print(f"Downloaded Waterloo-IV features to {clone_target}")


if __name__ == "__main__":
    download()
