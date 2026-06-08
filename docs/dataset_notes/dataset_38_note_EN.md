# Dataset 38: ISU-ILCC Battery Aging Dataset (Thelen 2023)

## Overview
Battery aging dataset from Iowa State University (ISU) and Iowa Lakes Community College (ILCC).
251 NMC/Graphite Li-polymer cells cycled under 63 unique conditions across two releases.
Designed to study capacity fade dependency on three stress factors: charge rate, discharge rate, and depth of discharge (DoD).

## Cell Information
- **Chemistry**: NMC/Graphite
- **Form Factor**: Pouch
- **Dimensions**: 50x20x3 mm (502030 format)
- **Nominal Capacity**: 250 mAh (0.25 Ah)
- **Voltage Range**: 3.0–4.2 V
- **Manufacturer**: Honghaosheng Electronics, Shenzhen, China
- **Test Temperature**: 30°C

## Experimental Design
- **Release 1.0**: 238 cells, 63 conditions
- **Release 2.0**: 13 additional cells
- **Stress Factors**: Charge rate / Discharge rate / Depth of discharge
- **Tester**: Neware BTS4000 (64-channel)

## Data Files
| File | Description |
|------|-------------|
| ISU_ILCC_timeseries.parquet | 5,505,000 rows; interpolated discharge curves per cycle |
| ISU_ILCC_cycle_summary.csv | 5,455 rows; capacity fade over time per cell |
| ISU_ILCC_metadata.csv | 251 cells with chemistry, form factor, dimensions |
| ISU_ILCC_timeseries_SAMPLE.csv | First 100 rows for GitHub preview |

## Key Columns
- `cell_id`: e.g. ISU_ILCC_G1C1
- `cycle_id`: cycle index
- `soc`: state of charge (0–1, interpolated)
- `capacity_Ah`: discharge capacity at this SOC point
- `time_days`: elapsed time in days (cycle summary)

## Reference
Thelen, A., Li, T., Liu, J., Tischer, C. & Hu, C. (2023).
ISU-ILCC Battery Aging Dataset. Iowa State University DataShare.
https://doi.org/10.25380/iastate.22582234.v2
