"""Download public crash detection datasets for model training.

Datasets:
- CADP (Car Accident Detection and Prediction): Dashcam crash videos
- UA-DETRAC: Traffic detection and tracking dataset
- Normal traffic: Sampled from DOT camera feeds
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

DATASETS = {
    "cadp": {
        "description": "Car Accident Detection and Prediction dataset (1,416 crash videos)",
        "url": "https://github.com/ankitshah009/CarAccidentDetectionAndPrediction",
        "type": "git",
    },
    "dota": {
        "description": "Detection of Traffic Anomaly dataset (4,677 anomaly videos)",
        "url": "https://github.com/MoonBlvd/Detection-of-Traffic-Anomaly",
        "type": "git",
    },
}


def download_git_repo(name: str, url: str, output_dir: Path) -> None:
    """Clone a git repository."""
    target = output_dir / name
    if target.exists():
        print(f"  {name}: Already exists, skipping")
        return

    print(f"  Cloning {name}...")
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target)],
        check=True,
        capture_output=True,
    )
    print(f"  {name}: Done")


def create_negative_samples_script() -> None:
    """Create a script to capture normal traffic frames from DOT feeds."""
    script = DATA_DIR / "raw" / "capture_normal_traffic.sh"
    script.parent.mkdir(parents=True, exist_ok=True)

    script.write_text("""#!/bin/bash
# Capture normal traffic frames from DOT cameras for negative training samples
# Run this for 24 hours to get diverse lighting and traffic conditions

CAMERAS=(
    "https://cwwp2.dot.ca.gov/data/d7/cctv/image/i405-nb-wilshire/i405-nb-wilshire.jpg"
    "https://images.wsdot.wa.gov/nw/005vc16757.jpg"
    "https://its.txdot.gov/ITS_WEB/FrontEnd/snapshots/camera_255.jpg"
)

OUTPUT_DIR="./normal_traffic"
mkdir -p "$OUTPUT_DIR"

INTERVAL=60  # Capture one frame per minute
DURATION=$((24 * 60))  # 24 hours

for i in $(seq 1 $DURATION); do
    for j in "${!CAMERAS[@]}"; do
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        curl -s -o "${OUTPUT_DIR}/cam${j}_${TIMESTAMP}.jpg" "${CAMERAS[$j]}" 2>/dev/null || true
    done
    sleep $INTERVAL
done

echo "Captured normal traffic samples in $OUTPUT_DIR"
""")
    os.chmod(script, 0o755)
    print("Created normal traffic capture script")


def main():
    parser = argparse.ArgumentParser(description="Download crash detection datasets")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()) + ["all"], default="all")
    args = parser.parse_args()

    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    datasets = DATASETS if args.dataset == "all" else {args.dataset: DATASETS[args.dataset]}

    for name, info in datasets.items():
        print(f"\nDataset: {info['description']}")
        try:
            if info["type"] == "git":
                download_git_repo(name, info["url"], raw_dir)
        except Exception as e:
            print(f"  Error downloading {name}: {e}")

    create_negative_samples_script()
    print("\nDone. Run preprocessing next: python preprocess.py")


if __name__ == "__main__":
    main()
