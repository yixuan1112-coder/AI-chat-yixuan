# Dataset Note: dataset_34 — Mechanically Induced Thermal Runaway

| Field | Value |
|-------|-------|
| **Dataset ID** | dataset_34 |
| **Data Category** | thermal_abuse |
| **Source** | eet-china collection |
| **URL** | https://data.mendeley.com/datasets/sn2kv34r4h/2 |
| **Reference** | doi.org/10.1016/j.est.2023.106798 |
| **Last Updated** | 2026/3/18 |

---

## 1. Why This Dataset Does Not Belong to the Current Cycle-Aging Mainline

This dataset records mechanical abuse tests (nail penetration) that deliberately trigger internal short circuits and thermal runaway. The data captures a single destructive event per cell, not repeated charge–discharge cycling. No capacity degradation or aging trajectory is present.

## 2. Physical Information Contained

- **Mechanical failure thresholds**: Force, displacement, and deformation data at the point of internal short circuit initiation.
- **Internal short circuit (ISC) characteristics**: Voltage drop rate and current spike profiles during nail penetration-induced ISC.
- **Thermal response to mechanical abuse**: Temperature evolution from ISC trigger through thermal runaway.
- **Failure mode classification**: Distinguishing between mild ISC (recoverable voltage sag) and catastrophic runaway based on penetration depth and speed.

## 3. Potential Future Tasks Supported

- **Crash safety modeling**: Providing mechanical-to-thermal failure data for EV crash simulation and battery pack design.
- **Abuse tolerance benchmarking**: Quantifying mechanical robustness across cell formats and chemistries.
- **ISC fault injection models**: Using nail penetration data to calibrate internal short circuit models for digital twin safety modules.
- **Early fault detection**: Correlating mechanical deformation signatures with electrical anomalies for real-time BMS fault detection.

## 4. Unified Fields Currently Missing

| Required Field | Status | Notes |
|---------------|--------|-------|
| `cycle_index` | N/A | Single destructive event, no cycling |
| `capacity_ah` | N/A | Cell destroyed during test |
| `soh` | N/A | Not applicable |
| `temperature` | Present | Thermocouple data during abuse event |
| `voltage_v` | Present | Logged until cell failure |
| `force_n` / `displacement_mm` | Present (non-standard) | Mechanical loading data, needs new schema fields |
| `penetration_depth_mm` | Present (non-standard) | Nail penetration parameter, needs schema definition |
| `isc_trigger_time` | Present (non-standard) | Timestamp of internal short circuit onset |
