# UL-PUR Battery Dataset - Data Preparation Note (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_08`
* **Original Data Scale**: Encompasses battery degradation data across various test temperatures (e.g., 23°C, 25°C) and multi-level C-rate operating conditions.
* **Cell Specifications**: Contains a mixture of 18650 cylindrical cells (approx. 3.4Ah capacity) and Pouch cells, both with a nominal voltage of 3.6V.
* **Material Chemistry**: NCA (Cathode: LiNiCoAlO2, Anode: Graphite).
* **Included Files**:
  1. `dataset_08_metadata.csv` (Metadata table, strictly aligned with the 18-column XJTU standard)
  2. `*_cycle_summary.csv` (Cycle-level summary tables)
  3. `*_timeseries.csv` (High-frequency timeseries tables)

## 2. Field Mapping and Physical Quantity Standardization

The raw data has been standardized according to the `BatteryTwin Schema v0.2` specification:

* **Form Factor Differentiation**: Addressing the dataset's mixed packaging nature, the metadata extraction script scans the filenames to successfully differentiate and map the `model_or_size` (18650 / Pouch) and `form_factor` (cylindrical / pouch) fields.
* **Floating-Point Precision Truncation (Long-Tail Decimal Elimination)**: Raw binary data tends to generate invalid floating-point inaccuracies during Pandas exports (e.g., `3.6699998...`). To restore the original precision of the testing equipment and optimize file size, an intelligent string formatting directive (`float_format='%g'`) was strictly enforced during the `to_csv` export phase, maintaining a pristine data appearance.
* **Temperature Feature Aggregation**: The raw cycle summary tables lack temperature records. This was resolved by parsing the high-frequency timeseries files and utilizing `groupby` operations per cycle to compute and extract `temperature_max_C` and `temperature_avg_C`.

## 3. Core Engineering Challenges & Data Cleaning Logic

*Note: The UL-PUR dataset presents specific idiosyncrasies regarding column nomenclature and end-of-life data quality. The following engineering bottlenecks were resolved using customized Python scripts:*

1. **Critical Interference from "Date_Time" String Columns**
   During the computation of timeseries time deltas, a fatal `unsupported operand type(s) for -: 'str' and 'str'` error was encountered. Investigation revealed that the first column in the raw CSVs was a string-based `Date_Time` column, which was erroneously identified as a temporal feature by the standard `find_col` function. The regex within the `find_col` function was refactored to include a **"defensive skip logic"** (executing a `continue` statement upon detecting the substring `date`). This allowed precise targeting of the purely numerical cumulative `Test_Time` column, completely resolving the NaN and calculation errors.
2. **Cleansing of End-of-Life Zero-Capacity Long Tails**
   After cells completely fail or test equipment powers down, the instruments often continue to record a massive number of invalid cycles with null or near-zero capacities, leading to severe distortion of the State of Health (SOH) degradation curves. Consequently, a consecutive zero-value detection and filtering algorithm (`KEEP_ZERO_N = 3`) was integrated into the cleaning pipeline. This algorithm intelligently truncates the "dead cycles" at the tail end, preserving only the first 3 zero-capacity data points as End-of-Life (EoL) boundary signals, significantly enhancing the signal-to-noise ratio for downstream feature engineering.
3. **Fuzzy Matching of Idiosyncratic Column Names**
   Slight variations in column naming conventions exist across different test channels (e.g., `Cell_Temperature`, `Temp`, `Environ`). The script establishes a prioritized keyword matching array, enabling highly robust extraction of all valid numerical columns (voltage, current, capacity, temperature, and cycle index).