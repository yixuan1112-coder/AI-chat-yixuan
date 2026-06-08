# Dataset Note: dataset_02 — CALCE CS2 Battery Aging

## 1. Data Source

| Item | Detail |
|------|--------|
| **Dataset name** | CALCE CS2 Battery Aging Dataset |
| **Provider** | Center for Advanced Life Cycle Engineering (CALCE), University of Maryland |
| **Download URL** | https://calce.umd.edu/battery-data (scroll to CS2 section) |
| **Format** | 13 cells: Arbin Excel (.xlsx); 2 cells (CS2_8, CS2_21): CADEX text (.txt) |
| **Cells** | 15 prismatic LCO cells (CS2_3, 5, 6, 7, 8, 9, 21, 24, 25, 33, 34, 35, 36, 37, 38) |
| **Chemistry** | LiCoO₂ / Graphite (LCO) |
| **Nominal capacity** | 1100 mAh (1.1 Ah) |
| **Form factor** | Prismatic, 5.4 × 33.6 × 50.6 mm |
| **Test period** | 2010–2014 |
| **Citation** | He et al., "Prognostics of lithium-ion batteries based on Dempster–Shafer theory and the Bayesian Monte Carlo method," J. Power Sources, 196(23), pp.10314–10321, 2011. |

## 2. Experimental Conditions

All cells share the same **charge protocol**: CC-CV at 0.5C (0.55A) to 4.2V, with current cutoff at 0.05A.

| Type | Cells | Discharge Condition | Notes |
|------|-------|---------------------|-------|
| 1 | CS2_8, CS2_21, CS2_33, CS2_34 | CC 0.5C (0.55A) to 2.7V | Standard cycling |
| 2 | CS2_35, CS2_36, CS2_37, CS2_38 | CC 1C (1.1A) to 2.7V | Higher C-rate |
| 3 | CS2_3, CS2_9 | CC variable (0.11–2.2A) to 2.7V | Alternating discharge rates |
| 4 | CS2_7 | CC 0.5C with random cutoff voltage | Simulating user behavior |
| 5 | CS2_5, CS2_6 | CC 0.5C, 3.77V–2.7V partial | Low-voltage regime cycling |
| 6 | CS2_24, CS2_25 | CC 0.5C, 4.2V–3.77V partial | High-voltage regime cycling |

**Temperature**: Room temperature (~25°C), not actively controlled or logged.

## 3. Raw Data Structure

### Arbin Excel format (13 cells)

Each cell has a folder of Excel files named by test date (e.g., `CS2_33_8_18_10.xlsx`).

Each Excel file contains:
- **Info sheet**: Test metadata (channel, schedule file, start date)
- **Channel_1-XXX sheet**: Timeseries data

Arbin columns:

| Column | Type | Description |
|--------|------|-------------|
| `Data_Point` | int | Row counter |
| `Test_Time(s)` | float | Cumulative test time in seconds |
| `Date_Time` | datetime | Absolute timestamp |
| `Step_Time(s)` | float | Time within current step |
| `Step_Index` | int | Step number in test schedule |
| `Cycle_Index` | int | Cycle counter (resets per file) |
| `Current(A)` | float | Positive=charge, Negative=discharge |
| `Voltage(V)` | float | Terminal voltage |
| `Charge_Capacity(Ah)` | float | Cumulative charge capacity |
| `Discharge_Capacity(Ah)` | float | Cumulative discharge capacity |
| `Charge_Energy(Wh)` | float | Cumulative charge energy |
| `Discharge_Energy(Wh)` | float | Cumulative discharge energy |
| `dV/dt(V/s)` | float | Voltage rate of change |
| `Internal_Resistance(Ohm)` | float | Mostly 0 |
| `Is_FC_Data` | int | Fast-charge flag (always 0) |
| `AC_Impedance(Ohm)` | float | AC impedance (always 0) |
| `ACI_Phase_Angle(Deg)` | float | AC impedance phase (always 0) |

### CADEX text format (CS2_8, CS2_21)

Tab-separated text files with different column structure. Parsed separately in the ETL script.

## 4. Field Mapping to BatteryTwin Schema v0.2

### Timeseries (7 columns)

| Schema field | Source | Transformation |
|-------------|--------|----------------|
| `cell_id` | Folder name | e.g., "CS2_33" |
| `cycle_id` | `Cycle_Index` | Globally renumbered across files |
| `time_s` | `Test_Time(s)` | Direct mapping |
| `voltage_V` | `Voltage(V)` | Direct mapping |
| `current_A` | `Current(A)` | Direct mapping |
| `temperature_C` | — | **NaN** (no sensor in dataset) |
| `step_type` | Derived from `Current(A)` | >0.01A → "charge", <-0.01A → "discharge", else → "rest" |

### Cycle Summary (14 columns)

| Schema field | Source | Transformation |
|-------------|--------|----------------|
| `cell_id` | Folder name | Direct |
| `cycle_id` | Global cycle counter | Renumbered |
| `step_type` | "charge" or "discharge" | Two rows per cycle |
| `capacity_Ah` | `Charge/Discharge_Capacity(Ah)` | max − min within step |
| `SOH` | Derived | (discharge_capacity / 1.1Ah) × 100 |
| `RUL` | — | **Empty** (to be computed later) |
| `charge_capacity_Ah` | From charge step | max − min |
| `discharge_capacity_Ah` | From discharge step | max − min |
| `temperature_max_C` | — | **NaN** |
| `temperature_avg_C` | — | **NaN** |
| `charge_duration_s` | time range of charge step | max(time_s) − min(time_s) |
| `discharge_duration_s` | time range of discharge step | max(time_s) − min(time_s) |
| `internal_resistance_Ohm` | — | **NaN** (data column is all 0) |
| `cycle_end_flag` | — | **Empty** |

### Metadata (18 columns)

All fields populated from known CALCE documentation. Key values:
- `chemistry`: LCO
- `nominal_capacity_Ah`: 1.1
- `charge_protocol`: CC-CV 0.5C to 4.2V (50mA cutoff)
- `temperature_C`: 25.0 (room temperature, approximate)

## 5. ETL Processing Decisions

1. **File concatenation**: Each cell's data is spread across multiple Excel files (one per test session). Files are sorted chronologically by date encoded in filename. `Cycle_Index` is globally renumbered by accumulating the max cycle index from each file.

2. **step_type determination**: Instead of relying on `Step_Index` (which varies by test schedule), we use the sign of `Current(A)` to determine charge/discharge/rest. Threshold: ±0.01A.

3. **CADEX cells (CS2_8, CS2_21)**: Parsed with a separate reader. Column names differ from Arbin format and are mapped dynamically.

4. **Calibration files excluded**: Files containing "calibration" in the name are skipped (e.g., `CS_2_5_15_12_calibration.xls`).

5. **Temperature**: This dataset has **no temperature sensor data**. All temperature fields are NaN. The `temperature_C` in metadata is set to 25°C as approximate room temperature.

## 6. Known Issues & Limitations

1. **No temperature data**: Unlike NASA PCoE, CALCE CS2 has no per-sample temperature measurements.

2. **Cycle numbering across files**: Each Excel file's `Cycle_Index` typically starts from 1. Our global renumbering assumes files are chronologically ordered by filename date. If files were interrupted or re-started, cycle numbering may have gaps.

3. **Partial cycling cells (Type 5, 6)**: CS2_5, CS2_6, CS2_24, CS2_25 cycle in restricted voltage windows. Their capacity values reflect partial capacity, not full cell capacity, so SOH calculations are less meaningful for these cells.

4. **CADEX format uncertainty**: CS2_8 and CS2_21 use a different tester and file format. The txt parser makes best-effort column mapping but may need manual verification.

5. **Some files may contain anomalies**: Files like `CS2_5_7_29_13_logicerror.xlsx` and `CS2_5_8_5_13_brokenchannel.xlsx` self-document issues in their filenames. These are still processed but may contain bad data.

6. **RUL not computed**: Remaining Useful Life requires an EOL definition (e.g., 30% capacity fade). To be computed in post-processing.

## 7. Reproduction

```bash
conda activate batterytwin
cd ~/Desktop/BatteryTwin-Benchmark-DataPrep

# Run ETL
python scripts/etl_calce.py \
    --input data/raw/dataset_02_CALCE \
    --output data/processed/dataset_02

# Run QC
python scripts/quality_check_calce.py \
    --input data/processed/dataset_02 \
    --output docs/qc_reports/dataset_02
```

## 8. File Inventory

| File | Location | Status |
|------|----------|--------|
| `CALCE_CS2_metadata.csv` | `data/processed/dataset_02/` | ✅ |
| `CALCE_CS2_cycle_summary.csv` | `data/processed/dataset_02/` | ✅ |
| `CALCE_CS2_timeseries.parquet` | `data/processed/dataset_02/` | ⚠️ May exceed GitHub 100MB |
| `CALCE_CS2_timeseries.csv` | `data/processed/dataset_02/` | ⚠️ May exceed GitHub 100MB |
| `etl_calce.py` | `scripts/` | ✅ |
| `quality_check_calce.py` | `scripts/` | ✅ |
| `dataset_02_CALCE_note.md` | `docs/dataset_notes/` | ✅ |
