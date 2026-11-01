# Comparación de técnicas de estratificación

## Técnicas

- Encontradas: 01_grid_base, 02_optimal_cuts, 03_regression_tree, 04_clustering

## Tabla única — todas las configuraciones

| technique | config | K | min_n | n_under_min | r2_log_fi | r2_log_fo | r2_log_n_versions | r2_age | eff_neyman_log_fi | eff_neyman_log_fo | gap_fi | gap_fo | silhouette | davies_bouldin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_grid_base | coarse_nocensus | 9 | 4.274 | 0 | 0,8539 | 0,8115 | 0,0761 | 0,0496 | 78,5988 | 8,597 | -0,0001 | 0,0001 | — | — |
| 01_grid_base | coarse_census | 10 | 1.625 | 0 | 0,885 | 0,8109 | 0,0764 | 0,0496 | 89,3832 | 8,5753 | -0,0003 | 0,0001 | — | — |
| 01_grid_base | medium_nocensus | 16 | 932 | 0 | 0,912 | 0,9331 | 0,0823 | 0,05 | 106,5882 | 28,2262 | -0,0005 | -0,0001 | — | — |
| 01_grid_base | medium_census | 17 | 766 | 0 | 0,9201 | 0,9325 | 0,0824 | 0,05 | 112,372 | 28,0776 | -0,0004 | -0,0001 | — | — |
| 01_grid_base | fine_census | 20 | 580 | 0 | 0,9199 | 0,9457 | 0,0828 | 0,0501 | 112,2238 | 32,5553 | -0,0004 | -0 | — | — |
| 01_grid_base | fine_nocensus | 21 | 580 | 0 | 0,9174 | 0,9462 | 0,0826 | 0,0501 | 111,0577 | 32,6862 | -0,0007 | -0 | — | — |
| 02_optimal_cuts | bands2_nocensus | 9 | 1.063 | 0 | 0,7968 | 0,7861 | 0,0713 | 0,0469 | 43,3164 | 7,5709 | 0,0012 | 0,0005 | — | — |
| 02_optimal_cuts | bands2_census | 10 | 1.141 | 0 | 0,8125 | 0,7855 | 0,0714 | 0,0469 | 46,2996 | 7,5526 | 0,0016 | 0,0005 | — | — |
| 02_optimal_cuts | bands3_nocensus | 15 | 924 | 0 | 0,8875 | 0,8969 | 0,0784 | 0,0486 | 78,5414 | 15,8529 | 0,0001 | 0,0002 | — | — |
| 02_optimal_cuts | bands3_census | 16 | 737 | 0 | 0,8952 | 0,8963 | 0,0787 | 0,0487 | 83,4017 | 15,7963 | 0,0001 | 0,0002 | — | — |
| 02_optimal_cuts | bands4_nocensus | 23 | 504 | 0 | 0,9324 | 0,9413 | 0,0886 | 0,0508 | 133 | 28,1545 | -0,0006 | 0,0001 | — | — |
| 02_optimal_cuts | bands4_census | 23 | 542 | 0 | 0,9358 | 0,9407 | 0,0885 | 0,0507 | 138,1054 | 28,0074 | -0,0003 | 0 | — | — |
| 03_regression_tree | leaves8 | 8 | 7.204 | 0 | 0,6706 | 0,6009 | 0,0893 | 0,0476 | 29,2726 | 4,0699 | 0,0026 | 0,0001 | — | — |
| 03_regression_tree | leaves15 | 15 | 7.204 | 0 | 0,6727 | 0,6147 | 0,3459 | 0,2547 | 30,4156 | 4,2575 | 0,0027 | 0,0003 | — | — |
| 03_regression_tree | leaves25 | 25 | 7.204 | 0 | 0,6894 | 0,6331 | 0,3591 | 0,3121 | 33,7777 | 4,514 | 0,0024 | 0,0006 | — | — |
| 04_clustering | k4 | 5 | 74.553 | 0 | 0,1955 | 0,5052 | 0,106 | 0,0714 | 2,5127 | 3,0993 | -0,0012 | -0,0001 | 0,1985 | 1,689 |
| 04_clustering | k8 | 9 | 5.454 | 0 | 0,1981 | 0,5092 | 0,1219 | 0,2394 | 2,4841 | 3,1263 | -0,0021 | 0,0001 | 0,2134 | 1,3952 |
| 04_clustering | k12 | 13 | 5.445 | 0 | 0,2674 | 0,5227 | 0,3188 | 0,3502 | 2,6446 | 3,2265 | 0,0002 | -0,0005 | 0,23 | 1,2385 |

## Configuraciones de K comparable

| target_K | technique | config | K | min_n | n_under_min | r2_log_fi | r2_log_fo | r2_log_n_versions | r2_age | eff_neyman_log_fi | eff_neyman_log_fo | gap_fi | gap_fo | silhouette | davies_bouldin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 01_grid_base | coarse_census | 10 | 1.625 | 0 | 0,885 | 0,8109 | 0,0764 | 0,0496 | 89,3832 | 8,5753 | -0,0003 | 0,0001 | — | — |
| 9 | 01_grid_base | coarse_nocensus | 9 | 4.274 | 0 | 0,8539 | 0,8115 | 0,0761 | 0,0496 | 78,5988 | 8,597 | -0,0001 | 0,0001 | — | — |
| 9 | 02_optimal_cuts | bands2_census | 10 | 1.141 | 0 | 0,8125 | 0,7855 | 0,0714 | 0,0469 | 46,2996 | 7,5526 | 0,0016 | 0,0005 | — | — |
| 9 | 02_optimal_cuts | bands2_nocensus | 9 | 1.063 | 0 | 0,7968 | 0,7861 | 0,0713 | 0,0469 | 43,3164 | 7,5709 | 0,0012 | 0,0005 | — | — |
| 9 | 03_regression_tree | leaves8 | 8 | 7.204 | 0 | 0,6706 | 0,6009 | 0,0893 | 0,0476 | 29,2726 | 4,0699 | 0,0026 | 0,0001 | — | — |
| 9 | 04_clustering | k8 | 9 | 5.454 | 0 | 0,1981 | 0,5092 | 0,1219 | 0,2394 | 2,4841 | 3,1263 | -0,0021 | 0,0001 | 0,2134 | 1,3952 |
| 15 | 01_grid_base | medium_census | 17 | 766 | 0 | 0,9201 | 0,9325 | 0,0824 | 0,05 | 112,372 | 28,0776 | -0,0004 | -0,0001 | — | — |
| 15 | 01_grid_base | medium_nocensus | 16 | 932 | 0 | 0,912 | 0,9331 | 0,0823 | 0,05 | 106,5882 | 28,2262 | -0,0005 | -0,0001 | — | — |
| 15 | 02_optimal_cuts | bands3_census | 16 | 737 | 0 | 0,8952 | 0,8963 | 0,0787 | 0,0487 | 83,4017 | 15,7963 | 0,0001 | 0,0002 | — | — |
| 15 | 02_optimal_cuts | bands3_nocensus | 15 | 924 | 0 | 0,8875 | 0,8969 | 0,0784 | 0,0486 | 78,5414 | 15,8529 | 0,0001 | 0,0002 | — | — |
| 15 | 03_regression_tree | leaves15 | 15 | 7.204 | 0 | 0,6727 | 0,6147 | 0,3459 | 0,2547 | 30,4156 | 4,2575 | 0,0027 | 0,0003 | — | — |
| 15 | 04_clustering | k12 | 13 | 5.445 | 0 | 0,2674 | 0,5227 | 0,3188 | 0,3502 | 2,6446 | 3,2265 | 0,0002 | -0,0005 | 0,23 | 1,2385 |
| 25 | 01_grid_base | fine_census | 20 | 580 | 0 | 0,9199 | 0,9457 | 0,0828 | 0,0501 | 112,2238 | 32,5553 | -0,0004 | -0 | — | — |
| 25 | 01_grid_base | fine_nocensus | 21 | 580 | 0 | 0,9174 | 0,9462 | 0,0826 | 0,0501 | 111,0577 | 32,6862 | -0,0007 | -0 | — | — |
| 25 | 02_optimal_cuts | bands4_census | 23 | 542 | 0 | 0,9358 | 0,9407 | 0,0885 | 0,0507 | 138,1054 | 28,0074 | -0,0003 | 0 | — | — |
| 25 | 02_optimal_cuts | bands4_nocensus | 23 | 504 | 0 | 0,9324 | 0,9413 | 0,0886 | 0,0508 | 133 | 28,1545 | -0,0006 | 0,0001 | — | — |
| 25 | 03_regression_tree | leaves25 | 25 | 7.204 | 0 | 0,6894 | 0,6331 | 0,3591 | 0,3121 | 33,7777 | 4,514 | 0,0024 | 0,0006 | — | — |
| 25 | 04_clustering | k12 | 13 | 5.445 | 0 | 0,2674 | 0,5227 | 0,3188 | 0,3502 | 2,6446 | 3,2265 | 0,0002 | -0,0005 | 0,23 | 1,2385 |

## Figuras

### Varianza explicada de Fan-In y Fan-Out vs K

![Varianza explicada de Fan-In y Fan-Out vs K](figures/fig01_r2_fan_vs_k.png)

### Varianza explicada de n_versions y age vs K

![Varianza explicada de n_versions y age vs K](figures/fig02_r2_profile_vs_k.png)

### Eficiencia de muestreo Neyman vs K

![Eficiencia de muestreo Neyman vs K](figures/fig03_neyman_efficiency_vs_k.png)

### Brecha de generalización (train − test) vs K

![Brecha de generalización (train − test) vs K](figures/fig04_train_test_gap_vs_k.png)

## Notas

- La cuadrícula y los cortes óptimos se arman con Fan-In y Fan-Out, por eso su varianza explicada de esas variables es alta por construcción.
- El árbol usa log(1+Fan-In) y log(1+Fan-Out) como objetivo.
- La clusterización no usa Fan-In ni Fan-Out.
- Todo es solo con el dataset B (sin familias).
