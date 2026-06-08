# BatteryTwin Benchmark Data Preparation

## Project Overview

This repository prepares heterogeneous battery datasets for the BatteryTwin benchmark. The goal is to consolidate multiple public datasets and one internal dataset into a unified lightweight schema that supports downstream benchmarking tasks.

The focus of this repository is **dataset integration and standardization**, not model training.

---

## Repository Structure

```text
BatteryTwin-Benchmark-DataPrep/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── configs/
├── docs/
├── scripts/
├── notebooks/
├── reports/
└── tests/
```

Raw datasets are stored in `data/raw`. Standardized outputs are stored in `data/processed`.

---

## Data Organization Principles

1. **Raw data must remain unchanged**  
   All original files are stored in `data/raw/`. They must never be edited.

2. **Processed outputs are stored separately**  
   Unified datasets are written to `data/processed/`.

3. **Processing must be reproducible**  
   All transformations should be implemented through scripts.

4. **Each dataset must contain four deliverables**
   - `metadata`
   - `timeseries`
   - `cycle_summary`
   - schema documentation

---

## BatteryTwin Schema v0.2 (Core Fields)

### Identity

- `dataset_id`
- `cell_id`
- `source_type`
- `split_tag`

### Battery Entity

- `chemistry`
- `cathode_material`
- `anode_material`
- `brand_or_manufacturer`
- `model_or_size`
- `form_factor`
- `nominal_capacity_Ah`
- `nominal_voltage_V`

### Protocol Information

- `temperature_C`
- `charge_protocol`
- `discharge_protocol`
- `C_rate`
- `cutoff_voltage_upper`
- `cutoff_voltage_lower`

### Time-Series Signals

- `time_s`
- `voltage_V`
- `current_A`
- `temperature_C`

### Cycle-Level Labels

- `cycle_id`
- `capacity_Ah`
- `SOH`
- `RUL`

Detailed schema documentation is available in [`docs/schema/schema_overview.md`](docs/schema/schema_overview.md).

---

## Quick Start

### Environment

Python 3.10 or above is recommended.

Install dependencies with:

```bash
pip install -r requirements.txt
```

Or create the conda environment with:

```bash
conda env create -f environment.yml
```

---

## Common Scripts

Run the dataset processing pipeline:

```bash
python scripts/run_pipeline.py --dataset dataset_01
```

Run quality checks:

```bash
python scripts/qc/check_required_fields.py
python scripts/qc/check_units.py
python scripts/qc/check_time_axis.py
```

Generate sample visualization:

```bash
python scripts/qc/plot_sample_cells.py
```

---

## Project Deliverables

A dataset integration is considered complete only if the following items are provided:

1. Raw data are preserved and unchanged  
2. A `metadata` file is generated  
3. A standardized `timeseries` file is generated  
4. A `cycle_summary` file is generated  
5. A schema description is provided  
6. Quality checks are completed  
7. The dataset can be loaded through the unified loader  

---

## Notes

- Do not modify files under `data/raw`
- All processing steps must be script-based
- Missing fields must be documented
- Battery metadata should be completed whenever possible
- Consistency is more important than optional extensions

---

## Maintainers

**Supervisor**  
Zhu Tianwen/ Wang Hao

**Capstone Students**  
Liu Kefan
Cao Han  

---

## Documentation

Detailed documentation is organized as follows:

- [`docs/schema/`](docs/schema/) for schema definitions and field descriptions
- [`docs/dataset_notes/`](docs/dataset_notes/) for dataset-specific notes and integration records
- [`docs/qc_reports/`](docs/qc_reports/) for quality-control reports and issue tracking
- [`docs/project_plan/`](docs/project_plan/) for planning, milestones, and handover materials
