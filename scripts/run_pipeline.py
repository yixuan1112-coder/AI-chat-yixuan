#!/usr/bin/env python3
"""
BatteryTwin Data Pipeline Runner
=================================
Orchestrates ETL + QC for a given dataset.

Usage:
  python scripts/run_pipeline.py --dataset dataset_01
  python scripts/run_pipeline.py --dataset dataset_01 --steps etl qc
"""

import argparse
import os
import subprocess
import sys

# Map dataset_id -> (etl_script, qc_script, raw_data_dir)
DATASET_CONFIG = {
    "dataset_01": {
        "name": "NASA PCoE",
        "etl_script": "scripts/etl_nasa.py",
        "qc_script": "scripts/quality_check_nasa.py",
        "raw_dir": "data/raw/dataset_01_NASA_PCoE",
        "processed_dir": "data/processed/dataset_01",
    },
    # Add more datasets here as they are developed
    # "dataset_02": { ... },
}


def run_command(cmd, description):
    """Run a shell command and report results."""
    print(f"\n{'─'*50}")
    print(f"STEP: {description}")
    print(f"CMD:  {' '.join(cmd)}")
    print(f"{'─'*50}")
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\n[ERROR] {description} failed with exit code {result.returncode}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="BatteryTwin Pipeline Runner")
    parser.add_argument("--dataset", required=True, help="Dataset ID (e.g., dataset_01)")
    parser.add_argument("--steps", nargs="+", default=["etl", "qc"],
                       choices=["etl", "qc"], help="Which steps to run")
    parser.add_argument("--base-dir", default=".", help="Repository root directory")
    args = parser.parse_args()

    if args.dataset not in DATASET_CONFIG:
        print(f"[ERROR] Unknown dataset: {args.dataset}")
        print(f"Available: {list(DATASET_CONFIG.keys())}")
        sys.exit(1)

    config = DATASET_CONFIG[args.dataset]
    base = args.base_dir

    print(f"Pipeline for: {config['name']} ({args.dataset})")
    print(f"Steps: {args.steps}")

    # Ensure output directory exists
    processed_dir = os.path.join(base, config["processed_dir"])
    os.makedirs(processed_dir, exist_ok=True)

    success = True

    if "etl" in args.steps:
        raw_dir = os.path.join(base, config["raw_dir"])
        if not os.path.exists(raw_dir):
            print(f"\n[ERROR] Raw data directory not found: {raw_dir}")
            print(f"Please download the raw data first. See the dataset note for instructions.")
            success = False
        else:
            etl_script = os.path.join(base, config["etl_script"])
            if not run_command(
                [sys.executable, etl_script, "--input", raw_dir, "--output", processed_dir],
                f"ETL: {config['name']}"
            ):
                success = False

    if "qc" in args.steps and success:
        qc_script = os.path.join(base, config["qc_script"])
        qc_output = os.path.join(base, "docs", "qc_reports", args.dataset)
        if not run_command(
            [sys.executable, qc_script, "--input", processed_dir, "--output", qc_output],
            f"QC: {config['name']}"
        ):
            success = False

    print(f"\n{'='*50}")
    if success:
        print(f"Pipeline COMPLETED for {args.dataset}")
    else:
        print(f"Pipeline FAILED for {args.dataset}")
    print(f"{'='*50}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
