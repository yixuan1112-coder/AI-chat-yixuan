# Dataset 05: RWTH Aachen — Dataset Note (EN)

## Basic Information

| Field | Value |
|-------|-------|
| Dataset ID | dataset_05 |
| Short Name | RWTH |
| Full Title | Time-series cyclic aging data on 48 commercial NMC/graphite Sanyo/Panasonic UR18650E cylindrical cells |
| Institution | ISEA, RWTH Aachen University, Germany |
| Year | 2021 |
| DOI | 10.18154/RWTH-2021-04545 |
| License | CC BY 4.0 |
| Paper | Li et al., "One-shot battery degradation trajectory prediction with deep learning", *Journal of Power Sources*, 506, 230024 (2021) |

## Cell Specifications

| Field | Value |
|-------|-------|
| Cell Model | Sanyo/Panasonic UR18650E |
| Form Factor | 18650 Cylindrical |
| Cathode | NMC (Nickel Manganese Cobalt Oxide) |
| Anode | Carbon (Graphite) |
| Nominal Capacity | 2.05 Ah (A-grade); ~1.85 Ah (grade C batch used) |
| Number of Cells | 48 |
| Manufacturer Grade | Grade C (same production lot) |

## Test Conditions

| Field | Value |
|-------|-------|
| Temperature | 25°C (constant ambient) |
| Cycling Protocol | CC discharge to 3.5V / CC charge to 3.9V, max 4A, 30 min each |
| Charge Turnover | ~1 Ah per cycle (~20%–80% SOC range) |
| RPT Intervals | Periodic capacity tests and pulse resistance at 25°C |
| RPT Voltage Window | 3.0V – 4.1V (wider than cycling window) |
| RPT Metric | 2A discharge capacity |
| BOL Test | Pulse resistance, capacity at multiple C-rates, impedance at 3 temperatures × 3 voltage levels |

## Data Format

- **Raw format**: CSV (one file per cell)
- **Columns**: time (s), current (A), voltage (V), temperature (°C)
- **Size**: ~48 files, total several hundred MB

## Processing Notes

1. **Current sign convention**: Verify per-file. Some cells may have positive = discharge. The ETL script auto-detects via voltage-current correlation.
2. **RPT filtering**: RPT cycles are identified by voltage windows exceeding normal cycling range (V > 4.0V or V < 3.2V) and flagged in cycle_summary.
3. **SOH calculation**: SOH = Q_discharge(cycle_n) / Q_discharge(cycle_1), using first non-RPT cycle as reference.
4. **Cycle detection**: A new cycle begins at each discharge onset (current transitions from positive/rest to negative).
5. **Grade C cells**: The actual capacity (~1.85 Ah) is lower than A-grade nominal (2.05 Ah) due to manufacturer grading; all cells are from the same production lot, ensuring consistency.

## Key Characteristics

- All 48 cells share the **identical** cycling protocol and temperature — this dataset is specifically designed for studying **cell-to-cell variability** in a controlled setting.
- The partial-cycle protocol (3.5V–3.9V, ~20%–80% SOC) is motivated by real-world operating regimes where voltage limits constrain usage.
- Charge turnover varies slightly with aging (resistance increase), but DOD relative to aged capacity remains nearly constant.

## Known Issues / Caveats

- Test batches started at slightly staggered times (2–3 days apart) due to equipment limitations.
- RPT cycles are interleaved with regular cycling and must be separated during analysis.
- No impedance data in periodic RPT (only in BOL test).

## BatteryLife Reference

In BatteryLife (Tan et al., KDD 2025), this dataset is identified as "RWTH" with 48 batteries, 1 format, 1 chemical system, 1 temperature, 1 protocol.
