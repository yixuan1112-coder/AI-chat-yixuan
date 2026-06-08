# Dataset 37: Munich Multistage Aging Samsung 21700 (Stroebl 2024)

## Overview
Multi-stage lithium-ion battery aging dataset from Munich University of Applied Sciences.
279 Samsung INR21700-50E cells aged under 71 distinct conditions across two stages.
This ETL covers a representative subset: 3 calendar aging (TP_k) + 3 cycle aging (TP_z) files.

## Cell Information
- **Chemistry**: NMC/Graphite, Samsung INR21700-50E
- **Form Factor**: Cylindrical
- **Dimensions**: 21x70 mm
- **Nominal Capacity**: 4.9 Ah
- **Max Charge Current**: 1C (4.9A)
- **Max Discharge Current**: 2C (9.8A)

## Experimental Design
- **Stage 1**: Non-model-based DoE (full-factorial + Latin hypercube)
- **Stage 2**: Model-based optimal experimental design (pi-OED)
- **Aging Types**: Calendar (TP_k) + Cycle (TP_z)
- **Labs**: Siemens (SIE), Intilion (INT), Munich UAS (HM)

## Data Files
| File | Description |
|------|-------------|
| Munich_multistage_timeseries.parquet | 16,039,771 rows; voltage/current/temp per step |
| Munich_multistage_cycle_summary.csv | 12 rows; aging conditions per cell |
| Munich_multistage_metadata.csv | 12 cells with full experimental metadata |
| Munich_multistage_timeseries_SAMPLE.csv | First 100 rows for GitHub preview |

## Key Columns (Timeseries)
- `cell_id`: e.g. Munich_TP_k01_05
- `aging_type`: calendar / cycle
- `test_type`: ET (entry test) / AT (aging test) / ZYK (cycling)
- `voltage_V`, `current_A`, `surf_temp_C`, `amb_temp_C`

## Reference
Stroebl, F., Petersohn, R., Schricker, B., et al. (2024).
A multi-stage lithium-ion battery aging dataset using various experimental
design methodologies. *Scientific Data*, 11, 1020.
https://doi.org/10.1038/s41597-024-03859-z
