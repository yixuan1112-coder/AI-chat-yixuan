This is the official English version of the Dataset Note for `dataset_07` (HNEI), prepared in strict accordance with the **BatteryTwin Schema v0.2**.

---

# HNEI Battery Dataset - Data Processing Notes (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_07`
* **Original Data Scale**: Contains 15+ raw test files (e.g., HNEI_18650_NMC_LCO_25C_a...t).
* **Battery Specifications**: 18650 cylindrical cells.
* **Material System**: NMC/LCO mixed cathode.
* **Included Files**:
    1.  `dataset_07_{cell_id}_metadata.csv` 
    2.  `dataset_07_{cell_id}_cycle_summary.csv` (14-column standard format)
    3.  `dataset_07_{cell_id}_timeseries.csv` (9-column standard format)

## 2. Field Mapping and Physical Standardization

Standardization mapping was performed strictly following the `BatteryTwin Schema v0.2`:

### Cycle Summary Table
| Schema Field | Original Field Mapping | Processing Notes |
| :--- | :--- | :--- |
| `cell_id` | Filename (prefix) | Formatted as `{dataset_id}_{Original_Filename}` |
| `cycle_id` | `Cycle_Index` | Converted to `int32` |
| `capacity_Ah` | `Discharge_Capacity (Ah)` | Primary degradation metric in Amp-hours |
| `temperature_max_C` | `Cell_Temperature (C)` | Aggregated maximum value from timeseries data |
| `charge_duration_s` | `Test_Time` | Calculated cumulative charging seconds based on current sign |

### Timeseries Table
* **Unit Consistency**: Raw data is already in standard units (V, A, s, Ah, °C); no additional mathematical scaling was required.
* **Type Coercion**: For potential non-numeric characters in raw CSVs, `pd.to_numeric` was applied during ingestion to convert data to floats, resolving string-related calculation errors.

---

## 3. Core Engineering Challenges & Pipeline Logic

### 1. Cross-table Feature Fusion & Extraction
Moving beyond simple summary reading, this process implements a **Timeseries-Driven Filling** logic. By performing `groupby` aggregations on millions of rows of timeseries data, we calculate the real temperature rise (`temperature_max_C`) and precise charge/discharge durations (`duration_s`) for each cycle. This resolves the issue of missing key features in the original HNEI summary tables.

### 2. Redundant Zero-Value Filtering Rule
To handle the massive amount of continuous zero-capacity records generated after battery failure (EOL), a `KEEP_ZERO_N = 3` rule was introduced:
* **Isolated Zeroes**: Single zero-capacity cycles are preserved to identify state-transition signals.
* **Continuous Zeroes**: For consecutive zero-capacity cycles, only the first 3 are kept to anchor the failure boundary. Subsequent redundant rows are pruned to improve the training efficiency of downstream LightGBM models.

### 3. Strict Schema Column Alignment
To ensure compatibility during the merging of all datasets (HNEI, UL, SNL), the scripts enforce the output of all fields defined in the Schema (14 columns for Cycle Summary, 9 for Timeseries). Fields not available in the original HNEI data, such as `SOH`, `RUL`, and `internal_resistance_Ohm`, are padded with `NaN`.

### 4. Abnormal Raw Data Processing
Among the raw data files, the file HNEI_18650_NMC_LCO_25C_0-100_0.5-1.5C_m_timeseries.csv under timeseries.csv is only 1 KB in size (while valid data exists in cycle_data). This file contains only the standard columns of the raw dataset with no actual data rows. Nevertheless, it shall be processed following the normal procedure to generate the corresponding time-series table, ensuring the integrity of the processed time-series table and cycle table associated with the time-series file.



