# Estratificación por árbol de regresión

## Parámetros

- Semilla: 42
- Mínimo por hoja (sobre B completo): 5,000
- Máximo de filas para ajuste: 500,000
- Total de hojas probadas: [8, 15, 25]
- Variables: n_versions, n_maintainers, n_keywords, n_peer, n_opt, age_years, has_github, deprecated, scoped, fan_in_dev, fan_out_dev

## Reparto de hojas por configuración

| config | total | Aislado | Consumidor | Consumido | Ambas |
| --- | --- | --- | --- | --- | --- |
| leaves8 | 8 | 1 | 3 | 2 | 2 |
| leaves15 | 15 | 1 | 9 | 2 | 3 |
| leaves25 | 25 | 1 | 17 | 3 | 4 |

## Métricas

| config | K | min_n | n_under_min | r2_log_fi | r2_log_fo | r2_log_n_versions | r2_age | eff_prop_log_fi | eff_neyman_log_fi | eff_prop_log_fo | eff_neyman_log_fo | r2_log_fi_train | r2_log_fi_test | r2_log_fo_train | r2_log_fo_test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| leaves8 | 8 | 7.204 | 0 | 0,6706 | 0,6009 | 0,0893 | 0,0476 | 3,0361 | 29,2726 | 2,5058 | 4,0699 | 0,672 | 0,6694 | 0,601 | 0,6009 |
| leaves15 | 15 | 7.204 | 0 | 0,6727 | 0,6147 | 0,3459 | 0,2547 | 3,0549 | 30,4156 | 2,5952 | 4,2575 | 0,6741 | 0,6714 | 0,6148 | 0,6145 |
| leaves25 | 25 | 7.204 | 0 | 0,6894 | 0,6331 | 0,3591 | 0,3121 | 3,219 | 33,7777 | 2,7253 | 4,514 | 0,6906 | 0,6882 | 0,6334 | 0,6328 |

## Tabla de estratos por configuración

### leaves8

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev > 7,50 | 451.325 | 16,7% | 0 | 1,6923 | 4 | 4,3943 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 | 995.761 | 36,8% | 0 | 1,3797 | 2 | 3,7098 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt > 0,50 | 7.204 | 0,3% | 0 | 2,3591 | 4 | 5,0691 |
| 4 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), fan_in_dev ≤ 5,50 | 87.026 | 3,2% | 1,1799 | 0 | 4 | 8,0684 |
| 5 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), fan_in_dev > 5,50 | 7.434 | 0,3% | 3,6953 | 0 | 14 | 10,3956 |
| 6 | Con ambas conexiones, fan_in_dev ≤ 6,50 | 205.934 | 7,6% | 1,1823 | 1,4686 | 6 | 6,8747 |
| 7 | Con ambas conexiones, fan_in_dev > 6,50 | 14.697 | 0,5% | 3,2707 | 1,531 | 25 | 10,308 |

#### Importancia de variables — leaves8

| cell | variable | importance |
| --- | --- | --- |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_versions | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_maintainers | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_keywords | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_peer | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_opt | 0,1872 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | age_years | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | has_github | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | deprecated | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | scoped | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | fan_in_dev | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | fan_out_dev | 0,8128 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_versions | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_maintainers | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_keywords | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_peer | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_opt | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | age_years | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | has_github | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | deprecated | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | scoped | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | fan_in_dev | 1 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | fan_out_dev | 0 |
| Con ambas conexiones | n_versions | 0 |
| Con ambas conexiones | n_maintainers | 0 |
| Con ambas conexiones | n_keywords | 0 |
| Con ambas conexiones | n_peer | 0 |
| Con ambas conexiones | n_opt | 0 |
| Con ambas conexiones | age_years | 0 |
| Con ambas conexiones | has_github | 0 |
| Con ambas conexiones | deprecated | 0 |
| Con ambas conexiones | scoped | 0 |
| Con ambas conexiones | fan_in_dev | 1 |
| Con ambas conexiones | fan_out_dev | 0 |

### leaves15

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt > 0,50 | 7.204 | 0,3% | 0 | 2,3591 | 4 | 5,0691 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions > 10,50 | 112.728 | 4,2% | 0 | 1,6381 | 18 | 5,3196 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev > 7,50 y n_versions > 37,50 | 28.356 | 1,0% | 0 | 2,0804 | 67 | 4,6242 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 0,50 y n_opt ≤ 0,50 y n_peer > 0,50 | 54.884 | 2,0% | 0 | 0,9651 | 3 | 4,668 |
| 5 | Consumidor (Fan-In 0, Fan-Out mayor a 0), 0,50 < fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer > 0,50 | 56.155 | 2,1% | 0 | 1,3248 | 4 | 2,6557 |
| 6 | Consumidor (Fan-In 0, Fan-Out mayor a 0), 7,50 < fan_out_dev ≤ 18,50 y n_versions ≤ 37,50 | 282.723 | 10,4% | 0 | 1,6019 | 3 | 3,9754 |
| 7 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev > 18,50 y n_versions ≤ 37,50 | 140.246 | 5,2% | 0 | 1,7963 | 4 | 5,0623 |
| 8 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years ≤ 2,40 | 313.865 | 11,6% | 0 | 1,4482 | 1 | 2,1629 |
| 9 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years > 2,40 | 458.129 | 16,9% | 0 | 1,3256 | 2 | 6,8693 |
| 10 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), fan_in_dev ≤ 5,50 | 87.026 | 3,2% | 1,1799 | 0 | 4 | 8,0684 |
| 11 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), fan_in_dev > 5,50 | 7.434 | 0,3% | 3,6953 | 0 | 14 | 10,3956 |
| 12 | Con ambas conexiones, fan_in_dev > 6,50 | 14.697 | 0,5% | 3,2707 | 1,531 | 25 | 10,308 |
| 13 | Con ambas conexiones, fan_in_dev ≤ 6,50 y age_years ≤ 2,65 | 51.293 | 1,9% | 1,3455 | 1,7343 | 2 | 2,2916 |
| 14 | Con ambas conexiones, fan_in_dev ≤ 6,50 y age_years > 2,65 | 154.641 | 5,7% | 1,1281 | 1,3805 | 7 | 8,553 |

#### Importancia de variables — leaves15

| cell | variable | importance |
| --- | --- | --- |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_versions | 0,178 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_maintainers | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_keywords | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_peer | 0,1121 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_opt | 0,1043 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | age_years | 0,0444 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | has_github | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | deprecated | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | scoped | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | fan_in_dev | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | fan_out_dev | 0,5612 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_versions | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_maintainers | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_keywords | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_peer | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_opt | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | age_years | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | has_github | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | deprecated | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | scoped | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | fan_in_dev | 1 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | fan_out_dev | 0 |
| Con ambas conexiones | n_versions | 0 |
| Con ambas conexiones | n_maintainers | 0 |
| Con ambas conexiones | n_keywords | 0 |
| Con ambas conexiones | n_peer | 0 |
| Con ambas conexiones | n_opt | 0 |
| Con ambas conexiones | age_years | 0,1611 |
| Con ambas conexiones | has_github | 0 |
| Con ambas conexiones | deprecated | 0 |
| Con ambas conexiones | scoped | 0 |
| Con ambas conexiones | fan_in_dev | 0,8389 |
| Con ambas conexiones | fan_out_dev | 0 |

### leaves25

| stratum | description | n | share | mean_log_fi | mean_log_fo | median_n_versions | median_age |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7% | 0 | 0 | 2 | 4,512 |
| 1 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt > 0,50 | 7.204 | 0,3% | 0 | 2,3591 | 4 | 5,0691 |
| 2 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions > 10,50 | 112.728 | 4,2% | 0 | 1,6381 | 18 | 5,3196 |
| 3 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev > 7,50 y n_versions > 37,50 | 28.356 | 1,0% | 0 | 2,0804 | 67 | 4,6242 |
| 4 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 0,50 y n_opt ≤ 0,50 y n_peer > 0,50 | 54.884 | 2,0% | 0 | 0,9651 | 3 | 4,668 |
| 5 | Consumidor (Fan-In 0, Fan-Out mayor a 0), 0,50 < fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer > 0,50 | 56.155 | 2,1% | 0 | 1,3248 | 4 | 2,6557 |
| 6 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev > 18,50 y n_versions ≤ 37,50 | 140.246 | 5,2% | 0 | 1,7963 | 4 | 5,0623 |
| 7 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years > 2,40 | 458.129 | 16,9% | 0 | 1,3256 | 2 | 6,8693 |
| 8 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y 2,29 < age_years ≤ 2,40 y n_keywords ≤ 3,50 | 57.278 | 2,1% | 0 | 1,6621 | 1 | 2,3354 |
| 9 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y 2,29 < age_years ≤ 2,40 y n_keywords > 3,50 | 26.522 | 1,0% | 0 | 2,1459 | 1 | 2,3299 |
| 10 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y 2,19 < age_years ≤ 2,29 y n_keywords ≤ 0,50 | 40.403 | 1,5% | 0 | 0,9086 | 1 | 2,245 |
| 11 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years ≤ 2,29 y 0,50 < n_keywords ≤ 1,50 | 10.289 | 0,4% | 0 | 1,9033 | 1 | 2,2122 |
| 12 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years ≤ 2,29 y n_keywords > 1,50 | 115.474 | 4,3% | 0 | 1,3653 | 2 | 0,7474 |
| 13 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years ≤ 2,19 y n_keywords ≤ 0,50 y has_github ≤ 0,50 | 44.979 | 1,7% | 0 | 1,2449 | 1 | 1,41 |
| 14 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y age_years ≤ 2,11 y n_keywords ≤ 0,50 y has_github > 0,50 | 11.207 | 0,4% | 0 | 1,3397 | 2 | 0,8049 |
| 15 | Consumidor (Fan-In 0, Fan-Out mayor a 0), fan_out_dev ≤ 7,50 y n_opt ≤ 0,50 y n_peer ≤ 0,50 y n_versions ≤ 10,50 y 2,11 < age_years ≤ 2,19 y n_keywords ≤ 0,50 y has_github > 0,50 | 7.713 | 0,3% | 0 | 2,2662 | 1 | 2,1492 |
| 16 | Consumidor (Fan-In 0, Fan-Out mayor a 0), 7,50 < fan_out_dev ≤ 18,50 y n_versions ≤ 37,50 y age_years ≤ 3,10 | 120.211 | 4,4% | 0 | 1,7041 | 2 | 1,9302 |
| 17 | Consumidor (Fan-In 0, Fan-Out mayor a 0), 7,50 < fan_out_dev ≤ 18,50 y n_versions ≤ 37,50 y age_years > 3,10 | 162.512 | 6,0% | 0 | 1,5263 | 4 | 6,5489 |
| 18 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), fan_in_dev > 5,50 | 7.434 | 0,3% | 3,6953 | 0 | 14 | 10,3956 |
| 19 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), fan_in_dev ≤ 0,50 | 73.043 | 2,7% | 1,0591 | 0 | 4 | 7,7591 |
| 20 | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0), 0,50 < fan_in_dev ≤ 5,50 | 13.983 | 0,5% | 1,8109 | 0 | 8 | 9,399 |
| 21 | Con ambas conexiones, fan_in_dev > 6,50 | 14.697 | 0,5% | 3,2707 | 1,531 | 25 | 10,308 |
| 22 | Con ambas conexiones, fan_in_dev ≤ 6,50 y age_years > 2,65 | 154.641 | 5,7% | 1,1281 | 1,3805 | 7 | 8,553 |
| 23 | Con ambas conexiones, fan_in_dev ≤ 6,50 y age_years ≤ 2,25 | 23.870 | 0,9% | 0,9131 | 1,4178 | 5 | 1,1745 |
| 24 | Con ambas conexiones, fan_in_dev ≤ 6,50 y 2,25 < age_years ≤ 2,65 | 27.423 | 1,0% | 1,7218 | 2,0098 | 1 | 2,4914 |

#### Importancia de variables — leaves25

| cell | variable | importance |
| --- | --- | --- |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_versions | 0,11 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_maintainers | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_keywords | 0,0936 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_peer | 0,0693 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | n_opt | 0,0645 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | age_years | 0,2891 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | has_github | 0,0264 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | deprecated | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | scoped | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | fan_in_dev | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | fan_out_dev | 0,347 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_versions | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_maintainers | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_keywords | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_peer | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | n_opt | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | age_years | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | has_github | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | deprecated | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | scoped | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | fan_in_dev | 1 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | fan_out_dev | 0 |
| Con ambas conexiones | n_versions | 0 |
| Con ambas conexiones | n_maintainers | 0 |
| Con ambas conexiones | n_keywords | 0 |
| Con ambas conexiones | n_peer | 0 |
| Con ambas conexiones | n_opt | 0 |
| Con ambas conexiones | age_years | 0,3244 |
| Con ambas conexiones | has_github | 0 |
| Con ambas conexiones | deprecated | 0 |
| Con ambas conexiones | scoped | 0 |
| Con ambas conexiones | fan_in_dev | 0,6756 |
| Con ambas conexiones | fan_out_dev | 0 |
