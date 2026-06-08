# Dataset Note: dataset_32 — Li-ion Batteries EIS Measurements

| Field | Value |
|-------|-------|
| **Dataset ID** | dataset_32 |
| **Data Category** | eis |
| **Source** | eet-china collection |
| **URL** | https://figshare.com/articles/dataset/Li-ion_Batteries_EIS_measurements/23736582 |
| **Chemistry** | LFP (600 mAh) |
| **Last Updated** | 2026/3/18 |

---

## 1. Why This Dataset Does Not Belong to the Current Cycle-Aging Mainline

This dataset consists of electrochemical impedance spectroscopy (EIS) frequency sweeps, not charge–discharge cycling records. EIS data is structured as frequency–impedance pairs (Nyquist/Bode format), which fundamentally differs from the voltage–current–time structure of cycling timeseries. No cycle-level capacity or efficiency metrics are provided.

## 2. Physical Information Contained

- **Impedance spectra (Nyquist plots)**: Real and imaginary impedance components across a range of excitation frequencies, encoding internal resistance and charge-transfer behavior.
- **Ohmic resistance (R₀)**: High-frequency intercept reflecting electrolyte and contact resistance.
- **Charge-transfer resistance (Rct)**: Mid-frequency semicircle diameter reflecting electrode kinetics.
- **Warburg diffusion**: Low-frequency tail capturing solid-state ion diffusion limitations.
- **SEI layer characterization**: Impedance features correlate with solid-electrolyte interphase growth.

## 3. Potential Future Tasks Supported

- **Impedance-based SOH diagnostics**: Tracking resistance growth as a non-invasive health indicator.
- **Degradation mechanism identification**: Separating ohmic, kinetic, and diffusion contributions to aging.
- **Rapid screening / quality control**: EIS as a fast diagnostic for cell grading and second-life assessment.
- **Physics-informed model validation**: Calibrating electrochemical models (P2D, SPM) against measured impedance spectra.
- **Multi-modal digital twin**: Fusing EIS snapshots with cycling history for comprehensive state estimation.

## 4. Unified Fields Currently Missing

| Required Field | Status | Notes |
|---------------|--------|-------|
| `cycle_index` | N/A | No cycling data present |
| `capacity_ah` | Missing | No capacity measurements |
| `voltage_v` / `current_a` | N/A | EIS uses AC perturbation, not DC charge/discharge |
| `soh` | Missing | No reference capacity |
| `temperature` | To verify | May be recorded as test condition |
| `frequency_hz` | Present (non-standard) | Core EIS field, not in current BatteryTwin schema |
| `z_real` / `z_imag` | Present (non-standard) | Core EIS field, needs new schema definition |
