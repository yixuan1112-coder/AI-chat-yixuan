# SNL Battery Dataset - Data Preparation Note (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_06`
* **Original Data Scale**: Contains multiple batches of real physical battery data organized into subfolders by test temperatures (e.g., 15C, 25C, 35C).
* **Cell Specifications**: 18650 commercial cylindrical cells. Covers three distinct specifications: LFP (1.1Ah, 3.3V), NMC (3.0Ah, 3.6V), and NCA (3.2Ah, 3.6V).
* **Material Chemistry**: A horizontal comparison of three chemistries (LFP-A123, NMC-LG Chem, NCA-Panasonic), all utilizing Graphite anodes.
* **Included Files**:
  1. `dataset_06_metadata.csv` (Global metadata table, strictly aligned with the 18-column XJTU standard)
  2. `*_cycle_summary.csv` (Cycle-level summary tables, stored in respective batch subfolders)
  3. `*_timeseries.csv` (High-frequency timeseries tables, stored in respective batch subfolders)

## 2. Field Mapping and Physical Quantity Standardization

The raw data has been standardized according to the `BatteryTwin Schema v0.2` and the downstream 18-column feature specification:

* **Globally Unique Identification (Cell ID Anti-Collision)**: Since the raw files are dispersed across different batch folders (e.g., `15C_Test`), identical filenames (like `cell_1.csv`) frequently occur. To ensure global uniqueness during the final wide-table concatenation, the `cell_id` is constructed using the `{Dataset_ID}_{Folder_Name}_{File_Name}` format (e.g., `dataset_06_15C_Test_cell_1`).
* **Dynamic Protocol Mapping**: Charge and discharge C-rates are implicitly embedded in the original filenames. The ETL pipeline utilizes regular expressions to extract these rates (e.g., `_0.5-1C_`) and dynamically couples them with the specific chemistry's voltage window to synthesize standardized protocol strings (e.g., `CC-CV 0.5C to 4.2V` and `CC 1C to 2.5V`) for the `charge/discharge_protocol` fields.
* **Data Split Reservation**: The `split_tag` field is uniformly preset to `unassigned` during the ETL phase, leaving the dynamic dataset partitioning (Train/Val/Test) to the subsequent LightGBM machine learning pipeline.

## 3. Core Engineering Challenges & Data Cleaning Logic

*Note: The SNL dataset exhibits high physical diversity and complex nested directory structures. The following engineering bottlenecks were resolved using customized multi-module Python scripts:*

1. **File I/O Isolation Due to Nested Subfolders**
   The raw files are not flattened in the root directory but segregated into different temperature batch folders. Standard single-level `glob.glob` searches fail to retrieve them. Therefore, an `os.scandir` traversal logic was introduced into the ETL scripts, enabling the pipeline to penetrate subfolders and automatically replicate the directory structure within the `processed` output path for isolated storage.
2. **Metadata Extraction and Imputation for Mixed Chemistries**
   This dataset amalgamates LFP, NMC, and NCA batteries, which possess vastly different nominal capacities and voltage windows (e.g., LFP is merely 1.1Ah, while NCA reaches 3.2Ah). To perfectly align with the 18-column standard metadata table, the filename parsing function incorporates hardcoded "physical dictionaries." This ensures accurate extraction of the chemistry type and precise automatic imputation of the corresponding capacity and upper/lower cutoff voltages (4.2V/3.6V and 2.5V/2.0V).
3. **Cross-Table Extraction of Derived Features**
   Critical features required for the summary table, such as `charge_duration_s` and `temperature_max_C`, are absent in the raw summary files. A "dual-table linkage" architecture was implemented: while processing the summary, the underlying timeseries data is simultaneously loaded. By evaluating current direction (`Current > 0.01`) and applying `groupby(cycle)`, the pipeline achieves second-level precision time integration and temperature extrema extraction.