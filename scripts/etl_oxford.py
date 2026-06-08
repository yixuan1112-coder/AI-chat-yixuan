#!/usr/bin/env python3
"""
ETL script for Dataset 04: Oxford Battery Degradation
Processes two sub-datasets:
  A) Kokam LCO pouch (8 cells, 740 mAh, 40°C) - characterization cycles
  B) NCA 18650 Path Dependent (12 cells, 3 Ah, 24°C) - cycling + RPT

Usage:
    conda activate batterytwin
    cd ~/Projects/BatteryTwin-Benchmark-DataPrep
    python scripts/etl_oxford.py

Output structure (mirrors raw sub-directories):
    data/processed/dataset_04/
    ├── Oxford_metadata.csv                          ← top-level, all 20 cells
    ├── DATA_LOCATION.txt
    ├── kokam_lco/
    │   ├── Oxford_kokam_lco_cycle_summary.csv
    │   ├── kokam_cell1_timeseries.csv               (full, local only)
    │   ├── kokam_cell1_timeseries.csv.txt            (first 100 rows, push to GitHub)
    │   └── ...
    └── nca_18650/
        ├── Oxford_nca_18650_cycle_summary.csv
        ├── nca_group1_cell1_timeseries.csv
        ├── nca_group1_cell1_timeseries.csv.txt
        └── ...

Author: Liu Kefan
Date: 2026-03-20
"""

import os
import sys
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Config
# ============================================================
REPO_ROOT = os.path.expanduser("~/Projects/BatteryTwin-Benchmark-DataPrep")
RAW_DIR = os.path.join(REPO_ROOT, "data/raw/dataset_04_Oxford")
PROC_DIR = os.path.join(REPO_ROOT, "data/processed/dataset_04")

KOKAM_MAT = os.path.join(RAW_DIR, "kokam_lco/Oxford_Battery_Degradation_Dataset_1.mat")
NCA_DIR = os.path.join(RAW_DIR, "nca_18650")

# Nominal capacities
KOKAM_NOMINAL_mAh = 740.0   # mAh
KOKAM_NOMINAL_Ah = 0.740     # Ah (converted)
NCA_NOMINAL_Ah = 3.0          # Ah

TIMESERIES_SAMPLE_ROWS = 100

# ============================================================
# Helper functions
# ============================================================
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def save_timeseries_with_index(df, filepath):
    """Save full CSV + first-100-row .csv.txt index."""
    df.to_csv(filepath, index=False)
    txt_path = filepath + ".txt"
    df.head(TIMESERIES_SAMPLE_ROWS).to_csv(txt_path, index=False)
    return txt_path

def load_mat_file(filepath):
    """Try scipy.io first, fall back to h5py."""
    try:
        import scipy.io as sio
        data = sio.loadmat(filepath, squeeze_me=True, struct_as_record=False)
        return data, 'scipy'
    except NotImplementedError:
        import h5py
        data = h5py.File(filepath, 'r')
        return data, 'h5py'

# ============================================================
# Part A: Kokam LCO Dataset 1
# ============================================================
def process_kokam():
    """
    Structure from readme:
      Layer 1: Cells (1-8)
      Layer 2: Cycle number of characterisation (e.g. cyc0100, cyc0200, ...)
      Layer 3: C1ch (1C charge), C1dc (1C discharge), OCVch, OCVdc
      Layer 4: t (seconds), v (Volts), q (mAh), T (°C)

    We extract 1C discharge (C1dc) as the main cycling data.
    Discharge capacity from C1dc.q gives the degradation trajectory.
    """
    print("\n" + "=" * 60)
    print("Processing Part A: Kokam LCO (8 cells)")
    print("=" * 60)

    if not os.path.exists(KOKAM_MAT):
        print(f"[ERROR] File not found: {KOKAM_MAT}")
        print("        Please download first. See DOWNLOAD.md")
        return [], pd.DataFrame()

    data, loader = load_mat_file(KOKAM_MAT)
    print(f"  Loaded with: {loader}")

    out_dir = os.path.join(PROC_DIR, "kokam_lco")
    ensure_dir(out_dir)

    all_cycle_summaries = []
    metadata_rows = []

    if loader == 'scipy':
        # Navigate the nested struct
        # Expected: data contains a top-level variable with cells as sub-structs
        # Find the main data variable (skip __header__, __version__, __globals__)
        main_keys = [k for k in data.keys() if not k.startswith('__')]
        print(f"  Top-level keys: {main_keys}")

        # The main struct should contain cells
        # Typical structure: data['cell'] or similar - adapt based on explore output
        # We'll try common patterns
        main_data = None
        for key in main_keys:
            obj = data[key]
            if hasattr(obj, '__dict__') or (hasattr(obj, 'dtype') and obj.dtype.names):
                main_data = obj
                main_key = key
                break

        if main_data is None:
            print("  [ERROR] Could not find main data struct. Run explore_oxford.py first.")
            return [], pd.DataFrame()

        print(f"  Main data key: {main_key}")

        # Process each cell
        for cell_idx in range(8):
            cell_id = f"kokam_cell{cell_idx + 1}"
            print(f"\n  Processing {cell_id}...")

            try:
                # Access cell - adapt based on actual structure
                # Pattern 1: struct array indexed by cell
                if hasattr(main_data, '__getitem__') and hasattr(main_data, 'shape'):
                    if main_data.ndim > 0:
                        cell_data = main_data.flat[cell_idx] if main_data.size > 1 else main_data.flat[0]
                    else:
                        cell_data = main_data
                elif hasattr(main_data, f'Cell{cell_idx + 1}'):
                    cell_data = getattr(main_data, f'Cell{cell_idx + 1}')
                elif hasattr(main_data, f'cell{cell_idx + 1}'):
                    cell_data = getattr(main_data, f'cell{cell_idx + 1}')
                else:
                    # Try direct indexing
                    cell_data = main_data[cell_idx]

                # Get characterization cycle names (cyc0100, cyc0200, etc.)
                if hasattr(cell_data, '_fieldnames'):
                    cyc_names = sorted(cell_data._fieldnames)
                elif hasattr(cell_data, 'dtype') and cell_data.dtype.names:
                    cyc_names = sorted(cell_data.dtype.names)
                else:
                    cyc_names = sorted([a for a in dir(cell_data) if a.startswith('cyc')])

                print(f"    Found {len(cyc_names)} characterization cycles")

                timeseries_frames = []
                cycle_rows = []

                for cyc_name in cyc_names:
                    # Extract cycle number from name (e.g. 'cyc0100' → 100)
                    try:
                        cyc_num = int(cyc_name.replace('cyc', ''))
                    except ValueError:
                        continue

                    # Access this characterization cycle
                    if hasattr(cell_data, cyc_name):
                        cyc_data = getattr(cell_data, cyc_name)
                    elif hasattr(cell_data, '__getitem__'):
                        cyc_data = cell_data[cyc_name]
                    else:
                        continue

                    # Get 1C discharge data (C1dc)
                    try:
                        if hasattr(cyc_data, 'C1dc'):
                            dc = cyc_data.C1dc
                        elif hasattr(cyc_data, '__getitem__'):
                            dc = cyc_data['C1dc']
                        else:
                            dc_fields = [f for f in dir(cyc_data) if 'dc' in f.lower() or 'C1dc' in f]
                            if dc_fields:
                                dc = getattr(cyc_data, dc_fields[0])
                            else:
                                continue
                    except (KeyError, AttributeError):
                        continue

                    # Extract t, v, q, T
                    try:
                        t = np.array(dc.t).flatten() if hasattr(dc, 't') else np.array(dc['t']).flatten()
                        v = np.array(dc.v).flatten() if hasattr(dc, 'v') else np.array(dc['v']).flatten()
                        q = np.array(dc.q).flatten() if hasattr(dc, 'q') else np.array(dc['q']).flatten()
                        T = np.array(dc.T).flatten() if hasattr(dc, 'T') else np.array(dc['T']).flatten()
                    except (AttributeError, KeyError) as e:
                        print(f"    [WARN] Skipping {cyc_name}: {e}")
                        continue

                    # Convert q from mAh to Ah
                    q_Ah = q / 1000.0

                    # Discharge capacity = max(q) in Ah
                    discharge_cap_Ah = np.max(np.abs(q_Ah)) if len(q_Ah) > 0 else np.nan

                    # Build timeseries dataframe for this cycle
                    ts_df = pd.DataFrame({
                        'cell_id': cell_id,
                        'cycle_number': cyc_num,
                        'time_s': t,
                        'voltage_V': v,
                        'charge_Ah': q_Ah,
                        'temperature_C': T,
                        'step_type': 'C1_discharge'
                    })
                    timeseries_frames.append(ts_df)

                    # Also get 1C charge data (C1ch) if available
                    try:
                        if hasattr(cyc_data, 'C1ch'):
                            ch = cyc_data.C1ch
                        elif hasattr(cyc_data, '__getitem__'):
                            ch = cyc_data['C1ch']
                        else:
                            ch = None

                        if ch is not None:
                            t_ch = np.array(ch.t).flatten() if hasattr(ch, 't') else np.array(ch['t']).flatten()
                            v_ch = np.array(ch.v).flatten() if hasattr(ch, 'v') else np.array(ch['v']).flatten()
                            q_ch = np.array(ch.q).flatten() if hasattr(ch, 'q') else np.array(ch['q']).flatten()
                            T_ch = np.array(ch.T).flatten() if hasattr(ch, 'T') else np.array(ch['T']).flatten()

                            charge_cap_Ah = np.max(np.abs(q_ch / 1000.0)) if len(q_ch) > 0 else np.nan

                            ts_ch_df = pd.DataFrame({
                                'cell_id': cell_id,
                                'cycle_number': cyc_num,
                                'time_s': t_ch,
                                'voltage_V': v_ch,
                                'charge_Ah': q_ch / 1000.0,
                                'temperature_C': T_ch,
                                'step_type': 'C1_charge'
                            })
                            timeseries_frames.append(ts_ch_df)
                        else:
                            charge_cap_Ah = np.nan
                    except Exception:
                        charge_cap_Ah = np.nan

                    # Cycle summary row
                    cycle_rows.append({
                        'cell_id': cell_id,
                        'cycle_number': cyc_num,
                        'discharge_capacity_Ah': discharge_cap_Ah,
                        'charge_capacity_Ah': charge_cap_Ah,
                        'max_temperature_C': np.max(T) if len(T) > 0 else np.nan,
                        'min_voltage_V': np.min(v) if len(v) > 0 else np.nan,
                        'max_voltage_V': np.max(v) if len(v) > 0 else np.nan,
                    })

                # Save timeseries
                if timeseries_frames:
                    ts_all = pd.concat(timeseries_frames, ignore_index=True)
                    ts_path = os.path.join(out_dir, f"{cell_id}_timeseries.csv")
                    save_timeseries_with_index(ts_all, ts_path)
                    print(f"    Saved timeseries: {len(ts_all)} rows, {len(cycle_rows)} cycles")

                all_cycle_summaries.extend(cycle_rows)

                # Metadata
                if cycle_rows:
                    caps = [r['discharge_capacity_Ah'] for r in cycle_rows if not np.isnan(r['discharge_capacity_Ah'])]
                    metadata_rows.append({
                        'cell_id': cell_id,
                        'dataset': 'Oxford_Kokam_LCO',
                        'sub_dataset': 'kokam_lco',
                        'chemistry': 'LCO',
                        'anode': 'Unknown',
                        'cathode': 'LiCoO2',
                        'form_factor': 'pouch',
                        'nominal_capacity_Ah': KOKAM_NOMINAL_Ah,
                        'manufacturer': 'Kokam',
                        'model': 'SLPB533459H4',
                        'temperature_C': 40,
                        'charge_protocol': '1C CC',
                        'discharge_protocol': 'Artemis Urban drive cycle',
                        'characterization_protocol': '1C CC charge/discharge + pseudo-OCV',
                        'num_characterization_cycles': len(cycle_rows),
                        'initial_discharge_capacity_Ah': caps[0] if caps else np.nan,
                        'final_discharge_capacity_Ah': caps[-1] if caps else np.nan,
                        'capacity_retention': caps[-1] / caps[0] if caps and caps[0] > 0 else np.nan,
                    })

            except Exception as e:
                print(f"    [ERROR] Failed to process cell {cell_idx + 1}: {e}")
                import traceback
                traceback.print_exc()

    elif loader == 'h5py':
        # HDF5 navigation - structure might differ
        # Run explore_oxford.py first to confirm exact paths
        import h5py

        print("  [INFO] HDF5 format detected. Navigating structure...")
        print(f"  Top-level keys: {list(data.keys())}")

        # Common HDF5 pattern: references to cell structs
        # You may need to adapt after running explore_oxford.py
        for key in data.keys():
            if key.startswith('#') or key.startswith('_'):
                continue
            print(f"  Exploring /{key}: type={type(data[key])}")
            if isinstance(data[key], h5py.Group):
                print(f"    Sub-keys: {list(data[key].keys())[:10]}")

        print("\n  [TODO] Adapt HDF5 navigation after running explore_oxford.py")
        print("         HDF5 MATLAB v7.3 files use object references")
        print("         You may need to dereference with f[ref] syntax")
        data.close()

    # Save cycle summary for kokam_lco
    if all_cycle_summaries:
        cs_df = pd.DataFrame(all_cycle_summaries)
        cs_path = os.path.join(out_dir, "Oxford_kokam_lco_cycle_summary.csv")
        cs_df.to_csv(cs_path, index=False)
        print(f"\n  Kokam cycle summary saved: {len(cs_df)} rows")

    return metadata_rows, pd.DataFrame(all_cycle_summaries) if all_cycle_summaries else pd.DataFrame()


# ============================================================
# Part B: NCA 18650 Path Dependent
# ============================================================
def process_nca():
    """
    Structure from readme:
      File format: TPGx.y - Cell z.mat (x=group, y=file_number, z=cell)
      Groups 1-4, 3 cells each = 12 cells
      Content: time, current, voltage, capacity columns
      Reference performance tests every 48 cycles
    """
    print("\n" + "=" * 60)
    print("Processing Part B: NCA 18650 Path Dependent (12 cells)")
    print("=" * 60)

    if not os.path.isdir(NCA_DIR):
        print(f"[ERROR] Directory not found: {NCA_DIR}")
        return [], pd.DataFrame()

    mat_files = sorted([f for f in os.listdir(NCA_DIR) if f.endswith('.mat')])
    print(f"  Found {len(mat_files)} .mat files")

    if not mat_files:
        print("  [ERROR] No .mat files found. Download first.")
        return [], pd.DataFrame()

    out_dir = os.path.join(PROC_DIR, "nca_18650")
    ensure_dir(out_dir)

    # Group info from readme
    group_protocols = {
        1: "1 day cycling C/2 + 5 days calendar aging 90% SoC",
        2: "1 day cycling C/4 + 5 days calendar aging 90% SoC",
        3: "2 days cycling C/2 + 10 days calendar aging 90% SoC",
        4: "2 days cycling C/4 + 10 days calendar aging 90% SoC",
    }

    all_cycle_summaries = []
    metadata_rows = []
    cells_processed = set()

    for mat_file in mat_files:
        filepath = os.path.join(NCA_DIR, mat_file)
        print(f"\n  Loading: {mat_file}")

        # Parse group and cell from filename: "TPG1.1 - Cell 1.mat"
        try:
            parts = mat_file.replace('.mat', '').split(' - ')
            tpg_part = parts[0].strip()  # "TPG1.1"
            cell_part = parts[1].strip() if len(parts) > 1 else "Cell_1"

            group_num = int(tpg_part.split('.')[0].replace('TPG', ''))
            file_num = int(tpg_part.split('.')[1])
            cell_num = int(cell_part.replace('Cell ', '').replace('Cell', ''))

            cell_id = f"nca_group{group_num}_cell{cell_num}"
        except Exception as e:
            print(f"    [WARN] Could not parse filename: {mat_file}, error: {e}")
            cell_id = mat_file.replace('.mat', '').replace(' ', '_')
            group_num = 0
            cell_num = 0

        print(f"    Cell ID: {cell_id}, Group: {group_num}, File: {file_num}")

        data, loader = load_mat_file(filepath)
        print(f"    Loaded with: {loader}")

        if loader == 'scipy':
            keys = [k for k in data.keys() if not k.startswith('__')]
            print(f"    Keys: {keys}")

            # The Path Dependent dataset typically has columns for
            # step, time, current, voltage, capacity, etc.
            # Exact key names need to be confirmed with explore script

            # Try to find the main data array
            for key in keys:
                obj = data[key]
                if hasattr(obj, 'shape') and len(obj.shape) == 2 and obj.shape[1] >= 4:
                    print(f"    Data array '{key}': shape={obj.shape}")

                    # Attempt to extract cycling data
                    # Common column order: step, time, current, voltage, capacity(Ah)
                    # This needs confirmation from explore_oxford.py
                    print(f"    [TODO] Confirm column mapping after explore_oxford.py")
                    print(f"    First row sample: {obj[0, :min(6, obj.shape[1])]}")

            # After confirming structure, extract cycles and build summaries
            # For now, just log what we find
            if hasattr(data.get(keys[0], None), 'dtype') and data[keys[0]].dtype.names:
                print(f"    Struct fields: {data[keys[0]].dtype.names}")

        elif loader == 'h5py':
            print(f"    HDF5 keys: {list(data.keys())[:10]}")
            for key in list(data.keys())[:3]:
                item = data[key]
                if isinstance(item, h5py.Dataset):
                    print(f"    {key}: shape={item.shape}, dtype={item.dtype}")
            data.close()

        # Build metadata row (partial - fill in after structure confirmed)
        if cell_id not in cells_processed:
            cells_processed.add(cell_id)
            metadata_rows.append({
                'cell_id': cell_id,
                'dataset': 'Oxford_NCA_PathDependent',
                'sub_dataset': 'nca_18650',
                'chemistry': 'NCA',
                'anode': 'Graphite',
                'cathode': 'NCA (LiNiCoAlO2)',
                'form_factor': '18650',
                'nominal_capacity_Ah': NCA_NOMINAL_Ah,
                'manufacturer': 'Panasonic',
                'model': 'NCR18650BD',
                'temperature_C': 24,
                'charge_protocol': f"Group {group_num}: {group_protocols.get(group_num, 'Unknown')}",
                'discharge_protocol': f"CC cycling + calendar aging",
                'num_cycles': None,  # fill after processing
                'initial_discharge_capacity_Ah': None,
                'final_discharge_capacity_Ah': None,
                'capacity_retention': None,
            })

    # Save cycle summary
    if all_cycle_summaries:
        cs_df = pd.DataFrame(all_cycle_summaries)
        cs_path = os.path.join(out_dir, "Oxford_nca_18650_cycle_summary.csv")
        cs_df.to_csv(cs_path, index=False)
        print(f"\n  NCA cycle summary saved: {len(cs_df)} rows")

    return metadata_rows, pd.DataFrame(all_cycle_summaries) if all_cycle_summaries else pd.DataFrame()


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("ETL: Dataset 04 - Oxford Battery Degradation")
    print("=" * 60)

    ensure_dir(PROC_DIR)

    # Process both sub-datasets
    kokam_meta, kokam_cs = process_kokam()
    nca_meta, nca_cs = process_nca()

    # Combine metadata
    all_meta = kokam_meta + nca_meta
    if all_meta:
        meta_df = pd.DataFrame(all_meta)
        meta_path = os.path.join(PROC_DIR, "Oxford_metadata.csv")
        meta_df.to_csv(meta_path, index=False)
        print(f"\n{'=' * 60}")
        print(f"Metadata saved: {meta_path} ({len(meta_df)} cells)")
    else:
        print("\n[WARN] No metadata generated - check data files")

    # DATA_LOCATION.txt
    loc_path = os.path.join(PROC_DIR, "DATA_LOCATION.txt")
    with open(loc_path, 'w') as f:
        f.write("Dataset 04: Oxford Battery Degradation\n")
        f.write("=" * 50 + "\n\n")
        f.write("Processed data location:\n")
        f.write(f"  Local: {PROC_DIR}\n")
        f.write(f"  Server (DGX-1): /path/to/battery_data/dataset_04/\n\n")
        f.write("Raw data location:\n")
        f.write(f"  Local: {RAW_DIR}\n\n")
        f.write("Note: Full timeseries CSV files are stored locally.\n")
        f.write("Only .csv.txt index files (first 100 rows) are pushed to GitHub.\n")
    print(f"DATA_LOCATION.txt saved: {loc_path}")

    print(f"\n{'=' * 60}")
    print("ETL COMPLETE")
    print(f"{'=' * 60}")
    print(f"\nNext steps:")
    print(f"  1. If structure errors → run explore_oxford.py, paste output to Claude")
    print(f"  2. Run quality_check_oxford.py")
    print(f"  3. Follow git push steps from battleplan")


if __name__ == "__main__":
    main()
