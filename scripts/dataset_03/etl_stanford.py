#!/usr/bin/env python3
"""
ETL script for Dataset_03: Stanford-MIT-TRI (Severson et al. 2019)
Reads MATLAB v7.3 HDF5 files using h5py.

Usage:
    python scripts/etl_stanford.py \
        --input data/raw/dataset_03_Stanford_MIT_TRI \
        --output data/processed/dataset_03_Stanford_MIT_TRI

Output:
    - Stanford_MIT_TRI_metadata.csv
    - Stanford_MIT_TRI_cycle_summary.csv
    - Stanford_MIT_TRI_timeseries.parquet (combined)
    - Per-cell subdirectories with individual timeseries parquet files
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Batch file mapping ──────────────────────────────────────────────────────
BATCH_FILES = [
    ("2017-05-12_batchdata_updated_struct_errorcorrect.mat", "batch1", "2017-05-12"),
    ("2017-06-30_batchdata_updated_struct_errorcorrect.mat", "batch2", "2017-06-30"),
    ("2018-04-12_batchdata_updated_struct_errorcorrect.mat", "batch3", "2018-04-12"),
]

# ── Helper functions ────────────────────────────────────────────────────────

def h5_deref(f, ref):
    """Dereference an HDF5 object reference."""
    return f[ref]


def h5_read_scalar(f, dataset, idx):
    """Read a scalar value from an object-reference dataset at index (idx, 0)."""
    ref = dataset[idx, 0]
    val = f[ref][()].flatten()
    if len(val) == 1:
        return val[0]
    return val


def h5_read_string(f, dataset, idx):
    """Read a string from an object-reference dataset at index (idx, 0)."""
    ref = dataset[idx, 0]
    val = f[ref][()].flatten()
    try:
        return "".join(chr(int(c)) for c in val)
    except (ValueError, TypeError):
        return str(val)


def h5_read_array(f, dataset, idx):
    """Read a 1-D float array from an object-reference dataset at index (idx, 0)."""
    ref = dataset[idx, 0]
    val = f[ref][()].flatten()
    return val


def process_batch(input_dir, mat_filename, batch_label, batch_date, output_dir):
    """Process a single batch .mat file and return metadata + cycle_summary DataFrames."""
    filepath = os.path.join(input_dir, mat_filename)
    if not os.path.exists(filepath):
        print(f"  [WARN] File not found: {filepath}, skipping.")
        return pd.DataFrame(), pd.DataFrame(), 0

    print(f"\n{'='*60}")
    print(f"Processing {batch_label}: {mat_filename}")
    print(f"{'='*60}")

    f = h5py.File(filepath, "r")
    batch = f["batch"]
    n_cells = batch["cycle_life"].shape[0]
    print(f"  Found {n_cells} cells")

    metadata_rows = []
    cycle_summary_rows = []
    ts_row_count = 0

    for i in range(n_cells):
        cell_id = f"{batch_label}_cell{i:02d}"
        print(f"  [{i+1}/{n_cells}] {cell_id}", end="", flush=True)

        # ── Metadata ────────────────────────────────────────────────
        cl_val = h5_read_scalar(f, batch["cycle_life"], i); cycle_life = -1 if (isinstance(cl_val, float) and np.isnan(cl_val)) else int(cl_val)
        policy_str = h5_read_string(f, batch["policy_readable"], i)

        try:
            barcode_val = h5_read_string(f, batch["barcode"], i)
        except Exception:
            barcode_val = ""

        try:
            channel_val = h5_read_scalar(f, batch["channel_id"], i)
            channel_val = int(channel_val)
        except Exception:
            channel_val = ""

        metadata_rows.append({
            "cell_id": cell_id,
            "dataset": "Stanford_MIT_TRI",
            "batch": batch_label,
            "batch_date": batch_date,
            "chemistry": "LFP/Graphite",
            "form_factor": "18650 cylindrical",
            "manufacturer": "A123 Systems",
            "model": "APR18650M1A",
            "nominal_capacity_Ah": 1.1,
            "nominal_voltage_V": 3.3,
            "cycle_life": cycle_life,
            "charging_policy": policy_str,
            "barcode": barcode_val,
            "channel_id": channel_val,
            "temperature_C": 30,
        })

        # ── Summary (cycle-level) ──────────────────────────────────
        summary_ref = batch["summary"][i, 0]
        summary_grp = f[summary_ref]

        n_cycles = summary_grp["cycle"].shape[1]

        cycle_arr = summary_grp["cycle"][0, :]
        qc_arr = summary_grp["QCharge"][0, :]
        qd_arr = summary_grp["QDischarge"][0, :]
        ir_arr = summary_grp["IR"][0, :]
        tavg_arr = summary_grp["Tavg"][0, :]
        tmax_arr = summary_grp["Tmax"][0, :]
        tmin_arr = summary_grp["Tmin"][0, :]
        ct_arr = summary_grp["chargetime"][0, :]

        for j in range(n_cycles):
            cycle_num = int(cycle_arr[j])
            # Skip cycle 0 or cycles with zero discharge capacity
            if cycle_num == 0 and qd_arr[j] == 0.0:
                continue
            cycle_summary_rows.append({
                "cell_id": cell_id,
                "cycle_number": cycle_num,
                "charge_capacity_Ah": round(qc_arr[j], 6),
                "discharge_capacity_Ah": round(qd_arr[j], 6),
                "internal_resistance_ohm": round(ir_arr[j], 8),
                "avg_temperature_C": round(tavg_arr[j], 4),
                "max_temperature_C": round(tmax_arr[j], 4),
                "min_temperature_C": round(tmin_arr[j], 4),
                "charge_time_min": round(ct_arr[j], 4),
            })

        # ── Timeseries (cycle-level detail) ─────────────────────────
        cycles_ref = batch["cycles"][i, 0]
        cycles_grp = f[cycles_ref]
        n_ts_cycles = cycles_grp["V"].shape[0]

        cell_dir = os.path.join(output_dir, cell_id)
        os.makedirs(cell_dir, exist_ok=True)

        cell_ts_frames = []
        for j in range(n_ts_cycles):
            # Skip cycle 0 placeholder
            try:
                v_ref = cycles_grp["V"][j, 0]
                v_data = f[v_ref][()].flatten()
            except Exception:
                continue
            if len(v_data) <= 2 and np.all(v_data == 0):
                continue

            try:
                t_data = f[cycles_grp["t"][j, 0]][()].flatten()
                i_data = f[cycles_grp["I"][j, 0]][()].flatten()
                qc_data = f[cycles_grp["Qc"][j, 0]][()].flatten()
                qd_data = f[cycles_grp["Qd"][j, 0]][()].flatten()
                temp_data = f[cycles_grp["T"][j, 0]][()].flatten()
            except Exception:
                continue

            n_pts = len(v_data)
            cycle_df = pd.DataFrame({
                "cell_id": cell_id,
                "cycle_number": j,  # 0-indexed from file, cycle 0 already skipped
                "time_s": t_data[:n_pts],
                "voltage_V": v_data[:n_pts],
                "current_A": i_data[:n_pts],
                "temperature_C": temp_data[:n_pts],
                "charge_capacity_Ah": qc_data[:n_pts],
                "discharge_capacity_Ah": qd_data[:n_pts],
            })
            cell_ts_frames.append(cycle_df)

        if cell_ts_frames:
            cell_ts = pd.concat(cell_ts_frames, ignore_index=True)
            # Save per-cell timeseries
            cell_ts.to_parquet(
                os.path.join(cell_dir, f"{cell_id}_timeseries.parquet"),
                index=False,
                engine="pyarrow",
            )
            ts_row_count += len(cell_ts)
            print(f" → {n_cycles} cycles, {len(cell_ts):,} ts rows")
        else:
            print(f" → {n_cycles} cycles, 0 ts rows (WARN: no timeseries)")

    f.close()

    meta_df = pd.DataFrame(metadata_rows)
    cs_df = pd.DataFrame(cycle_summary_rows)

    print(f"\n  {batch_label} summary: {len(meta_df)} cells, "
          f"{len(cs_df):,} cycle_summary rows, {ts_row_count:,} timeseries rows")

    return meta_df, cs_df, ts_row_count


def combine_timeseries_parquet(output_dir, cell_ids):
    """Combine per-cell parquet files into a single timeseries parquet."""
    print("\nCombining per-cell parquet files into unified timeseries...")
    frames = []
    for cid in cell_ids:
        pq_path = os.path.join(output_dir, cid, f"{cid}_timeseries.parquet")
        if os.path.exists(pq_path):
            frames.append(pd.read_parquet(pq_path))
    if frames:
        combined = pd.concat(frames, ignore_index=True)
        out_path = os.path.join(output_dir, "Stanford_MIT_TRI_timeseries.parquet")
        combined.to_parquet(out_path, index=False, engine="pyarrow")
        print(f"  Combined timeseries: {len(combined):,} rows → {out_path}")
        return combined
    return pd.DataFrame()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ETL for Stanford-MIT-TRI (Severson et al. 2019) battery dataset"
    )
    parser.add_argument("--input", required=True, help="Path to raw data directory")
    parser.add_argument("--output", required=True, help="Path to output directory")
    parser.add_argument(
        "--skip-timeseries-combine",
        action="store_true",
        help="Skip combining per-cell parquet into unified file (saves memory)",
    )
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    all_meta = []
    all_cs = []
    total_ts = 0

    for mat_file, batch_label, batch_date in BATCH_FILES:
        meta_df, cs_df, ts_count = process_batch(
            args.input, mat_file, batch_label, batch_date, args.output
        )
        if not meta_df.empty:
            all_meta.append(meta_df)
        if not cs_df.empty:
            all_cs.append(cs_df)
        total_ts += ts_count

    # ── Save metadata ───────────────────────────────────────────────────
    if all_meta:
        metadata = pd.concat(all_meta, ignore_index=True)
        meta_path = os.path.join(args.output, "Stanford_MIT_TRI_metadata.csv")
        metadata.to_csv(meta_path, index=False)
        print(f"\n✅ Metadata: {len(metadata)} cells → {meta_path}")
    else:
        print("\n❌ No metadata generated!")
        sys.exit(1)

    # ── Save cycle_summary ──────────────────────────────────────────────
    if all_cs:
        cycle_summary = pd.concat(all_cs, ignore_index=True)
        cs_path = os.path.join(args.output, "Stanford_MIT_TRI_cycle_summary.csv")
        cycle_summary.to_csv(cs_path, index=False)
        print(f"✅ Cycle summary: {len(cycle_summary):,} rows → {cs_path}")
    else:
        print("❌ No cycle summary generated!")

    # ── Combine timeseries ──────────────────────────────────────────────
    if not args.skip_timeseries_combine and all_meta:
        cell_ids = metadata["cell_id"].tolist()
        combined_ts = combine_timeseries_parquet(args.output, cell_ids)
        if not combined_ts.empty:
            # Save sample (first 1000 rows)
            sample = combined_ts.head(1000)
            sample_path = os.path.join(args.output, "Stanford_MIT_TRI_timeseries_SAMPLE.csv")
            sample.to_csv(sample_path, index=False)
            print(f"✅ Timeseries sample: 1000 rows → {sample_path}")
    else:
        print("⏭️  Skipped timeseries combine (use per-cell parquet files)")

    # ── Final report ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("ETL COMPLETE")
    print(f"{'='*60}")
    print(f"  Cells:          {len(metadata)}")
    print(f"  Cycle summary:  {len(cycle_summary):,} rows")
    print(f"  Timeseries:     {total_ts:,} rows (approx)")
    print(f"  Output:         {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
