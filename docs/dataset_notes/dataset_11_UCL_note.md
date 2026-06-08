
---

# UCL/Beihang Battery Dataset (Dataset 11) - Data Processing Notes (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_11`
* **Dataset Attribution & Provenance**:
* **Original Experimental Data Source**: Electrochemical Innovation Lab, University College London (UCL). Responsible for the charge/discharge cycle testing of the real physical batteries.
* **Simulation Data & Publisher**: Chengzhang Li, Beihang University. Responsible for generating theoretical degradation models based on physical data and packaging/publishing the dataset.


* **Cell Specifications**: LG INR18650-MJ1, cylindrical 18650 cell, nominal capacity 3.5Ah, nominal voltage 3.63V, charge/discharge voltage range 4.2V - 2.5V.
* **Chemistry**: NMC (Cathode: High-nickel NMC, Anode: Si-Graphite).
* **Output Files**:
1. `dataset_11_metadata.csv` (Metadata table)
2. `dataset_11_cycle_summary.csv` (Cycle-level features table)
3. `dataset_11_timeseries.csv` (High-frequency timeseries table)



## 2. Field Mapping & Standardization

In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw experimental data was standardized as follows:

* **Explicit Core Parameter Injection (Metadata)**: The raw data headers lack battery ontology information. Based on literature reviews and the `EIL-MJ1` model identifier, standard bench parameters for the LG MJ1 (e.g., `nominal_capacity_Ah` = 3.5, `chemistry` = NMC) were hard-coded and injected via the script.
* **Time Unit Alignment (Timeseries)**: The timeseries time unit output by the original test equipment was in hours (`Test Time (Hrs)`). This was multiplied by 3600 in the code to convert to standard seconds (`time_s`).
* **State of Health (SOH) Conversion**: `Discharge Capacity` was used as the core `capacity_Ah`. Based on the nominal capacity of 3.5Ah, dimensionless processing was performed using the formula `SOH = capacity_Ah / 3.5`.

## 3. Core Engineering Challenges & Scripting Logic

*Note: The raw file structure of this dataset is highly unusual. Macroscopic summary data and microscopic timeseries data are mixed within the same CSV table, featuring a rare horizontal data tiling phenomenon.*

1. **Separation of Heterogeneous Data in the Same Table**
When processing experimental files like `EIL-MJ1-015.csv`, the first 3 columns on the left contain macroscopic Summary data grouped by cycle, while the right side contains microscopic Timeseries data. The ETL pipeline was designed as two independent scripts to separately extract and structurally convert the left and right sections.
2. **Horizontal Deconstruction of Timeseries Data (Unstacking & Melt)**
The original timeseries data did not use traditional vertical stacking. Instead, `Test Time`, `Cycle Number`, `Temp`, and `Capacity` for different time periods were aggressively spliced horizontally to the right, resulting in numerous redundant column names and empty fills. The script utilizes dynamic feature column detection technology to slice the horizontally spread blocks one by one, subsequently executing vertical concatenation (`concat`) and missing value dropping (`dropna`) operations, successfully reshaping it into a standard Long Format table with monotonically increasing timestamps.
3. **Eliminating Pandas Empty Table Broadcasting Bug**
During the generation of the `Cycle Summary`, we encountered a low-level Pandas defect where assigning a scalar (like `cell_id`) to an empty table with pre-defined columns failed. By adjusting the code architecture to a strategy of "first filling a fixed-length array (`cycle_id`) to expand the DataFrame's row dimension, then filling the scalar," we ensured all output results were intact and correctly populated.

## 4. Simulation File Isolation & Baseline Policy

The compressed package includes several `.xlsx` files named `Simulation results...`.

* **Isolation Strategy**: To guarantee the absolute physical purity of the BatteryTwin Benchmark Ground Truth training data, the cleaning script incorporated a whitelist filtering mechanism, actively intercepting and removing all files tagged with "Simulation".
* **Future Usage**: These model deduction data have been saved in an unstandardized byproduct directory. They will serve as a **Baseline** comparison group for evaluating the platform's future digital twin algorithms and AI prediction performance.

## 5. Missing Fields Explanation

* **RUL**: No clear End of Life (EOL) threshold is defined; the Remaining Useful Life (`RUL`) field is left blank.
* **Internal Resistance**: No internal resistance data from DCR or EIS tests is provided for each cycle.
* **Charge/Discharge Protocol Details**: The data itself lacks specific C-rate records, which are marked as `unknown` in the Metadata.