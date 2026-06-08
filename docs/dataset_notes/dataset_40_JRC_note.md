# JRC Battery Dataset - Data Processing Notes (README)

## 1. Dataset Overview
* **Dataset ID**: `dataset_40`
* **Original Data Scope**: A single wide-format CSV file containing high-power dynamic tests for 6 different conditions (3300W down to 330W).
* **Cell Specifications**: High-energy NMC pouch cells, 25Ah nominal capacity.
* **Chemistry**: NMC (Lithium Nickel Manganese Cobalt Oxide).
* **Output Files**:
  1. `dataset_40_metadata.csv` (Metadata table)
  2. `JRC_{Condition}_cycle_summary.csv` (Cycle-level summary table)
  3. `JRC_{Condition}_timeseries.csv` (High-frequency timeseries table)

## 2. Field Mapping & Standardization
In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw data was standardized as follows:
* **Format Normalization**: The raw European CSV used semicolons (`;`) as delimiters and commas (`,`) as decimals. These were converted to standard CSV formats with numeric dot (`.`) decimals to ensure compatibility with Python data stacks.
* **Wide-to-Long Transformation**: The original "wide" table (where multiple cells were stored as adjacent columns) was decoupled into independent "long" format files for each power condition (e.g., `JRC_3300W`).
* **Current Sign Alignment (Discharge as Negative)**: Discharge currents were normalized to negative values to align with the standard BatteryTwin convention.
* **Derived Capacity (Ah Integration)**: Since the raw dataset lacked a pre-calculated capacity field, the discharge capacity was calculated using **Ampere-hour (Ah) Integration**: $\text{Capacity (Ah)} = \int \frac{|I|}{3600} \, dt$.

## 3. Core Engineering Challenges & Pipeline Logic
*Note: The processing of the JRC dataset focused on column decoupling and physical feature derivation from raw electrical signals.*

1. **Decoupling of Multi-Cell Wide Structures**
   The single raw CSV contained interleaved data for 6 different test scenarios. The pipeline utilized a column-mapping strategy to isolate specific signal pairs (e.g., `V_D_3300` and `C_D_3300`) and reconstructed them into individual cell records, preventing data leakage between test conditions.
2. **Implicit Capacity Reconstruction**
   Unlike aging datasets, these dynamic power profiles did not have explicit cycle-level discharge capacities. The script implemented a real-time integration module that calculates cumulative discharge capacity from the high-frequency current signal, enabling the generation of standard `capacity_Ah` fields.
3. **Time-Axis Standardization**
   Raw timestamps were reset to a continuous second-based axis (`time_s`) starting from 0 for each isolated condition. This ensures that the dynamic power profiles can be easily compared or used as inputs for machine learning models.

## 4. Missing Fields Explanation
Due to the limitations of the raw data, certain Schema fields were left blank:
* `internal_resistance_Ohm`: Internal resistance was not explicitly measured during these dynamic pulse tests.
* `SOH` & `RUL`: As these are characterization tests (Cycle 1) rather than long-term aging tests, health degradation metrics are not applicable.