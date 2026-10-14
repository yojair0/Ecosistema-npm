# Profile analysis report

Generated 2026-10-14 15:51. Fan-in measured at 2026-09-18; profile collected around 2026-10-10.

## 1. Population and coverage

| | n | share |
|---|---|---|
| Graph nodes | 4,395,451 | 100% |
| With profile | 4,389,236 | 99.86% |
| Without profile | 6,215 | 0.14% |

Packages with fan_in >= 1,000: 2,117 total, 2,117 (100.0%) with profile.

### Zero grid (all nodes)

| | fan-out = 0 | fan-out > 0 |
|---|---|---|
| fan-in = 0 | 1,511,124 (34.4%) | 2,161,405 (49.2%) |
| fan-in > 0 | 194,161 (4.4%) | 528,761 (12.0%) |

## 2. Descriptive statistics (packages with profile)

Statistics use only the values present for each variable. `n_null` indicates how many are missing. `pct_zeros` is computed over `n_valid`.

| variable | n_total | n_null | pct_null | n_valid | median | mean | p90 | p99 | max | pct_zeros |
|---|---|---|---|---|---|---|---|---|---|---|
| fan_in | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 3.72 | 1.00 | 18.00 | 195,952.00 | 83.55% |
| fan_out | 4,389,236 | 0 | 0.00% | 4,389,236 | 1.00 | 4.51 | 9.00 | 42.00 | 1,000.00 | 38.77% |
| fan_in_dev | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 5.51 | 0.00 | 8.00 | 1,224,874.00 | 94.53% |
| fan_out_dev | 4,389,236 | 0 | 0.00% | 4,389,236 | 1.00 | 5.54 | 16.00 | 45.00 | 881.00 | 45.06% |
| fan_in_peer | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 0.51 | 0.00 | 2.00 | 362,264.00 | 97.73% |
| fan_out_peer | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 0.51 | 2.00 | 7.00 | 708.00 | 80.21% |
| fan_in_opt | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 0.03 | 0.00 | 1.00 | 30,273.00 | 98.69% |
| fan_out_opt | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 0.03 | 0.00 | 1.00 | 106.00 | 98.51% |
| age_days | 4,389,236 | 4,395 | 0.10% | 4,384,841 | 1,298.00 | 1,585.18 | 3,438.00 | 4,697.00 | 20,714.00 | 0.11% |
| days_since_mod | 4,389,236 | 0 | 0.00% | 4,389,236 | 949.00 | 954.18 | 1,625.00 | 1,649.00 | 4,161.00 | 0.43% |
| n_versions | 4,389,236 | 0 | 0.00% | 4,389,236 | 3.00 | 16.88 | 23.00 | 241.00 | 37,328.00 | 0.00% |
| n_maintainers | 4,389,236 | 0 | 0.00% | 4,389,236 | 1.00 | 1.48 | 2.00 | 10.00 | 754.00 | 2.83% |
| n_keywords | 4,389,236 | 0 | 0.00% | 4,389,236 | 0.00 | 2.86 | 7.00 | 17.00 | 1,939.00 | 51.47% |
| file_count | 4,389,236 | 487,455 | 11.11% | 3,901,781 | 9.00 | 72.91 | 74.00 | 987.00 | 64,887.00 | 0.00% |
| unpacked | 4,389,236 | 487,455 | 11.11% | 3,901,781 | 32,654.00 | 2,202,977.41 | 1,506,925.00 | 48,555,115.60 | 5,963,579,668.00 | 0.00% |

| variable | n_total | n_null | n_valid | n_true | pct_true |
|---|---|---|---|---|---|
| deprecated | 4,389,236 | 0 | 4,389,236 | 136,070 | 3.10% |
| has_github | 4,389,236 | 0 | 4,389,236 | 2,638,061 | 60.10% |
| scoped | 4,389,236 | 0 | 4,389,236 | 1,690,379 | 38.51% |

## 3. Variables by fan-in

### 3a. Profile by fan-in range

| tramo | n | fan_out | fan_in_dev | fan_out_dev | fan_in_peer | fan_out_peer | fan_in_opt | fan_out_opt | age_days | days_since_mod | n_versions | n_maintainers | n_keywords | file_count | unpacked | deprecated | has_github | scoped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 3,667,034 | 1.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,257.00 | 986.00 | 2.00 | 1.00 | 0.00 | 9.00 | 29,348.00 | 2.81% | 58.31% | 35.18% |
| 1–9 | 650,113 | 2.00 | 0.00 | 3.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,579.00 | 900.00 | 6.00 | 1.00 | 0.00 | 13.00 | 45,453.50 | 4.50% | 67.27% | 56.58% |
| 10–99 | 58,626 | 2.00 | 1.00 | 3.00 | 0.00 | 0.00 | 0.00 | 0.00 | 2,332.00 | 716.00 | 18.00 | 1.00 | 2.00 | 15.00 | 57,143.50 | 5.15% | 84.52% | 48.65% |
| 100–999 | 11,346 | 2.00 | 15.00 | 4.00 | 1.00 | 0.00 | 0.00 | 0.00 | 2,780.00 | 886.00 | 18.00 | 1.00 | 3.00 | 11.00 | 38,528.00 | 4.91% | 96.75% | 29.44% |
| ≥ 1000 | 2,117 | 2.00 | 239.00 | 6.00 | 16.00 | 0.00 | 1.00 | 0.00 | 3,747.50 | 517.00 | 32.00 | 1.00 | 3.00 | 13.00 | 52,637.00 | 3.40% | 98.21% | 20.12% |

Total across tramos: 4,389,236 (expected 4,389,236).

### 3b. Share with value > 0 for zero-heavy variables

| tramo | n | fan_in_dev_pct_pos | fan_in_peer_pct_pos | fan_in_opt_pct_pos | fan_out_peer_pct_pos | fan_out_opt_pct_pos | n_keywords_pct_pos |
|---|---|---|---|---|---|---|---|
| 0 | 3,667,034 | 3.01% | 1.12% | 1.24% | 19.57% | 1.61% | 48.04% |
| 1–9 | 650,113 | 13.70% | 5.43% | 0.96% | 20.59% | 0.90% | 49.89% |
| 10–99 | 58,626 | 53.11% | 27.03% | 3.90% | 24.02% | 1.04% | 60.02% |
| 100–999 | 11,346 | 69.09% | 52.34% | 18.83% | 21.74% | 1.33% | 65.40% |
| ≥ 1000 | 2,117 | 78.37% | 74.68% | 52.48% | 21.97% | 1.65% | 68.21% |

### 3c. Spearman with fan-in

| variable | rho_all | n_all | rho_fan_in_pos | n_fan_in_pos |
|---|---|---|---|---|
| fan_out | +0.102 | 4,389,236 | +0.082 | 722,202 |
| fan_in_dev | +0.265 | 4,389,236 | +0.315 | 722,202 |
| n_versions | +0.249 | 4,389,236 | +0.189 | 722,202 |
| fan_in_peer | +0.191 | 4,389,236 | +0.234 | 722,202 |
| n_maintainers | +0.176 | 4,389,236 | +0.125 | 722,202 |
| scoped | +0.152 | 4,389,236 | -0.038 | 722,202 |
| file_count | +0.124 | 3,901,781 | +0.103 | 631,590 |
| fan_out_dev | +0.088 | 4,389,236 | +0.070 | 722,202 |
| has_github | +0.087 | 4,389,236 | +0.125 | 722,202 |
| unpacked | +0.083 | 3,901,781 | +0.057 | 631,590 |
| age_days | +0.081 | 4,384,841 | +0.100 | 721,672 |
| days_since_mod | -0.076 | 4,389,236 | -0.117 | 722,202 |
| deprecated | +0.037 | 4,389,236 | +0.002 | 722,202 |
| n_keywords | +0.023 | 4,389,236 | +0.056 | 722,202 |
| fan_out_opt | -0.021 | 4,389,236 | +0.003 | 722,202 |
| fan_in_opt | +0.016 | 4,389,236 | +0.080 | 722,202 |
| fan_out_peer | +0.010 | 4,389,236 | -0.004 | 722,202 |

## 4. Variables by fan-out

### 4a. Profile by fan-out range

| tramo | n | fan_in | fan_in_dev | fan_out_dev | fan_in_peer | fan_out_peer | fan_in_opt | fan_out_opt | age_days | days_since_mod | n_versions | n_maintainers | n_keywords | file_count | unpacked | deprecated | has_github | scoped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1,701,668 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,304.00 | 1,128.00 | 2.00 | 1.00 | 0.00 | 6.00 | 13,535.00 | 2.75% | 58.63% | 35.57% |
| 1–2 | 1,237,299 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,338.00 | 933.00 | 3.00 | 1.00 | 0.00 | 9.00 | 29,160.00 | 3.41% | 59.78% | 40.60% |
| 3–9 | 1,054,516 | 0.00 | 0.00 | 4.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,353.00 | 943.00 | 4.00 | 1.00 | 1.00 | 14.00 | 54,902.00 | 3.36% | 62.42% | 40.76% |
| 10–49 | 360,215 | 0.00 | 0.00 | 6.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1,083.00 | 887.00 | 4.00 | 1.00 | 0.00 | 25.00 | 153,810.50 | 3.10% | 59.46% | 40.29% |
| ≥ 50 | 35,538 | 0.00 | 0.00 | 7.00 | 0.00 | 1.00 | 0.00 | 0.00 | 906.00 | 925.00 | 1.00 | 1.00 | 4.00 | 20.00 | 35,749.00 | 1.44% | 79.48% | 21.82% |

Total across tramos: 4,389,236 (expected 4,389,236).

### 4b. Share with value > 0 for zero-heavy variables

| tramo | n | fan_in_pct_pos | fan_in_dev_pct_pos | fan_in_peer_pct_pos | fan_in_opt_pct_pos | fan_out_peer_pct_pos | fan_out_opt_pct_pos | n_keywords_pct_pos |
|---|---|---|---|---|---|---|---|---|
| 0 | 1,701,668 | 11.40% | 4.56% | 2.02% | 2.95% | 17.00% | 2.35% | 46.65% |
| 1–2 | 1,237,299 | 19.01% | 5.72% | 2.56% | 0.28% | 23.79% | 0.51% | 49.41% |
| 3–9 | 1,054,516 | 20.46% | 6.32% | 2.25% | 0.27% | 18.71% | 0.94% | 51.44% |
| 10–49 | 360,215 | 20.12% | 6.55% | 2.57% | 0.21% | 19.25% | 2.03% | 44.45% |
| ≥ 50 | 35,538 | 13.28% | 3.94% | 1.59% | 0.09% | 51.89% | 5.98% | 62.43% |

### 4c. Spearman with fan-out

| variable | rho_all | n_all | rho_fan_out_pos | n_fan_out_pos |
|---|---|---|---|---|
| fan_in | +0.102 | 4,389,236 | +0.019 | 2,687,568 |
| file_count | +0.353 | 3,901,781 | +0.257 | 2,393,269 |
| fan_out_dev | +0.296 | 4,389,236 | +0.203 | 2,687,568 |
| unpacked | +0.272 | 3,901,781 | +0.218 | 2,393,269 |
| n_versions | +0.179 | 4,389,236 | +0.077 | 2,687,568 |
| n_maintainers | +0.161 | 4,389,236 | +0.035 | 2,687,568 |
| fan_in_opt | -0.101 | 4,389,236 | -0.003 | 2,687,568 |
| scoped | +0.040 | 4,389,236 | -0.006 | 2,687,568 |
| n_keywords | +0.039 | 4,389,236 | +0.013 | 2,687,568 |
| fan_out_peer | +0.037 | 4,389,236 | -0.039 | 2,687,568 |
| age_days | +0.034 | 4,384,841 | -0.006 | 2,685,616 |
| fan_in_dev | +0.033 | 4,389,236 | +0.014 | 2,687,568 |
| fan_out_opt | -0.031 | 4,389,236 | +0.059 | 2,687,568 |
| has_github | +0.029 | 4,389,236 | +0.021 | 2,687,568 |
| deprecated | +0.012 | 4,389,236 | -0.006 | 2,687,568 |
| fan_in_peer | +0.009 | 4,389,236 | -0.007 | 2,687,568 |
| days_since_mod | +0.000 | 4,389,236 | +0.001 | 2,687,568 |

## 5. Variables en el grupo con ambas conexiones (fan_in > 0 y fan_out > 0)

Paquetes con fan_in > 0 **y** fan_out > 0: **528,170** (12.0% del universo con perfil).

| variable | rho_fan_in | rho_fan_out | n |
|---|---|---|---|
| fan_in_dev | +0.2998 | +0.0006 | 528,170 |
| file_count | +0.0874 | +0.2532 | 469,816 |
| unpacked | +0.0493 | +0.2329 | 469,816 |
| fan_in_peer | +0.2295 | +0.0053 | 528,170 |
| fan_out_dev | +0.0622 | +0.1913 | 528,170 |
| n_versions | +0.1714 | +0.1077 | 528,170 |
| fan_in_opt | +0.1319 | -0.0023 | 528,170 |
| n_maintainers | +0.1279 | +0.0871 | 528,170 |
| days_since_mod | -0.1236 | -0.0377 | 528,170 |
| has_github | +0.1101 | -0.0170 | 528,170 |
| age_days | +0.0782 | -0.0394 | 527,825 |
| fan_out_opt | +0.0052 | +0.0455 | 528,170 |
| n_keywords | +0.0452 | -0.0301 | 528,170 |
| scoped | -0.0300 | -0.0135 | 528,170 |
| fan_out_peer | +0.0015 | +0.0195 | 528,170 |
| deprecated | +0.0024 | -0.0191 | 528,170 |
| fan_in ~ fan_out | +0.1192 | +0.1192 | 528,170 |

## 6. Edad y cohortes

### 6a. Por año de creación

Paquetes con fecha de creación posterior al snapshot (2026-09-18) aparecen en el año 2026, no en 'sin fecha'.

| year | n | pct_fi_pos | median_fi_pos | median_fo | pct_fo_zero | pct_one_version | pct_github | pct_scoped |
|---|---|---|---|---|---|---|---|---|
| 1970 | 1 | 100.0% | 5.0 | 0.0 | 100.0% | 0.0% | 100.0% | 0.0% |
| 2010 | 107 | 71.0% | 27.0 | 1.0 | 45.8% | 3.7% | 90.7% | 0.0% |
| 2011 | 4,985 | 49.1% | 5.0 | 1.0 | 41.5% | 20.0% | 82.3% | 0.0% |
| 2012 | 13,261 | 39.7% | 3.0 | 1.0 | 35.5% | 23.9% | 83.3% | 0.0% |
| 2013 | 31,683 | 35.5% | 2.0 | 1.0 | 34.5% | 24.1% | 85.7% | 0.0% |
| 2014 | 61,493 | 31.1% | 2.0 | 1.0 | 33.1% | 23.7% | 85.6% | 0.0% |
| 2015 | 103,962 | 27.5% | 2.0 | 1.0 | 34.6% | 25.1% | 83.3% | 2.5% |
| 2016 | 164,819 | 22.1% | 2.0 | 1.0 | 40.1% | 27.7% | 73.8% | 8.9% |
| 2017 | 204,505 | 19.8% | 2.0 | 1.0 | 38.5% | 27.5% | 68.8% | 14.2% |
| 2018 | 247,888 | 18.6% | 2.0 | 1.0 | 36.4% | 26.9% | 61.7% | 26.6% |
| 2019 | 281,559 | 17.6% | 1.0 | 1.0 | 36.5% | 27.6% | 55.8% | 36.6% |
| 2020 | 297,169 | 17.0% | 1.0 | 1.0 | 37.0% | 27.3% | 55.4% | 39.7% |
| 2021 | 343,242 | 17.2% | 1.0 | 1.0 | 40.0% | 34.6% | 50.1% | 40.8% |
| 2022 | 376,351 | 15.3% | 1.0 | 1.0 | 44.0% | 32.3% | 53.7% | 48.8% |
| 2023 | 380,193 | 14.9% | 1.0 | 1.0 | 44.1% | 36.7% | 43.9% | 42.5% |
| 2024 | 707,057 | 12.4% | 2.0 | 2.0 | 23.7% | 64.6% | 59.1% | 28.6% |
| 2025 | 465,790 | 11.7% | 1.0 | 1.0 | 49.6% | 42.9% | 61.0% | 42.7% |
| 2026 | 705,168 | 16.6% | 1.0 | 1.0 | 44.0% | 29.8% | 67.5% | 66.7% |
| sin fecha | 3 | 100.0% | 366.0 | 2.0 | 33.3% | 0.0% | 100.0% | 0.0% |

### 6b. Ventana de 365 días

| group | n | pct_fi_pos | median_fi_pos | median_fo | pct_fo_zero | pct_one_version | pct_github | pct_scoped |
|---|---|---|---|---|---|---|---|---|
| ≥ 365 días | 3,485,940 | 16.9% | 1.0 | 1.0 | 36.3% | 37.4% | 57.8% | 33.0% |
| < 365 días | 898,901 | 14.8% | 1.0 | 1.0 | 48.2% | 35.8% | 69.2% | 59.7% |
| sin edad | 4,395 | 12.1% | 1.0 | 0.0 | 55.6% | 44.6% | 77.8% | 59.2% |

## 7. Perfil por rangos (deciles con grupo de moda aparte)

El grupo de la moda se separa antes de calcular los deciles. Cortes duplicados se descartan (`duplicates='drop'`). Para `n_maintainers` se separa además el grupo con valor 0.

### n_versions (mode = 1, n_mode = 1,625,981)

| range | n | median_fan_in | pct_fi_pos | median_fan_in_pos | median_fan_out | pct_fo_zero |
|---|---|---|---|---|---|---|
| mode = 1 | 1,625,981 | 0 | 7.6% | 1 | 1 | 47.4% |
| (1.999, 3.0] | 891,761 | 0 | 14.4% | 1 | 1 | 41.4% |
| (3.0, 4.0] | 253,104 | 0 | 16.6% | 1 | 1 | 36.4% |
| (4.0, 6.0] | 348,259 | 0 | 18.0% | 1 | 1 | 34.8% |
| (6.0, 8.0] | 230,465 | 0 | 20.2% | 1 | 1 | 33.5% |
| (8.0, 11.0] | 222,688 | 0 | 22.1% | 1 | 2 | 31.0% |
| (11.0, 18.0] | 277,307 | 0 | 25.5% | 2 | 2 | 28.3% |
| (18.0, 38.0] | 266,429 | 0 | 30.8% | 2 | 2 | 25.9% |
| (38.0, 37328.0] | 273,242 | 0 | 42.9% | 2 | 3 | 20.3% |

### n_maintainers (mode = 1, n_mode = 3,727,480)

| range | n | median_fan_in | pct_fi_pos | median_fan_in_pos | median_fan_out | pct_fo_zero |
|---|---|---|---|---|---|---|
| = 0 | 124,091 | 0 | 0.6% | 3 | 0 | 99.9% |
| mode = 1 | 3,727,480 | 0 | 14.7% | 1 | 1 | 38.4% |
| (1.999, 3.0] | 318,028 | 0 | 31.0% | 2 | 2 | 29.9% |
| (3.0, 4.0] | 67,185 | 0 | 33.4% | 2 | 2 | 23.4% |
| (4.0, 6.0] | 67,921 | 0 | 34.4% | 2 | 2 | 23.1% |
| (6.0, 9.0] | 34,342 | 0 | 38.0% | 2 | 2 | 23.3% |
| (9.0, 754.0] | 50,189 | 0 | 31.2% | 2 | 1 | 20.4% |

### n_keywords (mode = 0, n_mode = 2,259,202)

| range | n | median_fan_in | pct_fi_pos | median_fan_in_pos | median_fan_out | pct_fo_zero |
|---|---|---|---|---|---|---|
| mode = 0 | 2,259,202 | 0 | 15.7% | 1 | 1 | 40.2% |
| (0.999, 2.0] | 438,339 | 0 | 17.1% | 1 | 1 | 40.1% |
| (2.0, 3.0] | 301,095 | 0 | 17.8% | 1 | 1 | 38.0% |
| (3.0, 4.0] | 297,467 | 0 | 18.5% | 2 | 1 | 37.3% |
| (4.0, 5.0] | 279,621 | 0 | 17.0% | 1 | 1 | 41.0% |
| (5.0, 6.0] | 232,471 | 0 | 15.3% | 1 | 1 | 35.7% |
| (6.0, 8.0] | 262,821 | 0 | 16.3% | 1 | 1 | 33.5% |
| (8.0, 10.0] | 143,918 | 0 | 16.7% | 2 | 2 | 31.4% |
| (10.0, 1939.0] | 174,302 | 0 | 20.0% | 2 | 1 | 35.3% |

## 8. Variables binarias

| group | value | n | median_fan_in | pct_fi_pos | median_fan_in_pos | median_fan_out | pct_fo_zero |
|---|---|---|---|---|---|---|---|
| scoped | yes | 1,690,379 | 0 | 23.7% | 1 | 1 | 35.8% |
| scoped | no | 2,698,857 | 0 | 11.9% | 1 | 1 | 40.6% |
| deprecated | yes | 136,070 | 0 | 24.2% | 1 | 1 | 34.4% |
| deprecated | no | 4,253,166 | 0 | 16.2% | 1 | 1 | 38.9% |
| has_github | yes | 2,638,061 | 0 | 19.0% | 2 | 1 | 37.8% |
| has_github | no | 1,751,175 | 0 | 12.7% | 1 | 1 | 40.2% |
| has_keywords | yes | 2,130,034 | 0 | 17.3% | 2 | 1 | 37.3% |
| has_keywords | no | 2,259,202 | 0 | 15.7% | 1 | 1 | 40.2% |

## 9. Atípicos (solo descriptivo, no se eliminan paquetes)

Paquetes con fecha de creación posterior al snapshot (2026-09-18): **4,392** (aparecen en el año 2026 de la tabla §6a; `age_days = NaN`).

Paquetes con año de creación anterior a 2009: **1** (npm se publicó en enero 2010; años anteriores son artefactos).

Año mínimo encontrado: **1970** (artefacto Unix epoch).

| año | n |
|---|---|
| 1970 | 1 |

### Conteo por encima del percentil 99.9

| variable | p99.9 | n_above |
|---|---|---|
| fan_in | 471.0 | 4,382 |
| fan_out | 371.0 | 2,055 |
| fan_in_dev | 238.0 | 4,389 |
| fan_out_dev | 79.0 | 4,269 |
| fan_in_peer | 26.0 | 4,292 |
| fan_out_peer | 18.0 | 4,364 |
| fan_in_opt | 2.0 | 3,357 |
| fan_out_opt | 6.0 | 3,548 |
| age_days | 5,409.0 | 4,380 |
| days_since_mod | 1,649.0 | 1,820 |
| n_versions | 1,469.0 | 4,374 |
| n_maintainers | 33.0 | 3,994 |
| n_keywords | 50.0 | 4,355 |
| file_count | 7,975.9 | 3,902 |
| unpacked | 233,714,328.4 | 3,902 |

### Top 10 por variable numérica

**fan_in**

| name | fan_in |
|---|---|
| react | 195,952 |
| react-dom | 160,333 |
| lodash | 155,784 |
| axios | 155,552 |
| chalk | 152,943 |
| commander | 143,651 |
| tslib | 123,629 |
| zod | 119,005 |
| inquirer | 101,485 |
| express | 96,427 |

**fan_out**

| name | fan_out |
|---|---|
| 1000-packages | 1,000 |
| potionseller | 1,000 |
| sindresorhus.js | 1,000 |
| bloater | 998 |
| tldrawlignin | 985 |
| airplane-later-toy | 980 |
| atmosphere-lady-alphabet | 979 |
| length-settle-limited | 979 |
| pan-impossible-tales | 978 |
| chosen-community-inch7 | 977 |

**fan_in_dev**

| name | fan_in_dev |
|---|---|
| typescript | 1,224,874 |
| @types/node | 743,028 |
| eslint | 685,791 |
| prettier | 378,636 |
| jest | 333,539 |
| @types/react | 330,574 |
| react | 259,123 |
| mocha | 259,020 |
| vitest | 246,741 |
| @types/jest | 244,386 |

**fan_out_dev**

| name | fan_out_dev |
|---|---|
| @weareglow/story-unit | 881 |
| @vuga/react-demo | 847 |
| booking_calendar | 687 |
| yuanquanke-js-utils | 597 |
| bubanai-ng | 591 |
| @thewillhuang/react-org-chart | 554 |
| wide-smile | 538 |
| cordova-plugin-amplify-pay | 488 |
| cordova-plugin-amplify-payment | 488 |
| aws-sdk-js-v3-all | 451 |

**fan_in_peer**

| name | fan_in_peer |
|---|---|
| react | 362,264 |
| react-dom | 214,495 |
| @angular/core | 71,702 |
| @angular/common | 65,272 |
| vue | 47,183 |
| react-native | 46,404 |
| typescript | 30,953 |
| eslint | 25,764 |
| rxjs | 23,389 |
| styled-components | 16,708 |

**fan_out_peer**

| name | fan_out_peer |
|---|---|
| @teatime-code/ckeditor4-dev | 708 |
| @herefishyfish/nativescript-rxdb | 311 |
| @hongtangyun/react-native-mini-apps-engines | 229 |
| @aws-cdk/cloudformation-include | 220 |
| @mhy/config | 201 |
| @capawesome/capacitor-react-hooks | 191 |
| @next-levels/next-framework | 139 |
| volto-mosaic | 132 |
| @chromia/community | 129 |
| @libs-ui/exports | 129 |

**fan_in_opt**

| name | fan_in_opt |
|---|---|
| @types/hyper-function-component | 30,273 |
| fsevents | 3,655 |
| @rollup/rollup-linux-x64-gnu | 809 |
| better-sqlite3 | 727 |
| bufferutil | 676 |
| utf-8-validate | 569 |
| node-pty | 525 |
| react | 486 |
| sharp | 482 |
| pg | 437 |

**fan_out_opt**

| name | fan_out_opt |
|---|---|
| werkforce | 106 |
| @framers/agentos-extensions-registry | 103 |
| react-garden | 88 |
| openclaw | 79 |
| @songtonyli/dsh-cli | 76 |
| @v4fire/client | 72 |
| bio-scaffold-wdui | 66 |
| @holoscript/mesh | 55 |
| skyglass-cli | 54 |
| sprout-web-ui | 49 |

**age_days**

| name | age_days |
|---|---|
| tld | 20,714 |
| monomi | 5,790 |
| jison | 5,752 |
| nack | 5,752 |
| neko | 5,752 |
| recon | 5,752 |
| strftime | 5,752 |
| async | 5,751 |
| bitcoin | 5,751 |
| canvas | 5,751 |

**days_since_mod**

| name | days_since_mod |
|---|---|
| zachtestproject2 | 4,161 |
| zachtestproject3 | 4,161 |
| zachtestproject4 | 4,161 |
| testx2 | 3,846 |
| react-swipeable-clicked-bottom-sheet | 2,977 |
| cra-template-heretical | 2,427 |
| loyash | 1,942 |
| dhilip-package1 | 1,698 |
| @6blackbjorn/react-hr-component | 1,654 |
| @aaroncheung430/pcsclite | 1,654 |

**n_versions**

| name | n_versions |
|---|---|
| electron-remote-control | 37,328 |
| @npm-torg/public-scoped-free-org-test-package-2 | 37,301 |
| @octopusdeploy/type-utils | 33,966 |
| @octopusdeploy/design-system-components | 33,908 |
| @octopusdeploy/design-system-tokens | 29,390 |
| public-unscoped-test-package | 28,041 |
| carrot-scan | 27,708 |
| @npm-torg/public-test-package-2 | 27,618 |
| @adguard/dnr-rulesets | 22,204 |
| @mahdiarjangi/phetch-cli | 19,498 |

**n_maintainers**

| name | n_maintainers |
|---|---|
| @bbc/apache2-license-checker | 754 |
| @bbc/consumer-contracts | 754 |
| @bbc/http-transport-xray | 754 |
| @bbc/ibl-graph-fallbacks-key-generator | 754 |
| dependency-manifest-webpack-plugin | 622 |
| @ramp/kritkit | 549 |
| @vercel/global-config-fs | 420 |
| @bbc/tv-lrud-spatial | 407 |
| @vercel/ai-sdk-openai-websocket-fetch | 385 |
| @vercel/next-browser | 385 |

**n_keywords**

| name | n_keywords |
|---|---|
| coinpayments | 1,939 |
| iflow-mcp-sixhq-overture | 999 |
| overture-mcp | 999 |
| openvisio | 850 |
| @ryniaubenpm/quibusdam-harum-repudiandae | 796 |
| @ryniaubenpm/exercitationem-veritatis-quo | 794 |
| @ryniaubenpm2/exercitationem-molestias-temporibus | 794 |
| teachable-machine.js | 792 |
| @ryniaubenpm/ab-quisquam-at | 787 |
| @asdfgertyjhnpm/ipsam-illum-quidem | 781 |

**file_count**

| name | file_count |
|---|---|
| definitely-typed-koa-webpack-alt | 64,887 |
| chealth | 64,766 |
| @wirechunk/material-symbols-react-200 | 64,443 |
| @wirechunk/material-symbols-react-300 | 64,443 |
| @wirechunk/material-symbols-react-400 | 64,443 |
| @wirechunk/material-symbols-react-500 | 64,443 |
| @wirechunk/material-symbols-react-600 | 64,443 |
| abiweb3.js | 63,779 |
| @wunk/lb-script-api-types | 63,589 |
| @omerrj/phosphor-react-native | 63,519 |

**unpacked**

| name | unpacked |
|---|---|
| @chainsafe/eth2-spec-tests | 5,963,579,668 |
| modez | 4,397,802,621 |
| @mpetrunic/eth2-spec-tests | 4,133,982,179 |
| similar-persian-words | 3,045,825,802 |
| basic-react-steps | 1,703,354,873 |
| @kunal-mohta/duckdb-wasm | 1,695,566,406 |
| @proofofplay/erc721-extensions | 1,370,611,604 |
| docer-outdated_documentation- | 1,332,044,040 |
| roninjin10 | 1,327,328,123 |
| murmur-bloomfilter | 1,314,249,792 |

### Distribución mensual de la fecha de última modificación

Abril y junio de 2022 muestran conteos anómalos por actualizaciones masivas de metadata no relacionadas con cambios reales. **`days_since_mod` no es un indicador fiable de recencia.**

| month | n |
|---|---|
| 2022-05 | 589,051 |
| 2022-06 | 520,160 |
| 2022-04 | 469,072 |
| 2026-09 | 178,578 |
| 2024-05 | 155,281 |
| 2026-08 | 137,876 |
| 2026-10 | 137,482 |
| 2026-07 | 120,927 |
| 2025-11 | 115,397 |
| 2024-06 | 98,659 |
| 2026-06 | 97,903 |
| 2026-03 | 88,544 |
| 2026-05 | 87,328 |
| 2026-04 | 82,844 |
| 2024-04 | 80,431 |
| 2024-03 | 78,239 |
| 2024-07 | 72,656 |
| 2026-02 | 62,610 |
| 2022-08 | 56,741 |
| 2025-12 | 51,289 |

