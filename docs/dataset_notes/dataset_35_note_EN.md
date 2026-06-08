# Dataset Note: dataset_35 — ARC Exothermal Data 21700 (NMC/NCA/LFP)

| Field | Value |
|-------|-------|
| **Dataset ID** | dataset_35 |
| **Data Category** | thermal_abuse |
| **Source** | eet-china collection |
| **URL** | https://zenodo.org/records/7707929 |
| **Reference** | doi.org/10.3390/batteries9050237 |
| **Chemistry** | NMC, NCA, LFP (21700 format) |
| **Last Updated** | 2026/3/18 |

---

## 1. Why This Dataset Does Not Belong to the Current Cycle-Aging Mainline

This dataset contains accelerating rate calorimetry (ARC) measurements — controlled slow-heating experiments that characterize a cell's self-heating onset and thermal runaway behavior. The data is temperature–time under adiabatic conditions, not charge–discharge cycling. Each cell undergoes a single destructive thermal test with no capacity or cycling metrics.

## 2. Physical Information Contained

- **Self-heating onset temperature**: The critical temperature at which exothermic reactions begin and the cell can no longer be considered thermally stable.
- **Exothermal rate profiles (dT/dt)**: Temperature rise rate as a function of temperature, revealing reaction kinetics of SEI decomposition, anode–electrolyte reactions, and cathode breakdown.
- **Total heat release**: Integrated thermal energy output from onset to completion of thermal runaway.
- **Multi-chemistry comparison**: Parallel ARC data for NMC, NCA, and LFP in the same 21700 form factor enables direct thermal safety ranking.
- **Adiabatic thermal runaway trajectory**: Full temperature evolution under worst-case (no cooling) conditions.

## 3. Potential Future Tasks Supported

- **Chemistry safety ranking**: Quantitative comparison of thermal stability across cathode chemistries for cell selection.
- **Thermal model parameterization**: ARC-derived reaction kinetics (Arrhenius parameters) for coupled thermal-electrochemical models.
- **Battery safety certification support**: ARC data is a standard input for UN 38.3 and IEC 62660-3 safety evaluations.
- **Digital twin safety envelope**: Defining temperature-based safety boundaries and triggering conditions in battery management systems.
- **Second-life screening**: Using thermal stability metrics to assess aged cells for repurposing suitability.

## 4. Unified Fields Currently Missing

| Required Field | Status | Notes |
|---------------|--------|-------|
| `cycle_index` | N/A | Single destructive test |
| `capacity_ah` | N/A | Cell destroyed during ARC test |
| `voltage_v` / `current_a` | N/A | No electrical cycling |
| `soh` | N/A | Not applicable |
| `temperature` | Present | Core measurement — high-resolution ARC temperature profile |
| `self_heating_onset_c` | Present (non-standard) | Critical safety parameter, needs schema definition |
| `dt_dt_rate` | Present (non-standard) | Self-heating rate, needs schema definition |
| `total_heat_release_j` | Derivable | Can be calculated from ARC profile if cell mass/Cp known |
