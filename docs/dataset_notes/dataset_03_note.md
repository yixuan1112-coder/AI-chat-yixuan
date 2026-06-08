# Dataset Note Template

## Basic Information

**Dataset ID:**  
`dataset_xx`

**Dataset Name:**  
[Fill in dataset name]

**Assigned Student:**  
[Fill in student name]

**Reviewed By:**  
[Fill in reviewer name]

**Status:**  
`pending / processing / qc / finished`

**Last Updated:**  
`YYYY-MM-DD`

---

## Source Information

**Source Type:**  
`public / internal`

**Source Link or Reference:**  
[Paper link, repository link, website, or internal record]

**Original File Location:**  
`data/raw/...`

**License or Usage Restriction:**  
[Fill in if available]

---

## Dataset Summary

Provide a brief summary of this dataset, including:

- what the dataset contains
- number of cells or experiments
- chemistry or battery type
- whether it contains full time-series signals
- whether it contains cycle-level summaries
- any important limitation

---

## Raw File Inventory

List all raw files used for this dataset.

| File Name | File Type | Description | Used in Pipeline |
|---|---|---|---|
| example.csv | csv | raw timeseries data | yes |
| metadata.xlsx | xlsx | cell metadata | yes |

---

## Expected Output Files

Describe the expected standardized outputs for this dataset.

- `data/processed/<dataset_id>/<dataset_id>_metadata.csv`
- `data/processed/<dataset_id>/<dataset_id>_timeseries.parquet`
- `data/processed/<dataset_id>/<dataset_id>_cycle_summary.csv`
- `data/processed/<dataset_id>/README_schema.md`

---

## Field Mapping

Document how original fields are mapped into BatteryTwin Schema v0.2.

| Original Field Name | Standard Field Name | Unit | Conversion Needed | Notes |
|---|---|---|---|---|
| Time | time_s | s | no | |
| Voltage | voltage_V | V | no | |
| Current | current_A | A | yes/no | |
| Temperature | temperature_C | C | yes/no | |

Add more rows as needed.

---

## Available Core Fields

Mark whether the core fields are available in this dataset.

### Identity
- [ ] `dataset_id`
- [ ] `cell_id`
- [ ] `source_type`
- [ ] `split_tag`

### Battery Entity
- [ ] `chemistry`
- [ ] `cathode_material`
- [ ] `anode_material`
- [ ] `brand_or_manufacturer`
- [ ] `model_or_size`
- [ ] `form_factor`
- [ ] `nominal_capacity_Ah`
- [ ] `nominal_voltage_V`

### Protocol Information
- [ ] `temperature_C`
- [ ] `charge_protocol`
- [ ] `discharge_protocol`
- [ ] `C_rate`
- [ ] `cutoff_voltage_upper`
- [ ] `cutoff_voltage_lower`

### Time-Series Signals
- [ ] `time_s`
- [ ] `voltage_V`
- [ ] `current_A`
- [ ] `temperature_C`

### Cycle-Level Labels
- [ ] `cycle_id`
- [ ] `capacity_Ah`
- [ ] `SOH`
- [ ] `RUL`

---

## Unit Normalization

Record unit conversion rules applied in this dataset.

| Signal | Original Unit | Target Unit | Conversion Rule | Notes |
|---|---|---|---|---|
| time |  | s |  |  |
| voltage |  | V |  |  |
| current |  | A |  |  |
| temperature |  | C |  |  |

---

## Missing Fields and Gaps

List missing fields, ambiguous metadata, or unavailable signals.

| Category | Missing or Ambiguous Item | Impact | Action |
|---|---|---|---|
| metadata |  |  |  |
| timeseries |  |  |  |
| protocol |  |  |  |
| labels |  |  |  |

---

## Quality Control Notes

Summarize QC checks and observations.

### Required Field Check
- [ ] completed
- Notes:

### Unit Check
- [ ] completed
- Notes:

### Time-Axis Check
- [ ] completed
- Notes:

### Sample Visualization
- [ ] completed
- Notes:

---

## Known Issues

List all known issues that still need manual review or future correction.

1. [Issue 1]
2. [Issue 2]

---

## Processing Notes

Describe how the dataset was processed.

- scripts used
- assumptions made
- filtering rules
- interpolation or resampling strategy
- cycle segmentation logic if applicable

---

## Handover Checklist

- [ ] raw files preserved and unchanged
- [ ] metadata file generated
- [ ] timeseries file generated
- [ ] cycle_summary file generated
- [ ] schema description completed
- [ ] QC completed
- [ ] dataset_registry.csv updated
- [ ] ready for merge into main branch

---

## Commit and Branch Record

**Working Branch:**  
`student-name/dataset-xx`

**Main Processing Script:**  
`scripts/...`

**Latest Commit:**  
[Fill in commit hash or summary]
