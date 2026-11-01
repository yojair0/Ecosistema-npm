# Estratificación por cortes óptimos (Dalenius-Hodges)

## Parámetros

- Semilla: 42
- Mínimo por estrato (sobre B completo): 500
- Mínimo escalado a mitad de ajuste: 250
- Umbral de censo: Fan-In ≥ 1000
- Población B: 2,709,168 paquetes
- Bandas probadas: [2, 3, 4]
- Clases finas: cada entero de 1 a 1.000; sobre 1.000, intervalos que duplican el ancho (2.000, 4.000, 8.000, ...)

## Cortes calculados por configuración

| config | n_bands | fi_edges | fi_bands | fo_edges | fo_bands | reducida |
| --- | --- | --- | --- | --- | --- | --- |
| bands2_nocensus | 2 | [1, 67] | 1 a 66, 67 o más | [1, 12] | 1 a 11, 12 o más | no |
| bands2_census | 2 | [1, 63] | 1 a 62, 63 o más | [1, 12] | 1 a 11, 12 o más | no |
| bands3_nocensus | 3 | [1, 18, 194] | 1 a 17, 18 a 193, 194 o más | [1, 6, 25] | 1 a 5, 6 a 24, 25 o más | no |
| bands3_census | 3 | [1, 17, 180] | 1 a 16, 17 a 179, 180 o más | [1, 6, 25] | 1 a 5, 6 a 24, 25 o más | no |
| bands4_nocensus | 4 | [1, 9, 67, 306] | 1 a 8, 9 a 66, 67 a 305, 306 o más | [1, 4, 12, 40] | 1 a 3, 4 a 11, 12 a 39, 40 o más | no |
| bands4_census | 4 | [1, 9, 63, 285] | 1 a 8, 9 a 62, 63 a 284, 285 o más | [1, 4, 12, 40] | 1 a 3, 4 a 11, 12 a 39, 40 o más | no |

## Métricas de las 6 configuraciones

| config | K | min_n | n_under_min | r2_log_fi | r2_log_fo | r2_log_n_versions | r2_age | eff_prop_log_fi | eff_neyman_log_fi | eff_prop_log_fo | eff_neyman_log_fo | r2_log_fi_train | r2_log_fi_test | r2_log_fo_train | r2_log_fo_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bands2_nocensus | 9 | 1.063 | 0 | 0,7968 | 0,7861 | 0,0713 | 0,0469 | 4,9301 | 43,3164 | 4,6761 | 7,5709 | 0,7974 | 0,7962 | 0,7864 | 0,7858 |
| bands2_census | 10 | 1.141 | 0 | 0,8125 | 0,7855 | 0,0714 | 0,0469 | 5,3359 | 46,2996 | 4,6634 | 7,5526 | 0,8133 | 0,8117 | 0,7858 | 0,7853 |
| bands3_nocensus | 15 | 924 | 0 | 0,8875 | 0,8969 | 0,0784 | 0,0486 | 8,9289 | 78,5414 | 9,7082 | 15,8529 | 0,8875 | 0,8875 | 0,897 | 0,8968 |
| bands3_census | 16 | 737 | 0 | 0,8952 | 0,8963 | 0,0787 | 0,0487 | 9,5647 | 83,4017 | 9,6564 | 15,7963 | 0,8953 | 0,8952 | 0,8964 | 0,8962 |
| bands4_nocensus | 23 | 504 | 0 | 0,9324 | 0,9413 | 0,0886 | 0,0508 | 15,0773 | 133 | 17,0966 | 28,1545 | 0,932 | 0,9327 | 0,9414 | 0,9413 |
| bands4_census | 23 | 542 | 0 | 0,9358 | 0,9407 | 0,0885 | 0,0507 | 15,7394 | 138,1054 | 16,9005 | 28,0074 | 0,9357 | 0,9359 | 0,9407 | 0,9407 |

## Tabla de estratos por configuración

### bands2_nocensus

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 11 | 1.309.062 | 48,3% | 0 | 1,3052 | 2 | 4,0602 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 12 o más | 145.228 | 5,4% | 0 | 3,0716 | 3 | 3,4524 |
| 3 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 66 | 90.660 | 3,3% | 1,1985 | 0 | 5 | 8,1725 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 67 o más | 3.800 | 0,1% | 5,6564 | 0 | 15 | 10,9665 |
| 5 | Con ambas conexiones, Fan-In 1 a 66, Fan-Out 1 a 11 | 190.597 | 7,0% | 1,1305 | 1,2739 | 6 | 7,4689 |
| 6 | Con ambas conexiones, Fan-In 1 a 66, Fan-Out 12 o más | 22.800 | 0,8% | 1,5423 | 3,0838 | 5 | 3,3005 |
| 7 | Con ambas conexiones, Fan-In 67 o más, Fan-Out 1 a 11 | 6.171 | 0,2% | 5,6811 | 1,3263 | 25 | 10,1848 |
| 8 | Con ambas conexiones, Fan-In 67 o más, Fan-Out 12 o más | 1.063 | 0,0% | 5,5004 | 3,4335 | 4 | 2,5435 |

### bands2_census

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Censo (Fan-In 1000 o más) | 1.625 | 0,1% | 7,9043 | 1,025 | 31 | 11,2526 |
| 1 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 11 | 1.309.062 | 48,3% | 0 | 1,3052 | 2 | 4,0602 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 12 o más | 145.228 | 5,4% | 0 | 3,0716 | 3 | 3,4524 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 62 | 90.496 | 3,3% | 1,1931 | 0 | 5 | 8,1697 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 63 o más | 3.380 | 0,1% | 5,2021 | 0 | 14 | 10,7296 |
| 6 | Con ambas conexiones, Fan-In 1 a 62, Fan-Out 1 a 11 | 190.373 | 7,0% | 1,1269 | 1,2739 | 6 | 7,4661 |
| 7 | Con ambas conexiones, Fan-In 1 a 62, Fan-Out 12 o más | 22.586 | 0,8% | 1,5172 | 3,086 | 5 | 3,399 |
| 8 | Con ambas conexiones, Fan-In 63 o más, Fan-Out 1 a 11 | 5.490 | 0,2% | 5,2569 | 1,3159 | 23 | 10,0123 |
| 9 | Con ambas conexiones, Fan-In 63 o más, Fan-Out 12 o más | 1.141 | 0,0% | 4,9356 | 3,3605 | 3 | 2,5325 |

### bands3_nocensus

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 5 | 1.048.429 | 38,7% | 0 | 1,0911 | 2 | 4,1862 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 6 a 24 | 366.083 | 13,5% | 0 | 2,3501 | 3 | 3,5373 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 25 o más | 39.778 | 1,5% | 0 | 3,781 | 2 | 3,4251 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 17 | 85.879 | 3,2% | 1,0714 | 0 | 4 | 8,052 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 18 a 193 | 6.552 | 0,2% | 3,8024 | 0 | 11 | 10,3135 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 194 o más | 2.029 | 0,1% | 6,5183 | 0 | 17 | 11,217 |
| 7 | Con ambas conexiones, Fan-In 1 a 17, Fan-Out 1 a 5 | 153.801 | 5,7% | 1,0228 | 1,1062 | 5 | 7,3895 |
| 8 | Con ambas conexiones, Fan-In 1 a 17, Fan-Out 6 a 24 | 44.341 | 1,6% | 1,1647 | 2,4025 | 9 | 6,2943 |
| 9 | Con ambas conexiones, Fan-In 1 a 17, Fan-Out 25 o más | 5.722 | 0,2% | 1,4858 | 3,6388 | 3 | 2,527 |
| 10 | Con ambas conexiones, Fan-In 18 a 193, Fan-Out 1 a 5 | 8.784 | 0,3% | 3,7982 | 1,1241 | 18 | 10,0205 |
| 11 | Con ambas conexiones, Fan-In 18 a 193, Fan-Out 6 a 24 | 3.316 | 0,1% | 3,8 | 2,4177 | 22 | 7,41 |
| 12 | Con ambas conexiones, Fan-In 18 a 193, Fan-Out 25 o más | 924 | 0,0% | 3,899 | 4,0462 | 3 | 2,5298 |
| 13 | Con ambas conexiones, Fan-In 194 o más, Fan-Out 1 a 5 | 2.744 | 0,1% | 6,5268 | 1,1691 | 23 | 10,2752 |
| 14 | Con ambas conexiones, Fan-In 194 o más, Fan-Out 6 a 24 + Con ambas conexiones, Fan-In 194 o más, Fan-Out 25 o más | 999 | 0,0% | 6,6105 | 2,6232 | 52 | 9,5441 |

### bands3_census

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Censo (Fan-In 1000 o más) | 1.625 | 0,1% | 7,9043 | 1,025 | 31 | 11,2526 |
| 1 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 5 | 1.048.429 | 38,7% | 0 | 1,0911 | 2 | 4,1862 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 6 a 24 | 366.083 | 13,5% | 0 | 2,3501 | 3 | 3,5373 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 25 o más | 39.778 | 1,5% | 0 | 3,781 | 2 | 3,4251 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 16 | 85.563 | 3,2% | 1,0647 | 0 | 4 | 8,0438 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 17 a 179 | 6.783 | 0,3% | 3,7419 | 0 | 11 | 10,2368 |
| 7 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 180 o más | 1.530 | 0,1% | 5,9308 | 0 | 15 | 10,8884 |
| 8 | Con ambas conexiones, Fan-In 1 a 16, Fan-Out 1 a 5 | 153.358 | 5,7% | 1,0174 | 1,1062 | 5 | 7,3785 |
| 9 | Con ambas conexiones, Fan-In 1 a 16, Fan-Out 6 a 24 | 44.204 | 1,6% | 1,1594 | 2,4024 | 9 | 6,2888 |
| 10 | Con ambas conexiones, Fan-In 1 a 16, Fan-Out 25 o más | 5.696 | 0,2% | 1,4793 | 3,6384 | 3 | 2,527 |
| 11 | Con ambas conexiones, Fan-In 17 a 179, Fan-Out 1 a 5 | 9.097 | 0,3% | 3,7335 | 1,1222 | 18 | 9,9959 |
| 12 | Con ambas conexiones, Fan-In 17 a 179, Fan-Out 6 a 24 | 3.425 | 0,1% | 3,7519 | 2,418 | 22 | 7,4661 |
| 13 | Con ambas conexiones, Fan-In 17 a 179, Fan-Out 25 o más | 949 | 0,0% | 3,87 | 4,0376 | 3 | 2,5298 |
| 14 | Con ambas conexiones, Fan-In 180 o más, Fan-Out 1 a 5 | 2.124 | 0,1% | 5,9784 | 1,155 | 22 | 10,0233 |
| 15 | Con ambas conexiones, Fan-In 180 o más, Fan-Out 6 a 24 + Con ambas conexiones, Fan-In 180 o más, Fan-Out 25 o más | 737 | 0,0% | 5,9697 | 2,6277 | 43 | 9,0157 |

### bands4_nocensus

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 3 | 846.289 | 31,2% | 0 | 0,9485 | 2 | 4,1561 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 4 a 11 | 462.773 | 17,1% | 0 | 1,9575 | 3 | 3,885 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 12 a 39 | 128.122 | 4,7% | 0 | 2,9174 | 3 | 3,4333 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 40 o más | 17.106 | 0,6% | 0 | 4,2271 | 2 | 3,6085 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 8 | 81.015 | 3,0% | 0,9824 | 0 | 4 | 7,9261 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 9 a 66 | 9.645 | 0,4% | 3,0136 | 0 | 9 | 9,8782 |
| 7 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 67 a 305 | 2.301 | 0,1% | 4,8597 | 0 | 14 | 10,6804 |
| 8 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 306 o más | 1.499 | 0,1% | 6,8794 | 0 | 19 | 11,4716 |
| 9 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 1 a 3 | 119.650 | 4,4% | 0,9417 | 0,9769 | 5 | 7,1348 |
| 10 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 4 a 11 | 54.172 | 2,0% | 0,9752 | 1,9219 | 9 | 7,269 |
| 11 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 12 a 39 | 13.894 | 0,5% | 1,0178 | 2,93 | 13 | 5,8453 |
| 12 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 40 o más | 1.341 | 0,0% | 0,9568 | 4,2491 | 15 | 6,0808 |
| 13 | Con ambas conexiones, Fan-In 9 a 66, Fan-Out 1 a 3 | 11.190 | 0,4% | 2,9728 | 0,9783 | 14 | 9,7153 |
| 14 | Con ambas conexiones, Fan-In 9 a 66, Fan-Out 4 a 11 | 5.585 | 0,2% | 2,99 | 1,9421 | 24 | 9,2211 |
| 15 | Con ambas conexiones, Fan-In 9 a 66, Fan-Out 12 a 39 | 7.061 | 0,3% | 2,5547 | 3,0842 | 1 | 2,3299 |
| 16 | Con ambas conexiones, Fan-In 9 a 66, Fan-Out 40 o más | 504 | 0,0% | 3,3773 | 4,2151 | 3 | 2,5024 |
| 17 | Con ambas conexiones, Fan-In 67 a 305, Fan-Out 1 a 3 | 2.403 | 0,1% | 4,8744 | 1,0006 | 20 | 10,1684 |
| 18 | Con ambas conexiones, Fan-In 67 a 305, Fan-Out 4 a 11 | 1.257 | 0,0% | 4,8646 | 1,9176 | 34 | 9,5825 |
| 19 | Con ambas conexiones, Fan-In 67 a 305, Fan-Out 12 a 39 | 520 | 0,0% | 4,8113 | 3,017 | 4 | 2,5489 |
| 20 | Con ambas conexiones, Fan-In 67 a 305, Fan-Out 40 o más + Con ambas conexiones, Fan-In 306 o más, Fan-Out 40 o más + Con ambas conexiones, Fan-In 306 o más, Fan-Out 12 a 39 | 543 | 0,0% | 6,1604 | 3,8324 | 5 | 2,5435 |
| 21 | Con ambas conexiones, Fan-In 306 o más, Fan-Out 1 a 3 | 1.674 | 0,1% | 6,828 | 1,0536 | 19 | 10,2478 |
| 22 | Con ambas conexiones, Fan-In 306 o más, Fan-Out 4 a 11 | 837 | 0,0% | 6,9296 | 1,9184 | 51 | 10,7324 |

### bands4_census

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Censo (Fan-In 1000 o más) | 1.625 | 0,1% | 7,9043 | 1,025 | 31 | 11,2526 |
| 1 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 1 a 3 | 846.289 | 31,2% | 0 | 0,9485 | 2 | 4,1561 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 4 a 11 | 462.773 | 17,1% | 0 | 1,9575 | 3 | 3,885 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 12 a 39 | 128.122 | 4,7% | 0 | 2,9174 | 3 | 3,4333 |
| 5 | Consumidor (Fan-In 0, Fan-Out mayor a 0), Fan-Out 40 o más | 17.106 | 0,6% | 0 | 4,2271 | 2 | 3,6085 |
| 6 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 1 a 8 | 81.015 | 3,0% | 0,9824 | 0 | 4 | 7,9261 |
| 7 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 9 a 62 | 9.481 | 0,3% | 2,9934 | 0 | 9 | 9,8782 |
| 8 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 63 a 284 | 2.404 | 0,1% | 4,7922 | 0 | 13 | 10,6393 |
| 9 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), Fan-In 285 o más | 976 | 0,0% | 6,2118 | 0 | 15 | 11,1239 |
| 10 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 1 a 3 | 119.650 | 4,4% | 0,9417 | 0,9769 | 5 | 7,1348 |
| 11 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 4 a 11 | 54.172 | 2,0% | 0,9752 | 1,9219 | 9 | 7,269 |
| 12 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 12 a 39 | 13.894 | 0,5% | 1,0178 | 2,93 | 13 | 5,8453 |
| 13 | Con ambas conexiones, Fan-In 1 a 8, Fan-Out 40 o más | 1.341 | 0,0% | 0,9568 | 4,2491 | 15 | 6,0808 |
| 14 | Con ambas conexiones, Fan-In 9 a 62, Fan-Out 1 a 3 | 11.030 | 0,4% | 2,9552 | 0,9786 | 13 | 9,7002 |
| 15 | Con ambas conexiones, Fan-In 9 a 62, Fan-Out 4 a 11 | 5.521 | 0,2% | 2,9762 | 1,9415 | 24 | 9,2211 |
| 16 | Con ambas conexiones, Fan-In 9 a 62, Fan-Out 12 a 39 | 6.860 | 0,3% | 2,5065 | 3,0932 | 1 | 2,3272 |
| 17 | Con ambas conexiones, Fan-In 9 a 62, Fan-Out 40 o más + Con ambas conexiones, Fan-In 63 a 284, Fan-Out 40 o más + Con ambas conexiones, Fan-In 285 o más, Fan-Out 12 a 39 + Con ambas conexiones, Fan-In 285 o más, Fan-Out 40 o más | 955 | 0,0% | 4,3813 | 4,0917 | 3 | 2,527 |
| 18 | Con ambas conexiones, Fan-In 63 a 284, Fan-Out 1 a 3 | 2.477 | 0,1% | 4,8014 | 0,9968 | 20 | 10,2122 |
| 19 | Con ambas conexiones, Fan-In 63 a 284, Fan-Out 4 a 11 | 1.285 | 0,0% | 4,8072 | 1,9216 | 34 | 9,5387 |
| 20 | Con ambas conexiones, Fan-In 63 a 284, Fan-Out 12 a 39 | 677 | 0,0% | 4,5719 | 2,9543 | 2 | 2,5106 |
| 21 | Con ambas conexiones, Fan-In 285 o más, Fan-Out 1 a 3 | 1.186 | 0,0% | 6,2555 | 1,0444 | 17 | 9,8891 |
| 22 | Con ambas conexiones, Fan-In 285 o más, Fan-Out 4 a 11 | 542 | 0,0% | 6,22 | 1,9326 | 44,5 | 10,2724 |

**Nota:** con censo, la última banda de Fan-In llega hasta 999 aunque su etiqueta diga "o más".
