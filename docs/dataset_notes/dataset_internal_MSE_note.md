# NTU_MSE Internal Battery Dataset - Data Preparation Note (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_internal_MSE`
* **Original Data Scale**: Contains 167 groups of real physical battery data folders (e.g., `1.7AhLFP_001`, `3.3AhNCA_001`).
* **Cell Specifications**: Primarily 18650 cylindrical cells. Typical nominal capacities include 1.7Ah (LFP) and 3.3Ah (NCA), with nominal voltages distributed by chemistry.
* **Material Chemistry**: Mixed systems, mainly LFP (Lithium Iron Phosphate) and NCA (Lithium Nickel Cobalt Aluminum Oxide), all with Graphite anodes.
* **Included Files**:
    1.  `*_metadata.csv` (Metadata table, strictly aligned with XJTU 18-column standard)
    2.  `*_cycle_summary.csv` (Cycle summary table, aligned with XJTU 14-column standard)
    3.  `*_timeseries.csv` (Timeseries table, aligned with 9-column standard features)

## 2. Field Mapping and Physical Quantity Standardization

The raw data was standardized according to the `BatteryTwin Schema v0.2` specification:

* **Physical Imputation and Mapping**: Raw JSONs provided abbreviated material tags (e.g., "LFP"). The metadata ETL script utilizes an internal physical dictionary to expand these to standard formulas (e.g., `LiFePO4`) and automatically maps nominal voltages based on electrochemical properties (3.2V for LFP, 3.6V for NCA).
* **Unique Identification (Cell ID Isolation)**: To prevent ID collisions during multi-dataset merging, the `cell_id` is formatted as `{Dataset_ID}_{Folder_Name}` (e.g., `dataset_internal_MSE_1.7AhLFP_001`). However, prefixes were removed from filenames to maintain directory conciseness.
* **Charging Protocol Standardization**: Original logs recorded conditions as `1C CC`, etc. The cleaning logic uses regular expressions to extract C-rates and couples them with the cutoff voltages from JSON to reconstruct XJTU-style descriptive text (e.g., `1C CC to 3.65V`).
* **Floating-Point Precision Truncation**: Addressing binary conversion errors in high-frequency data, the export process utilizes `%g` smart formatting. This eliminates long-tail decimals (e.g., truncating `3.60000000002` to `3.6`), significantly reducing storage overhead without losing precision.

## 3. Core Engineering Challenges & Data Cleaning Logic

*Note: Due to the diversity of equipment sources and inconsistent file encoding in this internal dataset, the ETL process specifically addressed the following engineering bottlenecks:*

1.  **Automated Resolution of Multi-Encoding Conflicts**
    While processing specific batches like `3.3AhNCA`, standard `UTF-8` decoding failed with a `0xa6` error due to special characters (e.g., `℃` or Chinese remarks). To resolve this, the ETL script implements a **Smart Encoding Detection Architecture** based on a `Try-Except` cascade, automatically switching between `UTF-8 -> GBK -> GB18030 -> Latin1`. This ensured 100% successful automated reading of all 167 battery files.
2.  **Dynamic Transformation of Unstructured JSON to 18-Column Tables**
    The original `metadata.json` utilized a nested dictionary structure (e.g., ambient parameters nested under `environment_profile`). The script implements logic to traverse these nested levels to extract fields like `ambient_temp_c`. It also employs a **Smart Tokenization Algorithm** for the `form_factor` field (e.g., splitting `cylindrical_18650` into separate "form factor" and "size" columns) to achieve one-click alignment with the XJTU metadata standard.
3.  **"Slimming" and Distribution of Large-Scale Timeseries Data**
    Given the massive volume of timeseries data, a **"1:1 Mirrored Directory Distribution"** model was adopted, precisely storing processed features into 167 corresponding subfolders. During extraction, the script performs fuzzy matching on `Step Type` (e.g., mapping raw labels like `CC DChg` to the standard `discharge`), facilitating future feature extraction based on specific operating conditions.
