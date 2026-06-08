# Dataset 03: Stanford-MIT-TRI Dataset Note

## Overview

| Item | Detail |
|------|--------|
| Dataset Name | Stanford-MIT-TRI Battery Cycle Life Dataset |
| Institutions | Stanford University / MIT / Toyota Research Institute |
| Publication | Severson et al. (2019), "Data-driven prediction of battery cycle life before capacity degradation", *Nature Energy* |
| DOI | https://doi.org/10.1038/s41560-019-0356-8 |
| Data Source | https://data.matr.io/1/ |
| License | CC BY 4.0 |

## Battery Specifications

| Item | Detail |
|------|--------|
| Chemistry | LFP/Graphite (Lithium Iron Phosphate) |
| Model | A123 Systems APR18650M1A |
| Form Factor | 18650 cylindrical |
| Nominal Capacity | 1.1 Ah |
| Nominal Voltage | 3.3 V |
| Voltage Range | 2.0–3.6 V |
| Test Temperature | 30°C (temperature-controlled chamber) |

## Experimental Design

This dataset investigates the effect of **fast-charging protocols on battery cycle life**. A total of 124 commercial LFP cells were cycled to failure (80% SOH) under 72 different constant-current charging policies. All cells were discharged at 4C.

### Three Batches

| Batch | Filename | Date | Cells | Notes |
|-------|----------|------|-------|-------|
| Batch 1 | 2017-05-12_batchdata_updated_struct_errorcorrect.mat | 2017-05-12 | 46 | Initial experiment |
| Batch 2 | 2017-06-30_batchdata_updated_struct_errorcorrect.mat | 2017-06-30 | 48 | Expanded experiment |
| Batch 3 | 2018-04-12_batchdata_updated_struct_errorcorrect.mat | 2018-04-12 | 40 | Closed-loop optimization (Attia et al. 2020) |

### Charging Policy Format

Policies follow the `X1C(Y%)-X2C` convention:
- `X1C`: First-stage constant-current rate
- `Y%`: SOC threshold to switch to the second stage
- `X2C`: Second-stage constant-current rate
- All cells discharged at 4C

Example: `3.6C(80%)-3.6C` means charge at 3.6C until 80% SOC, then continue at 3.6C.

## Data Structure

### Summary (per-cycle)

| Field | Description | Unit |
|-------|-------------|------|
| cycle | Cycle number | - |
| QCharge | Charge capacity | Ah |
| QDischarge | Discharge capacity | Ah |
| IR | Internal resistance | Ω |
| Tavg | Average temperature | °C |
| Tmax | Maximum temperature | °C |
| Tmin | Minimum temperature | °C |
| chargetime | Charge time | min |

### Cycles (within-cycle timeseries)

| Field | Description | Unit |
|-------|-------------|------|
| t | Time | s |
| V | Voltage | V |
| I | Current | A |
| T | Temperature | °C |
| Qc | Charge capacity | Ah |
| Qd | Discharge capacity | Ah |
| Qdlin | Linearly interpolated discharge capacity | Ah |
| Tdlin | Linearly interpolated temperature | °C |
| discharge_dQdV | Discharge dQ/dV | Ah/V |

## ETL Processing Notes

### Raw Format
MATLAB v7.3 format (HDF5 under the hood). Requires `h5py` to read; `scipy.io.loadmat` cannot handle this format.

### Processing Pipeline
1. Read three batch `.mat` files sequentially using h5py
2. Extract per-cell metadata (cycle_life, charging_policy, barcode, channel_id)
3. Extract summary-level data → cycle_summary.csv
4. Extract cycle-level timeseries → per-cell parquet files
5. Combine all cell timeseries → unified parquet
6. Cycle 0 is a placeholder (all zeros) and is skipped in ETL

### Cell ID Convention
`{batch_label}_cell{index:02d}`, e.g., `batch1_cell00`, `batch2_cell15`, `batch3_cell39`

## Known Issues

1. **Cycle 0 placeholder**: Cycle 0 in the raw data contains all-zero values; automatically skipped in ETL
2. **Large file sizes**: Three batch files total ~7.7 GB raw; processing requires adequate memory
3. **Batch 3 origin**: Batch 3 data comes from Attia et al. (2020), where charging protocols were dynamically selected via Bayesian optimization

## Citations

Severson, K.A., Attia, P.M., Jin, N., Perkins, N., Jiang, B., Yang, Z., Chen, M.H., Aykol, M., Herring, P.K., Fraggedakis, D., Bazant, M.Z., Harris, S.J., Chueh, W.C., & Braatz, R.D. (2019). Data-driven prediction of battery cycle life before capacity degradation. *Nature Energy*, 4, 383–391.

Attia, P.M., Grover, A., Jin, N., Severson, K.A., Marber, T.M., Liao, M.H., Chen, M.H., Cheung, B., Chu, N., Dasgupta, S., Manthiram, R., Müller, A., Schäfer, F., Shinde, D., Srivatsan, H., Viswanathan, V., Braatz, R.D., & Chueh, W.C. (2020). Closed-loop optimization of fast-charging protocols for batteries with machine learning. *Nature*, 578, 397–402.
