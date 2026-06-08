# Dataset 01 — NASA PCoE Battery Aging Dataset

## 1. Basic Information

| Attribute | Value |
|-----------|-------|
| **Dataset Name** | NASA PCoE Li-ion Battery Aging Dataset |
| **Dataset ID** | NASA_PCoE |
| **Institution** | NASA Ames Research Center, Prognostics Center of Excellence (PCoE) |
| **Year Released** | 2007 |
| **Authors** | B. Saha, K. Goebel |
| **License** | Public Domain (NASA Open Data) |
| **Download URL** | https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip |
| **Official Page** | https://data.nasa.gov/dataset/li-ion-battery-aging-datasets |
| **PCoE Repository** | https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/ |
| **Citation** | B. Saha and K. Goebel (2007). "Battery Data Set", NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA |

## 2. Battery Specifications

| Attribute | Value |
|-----------|-------|
| **Chemistry** | LCO (LiCoO₂/Graphite) |
| **Cathode Material** | LiCoO₂ |
| **Anode Material** | Graphite |
| **Manufacturer** | Commercial (unspecified) |
| **Model / Size** | 18650 |
| **Form Factor** | Cylindrical |
| **Nominal Capacity** | 2.0 Ah |
| **Nominal Voltage** | 3.7 V |
| **Number of Cells** | ~34 cells (B0005–B0056, some IDs missing) |

## 3. Experimental Protocol

### 3.1 Charge Protocol
- CC-CV: Constant current at 1.5 A to 4.2 V, then constant voltage until current drops to 20 mA cutoff

### 3.2 Discharge Protocol
- CC: Constant current at 2 A to various cutoff voltages:
  - Standard group: 2.7 V (OEM recommended)
  - Deep discharge group: 2.5 V
  - Extra-deep discharge group: 2.2 V / 2.0 V (below OEM spec, intended to induce deep discharge aging effects)

### 3.3 EIS (Electrochemical Impedance Spectroscopy)
- Performed periodically during cycling
- Frequency range: 0.1 Hz – 5 kHz
- Measured parameters: Sense_current, Battery_impedance, Rectified_impedance, Re (electrolyte resistance), Rct (charge transfer resistance)

### 3.4 Temperature Conditions
- **4°C**: Low temperature group (B0033, B0034, B0036, B0049–B0052)
- **24°C**: Room temperature group (B0005–B0007, B0018, B0025–B0028, B0038–B0044, B0053–B0056)
- **43°C**: High temperature group (B0029–B0032, B0045–B0048)

### 3.5 End-of-Life (EOL) Criterion
- 30% capacity fade: from 2.0 Ah to 1.4 Ah

## 4. Raw Data Structure

### 4.1 File Format
- **Format**: MATLAB `.mat` files (v5)
- **Organization**: One file per cell (e.g., `B0005.mat`)
- **Size**: ~56 MB compressed

### 4.2 Internal .mat Structure
```
B0005.mat
└── B0005 (struct)
    └── cycle (1×N struct array)
        ├── type: 'charge' | 'discharge' | 'impedance'
        ├── ambient_temperature: float (°C)
        ├── time: datetime string
        └── data (struct)
            ├── Voltage_measured (V)      — Terminal voltage
            ├── Current_measured (A)       — Current
            ├── Temperature_measured (°C)  — Surface temperature
            ├── Current_charge (A)         — Charge current (charge only)
            ├── Voltage_charge (V)         — Charge voltage (charge only)
            ├── Time (s)                   — Elapsed time from step start
            └── Capacity (Ah)             — Discharge capacity (discharge only)
```

### 4.3 Sampling Rate
- Approximately 10 Hz (varies slightly across test phases)

## 5. Field Mapping (Raw → BatteryTwin Schema v0.2)

### 5.1 Timeseries Mapping

| Raw Field | → Unified Field | Type | Unit | Required | Notes |
|-----------|----------------|------|------|----------|-------|
| (filename) | cell_id | str | - | ✓ | Filename is cell_id (B0005, B0006, ...) |
| (cycle index) | cycle_id | int | - | ✓ | 1-indexed cycle number |
| type | step_type | str | - | ✓ | charge/discharge (impedance skipped) |
| Time | time_s | float | s | ✓ | Elapsed time from step start, no conversion |
| Voltage_measured | voltage_V | float | V | ✓ | Terminal voltage, no conversion |
| Current_measured | current_A | float | A | ✓ | Current (positive = charge), no conversion |
| Temperature_measured | temperature_C | float | °C | ✓ | Surface temperature, no conversion |
| (integrated) | charge_capacity_Ah | float | Ah | ○ | Estimated via ∫|I|dt for charge cycles |
| Capacity | discharge_capacity_Ah | float | Ah | ○ | Discharge cycles only |

### 5.2 Cycle Summary Mapping

| Raw Source | → Unified Field | Notes |
|-----------|----------------|-------|
| max(Capacity) per discharge cycle | discharge_capacity_Ah | Max discharge capacity per cycle |
| ∫\|I\|dt per charge cycle | charge_capacity_Ah | Estimated from current integration |
| max(Temperature_measured) | temperature_max_C | Max temperature per cycle |
| mean(Temperature_measured) | temperature_avg_C | Mean temperature per cycle |
| min(Temperature_measured) | temperature_min_C | Min temperature per cycle |
| time[-1] - time[0] | charge_duration_s / discharge_duration_s | Step duration |
| (N/A) | discharge_energy_Wh | Not provided in raw data, left NaN |
| (N/A) | internal_resistance_Ohm | Requires separate EIS extraction |

## 6. Data Processing Notes

### 6.1 Processing Steps
1. Load .mat files using `scipy.io.loadmat`
2. Iterate over cycle struct array, skip cycles where type = 'impedance'
3. Extract charge/discharge time-series data, map to unified field names
4. For discharge cycles: take max(Capacity) as cycle-level discharge capacity
5. For charge cycles: estimate charge capacity via ∫|I|dt integration
6. Write to timeseries (Parquet + CSV) and cycle_summary (CSV)

### 6.2 Unit Conversions
- **None**: All raw field units match the target schema (V, A, °C, s, Ah)

### 6.3 Missing / Null Value Documentation

| Field | Missing Situation | Handling |
|-------|------------------|----------|
| charge_capacity_Ah | Not natively available | Estimated via current integration; accuracy depends on sampling rate |
| discharge_capacity_Ah | Only available for discharge cycles | NaN for charge cycles |
| discharge_energy_Wh | Not provided in raw data | NaN throughout |
| charge_energy_Wh | Not provided in raw data | NaN throughout |
| internal_resistance_Ohm | Requires separate EIS extraction | NaN currently; can be added later |
| coulombic_efficiency | Requires paired charge+discharge | NaN currently |

### 6.4 Data Quality Flags (cycle_end_flag)
- `normal`: Normal cycle
- `capacity_jump`: Capacity change exceeds 5× median change or > 0.05 Ah compared to previous cycle
- `missing_data`: Time-series data missing or truncated

### 6.5 Known Issues
1. **EIS data not included**: Impedance cycles have a different structure; current ETL skips them. Can be processed separately in the future.
2. **Missing cell IDs**: B0035 does not exist in the dataset.
3. **charge_capacity_Ah is estimated**: Accuracy is lower than native discharge Capacity field.
4. **Some cells have incomplete data**: Some cells may have had testing interrupted before reaching EOL.

## 7. Output File List

| Filename | Format | Description | Approximate Size |
|----------|--------|-------------|-----------------|
| `NASA_PCoE_metadata.csv` | CSV | Metadata, one row per cell | ~34 rows |
| `NASA_PCoE_timeseries.parquet` | Parquet | Time-series, sampled per second | ~millions of rows |
| `NASA_PCoE_timeseries.csv` | CSV | Time-series CSV copy | Same as above |
| `NASA_PCoE_cycle_summary.csv` | CSV | Cycle-level summary | ~thousands of rows |

## 8. References

- [1] B. Saha, K. Goebel. "Battery Data Set", NASA Prognostics Data Repository, 2007.
- [2] B. Saha, K. Goebel. "Modeling Li-ion Battery Capacity Depletion in a Particle Filtering Framework", Annual Conf. of the PHM Society, 2009.
- [3] NASA PCoE Data Repository: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/

## 9. Processing Information

- **Processed by**: Liu Kefan
- **Date**: 2026-03-12
- **ETL Script**: `scripts/etl_nasa.py`
- **QC Script**: `scripts/quality_check_nasa.py`
