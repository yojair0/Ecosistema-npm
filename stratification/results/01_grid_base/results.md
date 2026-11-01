# Estratificación por cuadrícula base

## Parámetros

- Semilla: 42
- Mínimo por estrato (sobre B completo): 500
- Mínimo escalado a mitad de ajuste: 250
- Umbral de censo: Fan-In ≥ 1000
- Población B: 2,709,168 paquetes

### Granularidades

- **coarse**: Fan-In [1 a 9, 10 o más] — Fan-Out [1 a 9, 10 o más]
- **medium**: Fan-In [1 a 9, 10 a 99, 100 o más] — Fan-Out [1 a 2, 3 a 9, 10 o más]
- **fine**: Fan-In [1 a 9, 10 a 99, 100 a 999, 1000 o más] — Fan-Out [1 a 2, 3 a 9, 10 a 49, 50 o más]

## Métricas de las 6 configuraciones

| config | K | min_n | n_under_min | r2_log_fi | r2_log_fo | r2_log_n_versions | r2_age | eff_prop_log_fi | eff_neyman_log_fi | eff_prop_log_fo | eff_neyman_log_fo | r2_log_fi_train | r2_log_fi_test | r2_log_fo_train | r2_log_fo_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| coarse_nocensus | 9 | 4.274 | 0 | 0,8539 | 0,8115 | 0,0761 | 0,0496 | 6,8439 | 78,5988 | 5,3051 | 8,597 | 0,8539 | 0,854 | 0,8116 | 0,8115 |
| coarse_census | 10 | 1.625 | 0 | 0,885 | 0,8109 | 0,0764 | 0,0496 | 8,6951 | 89,3832 | 5,2895 | 8,5753 | 0,8849 | 0,8852 | 0,811 | 0,8109 |
| medium_nocensus | 16 | 932 | 0 | 0,912 | 0,9331 | 0,0823 | 0,05 | 11,4309 | 106,5882 | 14,9751 | 28,2262 | 0,9118 | 0,9123 | 0,9331 | 0,9332 |
| medium_census | 17 | 766 | 0 | 0,9201 | 0,9325 | 0,0824 | 0,05 | 12,5449 | 112,372 | 14,8465 | 28,0776 | 0,9199 | 0,9203 | 0,9325 | 0,9326 |
| fine_nocensus | 21 | 580 | 0 | 0,9174 | 0,9462 | 0,0826 | 0,0501 | 12,4368 | 111,0577 | 18,6509 | 32,6862 | 0,9171 | 0,9178 | 0,9462 | 0,9462 |
| fine_census | 20 | 580 | 0 | 0,9199 | 0,9457 | 0,0828 | 0,0501 | 12,5693 | 112,2238 | 18,4725 | 32,5553 | 0,9197 | 0,9201 | 0,9457 | 0,9458 |

## Tabla de estratos por configuración

### coarse_nocensus

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 9 | 1.256.063 | 46,4% | 0 | 1,2575 | 3 | 4,1095 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 10 o más | 198.227 | 7,3% | 0 | 2,9017 | 2 | 3,2936 |
| 3 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 9 | 81.985 | 3,0% | 0,998 | 0 | 4 | 7,9507 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 10 o más | 12.475 | 0,5% | 3,8739 | 0 | 11 | 10,2396 |
| 5 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 1 a 9 | 170.636 | 6,3% | 0,965 | 1,2378 | 5 | 7,2334 |
| 6 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 10 o más | 25.307 | 0,9% | 1,2692 | 2,9489 | 7 | 4,2574 |
| 7 | Con ambas conexiones, Fan-In 10 o más, Fan-Out 1 a 9 | 20.414 | 0,8% | 3,8237 | 1,2655 | 18 | 9,7906 |
| 8 | Con ambas conexiones, Fan-In 10 o más, Fan-Out 10 o más | 4.274 | 0,2% | 3,9066 | 3,1041 | 5 | 2,5708 |

### coarse_census

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Censo (Fan-In 1000 o más) | 1.625 | 0,1% | 7,9043 | 1,025 | 31 | 11,2526 |
| 1 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 9 | 1.256.063 | 46,4% | 0 | 1,2575 | 3 | 4,1095 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 10 o más | 198.227 | 7,3% | 0 | 2,9017 | 2 | 3,2936 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 9 | 81.985 | 3,0% | 0,998 | 0 | 4 | 7,9507 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 10 o más | 11.891 | 0,4% | 3,6776 | 0 | 11 | 10,1602 |
| 6 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 1 a 9 | 170.636 | 6,3% | 0,965 | 1,2378 | 5 | 7,2334 |
| 7 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 10 o más | 25.307 | 0,9% | 1,2692 | 2,9489 | 7 | 4,2574 |
| 8 | Con ambas conexiones, Fan-In 10 o más, Fan-Out 1 a 9 | 19.539 | 0,7% | 3,6424 | 1,2624 | 18 | 9,744 |
| 9 | Con ambas conexiones, Fan-In 10 o más, Fan-Out 10 o más | 4.108 | 0,2% | 3,7338 | 3,1084 | 5 | 2,5489 |

### medium_nocensus

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 2 | 677.952 | 25,0% | 0 | 0,8398 | 2 | 4,1068 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 3 a 9 | 578.111 | 21,3% | 0 | 1,7473 | 3 | 4,1177 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 10 o más | 198.227 | 7,3% | 0 | 2,9017 | 2 | 3,2936 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 9 | 81.985 | 3,0% | 0,998 | 0 | 4 | 7,9507 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 10 a 99 | 9.510 | 0,4% | 3,2076 | 0 | 10 | 9,9507 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 100 o más | 2.965 | 0,1% | 6,0109 | 0 | 17 | 11,1129 |
| 7 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 1 a 2 | 92.023 | 3,4% | 0,9556 | 0,8489 | 5 | 7,4689 |
| 8 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 3 a 9 | 78.613 | 2,9% | 0,976 | 1,6931 | 7 | 6,976 |
| 9 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 10 o más | 25.307 | 0,9% | 1,2692 | 2,9489 | 7 | 4,2574 |
| 10 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 1 a 2 | 8.324 | 0,3% | 3,1553 | 0,855 | 14 | 9,9507 |
| 11 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 3 a 9 | 7.310 | 0,3% | 3,1625 | 1,7107 | 21 | 9,3977 |
| 12 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 10 o más | 3.342 | 0,1% | 3,3435 | 3,0444 | 4 | 2,5489 |
| 13 | Con ambas conexiones, Fan-In 100 o más, Fan-Out 1 a 2 | 2.210 | 0,1% | 5,9556 | 0,8665 | 22 | 10,8487 |
| 14 | Con ambas conexiones, Fan-In 100 o más, Fan-Out 3 a 9 | 2.570 | 0,1% | 6,0362 | 1,672 | 25 | 9,399 |
| 15 | Con ambas conexiones, Fan-In 100 o más, Fan-Out 10 o más | 932 | 0,0% | 5,9259 | 3,3181 | 10,5 | 2,6502 |

### medium_census

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Censo (Fan-In 1000 o más) | 1.625 | 0,1% | 7,9043 | 1,025 | 31 | 11,2526 |
| 1 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 2 | 677.952 | 25,0% | 0 | 0,8398 | 2 | 4,1068 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 3 a 9 | 578.111 | 21,3% | 0 | 1,7473 | 3 | 4,1177 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 10 o más | 198.227 | 7,3% | 0 | 2,9017 | 2 | 3,2936 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 9 | 81.985 | 3,0% | 0,998 | 0 | 4 | 7,9507 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 10 a 99 | 9.510 | 0,4% | 3,2076 | 0 | 10 | 9,9507 |
| 7 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 100 o más | 2.381 | 0,1% | 5,5546 | 0 | 15 | 10,8884 |
| 8 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 1 a 2 | 92.023 | 3,4% | 0,9556 | 0,8489 | 5 | 7,4689 |
| 9 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 3 a 9 | 78.613 | 2,9% | 0,976 | 1,6931 | 7 | 6,976 |
| 10 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 10 o más | 25.307 | 0,9% | 1,2692 | 2,9489 | 7 | 4,2574 |
| 11 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 1 a 2 | 8.324 | 0,3% | 3,1553 | 0,855 | 14 | 9,9507 |
| 12 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 3 a 9 | 7.310 | 0,3% | 3,1625 | 1,7107 | 21 | 9,3977 |
| 13 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 10 o más | 3.342 | 0,1% | 3,3435 | 3,0444 | 4 | 2,5489 |
| 14 | Con ambas conexiones, Fan-In 100 o más, Fan-Out 1 a 2 | 1.869 | 0,1% | 5,6114 | 0,8689 | 21 | 10,6119 |
| 15 | Con ambas conexiones, Fan-In 100 o más, Fan-Out 3 a 9 | 2.036 | 0,1% | 5,5489 | 1,6798 | 24 | 9,2772 |
| 16 | Con ambas conexiones, Fan-In 100 o más, Fan-Out 10 o más | 766 | 0,0% | 5,4369 | 3,3877 | 6 | 2,5462 |

### fine_nocensus

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 2 | 677.952 | 25,0% | 0 | 0,8398 | 2 | 4,1068 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 3 a 9 | 578.111 | 21,3% | 0 | 1,7473 | 3 | 4,1177 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 10 a 49 | 187.318 | 6,9% | 0 | 2,8107 | 2 | 3,2827 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 50 o más | 10.909 | 0,4% | 0 | 4,464 | 2 | 3,4798 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 9 | 81.985 | 3,0% | 0,998 | 0 | 4 | 7,9507 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 10 a 99 | 9.510 | 0,4% | 3,2076 | 0 | 10 | 9,9507 |
| 7 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 100 a 999 | 2.381 | 0,1% | 5,5546 | 0 | 15 | 10,8884 |
| 8 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1000 o más | 584 | 0,0% | 7,871 | 0 | 27 | 11,9986 |
| 9 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 1 a 2 | 92.023 | 3,4% | 0,9556 | 0,8489 | 5 | 7,4689 |
| 10 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 3 a 9 | 78.613 | 2,9% | 0,976 | 1,6931 | 7 | 6,976 |
| 11 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 10 a 49 | 24.425 | 0,9% | 1,2802 | 2,8932 | 7 | 4,1889 |
| 12 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 50 o más | 882 | 0,0% | 0,9655 | 4,4902 | 10 | 6,0096 |
| 13 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 1 a 2 | 8.324 | 0,3% | 3,1553 | 0,855 | 14 | 9,9507 |
| 14 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 3 a 9 | 7.310 | 0,3% | 3,1625 | 1,7107 | 21 | 9,3977 |
| 15 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 10 a 49 | 2.939 | 0,1% | 3,3196 | 2,8681 | 9 | 4,052 |
| 16 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 50 o más + Con ambas conexiones, Fan-In 100 a 999, Fan-Out 50 o más + Con ambas conexiones, Fan-In 1000 o más, Fan-Out 10 a 49 + Con ambas conexiones, Fan-In 1000 o más, Fan-Out 50 o más | 755 | 0,0% | 4,9368 | 4,1817 | 3 | 2,5325 |
| 17 | Con ambas conexiones, Fan-In 100 a 999, Fan-Out 1 a 2 | 1.869 | 0,1% | 5,6114 | 0,8689 | 21 | 10,6119 |
| 18 | Con ambas conexiones, Fan-In 100 a 999, Fan-Out 3 a 9 | 2.036 | 0,1% | 5,5489 | 1,6798 | 24 | 9,2772 |
| 19 | Con ambas conexiones, Fan-In 100 a 999, Fan-Out 10 a 49 | 580 | 0,0% | 5,5398 | 2,8973 | 38 | 5,9986 |
| 20 | Con ambas conexiones, Fan-In 1000 o más, Fan-Out 3 a 9 + Con ambas conexiones, Fan-In 1000 o más, Fan-Out 1 a 2 | 875 | 0,0% | 7,8737 | 1,3349 | 32 | 10,8884 |

### fine_census

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Censo (Fan-In 1000 o más) | 1.625 | 0,1% | 7,9043 | 1,025 | 31 | 11,2526 |
| 1 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 2 | 677.952 | 25,0% | 0 | 0,8398 | 2 | 4,1068 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 3 a 9 | 578.111 | 21,3% | 0 | 1,7473 | 3 | 4,1177 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 10 a 49 | 187.318 | 6,9% | 0 | 2,8107 | 2 | 3,2827 |
| 5 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 50 o más | 10.909 | 0,4% | 0 | 4,464 | 2 | 3,4798 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 9 | 81.985 | 3,0% | 0,998 | 0 | 4 | 7,9507 |
| 7 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 10 a 99 | 9.510 | 0,4% | 3,2076 | 0 | 10 | 9,9507 |
| 8 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 100 a 999 | 2.381 | 0,1% | 5,5546 | 0 | 15 | 10,8884 |
| 9 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 1 a 2 | 92.023 | 3,4% | 0,9556 | 0,8489 | 5 | 7,4689 |
| 10 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 3 a 9 | 78.613 | 2,9% | 0,976 | 1,6931 | 7 | 6,976 |
| 11 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 10 a 49 | 24.425 | 0,9% | 1,2802 | 2,8932 | 7 | 4,1889 |
| 12 | Con ambas conexiones, Fan-In 1 a 9, Fan-Out 50 o más | 882 | 0,0% | 0,9655 | 4,4902 | 10 | 6,0096 |
| 13 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 1 a 2 | 8.324 | 0,3% | 3,1553 | 0,855 | 14 | 9,9507 |
| 14 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 3 a 9 | 7.310 | 0,3% | 3,1625 | 1,7107 | 21 | 9,3977 |
| 15 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 10 a 49 | 2.939 | 0,1% | 3,3196 | 2,8681 | 9 | 4,052 |
| 16 | Con ambas conexiones, Fan-In 10 a 99, Fan-Out 50 o más + Con ambas conexiones, Fan-In 100 a 999, Fan-Out 50 o más | 589 | 0,0% | 4,0222 | 4,5157 | 3 | 2,527 |
| 17 | Con ambas conexiones, Fan-In 100 a 999, Fan-Out 1 a 2 | 1.869 | 0,1% | 5,6114 | 0,8689 | 21 | 10,6119 |
| 18 | Con ambas conexiones, Fan-In 100 a 999, Fan-Out 3 a 9 | 2.036 | 0,1% | 5,5489 | 1,6798 | 24 | 9,2772 |
| 19 | Con ambas conexiones, Fan-In 100 a 999, Fan-Out 10 a 49 | 580 | 0,0% | 5,5398 | 2,8973 | 38 | 5,9986 |
