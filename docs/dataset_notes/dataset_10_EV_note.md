
---

# EV Charging Dataset (Dataset 10) - Data Processing Notes (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_10_EV`
* **Original Data Scope**: All data is centralized in a highly flattened global file named `ev_battery_charging_data.csv`, which contains charging cycle data for multiple electric vehicles.
* **Vehicle & Cell Specifications**: Covers various EV models (e.g., Model A, Model B). Specific cell specifications (Form factor / Model size) are not indicated in the raw data and are marked as `unknown`.
* **Chemistry**: Mixed chemistry. Based on the raw field `Battery Type`, it includes `LiFePO4` (mapped to the standard Schema as `LFP`) and generic `Li-ion` (uniformly mapped as `unknown` lithium-ion batteries).
* **Output Files**:
1. `dataset_10_EV_metadata.csv` (Metadata table)
2. `dataset_10_EV_cycle_summary.csv` (Cycle-level features table)
3. `dataset_10_EV_timeseries.csv` (High-frequency timeseries table)



## 2. Field Mapping & Standardization

In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw EV charging data was standardized and estimated as follows:

* **Unique Identification (Cell ID) Construction**: Since the raw data does not directly provide a unique ID for cells or battery packs and the data is highly mixed, the script generates a pseudo-unique primary key by concatenating `{EV_Model}` and `{Battery_Type}`. Example: `ev_charging_ModelA_Liion`.
* **Time Unit Alignment**: The charging duration in the raw records is in minutes (`Charging Duration (min)`). This was multiplied by 60 in the Timeseries table to convert to standard seconds (`time_s`).
* **Capacity Estimation**: The raw data lacks direct capacity measurements. Based on the physical logic of ampere-hour integration, the script estimates an approximate `charge_capacity_Ah` using the formula: `Current (A) * (Charging Duration (min) / 60)`. In the Cycle Summary, this value is used as the `capacity_Ah` for the current cycle.
* **State of Health (SOH) Conversion**: The raw data provides a `Degradation Rate (%)`. To align with the Benchmark's dimensionless SOH standard, the script applies the conversion formula `SOH = (100 - Degradation Rate) / 100`, rounding to 4 decimal places.
* **Chemistry Alignment**: Strictly adhering to the specifications, `LiFePO4` from the raw data is converted to `LFP`, while the generic `Li-ion` is filled as `unknown`. The original names are preserved in the `cathode_material` field to prevent information loss.

## 3. Core Engineering Challenges & Scripting Logic

*Note: Unlike processing complex multi-nested Matlab `.mat` structures (like XJTU) or parsing filenames via regular expressions (like SNL), the core ETL challenge for this dataset lies in "reverse decoupling of relationships from flattened data."*

1. **Aggregation and Extraction from Flattened Tables (Metadata Extraction)**
The raw data is a massive, mixed table containing all timeseries and ontology attributes. To generate a compliant `metadata.csv`, the script abandons the traditional file-by-file reading approach. Instead, it utilizes Pandas' `groupby('cell_id')` combined with the `agg('first')` method to reversely extract the inherent physical information (e.g., ambient temperature mean, vehicle model) of each battery entity from tens of thousands of rows of timeseries data, achieving dimensionality reduction and normalization.
2. **Deduplication and Primary Key Conflict Resolution (Cycle Summary Aggregation)**
When extracting `cycle_summary.csv`, multiple records might exist for the same `Charging Cycles` due to sampling or anomalies. Directly extracting them could lead to duplicate primary keys. The script adopts a safe strategy of first using `groupby(['cell_id', 'Charging Cycles'])` and then applying `mean` and `sum` aggregations. This ensures that every output `cycle_id` is globally unique and monotonically increasing.

## 4. Missing Fields Explanation

Due to the limited collection dimensions of the raw data in this batch of EV charging scenarios, some Schema fields are unavailable and have been left blank (`NaN`) or filled with `unknown`:

* **Discharge-related Fields (All Tables)**: This dataset only records characteristics of the charging phase. Therefore, all discharge-related indicators in both Timeseries and Cycle Summary (e.g., `discharge_capacity_Ah`, `discharge_duration_s`, `discharge_protocol`) are empty.
* **Static Physical Parameters (Metadata)**: Battery static bench parameters such as `nominal_capacity_Ah`, `nominal_voltage_V`, cutoff voltages, and `form_factor` are completely missing from the raw data.
* **Advanced Health Indicators (Cycle Summary)**: The data does not provide `internal_resistance_Ohm` measurements for each cycle. Additionally, because there is no clearly defined End of Life (EOL) threshold, the Remaining Useful Life (`RUL`) field is left blank.