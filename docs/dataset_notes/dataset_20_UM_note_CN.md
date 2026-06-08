# UM Battery Dataset - Data Preparation Notes (README)

## 1. Dataset Overview

* **Dataset ID**: `dataset_20`
* **Original Title**: Battery Test Data (University of Malaya)
* **Dataset Scale**: Features 3 mainstream commercial 18650 cells tested across 4 temperature levels under various advanced driving cycles and aging protocols. The physical directory structure is highly chaotic due to irregular naming conventions.
* **Cell Specifications & Chemistry**:
  1. **LFP Chemistry**: A123 Systems (APR18650M1A), Nominal Capacity: 1.1Ah, Nominal Voltage: 3.3V. Cathode: LiFePO4, Anode: Graphite.
  2. **NCA Chemistry**: Panasonic (NCR18650B), Nominal Capacity: 3.4Ah, Nominal Voltage: 3.6V. Cathode: LiNiCoAlO2, Anode: Graphite.
  3. **NMC Chemistry**: Murata/Sony (US18650VTC6), Nominal Capacity: 3.0Ah, Nominal Voltage: 3.6V. Cathode: LiNiMnCoO2, Anode: Graphite.
* **Output Files Included**:
  1. `dataset_20_metadata.csv` (Global Master Metadata Sheet)
  2. `timeseries.csv` (Located in each cell's mirrored directory)
  3. `cycle_summary.csv` (Located in each cell's mirrored directory)

## 2. Field Mapping & Physical Quantity Normalization

All raw files have been flattened and standard-cleaned in strict accordance with the `BatteryTwin Schema v0.2` specification:

* **Adaptive Unit Normalization**: The raw data suffered from severe unit inconsistency (some sheets used `A/Ah`, while some Neware-exported Detail sheets used `mA/mAh`). The extraction engine implements a boundary-sniffing mechanism (automatically flags mA if the maximum absolute value > 50) to dynamically normalize all inputs into standard Amperes (`current_A`) and Ampere-hours (`capacity_Ah`, etc.) across all timeseries and cycle summaries.
* **Timestamp Shift Fallback**: For certain low-level Neware tables where absolute timestamps are missing and only `Record Index` is available, the ETL pipeline applies a fallback shift (`Record Index - 1`) to correctly align the sequence as standard seconds (`time_s`) starting from 0.
* **Global Unique Cell Identification**: To guarantee uniqueness, `cell_id` is standardized into the following uniform format: `UM_{Chemistry}_{Temperature_C}C` (e.g., `UM_NMC_25C`, `UM_NMC_-5C`).

## 3. Core Engineering Challenges & ETL Cleaning Logic

*Note: The processing of this dataset was uniquely demanding. The raw repository was maintained with considerable casualness over multiple generations of testers, resulting in heavily fragmented data structures. Through numerous iterations of code refactoring, the following robust, industrial-grade cleaning strategies were developed:*

1. **Bypassing the Windows 260-Character Path Limit (MAX_PATH Limit)**
   The nested directory structure in the raw unzipped folder exceeded 300 characters because the original authors embedded excessively long cell parameter strings into the folder names. This triggered path truncation at the OS level, throwing fatal `DirectoryNotFoundException` errors in Python and PowerShell even though the files visually existed. This was solved by flattening the base path down to `D:\p\...\Battery Test Data`, removing redundant layers and unlocking file I/O.
2. **"Schrödinger's Typos" — Multi-Alias Temperature Extraction**
   Folder names for temperature levels were written haphazardly with inconsistent capitalization and spelling. For instance, +25°C was written as `25 Degree`, while -5°C appeared as `Negative 5 degree`, `N5 Degree`, and even misspelled as `Negative 5 drgree` (with an extra 'r'). Meanwhile, 45°C was labeled as `45 dgree` (missing an 'e'). Traditional rigid string matching would cause massive data loss for the -5°C and 45°C subfolders. The cleaning engine employs a vertical path-tree scanner combined with a fuzzy regex dictionary, normalizing `drgree`, `dgree`, `negative`, `minus`, and `n` into clean floating-point temperatures. This renders the script completely immune to human typos.
3. **Breaking the "Filename Shackle" via Full-Sheet Signature Auditing**
   The raw files were poorly categorized; aging data (Cycle Summary) and driving cycles (Timeseries) were frequently crammed into a single Excel file, often under obfuscated sheet names like `Cycle_9_1_3` or generic labels like `Sheet1`. Standard file-name-based extraction scripts failed completely here. The pipeline resolved this by adopting a content-driven strategy: it bypasses filename/sheetname restrictions entirely and inspects the internal column metadata of every sheet. If a sheet exhibits the joint signature of `total of cycle` and `discharge capacity`, it is immediately harvested as a Cycle Summary, successfully recovering all missing degradation profiles.
4. **Self-Healing Patches for String-Polluted Data Columns**
   When exporting massive时序 (Detail) tables, Neware hardware occasionally slips textual control characters (e.g., `"▼"`, `"▲"`, `"End"`, `"Rest"`) directly into numeric current or voltage columns. This caused Pandas to throw `bad operand type for abs(): 'str'` and crash silently during unit conversion. The extraction engine mitigates this by inserting a self-healing layer using `pd.to_numeric(..., errors='coerce')` prior to mathematical computations. This safely turns string anomalies into `NaN` values and filters them out, ensuring smooth pipeline flow for tens of millions of timeseries rows.
5. **Mirrored Tree Directory Mapping**
   To preserve the explicit context of the original data and prevent chaotic flat-file blending, both `timeseries.py` and `cyclesummary.py` utilize path-cloning techniques. They replicate the exact original nested tree structure (e.g., preserving distinct branches like `NMC/25 Degree`) under `data/processed/dataset_20/`, dropping the clean, compliant `timeseries.csv` and `cycle_summary.csv` precisely at the deepest leaves of the directory tree.

## 4. Missing Fields and Data Gaps

Due to structural constraints in the physical experiment, certain schema fields are handled with special fallbacks or omitted:

* `cutoff_voltage_upper` & `cutoff_voltage_lower`: Perfectly injected as uniform constants by cross-referencing published Mendeley papers and official cell datasheets (LFP: 3.6V/2.0V; NCA: 4.2V/2.5V; NMC: 4.2V/2.5V).
* **Missing NMC 45°C Cycle Summary**: Deep global recursive file auditing confirmed that the original authors **did not perform life-cycle aging tests** under the `NMC/45 degree` bracket. Only driving cycles are present. The absence of `cycle_summary.csv` here represents a genuine data gap in the physical experiment itself, and the code correctly passes over it.
* `discharge_capacity_Ah` (Timeseries): Since several large driving cycle sheets do not distinctly separate cumulative charge and discharge capacities during continuous cycling, all raw capacities are mapped into `charge_capacity_Ah` as the base cumulative capacity to prevent misleading modeling downstream, leaving the discharge column blank.

---