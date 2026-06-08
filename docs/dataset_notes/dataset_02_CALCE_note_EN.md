# Dataset Note: dataset_02 — CALCE CS2 Battery Aging (English)

## 1. Data Source

| Item | Detail |
|------|--------|
| **Dataset name** | CALCE CS2 Battery Aging Dataset |
| **Provider** | Center for Advanced Life Cycle Engineering (CALCE), University of Maryland |
| **Download URL** | https://calce.umd.edu/battery-data (CS2 section) |
| **Format** | 13 cells: Arbin Excel (.xlsx); 2 cells (CS2_8, CS2_21): CADEX text (.txt) |
| **Total cells** | 15 prismatic LCO cells |
| **Chemistry** | LiCoO₂ / Graphite (LCO) |
| **Nominal capacity** | 1100 mAh (1.1 Ah) |
| **Form factor** | Prismatic, 5.4 × 33.6 × 50.6 mm |
| **Test period** | 2010–2014 |

## 2. Experimental Conditions

All cells share the same charge protocol: CC-CV at 0.5C (0.55A) to 4.2V, current cutoff at 0.05A.

| Type | Cells | Discharge Condition |
|------|-------|---------------------|
| 1 | CS2_8, CS2_21, CS2_33, CS2_34 | CC 0.5C (0.55A) to 2.7V |
| 2 | CS2_35, CS2_36, CS2_37, CS2_38 | CC 1C (1.1A) to 2.7V |
| 3 | CS2_3, CS2_9 | CC variable (0.11–2.2A) to 2.7V |
| 4 | CS2_7 | CC 0.5C with random cutoff voltage |
| 5 | CS2_5, CS2_6 | CC 0.5C partial cycling (3.77V–2.7V) |
| 6 | CS2_24, CS2_25 | CC 0.5C partial cycling (4.2V–3.77V) |

Temperature: Room temperature (~25°C), not actively controlled or logged.

## 3. Field Mapping to BatteryTwin Schema v0.2

### Timeseries (7 columns)

| Schema field | Source | Transformation |
|-------------|--------|----------------|
| `cell_id` | Folder name | e.g., "CS2_33" |
| `cycle_id` | `Cycle_Index` | Globally renumbered across files |
| `time_s` | `Test_Time(s)` | Direct mapping |
| `voltage_V` | `Voltage(V)` | Direct mapping |
| `current_A` | `Current(A)` | Direct mapping |
| `temperature_C` | — | NaN (no temperature sensor) |
| `step_type` | Derived from `Current(A)` | >0.01A → charge, <-0.01A → discharge, else → rest |

### Cycle Summary (14 columns)

| Schema field | Source | Notes |
|-------------|--------|-------|
| `capacity_Ah` | `Charge/Discharge_Capacity(Ah)` | max − min within step |
| `SOH` | Derived | (discharge_capacity / 1.1Ah) × 100 |
| `RUL` | — | Empty, to be computed later |
| `temperature_max_C` / `temperature_avg_C` | — | NaN (no sensor) |
| `internal_resistance_Ohm` | — | NaN |

### Metadata (18 columns)

All fields populated from CALCE documentation. Key values: chemistry=LCO, nominal_capacity=1.1Ah, charge_protocol=CC-CV 0.5C to 4.2V.

## 4. Processing Decisions

1. **File concatenation**: Each cell has multiple Excel files (one per test session), sorted chronologically by date in filename. Cycle_Index globally renumbered.
2. **step_type**: Determined by current sign (±0.01A threshold), not Step_Index.
3. **CADEX cells skipped**: CS2_8 and CS2_21 use CADEX tester with different txt format. Parser needs update — these 2 cells are not included in current output.
4. **Calibration files excluded**: Files with "calibration" in filename are skipped.

## 5. Known Issues

1. **No temperature data**: All temperature fields are NaN.
2. **CADEX cells missing**: CS2_8 and CS2_21 (2/15) not parsed yet.
3. **Partial cycling SOH**: Type 5/6 cells (CS2_5, CS2_6, CS2_24, CS2_25) have artificially low/high SOH because they cycle in restricted voltage windows.
4. **Anomalous voltage range**: -2.5V to 5.3V observed (expected 2.7–4.2V). Likely from variable-rate discharge cells (Type 3) or transient sensor artifacts.
5. **RUL not computed**: Requires EOL definition, to be added later.

## 6. ETL Output Summary

| Metric | Value |
|--------|-------|
| Cells processed | 13 / 15 |
| Total timeseries rows | 8,519,545 |
| Total cycle_summary rows | 65,296 |
| Voltage range | -2.544 ~ 5.310 V |
| Current range | -5.934 ~ 5.332 A |

## 7. Reproduction

```bash
conda activate batterytwin
cd ~/Projects/BatteryTwin-Benchmark-DataPrep
python scripts/etl_calce.py --input data/raw/dataset_02_CALCE --output data/processed/dataset_02
python scripts/quality_check_calce.py --input data/processed/dataset_02 --output docs/qc_reports/dataset_02
```

## 8. Citation

He, W., Williard, N., Osterman, M., & Pecht, M. (2011). Prognostics of lithium-ion batteries based on Dempster–Shafer theory and the Bayesian Monte Carlo method. *Journal of Power Sources*, 196(23), 10314–10321.
