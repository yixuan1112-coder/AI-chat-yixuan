# Dataset Note: dataset_33 — Thermal Runaway Propagation NMC-811 and LFP (TUM)

| Field | Value |
|-------|-------|
| **Dataset ID** | dataset_33 |
| **Data Category** | thermal_abuse |
| **Source** | eet-china collection |
| **URL** | https://mediatum.ub.tum.de/node?id=1717758 |
| **Chemistry** | NMC-811, LFP (automotive-grade) |
| **Last Updated** | 2026/3/18 |

---

## 1. Why This Dataset Does Not Belong to the Current Cycle-Aging Mainline

This dataset captures thermal runaway propagation experiments — intentional overheating of battery cells/modules to study failure cascading behavior. The data consists of temperature–time profiles from multiple thermocouples during abuse events, not charge–discharge cycling. There is no capacity degradation trajectory or cycle-level performance data.

## 2. Physical Information Contained

- **Thermal runaway onset temperature**: Critical temperature at which self-heating becomes uncontrollable for NMC-811 and LFP cells.
- **Propagation dynamics**: Time delays and thermal pathways between adjacent cells in a module during cascading failure.
- **Peak temperature profiles**: Maximum temperatures reached during thermal runaway (typically 700–1000°C for NMC).
- **Chemistry-dependent safety margins**: Comparative thermal stability data between NMC-811 (lower onset) and LFP (higher onset) under identical abuse conditions.
- **Heat release rates**: Thermal energy output during runaway events, critical for thermal management design.

## 3. Potential Future Tasks Supported

- **Safety-aware digital twin**: Incorporating thermal abuse limits into battery model safety boundaries.
- **Thermal management system design**: Using propagation data to validate cooling strategies and cell spacing.
- **Failure prediction**: Identifying early-warning thermal signatures before runaway onset.
- **Risk scoring**: Providing reference data for battery system safety ratings across chemistries.
- **Multi-physics simulation validation**: Calibrating coupled electrochemical-thermal models at extreme conditions.

## 4. Unified Fields Currently Missing

| Required Field | Status | Notes |
|---------------|--------|-------|
| `cycle_index` | N/A | No cycling structure |
| `capacity_ah` | N/A | Cells are destroyed during testing |
| `voltage_v` | Partial | May be logged until cell venting/short circuit |
| `current_a` | N/A | No controlled charge/discharge |
| `soh` | N/A | Not applicable to abuse testing |
| `temperature` | Present | Core measurement — multi-point thermocouple data |
| `abuse_trigger_method` | Present (non-standard) | Needs new schema field for abuse test type |
| `propagation_delay_s` | Present (non-standard) | Time between cell failures, needs schema definition |
