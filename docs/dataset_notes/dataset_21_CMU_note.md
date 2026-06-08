
---

# CMU eVTOL Battery Dataset (Dataset 21) - Data Processing Notes (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_21`
* **Dataset Attribution & Provenance**: Provided by Alexander Bills et al. from Carnegie Mellon University (CMU). This dataset is specifically designed for high-rate pulse profiles relevant to electric Vertical Takeoff and Landing (eVTOL) aircraft.
* **Cell Specifications**: Sony-Murata 18650 VTC-6 cells, 3.0Ah nominal capacity, 3.6V nominal voltage.
* **Chemistry**: NMC (Cathode: NMC, Anode: Graphite).
* **Output Files**:
1. `dataset_21_metadata.csv` (Metadata table)
2. `dataset_21_VAHxx_cycle_summary.csv` (Cycle-level features, per cell)
3. `dataset_21_VAHxx_timeseries.csv` (High-frequency timeseries, per cell)

## 2. Field Mapping & Standardization

In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw data was standardized as follows:

* **Physical Unit Conversion**: The raw CSV data used milli-units. The script performs automatic conversion: Current is converted from `I_mA` to `current_A` (/1000), and capacity from `Q_mA_h` to `capacity_Ah` (/1000).
* **Internal Resistance Fusion**: Impedance data was originally stored in separate `_impedance.csv` files. The script uses `cycleNumber` as a join key to extract the "1-second resistance measured at 60% SOC" and populate the `internal_resistance_Ohm` field in the summary table.
* **Dynamic Protocol Extraction**: The script scans the `README.txt` using regular expressions to identify descriptions such as "Extended cruise" or "Baseline" and injects them into the experimental protocol fields of `metadata.csv`.

## 3. Core Engineering Challenges & Scripting Logic

1. **"1-to-1" Deconstruction of Heterogeneous Sources**
Unlike single-table datasets, each cell in the CMU dataset consists of one timeseries file and one impedance file. The ETL pipeline implements "file-pair" recognition logic to ensure each physical cell produces a standard set of summary and timeseries tables, preventing memory overflows associated with massive consolidated files.
2. **Capacity Baseline Selection**
Given the complex pulse discharge in eVTOL profiles, raw discharge capacity records might fluctuate under extreme cycles. The script employs a "Discharge Capacity Priority, Charge Capacity Backup" logic, with SOH calculated based on the 3.0Ah nominal value.

## 4. Missing Fields Explanation

* **RUL**: No EOL threshold is defined in the raw source; the `RUL` field is left blank.
* **Temperature (Metadata)**: As environmental temperatures may vary with cycle protocols, `temperature_C` in the metadata is marked as `unknown`. Detailed temperature records are preserved at each sampling point in the timeseries and summary tables.