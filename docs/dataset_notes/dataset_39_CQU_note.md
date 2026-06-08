
# CQU Battery Dataset - Data Processing Notes (README)

## 1. Dataset Overview
* **Dataset ID**: `dataset_39`
* **Original Data Scope**: Includes multiple consolidated files such as `Dataset1_Dataset2.mat`, `Dataset3.mat`, and `Dataset4.mat`.
* **Cell Specifications**: Samsung SDI INR18650-20R cylindrical cells, 2.0Ah nominal capacity, 3.6V nominal voltage.
* **Chemistry**: NMC (Cathode: LiNiMnCoO2, Anode: Graphite).
* **Output Files**:
  1. `dataset_39_CQU_metadata.csv` (Metadata table)
  2. `CQU_{Cell_ID}_cycle_summary.csv` (Cycle-level summary table)
  3. `CQU_{Cell_ID}_timeseries.csv` (High-frequency timeseries table, where available)

## 2. Field Mapping & Standardization
In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw data was standardized as follows:
* **Unit Normalization**: 
    - Raw capacity values in summary files were stored as percentages (%). These were converted to standard Ampere-hours (`capacity_Ah`) using the formula `(val / 100.0) * 2.0`.
    - Current in milliamperes (`mA`) was divided by 1000 to convert to Amperes (`current_A`).
* **Current Sign Alignment (Discharge as Negative)**: Strictly follows the standard convention. The script ensures all discharge currents under the `current_A` field are negative.
* **Unique Identification (Cell ID)**: Since 30 cells are bundled in a single `.mat` file, the script extracts the inner cell label (e.g., `C1`) and prepends a prefix to create a globally unique `cell_id` (e.g., `CQU_C1`).

## 3. Core Engineering Challenges & Pipeline Logic
*Note: The ETL process for the CQU dataset involved deep pointer dereferencing due to its complex MATLAB v7.3 nested format.*

1. **MATLAB v7.3 (HDF5) Compatibility Bottleneck**
   The raw files are in `v7.3` format, which is incompatible with `scipy.io.loadmat`. The pipeline utilizes the `h5py` library to treat `.mat` files as HDF5 databases, enabling hierarchical traversal of modern MATLAB structures.
2. **Multi-level Dereferencing & Recursive Drilling**
   The data hierarchy is exceptionally deep (Top-level Group -> Workingprofile Pointer List -> Segment References -> Final Matrix). A **recursive unpacking logic** was implemented to penetrate reference lists (Cell Arrays) and resolve HDF5 pointer chains to reach the underlying numerical samples.
3. **Vertical Stitching of Timeseries Segments**
   Timeseries data for a single cell is often stored across multiple segments (e.g., 14 segments). The script performs vertical stacking using `numpy.concatenate` and regenerates a continuous time axis (`time_s`) to fix overlapping timestamps at segment boundaries.
4. **Differential Handling of Summary vs. Raw Files**
   Analysis revealed that files like `Dataset4.mat` contain test condition strings rather than raw sampling matrices. The pipeline includes an **intelligent detection module**: if raw timeseries data is missing, it skips `timeseries` generation and extracts aging summary data (700+ cycles) from the `Capacity` variable.

## 4. Missing Fields Explanation
Due to the limitations of the raw data, certain Schema fields were left blank:
* `internal_resistance_Ohm` (Cycle Summary): No cycle-by-cycle internal resistance measurements were provided.
* `temperature_C` (Timeseries): Some dynamic profiles lacked temperature recordings; these are filled with 25.0°C or `NaN`.

