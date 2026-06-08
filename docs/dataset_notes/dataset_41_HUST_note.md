# HUST Battery Dataset - Data Processing Notes (README)

## 1. Dataset Overview
* **Dataset ID**: `dataset_41`
* **Original Data Scope**: Multiple Python Pickle (`.pkl`) files, organized by cell naming (e.g., `1-1`, `2-5`).
* **Cell Specifications**: A123 Systems APR18650M1A cylindrical cells, 1.1Ah nominal capacity, 3.3V nominal voltage.
* **Chemistry**: LFP (Lithium Iron Phosphate).
* **Output Files**:
  1. `dataset_41_HUST_metadata.csv` (Metadata table)
  2. `HUST_{Cell_ID}_cycle_summary.csv` (Cycle-level summary table)
  3. `HUST_{Cell_ID}_timeseries.csv` (High-frequency timeseries table)

## 2. Field Mapping & Standardization
In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw data was standardized as follows:
* **Unit Alignment**: 
    - Raw current recorded in milliamperes (`mA`) was divided by 1000 to convert to standard Amperes (`current_A`).
    - Raw capacity in `mAh` was converted to Ampere-hours (`capacity_Ah`).
* **Current Sign Alignment (Discharge as Negative)**: Standardized to ensure all discharge currents are negative values, consistent with the project's sign convention.
* **SOH Calculation**: Health status was derived using the formula: $\text{SOH} = \frac{\text{Discharge Capacity}}{\text{Nominal Capacity (1.1Ah)}}$.
* **Structure Flattening**: The raw data was deeply nested in Python dictionaries. The script flattened these structures into relational tables while maintaining strict `cycle_id` indexing.

## 3. Core Engineering Challenges & Pipeline Logic
*Note: The HUST dataset processing focused on handling serialized Python objects and reconstructing cycle-level features from embedded DataFrames.*

1. **Pickle Object Traversal & Deserialization**
   Unlike MAT or CSV formats, HUST data is stored as serialized Python Pickle objects. The ETL pipeline implemented a robust traversal of the `rul`, `dq`, and `data` keys to extract consistent physical features across the entire battery life cycle (up to 1,000+ cycles).
2. **Segmented Feature Extraction from Nested DataFrames**
   While cumulative metrics like discharge capacity were available at the dictionary root, specific cycle features (e.g., charge/discharge durations) were buried within thousands of individual Pandas DataFrames. The script iterates through these sub-objects to calculate precise temporal metrics for each cycle.
3. **Cross-Table Life-Cycle Synchronization**
   The pipeline ensures that the `cycle_id` in the Summary table remains perfectly synchronized with the indices in the high-frequency Timeseries CSVs. This alignment is critical for downstream machine learning tasks such as RUL (Remaining Useful Life) prediction.

## 4. Missing Fields Explanation
Due to the limitations of the raw data, certain Schema fields were left blank:
* `temperature_C` (Timeseries): High-frequency temperature sampling was not included in the provided `.pkl` DataFrames.
* `internal_resistance_Ohm` (Cycle Summary): No explicit internal resistance measurements were recorded for each cycle in this version of the dataset.