# Dataset 04: Oxford Battery Degradation – Dataset Note

## Overview

The Oxford Battery Degradation dataset originates from the Battery Intelligence Lab at the University of Oxford. It comprises two sub-datasets:

1. **Kokam LCO Pouch Cells** (Dataset 1): Long-term aging data for 8 Kokam SLPB533459H4 (740 mAh) lithium cobalt oxide pouch cells.
2. **NCA 18650 Path Dependent** (Part 1): Path-dependent aging data for 12 Panasonic NCR18650BD (3 Ah) nickel cobalt aluminium oxide cylindrical cells.

## Sub-dataset A: Kokam LCO Pouch Cells

| Item | Details |
|------|---------|
| Number of cells | 8 |
| Model | Kokam SLPB533459H4 |
| Chemistry | LCO (LiCoO₂) cathode / graphite anode |
| Form factor | Pouch |
| Nominal capacity | 740 mAh (0.740 Ah) |
| Temperature | 40°C |
| Cycling protocol | Artemis Urban drive cycle discharge + 2C CC charge |
| Characterization | 1C charge/discharge + pseudo-OCV every 100 drive cycles |
| Equipment | Bio-Logic MPG-205, 8-channel |
| Data format | .mat (MATLAB binary, 4-layer nested structure) |
| License | ODbL 1.0 |

### Data Structure

```
Layer 1: Cell (1-8)
  └─ Layer 2: Characterization cycle ID (cyc0100, cyc0200, ...)
       └─ Layer 3: C1ch (1C charge), C1dc (1C discharge), OCVch, OCVdc
            └─ Layer 4: t (seconds), v (Volts), q (mAh), T (°C)
```

### Key Notes

- **Characterization data only**: The actual Artemis Urban drive cycle data is not included in the published dataset.
- **Unit conversion required**: The charge field (q) is in mAh; must be converted to Ah for standardized output.
- The cycle_number in cycle_summary corresponds to the number of completed drive cycles (e.g., 100, 200, ...), not the index of characterization events.

## Sub-dataset B: NCA 18650 Path Dependent

| Item | Details |
|------|---------|
| Number of cells | 12 (4 groups × 3 cells) |
| Model | Panasonic NCR18650BD |
| Chemistry | NCA (LiNiCoAlO₂) cathode / graphite anode |
| Form factor | 18650 cylindrical |
| Nominal capacity | 3 Ah |
| Temperature | 24°C |
| Data format | .mat |
| License | ODbL 1.0 |

### Experimental Groups

| Group | Cycling Protocol | Calendar Aging |
|-------|-----------------|----------------|
| Group 1 | 1 day CC cycling at C/2 | 5 days at 90% SoC |
| Group 2 | 1 day CC cycling at C/4 | 5 days at 90% SoC |
| Group 3 | 2 days CC cycling at C/2 | 10 days at 90% SoC |
| Group 4 | 2 days CC cycling at C/4 | 10 days at 90% SoC |

Reference performance tests (RPT) were conducted every 48 cycles, consisting of CC-CV discharge/charge at C/2 and pseudo-OCV at C/24.

## References

1. Birkl, C.R., Roberts, M.R., McTurk, E., Bruce, P.G. and Howey, D.A. "Degradation diagnostics for lithium ion cells." *Journal of Power Sources*, 341, 2017, pp. 373-386. DOI: 10.1016/j.jpowsour.2016.12.011
2. Raj, T., Wang, A.A., Monroe, C.W. and Howey, D.A. "Investigation of path-dependent degradation in lithium-ion batteries." *Batteries & Supercaps*, 3(12), 2020, pp. 1377-1385. DOI: 10.1002/batt.202000160
