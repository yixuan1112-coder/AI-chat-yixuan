#!/usr/bin/env python3
"""
ETL script for Dataset 05: RWTH Aachen
Reads processed .mat files from the ISEA GitLab repo.

Data structure:
  processed_repo/Processed Experimental Data/P001/epSanyo{002-049}/
    TS{number}/
      lean_data.mat   -> segment summary (AhEla, avg_Ah_per_cycle, subcycles, voltages, etc.)

Segment types (from DigaProgrammName):
  - TBA_BOL_P1/P2 (Begin of Life tests)
  - TBA_Zyk (Zyklierung = cycling)
  - TBA_CU / TBA_CUv2 (Checkup = RPT capacity tests)
  - TBA_CHA (Characterization / final)
  - EIS (Impedance - separate folders)

Usage:
    conda activate batterytwin
    python scripts/etl_rwth.py
"""

import os
import numpy as np
import pandas as pd
import scipy.io

# Config
BASE_DIR = os.path.expanduser("~/Projects/BatteryTwin-Benchmark-DataPrep")
REPO_DIR = os.path.join(BASE_DIR, "data/raw/dataset_05_RWTH/processed_repo",
                        "Processed Experimental Data", "P001")
OUT_DIR = os.path.join(BASE_DIR, "data/processed/dataset_05")

NOMINAL_CAPACITY_AH = 2.05
CELL_MODEL = "Sanyo/Panasonic UR18650E"
CHEMISTRY_CATHODE = "NMC"
CHEMISTRY_ANODE = "Carbon (Graphite)"
FORM_FACTOR = "18650 Cylindrical"
TEMPERATURE_C = 25
TIMESERIES_SAMPLE_ROWS = 100


def matlab_datenum_to_str(datenum):
    try:
        from datetime import datetime, timedelta
        dt = datetime.fromordinal(int(datenum)) + timedelta(days=datenum % 1) - timedelta(days=366)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(datenum)


def read_lean_data(mat_path):
    try:
        d = scipy.io.loadmat(mat_path)
    except Exception:
        return None

    result = {}
    for k in ['StartDate', 'EndDate', 'StartVoltage', 'EndVoltage',
              'AhEla', 'checkup_temp', 'ChargeCurrent',
              'MeanCycleVoltage', 'subcycles',
              'avg_Ah_per_cycle', 'avg_Energy_per_cycle']:
        if k in d:
            val = d[k].flatten()
            if len(val) > 0:
                result[k] = float(val[0])

    for k in ['DigaProgrammName', 'Equipment']:
        if k in d:
            try:
                result[k] = str(d[k].flatten()[0])
            except Exception:
                result[k] = ''
    return result


def classify_segment(ts_name, lean_info):
    prog = (lean_info.get('DigaProgrammName', '') if lean_info else '').lower()
    if 'eis' in ts_name.lower():
        return 'EIS'
    if 'bol' in prog:
        return 'BOL'
    if 'zyk' in prog:
        return 'ZYK'
    if 'cu' in prog:
        return 'CU'
    if 'cha' in prog:
        return 'CHA'
    if lean_info:
        if lean_info.get('subcycles', 0) > 50:
            return 'ZYK'
    return 'OTHER'


def process_cell(cell_path, cell_name):
    segments = []
    for ts_name in sorted(os.listdir(cell_path)):
        ts_path = os.path.join(cell_path, ts_name)
        if not os.path.isdir(ts_path):
            continue
        lean_path = os.path.join(ts_path, 'lean_data.mat')
        if not os.path.exists(lean_path):
            continue
        lean_info = read_lean_data(lean_path)
        if lean_info is None:
            continue
        seg_type = classify_segment(ts_name, lean_info)
        segments.append({
            'cell_id': cell_name,
            'segment_id': ts_name,
            'segment_type': seg_type,
            'start_date': lean_info.get('StartDate', np.nan),
            'end_date': lean_info.get('EndDate', np.nan),
            'start_date_str': matlab_datenum_to_str(lean_info['StartDate']) if 'StartDate' in lean_info else '',
            'start_voltage_V': lean_info.get('StartVoltage', np.nan),
            'end_voltage_V': lean_info.get('EndVoltage', np.nan),
            'Ah_throughput': lean_info.get('AhEla', np.nan),
            'subcycles': int(lean_info.get('subcycles', 0)),
            'avg_Ah_per_cycle': lean_info.get('avg_Ah_per_cycle', np.nan),
            'avg_Energy_per_cycle': lean_info.get('avg_Energy_per_cycle', np.nan),
            'mean_cycle_voltage_V': lean_info.get('MeanCycleVoltage', np.nan),
            'charge_current_A': lean_info.get('ChargeCurrent', np.nan),
            'temperature_C': lean_info.get('checkup_temp', TEMPERATURE_C),
            'program_name': lean_info.get('DigaProgrammName', ''),
            'equipment': lean_info.get('Equipment', ''),
        })
    if not segments:
        return None
    return pd.DataFrame(segments).sort_values('start_date').reset_index(drop=True)


def build_cycle_summary(all_segments_df):
    rows = []
    for cell_id, cell_df in all_segments_df.groupby('cell_id'):
        cell_df = cell_df.sort_values('start_date')
        cumulative_cycles = 0
        for _, seg in cell_df.iterrows():
            if seg['segment_type'] in ('ZYK', 'CU', 'CHA'):
                subcycles = seg['subcycles']
                cumulative_cycles += subcycles
                rows.append({
                    'cell_id': cell_id,
                    'segment_id': seg['segment_id'],
                    'segment_type': seg['segment_type'],
                    'start_date': seg['start_date_str'],
                    'subcycles_in_segment': subcycles,
                    'cumulative_cycles': cumulative_cycles,
                    'Ah_throughput': round(seg['Ah_throughput'], 4) if not np.isnan(seg['Ah_throughput']) else np.nan,
                    'avg_Ah_per_cycle': round(seg['avg_Ah_per_cycle'], 6) if not np.isnan(seg['avg_Ah_per_cycle']) else np.nan,
                    'avg_Energy_per_cycle': round(seg['avg_Energy_per_cycle'], 6) if not np.isnan(seg['avg_Energy_per_cycle']) else np.nan,
                    'start_voltage_V': round(seg['start_voltage_V'], 4) if not np.isnan(seg['start_voltage_V']) else np.nan,
                    'end_voltage_V': round(seg['end_voltage_V'], 4) if not np.isnan(seg['end_voltage_V']) else np.nan,
                    'mean_cycle_voltage_V': round(seg['mean_cycle_voltage_V'], 4) if not np.isnan(seg['mean_cycle_voltage_V']) else np.nan,
                    'temperature_C': round(seg['temperature_C'], 1) if not np.isnan(seg['temperature_C']) else TEMPERATURE_C,
                    'is_rpt': seg['segment_type'] == 'CU',
                })
    return pd.DataFrame(rows)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 60)
    print("ETL: Dataset 05 - RWTH Aachen (48 NMC/Graphite UR18650E)")
    print("  Source: processed_repo .mat files")
    print("=" * 60)

    if not os.path.isdir(REPO_DIR):
        print(f"\nERROR: Not found: {REPO_DIR}")
        print("Run: cd data/raw/dataset_05_RWTH && git clone https://git.rwth-aachen.de/isea/battery-degradation-trajectory-prediction.git processed_repo")
        return

    cell_dirs = sorted([d for d in os.listdir(REPO_DIR)
                        if d.startswith('epSanyo') and os.path.isdir(os.path.join(REPO_DIR, d))])
    print(f"\nFound {len(cell_dirs)} cells")

    all_segments = []
    metadata_rows = []

    for cell_dir_name in cell_dirs:
        cell_num = cell_dir_name.replace('epSanyo', '')
        cell_name = f"RWTH_Cell{cell_num}"
        cell_path = os.path.join(REPO_DIR, cell_dir_name)
        print(f"\n-- {cell_name} --")

        seg_df = process_cell(cell_path, cell_name)
        if seg_df is None or len(seg_df) == 0:
            print("  SKIP: no valid segments")
            continue

        n_zyk = len(seg_df[seg_df['segment_type'] == 'ZYK'])
        n_cu = len(seg_df[seg_df['segment_type'] == 'CU'])
        total_subcycles = int(seg_df[seg_df['segment_type'] == 'ZYK']['subcycles'].sum())
        print(f"  Segments: {len(seg_df)} (ZYK={n_zyk}, CU={n_cu}), subcycles={total_subcycles}")

        zyk = seg_df[seg_df['segment_type'] == 'ZYK'].sort_values('start_date')
        first_ah = zyk['avg_Ah_per_cycle'].iloc[0] if len(zyk) > 0 else np.nan
        last_ah = zyk['avg_Ah_per_cycle'].iloc[-1] if len(zyk) > 0 else np.nan

        all_segments.append(seg_df)

        sample_path = os.path.join(OUT_DIR, f"rwth_cell{cell_num}_timeseries.csv.txt")
        seg_df.head(TIMESERIES_SAMPLE_ROWS).to_csv(sample_path, index=False)

        metadata_rows.append({
            'cell_id': cell_name, 'dataset': 'RWTH', 'source_dir': cell_dir_name,
            'cell_model': CELL_MODEL, 'form_factor': FORM_FACTOR,
            'cathode': CHEMISTRY_CATHODE, 'anode': CHEMISTRY_ANODE,
            'nominal_capacity_Ah': NOMINAL_CAPACITY_AH, 'temperature_C': TEMPERATURE_C,
            'protocol': 'CC discharge to 3.5V / CC charge to 3.9V, max 4A, 30min each',
            'total_segments': len(seg_df), 'cycling_segments': n_zyk,
            'checkup_segments': n_cu, 'total_subcycles': total_subcycles,
            'first_avg_Ah_per_cycle': round(first_ah, 6) if not np.isnan(first_ah) else '',
            'last_avg_Ah_per_cycle': round(last_ah, 6) if not np.isnan(last_ah) else '',
        })

    if not all_segments:
        print("\nERROR: No data extracted!")
        return

    full_segments = pd.concat(all_segments, ignore_index=True)
    cycle_summary = build_cycle_summary(full_segments)

    summary_path = os.path.join(OUT_DIR, "RWTH_cycle_summary.csv")
    cycle_summary.to_csv(summary_path, index=False)
    print(f"\n  Cycle summary: {summary_path} ({len(cycle_summary)} rows)")

    meta_df = pd.DataFrame(metadata_rows)
    meta_path = os.path.join(OUT_DIR, "RWTH_metadata.csv")
    meta_df.to_csv(meta_path, index=False)
    print(f"  Metadata: {meta_path} ({len(meta_df)} cells)")

    loc_path = os.path.join(OUT_DIR, "DATA_LOCATION.txt")
    with open(loc_path, 'w') as f:
        f.write("Dataset 05: RWTH Aachen\n")
        f.write("=" * 40 + "\n\n")
        f.write("Source: ISEA GitLab processed .mat files\n")
        f.write("Repo: https://git.rwth-aachen.de/isea/battery-degradation-trajectory-prediction\n")
        f.write("Local: data/raw/dataset_05_RWTH/processed_repo/\n\n")
        f.write(f"Total cells: {len(metadata_rows)}\n")
        f.write(f"Total cycle summary rows: {len(cycle_summary)}\n")
    print(f"  DATA_LOCATION: {loc_path}")

    print(f"\n  Segment types: {dict(full_segments['segment_type'].value_counts())}")
    print("\nDone! Now run:")
    print("  git pull origin main")
    print("  git add -f data/processed/dataset_05/ data/raw/dataset_05_RWTH/DOWNLOAD.md")
    print("  git add scripts/etl_rwth.py docs/dataset_notes/dataset_05_RWTH_note*.md")
    print("  git add docs/project_plan/weekly_comparison_batterylife_vs_batterytwin_tables.md")
    print("  git add -f dataset_registry.csv")
    print("  git commit -m 'feat: add dataset_05 RWTH Aachen (48 NMC/Graphite cells)'")
    print("  git push origin main")


if __name__ == "__main__":
    main()
