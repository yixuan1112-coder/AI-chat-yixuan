# XJTU Battery Dataset - Data Processing Notes (README)

## 1. Dataset Overview
* **Dataset ID**: `dataset_XJTU`
* **Original Data Scope**: Includes Batches 1-6, totaling 48 physical cell files (excluding calibration/compensation files).
* **Cell Specifications**: Lishen 18650 cylindrical cells, 2.0Ah nominal capacity, 3.6V nominal voltage.
* **Chemistry**: NCM (Cathode: LiNi0.5Co0.2Mn0.3O2, Anode: Graphite).
* **Output Files**:
  1. `dataset_XJTU_metadata.csv` (Metadata table)
  2. `dataset_XJTU_cycle_summary.csv` (Cycle-level features table)
  3. `dataset_XJTU_timeseries.csv` (High-frequency timeseries table)

## 2. Field Mapping & Standardization
In strict accordance with the `BatteryTwin Schema v0.2` specifications, the raw data was standardized as follows:
* **Time Unit Alignment**: The relative time output by the raw tester was in minutes (`relative_time_min`). This was multiplied by 60 in the timeseries table to convert to standard seconds (`time_s`).
* **Current Sign Alignment (Discharge as Negative)**: Follows the standard convention strictly. Raw discharge currents were recorded as positive values; they were multiplied by `-1` via the script to ensure all discharge currents under the `current_A` field are negative.
* **Unique Identification (Cell ID)**: Filenames were duplicated across different Batches (e.g., `2C_battery-1.mat`). To ensure global uniqueness, the `cell_id` was concatenated using the `{Batch_Name}_{File_Name}` format (e.g., `Batch-1_2C_battery-1`).

## 3. Core Engineering Challenges & Pipeline Logic
*Note: Due to the idiosyncratic structure of the raw XJTU `.mat` files, the ETL (Extract, Transform, Load) process for this dataset was highly complex. The following engineering bottlenecks were resolved using a customized, multi-module Python pipeline:*

1. **Deconstruction of Nested Data Structures**
   The raw data is not a flat table but a `(1, N)` dimensional nested MATLAB struct. The script utilized multiple nested loops to drill down into the underlying dictionaries, extracting variable-length arrays for each cell's life cycle (up to nearly 400 cycles) and restructuring them into a Long DataFrame format.
2. **Out-of-Memory (OOM) Defense for Massive Timeseries Files**
   Loading the full-life-cycle, second-by-second timeseries data (tens of millions of rows) into RAM conventionally causes memory thrashing and crashes. Therefore, the timeseries extraction utilized a **`ProcessPoolExecutor` (multi-processing) + "Calculate-and-Save" (incremental append mode)** architecture, keeping peak memory usage well within safe limits.
3. **Implicit Metadata Traceability and Injection**
   The raw `.mat` files contain only physical test signals, completely lacking cell physical parameters (brand, chemistry, nominal voltage, test protocols, etc.). During processing, the original published literature for this dataset was traced, and the accurate NCM ternary material properties and detailed charge/discharge protocols (e.g., `CC-CV 4A to 4.2V`) were manually injected and aligned into `metadata.csv`.
4. **Scripting Logic**
   Initially, the data processing scripts were centralized in etl_xjtu.py and organized into three files for metadata, cycle summaries, and time-series data. While this approach allowed for concurrent processing of all datasets—saving some time in theory—it suffered from a lengthy total execution time of 20 to 30 minutes. Furthermore, there was a lack of a one-to-one mapping between the raw datasets and the scripts, resulting in poor visibility and traceability.
   To resolve this, the architecture was restructured to align scripts and output files with their respective batches using dedicated folders. This change has significantly improved performance: processing a single batch's cycle summary now takes only 30 to 90 seconds, while processing the timing data for all batteries in various batches takes just 1-3 minutes. ("If you find running all scripts manually too tedious, you can create a run_all.py script to execute them all independently.")

## 4. Missing Fields Explanation
Due to the limitations of the raw data, certain Schema fields were left blank (filled with `NaN` or `unknown`):
* `charge_capacity_Ah` (Timeseries): This batch of data primarily records the discharge phase; thus, charging capacity at the timeseries level is empty.
* `internal_resistance_Ohm` (Cycle Summary): The raw test did not provide internal resistance measurements for each cycle.