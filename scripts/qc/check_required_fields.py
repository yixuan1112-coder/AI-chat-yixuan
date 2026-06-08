#!/usr/bin/env python3
"""
Check Required Fields — BatteryTwin Schema v0.2
================================================
Validates that all required fields exist and contain non-null values
across metadata, timeseries, and cycle_summary files.

Usage:
  python scripts/qc/check_required_fields.py --dataset dataset_01
  python scripts/qc/check_required_fields.py --all
"""

import argparse
import glob
import os
import sys

import pandas as pd

REQUIRED_METADATA = [
    "dataset_id", "cell_id", "source_type", "chemistry",
    "cathode_material", "anode_material", "form_factor",
    "nominal_capacity_Ah", "temperature_C",
    "charge_protocol", "discharge_protocol",
]

REQUIRED_TIMESERIES = [
    "cell_id", "cycle_id", "time_s", "voltage_V", "current_A", "temperature_C",
]

REQUIRED_CYCLE_SUMMARY = [
    "cell_id", "cycle_id", "capacity_Ah",
]

PROCESSED_DIR = "data/processed"


def find_files(dataset_dir):
    """Find metadata, timeseries, and cycle_summary files in a dataset dir."""
    files = {}
    for f in os.listdir(dataset_dir):
        fl = f.lower()
        if "metadata" in fl and fl.endswith(".csv"):
            files["metadata"] = os.path.join(dataset_dir, f)
        elif "timeseries" in fl and fl.endswith(".parquet"):
            files["timeseries"] = os.path.join(dataset_dir, f)
        elif "timeseries" in fl and fl.endswith(".csv") and "timeseries" not in files:
            files["timeseries"] = os.path.join(dataset_dir, f)
        elif "cycle_summary" in fl and fl.endswith(".csv"):
            files["cycle_summary"] = os.path.join(dataset_dir, f)
    return files


def check_fields(filepath, required_fields, file_type):
    """Check required fields in a single file."""
    print(f"\n  [{file_type}] {os.path.basename(filepath)}")
    
    if filepath.endswith(".parquet"):
        df = pd.read_parquet(filepath)
    else:
        df = pd.read_csv(filepath)

    issues = []
    for col in required_fields:
        if col not in df.columns:
            issues.append(f"    MISSING: {col}")
        else:
            null_pct = df[col].isna().mean() * 100
            if null_pct == 0:
                print(f"    {col}: OK")
            elif null_pct < 10:
                print(f"    {col}: WARN ({null_pct:.1f}% null)")
            else:
                issues.append(f"    {col}: FAIL ({null_pct:.1f}% null)")

    for issue in issues:
        print(issue)

    return len(issues) == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help="Dataset ID (e.g., dataset_01)")
    parser.add_argument("--all", action="store_true", help="Check all datasets")
    parser.add_argument("--base-dir", default=".", help="Repository root directory")
    args = parser.parse_args()

    base = args.base_dir
    processed = os.path.join(base, PROCESSED_DIR)

    if args.all:
        datasets = sorted([d for d in os.listdir(processed) 
                          if os.path.isdir(os.path.join(processed, d)) and d.startswith("dataset")])
    elif args.dataset:
        datasets = [args.dataset]
    else:
        print("Usage: --dataset <id> or --all")
        sys.exit(1)

    total_pass = 0
    total_fail = 0

    for ds in datasets:
        ds_dir = os.path.join(processed, ds)
        if not os.path.isdir(ds_dir):
            print(f"\n[SKIP] {ds}: directory not found")
            continue

        print(f"\n{'='*60}")
        print(f"Checking: {ds}")
        print(f"{'='*60}")

        files = find_files(ds_dir)
        passed = True

        if "metadata" in files:
            if not check_fields(files["metadata"], REQUIRED_METADATA, "metadata"):
                passed = False
        else:
            print(f"\n  [metadata] NOT FOUND")
            passed = False

        if "timeseries" in files:
            if not check_fields(files["timeseries"], REQUIRED_TIMESERIES, "timeseries"):
                passed = False
        else:
            print(f"\n  [timeseries] NOT FOUND")
            passed = False

        if "cycle_summary" in files:
            if not check_fields(files["cycle_summary"], REQUIRED_CYCLE_SUMMARY, "cycle_summary"):
                passed = False
        else:
            print(f"\n  [cycle_summary] NOT FOUND")
            passed = False

        if passed:
            total_pass += 1
            print(f"\n  >> RESULT: PASS")
        else:
            total_fail += 1
            print(f"\n  >> RESULT: ISSUES FOUND")

    print(f"\n{'='*60}")
    print(f"SUMMARY: {total_pass} passed, {total_fail} with issues")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
