# Fan-In counted only with dependents in population A

Generated 2026-11-04 16:41. `fan_in` counts dependents from the whole registry; `fan_in_clean` counts only those in population A.

## With families (population A, fan_in > 0)

- Packages with fan_in > 0: 680.373
- With fan_in_clean = 0 (only excluded packages depend on them): 11.949 (1,8%)
- Change Fan-In band: 14.176 (2,1%)

| Band by fan_in | Packages | Drop to 0 | Change band |
|---|---|---|---|
| 1-9 | 613.461 | 11.497 | 11.497 |
| 10-99 | 55.157 | 198 | 1.764 |
| 100-999 | 9.734 | 246 | 795 |
| 1000+ | 2.021 | 8 | 120 |

## Without families (population B, fan_in > 0)

- Packages with fan_in > 0: 300.348
- With fan_in_clean = 0 (only excluded packages depend on them): 5.279 (1,8%)
- Change Fan-In band: 6.680 (2,2%)

| Band by fan_in | Packages | Drop to 0 | Change band |
|---|---|---|---|
| 1-9 | 263.227 | 4.891 | 4.891 |
| 10-99 | 28.444 | 162 | 1.116 |
| 100-999 | 7.052 | 220 | 595 |
| 1000+ | 1.625 | 6 | 78 |

Check: packages with fan_in_clean > fan_in (should be 0): 0.
