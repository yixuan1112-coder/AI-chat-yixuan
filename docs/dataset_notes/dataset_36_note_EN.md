# Dataset 36: Imperial College 21700 Cycle Aging (Kirkaldy 2024)

## Overview
Cycle aging dataset from Imperial College London. Commercial 21700 cylindrical
cells (LG M50T / LG GBM50T2170) aged under controlled conditions.
This ETL covers Experiment 2,2 (C-based Degradation 2) as a representative subset.

## Cell Information
- **Chemistry**: NMC/Graphite-SiO, 21700 cylindrical
- **Nominal Capacity**: 5.0 Ah
- **Number of Cells**: 6 (A–F)
- **Temperature Conditions**: 10°C (A,B) / 25°C (C,D) / 40°C (E,F)
- **SoC Range**: 0–100%
- **C-rates**: 0.3C charge / 1C discharge

## Data Structure
| File | Description |
|------|-------------|
| Imperial_21700_timeseries.parquet | 2,548,630 rows; time/voltage/current/charge/temp per RPT |
| Imperial_21700_cycle_summary.csv | 78 rows; SoH, LAM, LLI, capacity per RPT |
| Imperial_21700_metadata.csv | 6 cells with temperature and chemistry info |
| Imperial_21700_timeseries_SAMPLE.csv | First 100 rows for GitHub preview |

## Key Columns (Timeseries)
- `cell_id`: e.g. Imperial_Expt2_2_cell_A
- `cycle_id`: RPT number (0–12)
- `time_s`: elapsed time in seconds
- `voltage_V`: cell voltage
- `current_mA`: applied current
- `charge_mAh`: cumulative charge
- `temperature_C`: measured temperature
- `temperature_nominal_C`: nominal test temperature (10/25/40)
- `step_type`: discharge_0.1C

## Reference
Kirkaldy, N., Samieian, M. A., Offer, G. J., Marinescu, M. & Patel, Y. (2024).
Lithium-ion battery degradation: Comprehensive cycle ageing data and analysis
for commercial 21700 cells. *Journal of Power Sources*, 603, 234185.
https://doi.org/10.1016/j.jpowsour.2024.234185
