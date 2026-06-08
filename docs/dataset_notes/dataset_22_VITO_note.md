# VITO Calendar Ageing Dataset (Dataset 22) - Data Processing Notes (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_22`
* **Dataset Attribution & Provenance**: Provided by the Battery Testing Laboratory of VITO/EnergyVille (Belgium) as part of the H2020 European project Everlasting. All tests were performed on a PEC battery tester.
* **Cell Specifications**: Commercial 18650 cylindrical cells.
* **Chemistry**: Ni-rich positive electrode and Si/Gr based negative electrode.
* **Experimental Protocol**: This dataset contains calendar ageing tests. Cells were stored at different environmental temperatures (25°C and 45°C) and fixed SOC levels (10%, 70%, and 90%). The calendar test was regularly interrupted to run a reference performance test to track degradation.

## 2. Field Mapping & Engineering Logic

In strict accordance with the `BatteryTwin Schema v0.2` specifications:
* **Dynamic Column Detection**: Because the exact column headers of the raw CSVs vary or are non-standard, the ETL scripts utilize a `find_col` fuzzy matching function to automatically detect essential time, voltage, current, and capacity sequences.
* **SOH Estimation Algorithm**: The original ReadMe does not explicitly state the nominal capacity of these commercial cells. Therefore, the Cycle Summary script dynamically calculates the State of Health (SOH) by using the first recorded cycle capacity as the baseline (`SOH_i = Capacity_i / Capacity_initial`).

## 3. Missing Fields Explanation
* `nominal_capacity_Ah` (Metadata): The exact manufacturer rated capacity is omitted in the raw source and thus left blank.
* `chemistry` (Metadata): While designated as "Ni-rich", the exact classification (e.g., NMC or NCA) is not defined, so it is marked as `unknown` (with the material details preserved in the cathode/anode specific columns).