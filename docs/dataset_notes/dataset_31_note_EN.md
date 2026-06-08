# Dataset Note: dataset_31 — Relaxation Data NMC and LFP (Mendeley)

| Field | Value |
|-------|-------|
| **Dataset ID** | dataset_31 |
| **Data Category** | relaxation |
| **Source** | eet-china collection |
| **URL** | https://data.mendeley.com/datasets/y8nstxmdrg/1 |
| **Reference** | doi.org/10.1016/j.xcrp.2023.101754 |
| **Chemistry** | NMC811, LFP |
| **Last Updated** | 2026/3/18 |

---

## 1. Why This Dataset Does Not Belong to the Current Cycle-Aging Mainline

This dataset contains voltage relaxation curves recorded during rest periods, not continuous charge–discharge cycling data. There are no cycle-level capacity fade trajectories or coulombic efficiency trends, which are the core outputs of the BatteryTwin cycle-aging pipeline. The data structure (time vs. open-circuit voltage during rest) does not map to the standard `timeseries` and `cycle_summary` schemas used for aging datasets.

## 2. Physical Information Contained

- **Open-circuit voltage (OCV) relaxation profiles**: Time-resolved voltage evolution after current interruption, reflecting internal electrochemical equilibration.
- **SOC–OCV relationship indicators**: Relaxation endpoints approximate equilibrium OCV at various states of charge.
- **Diffusion dynamics signatures**: Relaxation time constants encode solid-state lithium diffusion coefficients and charge-transfer kinetics.
- **Chemistry comparison**: Parallel NMC811 and LFP data enable cross-chemistry analysis of relaxation behavior.

## 3. Potential Future Tasks Supported

- **SOH estimation from rest voltage**: Non-invasive health estimation using relaxation curve features (slope, settling time, endpoint voltage).
- **Equivalent circuit model (ECM) parameterization**: Extracting R₀, R₁, C₁ parameters from relaxation transients.
- **Digital twin state initialization**: Using relaxation data to calibrate initial states for physics-based battery models.
- **Multi-modal fusion**: Combining relaxation features with cycling data for improved prognostics.

## 4. Unified Fields Currently Missing

| Required Field | Status | Notes |
|---------------|--------|-------|
| `cycle_index` | N/A | No cycling structure; data is rest-period only |
| `capacity_ah` | Missing | No discharge capacity measurement |
| `coulombic_efficiency` | N/A | Not applicable to relaxation data |
| `soh` | Missing | No reference capacity for SOH calculation |
| `temperature` | To verify | May or may not be recorded alongside voltage |
| `current_a` | Partial | Current is nominally zero during relaxation; pre-rest current may not be logged |
