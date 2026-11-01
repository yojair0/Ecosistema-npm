# Resultados: selección de variables (08b)

## 1. Los tres grupos

| Grupo | Etiqueta | Fan-In | Fan-Out |
|:---|:---|:---|:---|
| A | A: con familias | fan_in | fan_out |
| A externo | A externo: mismos paquetes, solo vínculos externos | fan_in_external | fan_out_external |
| B | B: sin familias | fan_in | fan_out |

fan_in_dev y fan_out_dev se usan con su valor total, sin descontar familias, en los tres grupos.

## 2. Tabla comparativa

| Métrica | A | A externo | B |
| :--- | ---: | ---: | ---: |
| N | 4.080.297 | 4.080.297 | 2.709.168 |
| % Fan-In = 0 | 82,9 | 89,8 | 88,4 |
| % Fan-Out = 0 | 36,4 | 40,6 | 38,2 |
| % Aislados | 31,8 | 37,3 | 34,7 |
| p99 Fan-In | 18 | 13 | 16 |
| p99 Fan-Out | 34 | 32 | 34 |
| ρ Fan-In ↔ Fan-Out | 0,082 | 0,048 | 0,052 |
| ρ n_versions – Fan-In | 0,248 | 0,191 | 0,206 |
| ρ n_versions – Fan-Out | 0,173 | 0,131 | 0,151 |
| ρ n_maintainers – Fan-In | 0,166 | 0,091 | 0,152 |
| ρ n_maintainers – Fan-Out | 0,090 | 0,031 | 0,063 |
| ρ n_keywords – Fan-In | 0,011 | 0,049 | 0,065 |
| ρ n_keywords – Fan-Out | -0,013 | -0,007 | 0,029 |
| ρ n_peer – Fan-In | 0,004 | -0,031 | -0,028 |
| ρ n_peer – Fan-Out | 0,000 | -0,023 | -0,014 |
| ρ n_opt – Fan-In | -0,023 | -0,016 | 0,007 |
| ρ n_opt – Fan-Out | -0,037 | -0,033 | 0,056 |
| ρ age_years – Fan-In | 0,066 | 0,177 | 0,192 |
| ρ age_years – Fan-Out | -0,007 | 0,032 | -0,027 |
| ρ has_github – Fan-In | 0,109 | 0,118 | 0,138 |
| ρ has_github – Fan-Out | 0,065 | 0,055 | 0,088 |
| ρ deprecated – Fan-In | 0,033 | 0,028 | 0,035 |
| ρ deprecated – Fan-Out | 0,007 | -0,002 | -0,004 |
| ρ scoped – Fan-In | 0,151 | -0,094 | -0,085 |
| ρ scoped – Fan-Out | 0,041 | -0,065 | 0,007 |
| ρ fan_in_dev – Fan-In | 0,261 | 0,263 | 0,310 |
| ρ fan_in_dev – Fan-Out | 0,029 | 0,016 | 0,022 |
| ρ fan_out_dev – Fan-In | 0,068 | 0,074 | 0,091 |
| ρ fan_out_dev – Fan-Out | 0,258 | 0,260 | 0,259 |
| R² Fan-In | 0,321 | 0,382 | 0,390 |
| AUC Fan-In | 0,777 | 0,809 | 0,814 |
| Variable top Fan-In | n_versions | n_versions | age_years |
| R² Fan-Out | 0,195 | 0,185 | 0,257 |
| AUC Fan-Out | 0,688 | 0,698 | 0,767 |
| Variable top Fan-Out | fan_out_dev | fan_out_dev | fan_out_dev |
| % interno Fan-In | 8,6 | – | – |
| % interno Fan-Out | 8,4 | – | – |
| Retención B/A | – | – | 66,4 |

## 3. Tamaño y ceros

**A: con familias** (N = 4.080.297)

| Celda | N | % |
| :--- | ---: | ---: |
| Aislado (Fan-In 0, Fan-Out 0) | 1.297.827 | 31,8 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | 2.084.853 | 51,1 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | 187.615 | 4,6 |
| Con ambas conexiones | 510.002 | 12,5 |

**A externo: mismos paquetes, solo vinculos externos** (N = 4.080.297)

| Celda | N | % |
| :--- | ---: | ---: |
| Aislado (Fan-In 0, Fan-Out 0) | 1.520.157 | 37,3 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | 2.144.576 | 52,6 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | 135.769 | 3,3 |
| Con ambas conexiones | 279.795 | 6,9 |

**B: sin familias** (N = 2.709.168)

| Celda | N | % |
| :--- | ---: | ---: |
| Aislado (Fan-In 0, Fan-Out 0) | 939.787 | 34,7 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | 1.454.290 | 53,7 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | 94.460 | 3,5 |
| Con ambas conexiones | 220.631 | 8,1 |

## 4. Grilla conjunta

**A: con familias**

| FI \ FO | 0 | 1-2 | 3-9 | 10-49 | 50+ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1.297.827 | 980.156 | 816.248 | 273.571 | 14.878 |
| 1-9 | 169.002 | 211.516 | 192.849 | 55.426 | 1.861 |
| 10-99 | 15.149 | 16.467 | 16.649 | 6.423 | 520 |
| 100-999 | 2.829 | 2.555 | 2.988 | 1.102 | 260 |
| 1000+ | 635 | 436 | 675 | 269 | 6 |

**A externo: mismos paquetes, solo vinculos externos**

| FI \ FO | 0 | 1-2 | 3-9 | 10-49 | 50+ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1.520.157 | 1.028.440 | 832.020 | 269.182 | 14.934 |
| 1-9 | 118.289 | 118.169 | 97.731 | 30.081 | 1.110 |
| 10-99 | 13.695 | 11.818 | 9.758 | 3.716 | 433 |
| 100-999 | 3.074 | 2.416 | 2.479 | 707 | 192 |
| 1000+ | 711 | 414 | 591 | 176 | 4 |

**B: sin familias**

| FI \ FO | 0 | 1-2 | 3-9 | 10-49 | 50+ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 0 | 939.787 | 677.952 | 578.111 | 187.318 | 10.909 |
| 1-9 | 81.985 | 92.023 | 78.613 | 24.425 | 882 |
| 10-99 | 9.510 | 8.324 | 7.310 | 2.939 | 403 |
| 100-999 | 2.381 | 1.869 | 2.036 | 580 | 186 |
| 1000+ | 584 | 341 | 534 | 162 | 4 |

## 5. Estadísticos por variable

**A: con familias**

| Variable | % cero | Mediana | p90 | p99 | Máx |
| :--- | ---: | ---: | ---: | ---: | ---: |
| fi | 82,9 | 0,000 | 1 | 18 | 195.952 |
| fo | 36,4 | 1,000 | 9 | 34 | 1.000 |
| n_versions | 0,0 | 3,000 | 24 | 251 | 37.328 |
| n_maintainers | 0,0 | 1,000 | 2 | 11 | 754 |
| n_keywords | 49,0 | 1,000 | 8 | 17 | 1.939 |
| n_peer | 79,2 | 0,000 | 2 | 7 | 708 |
| n_opt | 98,4 | 0,000 | 0 | 1 | 106 |
| age_years | 0,1 | 3,855 | 9 | 12 | 15 |
| fan_in_dev | 94,3 | 0,000 | 0 | 8 | 1.224.874 |
| fan_out_dev | 41,9 | 2,000 | 17 | 45 | 881 |

| Variable | % verdadero |
| :--- | ---: |
| has_github | 58,1 |
| deprecated | 3,2 |
| scoped | 39,3 |

**A externo: mismos paquetes, solo vinculos externos**

| Variable | % cero | Mediana | p90 | p99 | Máx |
| :--- | ---: | ---: | ---: | ---: | ---: |
| fi | 89,8 | 0,000 | 1 | 13 | 195.952 |
| fo | 40,6 | 1,000 | 8 | 32 | 1.000 |
| n_versions | 0,0 | 3,000 | 24 | 251 | 37.328 |
| n_maintainers | 0,0 | 1,000 | 2 | 11 | 754 |
| n_keywords | 49,0 | 1,000 | 8 | 17 | 1.939 |
| n_peer | 79,2 | 0,000 | 2 | 7 | 708 |
| n_opt | 98,4 | 0,000 | 0 | 1 | 106 |
| age_years | 0,1 | 3,855 | 9 | 12 | 15 |
| fan_in_dev | 94,3 | 0,000 | 0 | 8 | 1.224.874 |
| fan_out_dev | 41,9 | 2,000 | 17 | 45 | 881 |

| Variable | % verdadero |
| :--- | ---: |
| has_github | 58,1 |
| deprecated | 3,2 |
| scoped | 39,3 |

**B: sin familias**

| Variable | % cero | Mediana | p90 | p99 | Máx |
| :--- | ---: | ---: | ---: | ---: | ---: |
| fi | 88,4 | 0,000 | 1 | 16 | 195.952 |
| fo | 38,2 | 1,000 | 8 | 34 | 1.000 |
| n_versions | 0,0 | 2,000 | 17 | 107 | 37.328 |
| n_maintainers | 0,0 | 1,000 | 1 | 4 | 622 |
| n_keywords | 47,9 | 1,000 | 7 | 17 | 1.939 |
| n_peer | 84,2 | 0,000 | 1 | 5 | 708 |
| n_opt | 99,3 | 0,000 | 0 | 0 | 106 |
| age_years | 0,1 | 4,545 | 10 | 13 | 15 |
| fan_in_dev | 95,9 | 0,000 | 0 | 7 | 1.224.874 |
| fan_out_dev | 44,2 | 1,000 | 17 | 46 | 687 |

| Variable | % verdadero |
| :--- | ---: |
| has_github | 56,1 |
| deprecated | 2,9 |
| scoped | 8,6 |

## 6. Spearman

**ρ de Spearman con Fan-In**

| Variable | A Todos | A Positivos | A ext Todos | A ext Positivos | B Todos | B Positivos |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| n_versions | 0,248 | 0,226 | 0,191 | 0,231 | 0,206 | 0,219 |
| n_maintainers | 0,166 | 0,144 | 0,091 | 0,185 | 0,152 | 0,188 |
| n_keywords | 0,011 | 0,065 | 0,049 | 0,105 | 0,065 | 0,121 |
| n_peer | 0,004 | -0,000 | -0,031 | 0,055 | -0,028 | 0,043 |
| n_opt | -0,023 | 0,006 | -0,016 | 0,008 | 0,007 | 0,013 |
| age_years | 0,066 | 0,112 | 0,177 | 0,169 | 0,192 | 0,179 |
| has_github | 0,109 | 0,136 | 0,118 | 0,177 | 0,138 | 0,182 |
| deprecated | 0,033 | 0,001 | 0,028 | 0,012 | 0,035 | 0,011 |
| scoped | 0,151 | -0,020 | -0,094 | -0,018 | -0,085 | -0,070 |
| fan_in_dev | 0,261 | 0,323 | 0,263 | 0,418 | 0,310 | 0,412 |
| fan_out_dev | 0,068 | 0,064 | 0,074 | 0,111 | 0,091 | 0,124 |
| fo | 0,082 | 0,048 | 0,048 | 0,036 | 0,052 | 0,037 |

**Diferencias de ρ con Fan-In (todos)**

| Variable | A ext − A |  | B − A ext |  |
| :--- | ---: | :---: | ---: | :---: |
| n_versions | -0,057 |  | 0,014 |  |
| n_maintainers | -0,075 |  | 0,062 |  |
| n_keywords | 0,038 |  | 0,016 |  |
| n_peer | -0,034 |  ⚠ | 0,002 |  |
| n_opt | 0,007 |  | 0,023 |  |
| age_years | 0,111 |  | 0,015 |  |
| has_github | 0,008 |  | 0,020 |  |
| deprecated | -0,005 |  | 0,008 |  |
| scoped | -0,245 |  ⚠ | 0,008 |  |
| fan_in_dev | 0,002 |  | 0,047 |  |
| fan_out_dev | 0,006 |  | 0,017 |  |
| fo | -0,034 |  | 0,003 |  |

**ρ de Spearman con Fan-Out**

| Variable | A Todos | A Positivos | A ext Todos | A ext Positivos | B Todos | B Positivos |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| n_versions | 0,173 | 0,106 | 0,131 | 0,083 | 0,151 | 0,089 |
| n_maintainers | 0,090 | 0,041 | 0,031 | 0,023 | 0,063 | 0,044 |
| n_keywords | -0,013 | -0,005 | -0,007 | 0,003 | 0,029 | 0,022 |
| n_peer | 0,000 | -0,058 | -0,023 | -0,055 | -0,014 | -0,050 |
| n_opt | -0,037 | 0,061 | -0,033 | 0,061 | 0,056 | 0,067 |
| age_years | -0,007 | 0,005 | 0,032 | 0,006 | -0,027 | -0,035 |
| has_github | 0,065 | 0,018 | 0,055 | 0,008 | 0,088 | 0,015 |
| deprecated | 0,007 | 0,004 | -0,002 | -0,001 | -0,004 | 0,003 |
| scoped | 0,041 | 0,008 | -0,065 | -0,027 | 0,007 | 0,027 |
| fan_in_dev | 0,029 | 0,026 | 0,016 | 0,016 | 0,022 | 0,011 |
| fan_out_dev | 0,258 | 0,200 | 0,260 | 0,219 | 0,259 | 0,204 |
| fi | 0,082 | 0,013 | 0,048 | 0,002 | 0,052 | -0,002 |

**Diferencias de ρ con Fan-Out (todos)**

| Variable | A ext − A |  | B − A ext |  |
| :--- | ---: | :---: | ---: | :---: |
| n_versions | -0,042 |  | 0,019 |  |
| n_maintainers | -0,059 |  | 0,033 |  |
| n_keywords | 0,006 |  | 0,036 |  ⚠ |
| n_peer | -0,024 |  | 0,009 |  |
| n_opt | 0,004 |  | 0,089 |  ⚠ |
| age_years | 0,039 |  ⚠ | -0,059 |  ⚠ |
| has_github | -0,010 |  | 0,032 |  |
| deprecated | -0,009 |  | -0,002 |  |
| scoped | -0,106 |  ⚠ | 0,072 |  ⚠ |
| fan_in_dev | -0,013 |  | 0,006 |  |
| fan_out_dev | 0,002 |  | -0,001 |  |
| fi | -0,034 |  | 0,003 |  |

## 7. Correlación entre Fan-In y Fan-Out y pares redundantes

| Grupo | ρ todos | ρ ambos > 0 |
| :--- | ---: | ---: |
| A: con familias | 0,082 | 0,082 |
| A externo: mismos paquetes, solo vinculos externos | 0,048 | 0,091 |
| B: sin familias | 0,052 | 0,117 |

Sin pares redundantes — A: con familias

Sin pares redundantes — A externo: mismos paquetes, solo vinculos externos

Sin pares redundantes — B: sin familias

## 8. AUC Mann-Whitney

**AUC con Fan-In**

| Variable | A | A ext | B |
| :--- | ---: | ---: | ---: |
| n_versions | 0,681 | 0,675 | 0,676 |
| n_maintainers | 0,571 | 0,548 | 0,548 |
| n_keywords | 0,506 | 0,542 | 0,553 |
| n_peer | 0,502 | 0,479 | 0,483 |
| n_opt | 0,496 | 0,497 | 0,501 |
| age_years | 0,547 | 0,666 | 0,670 |
| has_github | 0,569 | 0,594 | 0,604 |
| deprecated | 0,508 | 0,508 | 0,509 |
| scoped | 0,599 | 0,424 | 0,463 |
| fan_in_dev | 0,574 | 0,596 | 0,591 |
| fan_out_dev | 0,549 | 0,566 | 0,576 |

**AUC con Fan-Out**

| Variable | A | A ext | B |
| :--- | ---: | ---: | ---: |
| n_versions | 0,590 | 0,567 | 0,578 |
| n_maintainers | 0,529 | 0,509 | 0,511 |
| n_keywords | 0,493 | 0,495 | 0,514 |
| n_peer | 0,512 | 0,498 | 0,502 |
| n_opt | 0,491 | 0,493 | 0,503 |
| age_years | 0,494 | 0,520 | 0,492 |
| has_github | 0,534 | 0,530 | 0,548 |
| deprecated | 0,501 | 0,500 | 0,499 |
| scoped | 0,522 | 0,469 | 0,499 |
| fan_in_dev | 0,505 | 0,503 | 0,504 |
| fan_out_dev | 0,620 | 0,617 | 0,619 |

## 9. Tamaño de efecto

**Efecto con Fan-In**

| Variable | Medida | A | A ext | B |
| :--- | ---: | ---: | ---: | ---: |
| n_versions | ε² | 0,060 | 0,037 | 0,041 |
| n_maintainers | ε² | 0,010 | 0,004 | 0,004 |
| n_keywords | ε² | 0,001 | 0,003 | 0,005 |
| n_peer | ε² | 0,000 | 0,001 | 0,000 |
| n_opt | ε² | 0,000 | 0,000 | 0,000 |
| age_years | ε² | 0,008 | 0,032 | 0,038 |
| has_github | Cramér V | 0,116 | 0,123 | 0,143 |
| deprecated | Cramér V | 0,033 | 0,028 | 0,035 |
| scoped | Cramér V | 0,157 | 0,094 | 0,085 |
| fan_in_dev | ε² | 0,019 | 0,020 | 0,021 |
| fan_out_dev | ε² | 0,004 | 0,005 | 0,008 |

**Efecto con Fan-Out**

| Variable | Medida | A | A ext | B |
| :--- | ---: | ---: | ---: | ---: |
| n_versions | ε² | 0,028 | 0,016 | 0,021 |
| n_maintainers | ε² | 0,003 | 0,000 | 0,001 |
| n_keywords | ε² | 0,001 | 0,001 | 0,002 |
| n_peer | ε² | 0,002 | 0,001 | 0,001 |
| n_opt | ε² | 0,000 | 0,000 | 0,000 |
| age_years | ε² | 0,000 | 0,002 | 0,002 |
| has_github | Cramér V | 0,070 | 0,063 | 0,098 |
| deprecated | Cramér V | 0,007 | 0,004 | 0,008 |
| scoped | Cramér V | 0,045 | 0,066 | 0,020 |
| fan_in_dev | ε² | 0,000 | 0,000 | 0,000 |
| fan_out_dev | ε² | 0,059 | 0,061 | 0,060 |

## 10. Información mutua normalizada

**NMI con Fan-In**

| Variable | A | A ext | B |
| :--- | ---: | ---: | ---: |
| n_versions | 0,061 | 0,052 | 0,053 |
| n_maintainers | 0,023 | 0,012 | 0,023 |
| n_keywords | 0,002 | 0,006 | 0,009 |
| n_peer | 0,000 | 0,002 | 0,002 |
| n_opt | 0,000 | 0,000 | 0,000 |
| age_years | 0,014 | 0,050 | 0,058 |
| has_github | 0,014 | 0,023 | 0,028 |
| deprecated | 0,001 | 0,001 | 0,001 |
| scoped | 0,023 | 0,012 | 0,012 |
| fan_in_dev | 0,000 | 0,000 | 0,000 |
| fan_out_dev | 0,005 | 0,006 | 0,012 |

**NMI con Fan-Out**

| Variable | A | A ext | B |
| :--- | ---: | ---: | ---: |
| n_versions | 0,016 | 0,010 | 0,013 |
| n_maintainers | 0,003 | 0,000 | 0,001 |
| n_keywords | 0,002 | 0,001 | 0,002 |
| n_peer | 0,002 | 0,001 | 0,001 |
| n_opt | 0,000 | 0,000 | 0,000 |
| age_years | 0,011 | 0,014 | 0,019 |
| has_github | 0,002 | 0,002 | 0,004 |
| deprecated | 0,000 | 0,000 | 0,000 |
| scoped | 0,001 | 0,002 | 0,000 |
| fan_in_dev | 0,000 | 0,000 | 0,000 |
| fan_out_dev | 0,025 | 0,026 | 0,029 |

## 11. Techo de explicación e importancia por permutación

| Grupo | Objetivo | R² | AUC | Top regresor | Top clasificador |
| :--- | ---: | ---: | ---: | ---: | ---: |
| A | Fan-In | 0,321 | 0,777 | fan_in_dev | n_versions |
| A | Fan-Out | 0,195 | 0,688 | fan_out_dev | fan_out_dev |
| A ext | Fan-In | 0,382 | 0,809 | fan_in_dev | n_versions |
| A ext | Fan-Out | 0,185 | 0,698 | fan_out_dev | fan_out_dev |
| B | Fan-In | 0,390 | 0,814 | fan_in_dev | age_years |
| B | Fan-Out | 0,257 | 0,767 | fan_out_dev | fan_out_dev |

**Importancia clasificador — A — Fan-In**

| Variable | Importancia |
| :--- | ---: |
| n_versions | 0,081 |
| scoped | 0,060 |
| age_years | 0,053 |
| fan_out_dev | 0,024 |
| fan_in_dev | 0,023 |
| n_keywords | 0,017 |
| has_github | 0,012 |
| n_peer | 0,008 |
| n_maintainers | 0,003 |
| deprecated | 0,002 |
| n_opt | 0,000 |

**Importancia clasificador — A — Fan-Out**

| Variable | Importancia |
| :--- | ---: |
| fan_out_dev | 0,116 |
| age_years | 0,063 |
| n_versions | 0,061 |
| n_peer | 0,033 |
| has_github | 0,010 |
| n_keywords | 0,010 |
| scoped | 0,005 |
| n_maintainers | 0,003 |
| fan_in_dev | 0,002 |
| deprecated | 0,000 |
| n_opt | -0,049 |

**Importancia clasificador — A ext — Fan-In**

| Variable | Importancia |
| :--- | ---: |
| n_versions | 0,093 |
| age_years | 0,070 |
| scoped | 0,043 |
| fan_in_dev | 0,023 |
| fan_out_dev | 0,023 |
| has_github | 0,015 |
| n_keywords | 0,010 |
| n_peer | 0,008 |
| n_maintainers | 0,003 |
| deprecated | 0,001 |
| n_opt | 0,000 |

**Importancia clasificador — A ext — Fan-Out**

| Variable | Importancia |
| :--- | ---: |
| fan_out_dev | 0,128 |
| age_years | 0,069 |
| n_versions | 0,047 |
| n_peer | 0,035 |
| scoped | 0,012 |
| n_keywords | 0,010 |
| has_github | 0,010 |
| n_maintainers | 0,002 |
| fan_in_dev | 0,002 |
| deprecated | 0,000 |
| n_opt | -0,041 |

**Importancia clasificador — B — Fan-In**

| Variable | Importancia |
| :--- | ---: |
| age_years | 0,085 |
| n_versions | 0,083 |
| fan_out_dev | 0,029 |
| fan_in_dev | 0,024 |
| has_github | 0,021 |
| scoped | 0,015 |
| n_keywords | 0,015 |
| n_peer | 0,009 |
| n_maintainers | 0,002 |
| deprecated | 0,001 |
| n_opt | 0,000 |

**Importancia clasificador — B — Fan-Out**

| Variable | Importancia |
| :--- | ---: |
| fan_out_dev | 0,144 |
| age_years | 0,111 |
| n_versions | 0,065 |
| n_peer | 0,041 |
| has_github | 0,012 |
| n_keywords | 0,012 |
| n_opt | 0,003 |
| fan_in_dev | 0,001 |
| deprecated | 0,001 |
| scoped | 0,001 |
| n_maintainers | 0,001 |

## 12. Perfiles por tramo y celda de ceros

**Perfil por tramo de Fan-In**

| Nivel | Grupo | N | % | med_n_versions | med_n_maintainers | med_n_keywords | med_age_years | % has_github | % scoped | % deprecated | % fan_in_dev>0 | % fan_out_dev>0 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | A | 3.382.680 | 82,9 | 2,000 | 1,000 | 1,000 | 3,693 | 55,8 | 35,9 | 3,0 | 3,2 | 56,0 |
| 0 | A ext | 3.664.733 | 89,8 | 3,000 | 1,000 | 1,000 | 3,587 | 56,2 | 40,8 | 3,1 | 3,8 | 56,7 |
| 0 | B | 2.394.077 | 88,4 | 2,000 | 1,000 | 1,000 | 4,227 | 53,7 | 9,4 | 2,7 | 2,0 | 54,0 |
| 1-9 | A | 630.654 | 15,5 | 6,000 | 1,000 | 1,000 | 4,392 | 67,6 | 56,9 | 4,5 | 13,6 | 67,9 |
| 1-9 | A ext | 365.380 | 9,0 | 6,000 | 1,000 | 2,000 | 6,174 | 72,5 | 25,6 | 4,6 | 16,3 | 69,1 |
| 1-9 | B | 277.928 | 10,3 | 5,000 | 1,000 | 2,000 | 7,264 | 72,0 | 2,2 | 4,4 | 13,9 | 68,8 |
| 10-99 | A | 55.208 | 1,4 | 20,000 | 1,000 | 3,000 | 6,508 | 85,2 | 48,7 | 4,9 | 53,9 | 73,0 |
| 10-99 | A ext | 39.420 | 1,0 | 20,000 | 1,000 | 3,000 | 8,134 | 91,6 | 28,2 | 5,3 | 65,1 | 77,5 |
| 10-99 | B | 28.486 | 1,1 | 13,000 | 1,000 | 4,000 | 9,511 | 92,3 | 0,7 | 5,2 | 61,6 | 78,3 |
| 100-999 | A | 9.734 | 0,2 | 23,000 | 1,000 | 3,000 | 8,549 | 96,9 | 27,9 | 5,0 | 77,4 | 73,2 |
| 100-999 | A ext | 8.868 | 0,2 | 25,000 | 1,000 | 4,000 | 9,088 | 97,8 | 20,8 | 4,7 | 82,3 | 76,2 |
| 100-999 | B | 7.052 | 0,3 | 18,500 | 1,000 | 4,000 | 10,137 | 98,1 | 0,4 | 4,7 | 79,5 | 76,8 |
| 1000+ | A | 2.021 | 0,0 | 34,000 | 1,000 | 3,000 | 10,335 | 98,5 | 19,8 | 3,1 | 79,7 | 78,8 |
| 1000+ | A ext | 1.896 | 0,0 | 38,000 | 1,000 | 4,000 | 10,689 | 98,5 | 14,6 | 3,3 | 84,6 | 83,5 |
| 1000+ | B | 1.625 | 0,1 | 31,000 | 1,000 | 4,000 | 11,253 | 98,7 | 0,3 | 3,1 | 83,0 | 84,4 |

**Perfil por tramo de Fan-Out**

| Nivel | Grupo | N | % | med_n_versions | med_n_maintainers | med_n_keywords | med_age_years | % has_github | % scoped | % deprecated | % fan_in_dev>0 | % fan_out_dev>0 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | A | 1.485.442 | 36,4 | 2,000 | 1,000 | 1,000 | 4,101 | 53,8 | 36,4 | 3,1 | 5,0 | 44,1 |
| 0 | A ext | 1.655.926 | 40,6 | 2,000 | 1,000 | 1,000 | 3,923 | 54,6 | 43,0 | 3,3 | 5,4 | 45,8 |
| 0 | B | 1.034.247 | 38,2 | 2,000 | 1,000 | 1,000 | 4,802 | 50,2 | 8,7 | 3,0 | 3,6 | 42,3 |
| 1-2 | A | 1.211.130 | 29,7 | 3,000 | 1,000 | 1,000 | 3,696 | 59,5 | 40,6 | 3,3 | 5,5 | 59,4 |
| 1-2 | A ext | 1.161.257 | 28,5 | 3,000 | 1,000 | 1,000 | 3,844 | 59,7 | 38,1 | 3,2 | 5,6 | 59,6 |
| 1-2 | B | 780.509 | 28,8 | 2,000 | 1,000 | 1,000 | 4,583 | 58,5 | 7,9 | 2,7 | 4,2 | 57,1 |
| 3-9 | A | 1.029.409 | 25,2 | 4,000 | 1,000 | 1,000 | 3,797 | 62,2 | 41,2 | 3,4 | 6,4 | 72,3 |
| 3-9 | A ext | 942.579 | 23,1 | 4,000 | 1,000 | 1,000 | 3,932 | 62,2 | 35,7 | 3,2 | 6,1 | 72,8 |
| 3-9 | B | 666.604 | 24,6 | 3,000 | 1,000 | 1,000 | 4,449 | 62,0 | 9,1 | 2,9 | 4,6 | 70,8 |
| 10-49 | A | 336.791 | 8,3 | 4,000 | 1,000 | 0,000 | 3,206 | 60,0 | 41,4 | 3,2 | 6,9 | 71,0 |
| 10-49 | A ext | 303.862 | 7,4 | 4,000 | 1,000 | 0,000 | 3,291 | 58,6 | 35,1 | 3,0 | 6,6 | 72,6 |
| 10-49 | B | 215.424 | 8,0 | 3,000 | 1,000 | 0,000 | 3,368 | 57,7 | 8,4 | 2,7 | 4,5 | 69,0 |
| 50+ | A | 17.525 | 0,4 | 3,000 | 1,000 | 0,000 | 3,346 | 61,8 | 38,4 | 2,8 | 7,3 | 74,5 |
| 50+ | A ext | 16.673 | 0,4 | 3,000 | 1,000 | 0,000 | 3,406 | 61,2 | 35,3 | 2,7 | 6,9 | 75,3 |
| 50+ | B | 12.384 | 0,5 | 2,000 | 1,000 | 0,000 | 3,374 | 59,9 | 12,9 | 2,3 | 5,0 | 71,9 |

**Perfil por celda de ceros**

| Nivel | Grupo | N | % | med_n_versions | med_n_maintainers | med_n_keywords | med_age_years | % has_github | % scoped | % deprecated | % fan_in_dev>0 | % fan_out_dev>0 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Aislado (Fan-In 0, Fan-Out 0) | A | 1.297.827 | 31,8 | 2,000 | 1,000 | 1,000 | 4,033 | 51,3 | 34,4 | 2,9 | 2,9 | 41,3 |
| Aislado (Fan-In 0, Fan-Out 0) | A ext | 1.520.157 | 37,3 | 2,000 | 1,000 | 1,000 | 3,688 | 52,6 | 44,0 | 3,2 | 3,7 | 44,2 |
| Aislado (Fan-In 0, Fan-Out 0) | B | 939.787 | 34,7 | 2,000 | 1,000 | 0,000 | 4,512 | 47,4 | 9,4 | 2,9 | 1,7 | 40,0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | A | 2.084.853 | 51,1 | 3,000 | 1,000 | 0,000 | 3,493 | 58,6 | 36,8 | 3,0 | 3,4 | 65,1 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | A ext | 2.144.576 | 52,6 | 3,000 | 1,000 | 0,000 | 3,515 | 58,8 | 38,6 | 3,0 | 3,8 | 65,6 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | B | 1.454.290 | 53,7 | 2,000 | 1,000 | 1,000 | 3,995 | 57,7 | 9,5 | 2,5 | 2,2 | 63,0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | A | 187.615 | 4,6 | 5,000 | 1,000 | 2,000 | 5,142 | 70,7 | 50,6 | 4,3 | 19,9 | 63,6 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | A ext | 135.769 | 3,3 | 6,000 | 1,000 | 3,000 | 6,667 | 77,0 | 31,7 | 4,4 | 24,6 | 64,2 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | B | 94.460 | 3,5 | 5,000 | 1,000 | 3,000 | 8,287 | 77,3 | 1,9 | 4,3 | 22,7 | 64,3 |
| Con ambas conexiones | A | 510.002 | 12,5 | 8,000 | 1,000 | 0,000 | 4,400 | 69,1 | 57,6 | 4,6 | 17,1 | 70,2 |
| Con ambas conexiones | A ext | 279.795 | 6,9 | 8,000 | 1,000 | 2,000 | 6,308 | 74,1 | 22,8 | 4,8 | 21,7 | 73,0 |
| Con ambas conexiones | B | 220.631 | 8,1 | 6,000 | 1,000 | 2,000 | 7,225 | 73,3 | 2,1 | 4,6 | 18,9 | 72,3 |

## 13. Familias

**Parte interna y externa — Fan-In**

| Tramo | Interno | Externo | % interno |
| :--- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0,0 |
| 1-9 | 582.080 | 735.179 | 44,2 |
| 10-99 | 327.697 | 1.142.867 | 22,3 |
| 100-999 | 182.026 | 2.801.224 | 6,1 |
| 1000+ | 193.609 | 9.045.482 | 2,1 |
| Total | 1.285.412 | 13.724.752 | 8,6 |

**Parte interna y externa — Fan-Out**

| Tramo | Interno | Externo | % interno |
| :--- | ---: | ---: | ---: |
| 0 | 0 | 0 | 0,0 |
| 1-2 | 207.318 | 1.446.647 | 12,5 |
| 3-9 | 458.587 | 4.636.259 | 9,0 |
| 10-49 | 506.149 | 5.419.317 | 8,5 |
| 50+ | 65.019 | 1.993.667 | 3,2 |
| Total | 1.237.073 | 13.495.890 | 8,4 |

**Cambio de estrato A → A externo**

| Cambio | N | % |
| :--- | ---: | ---: |
| no_change | 3.610.648 | 88,5 |
| fi_only | 194.321 | 4,8 |
| fo_only | 181.350 | 4,4 |
| both | 93.978 | 2,3 |

**Cruce Fan-In: total vs externo**

| FI \ FO | 0 | 1-9 | 10-99 | 100-999 | 1000+ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 0 | 3.382.680 | 0 | 0 | 0 | 0 |
| 1-9 | 271.283 | 359.371 | 0 | 0 | 0 |
| 10-99 | 10.077 | 5.933 | 39.198 | 0 | 0 |
| 100-999 | 588 | 71 | 222 | 8.853 | 0 |
| 1000+ | 105 | 5 | 0 | 15 | 1.896 |

**Cruce Fan-Out: total vs externo**

| FI \ FO | 0 | 1-2 | 3-9 | 10-49 | 50+ |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 0 | 1.485.442 | 0 | 0 | 0 | 0 |
| 1-2 | 130.823 | 1.080.307 | 0 | 0 | 0 |
| 3-9 | 33.421 | 76.893 | 919.095 | 0 | 0 |
| 10-49 | 5.917 | 3.989 | 23.433 | 303.452 | 0 |
| 50+ | 323 | 68 | 51 | 410 | 16.673 |

**Cruce Celda de ceros: total vs externo**

| FI \ FO | Aislado (Fan-In 0, Fan-Out 0) | Consumidor (Fan-In 0, Fan-Out mayor a 0) | Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | Con ambas conexiones |
| :--- | ---: | ---: | ---: | ---: |
| Aislado (Fan-In 0, Fan-Out 0) | 1.297.827 | 0 | 0 | 0 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | 97.219 | 1.987.634 | 0 | 0 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | 68.143 | 0 | 119.472 | 0 |
| Con ambas conexiones | 56.968 | 156.942 | 16.297 | 279.795 |

**Retención B/A por grilla conjunta**

| FI tramo | FO tramo | N en A | Retenidos | % |
| :--- | ---: | ---: | ---: | ---: |
| 0 | 0 | 1.297.827 | 939.787 | 72,4 |
| 0 | 1-2 | 980.156 | 677.952 | 69,2 |
| 0 | 3-9 | 816.248 | 578.111 | 70,8 |
| 0 | 10-49 | 273.571 | 187.318 | 68,5 |
| 0 | 50+ | 14.878 | 10.909 | 73,3 |
| 1-9 | 0 | 169.002 | 81.985 | 48,5 |
| 1-9 | 1-2 | 211.516 | 92.023 | 43,5 |
| 1-9 | 3-9 | 192.849 | 78.613 | 40,8 |
| 1-9 | 10-49 | 55.426 | 24.425 | 44,1 |
| 1-9 | 50+ | 1.861 | 882 | 47,4 |
| 10-99 | 0 | 15.149 | 9.510 | 62,8 |
| 10-99 | 1-2 | 16.467 | 8.324 | 50,5 |
| 10-99 | 3-9 | 16.649 | 7.310 | 43,9 |
| 10-99 | 10-49 | 6.423 | 2.939 | 45,8 |
| 10-99 | 50+ | 520 | 403 | 77,5 |
| 100-999 | 0 | 2.829 | 2.381 | 84,2 |
| 100-999 | 1-2 | 2.555 | 1.869 | 73,2 |
| 100-999 | 3-9 | 2.988 | 2.036 | 68,1 |
| 100-999 | 10-49 | 1.102 | 580 | 52,6 |
| 100-999 | 50+ | 260 | 186 | 71,5 |
| 1000+ | 0 | 635 | 584 | 92,0 |
| 1000+ | 1-2 | 436 | 341 | 78,2 |
| 1000+ | 3-9 | 675 | 534 | 79,1 |
| 1000+ | 10-49 | 269 | 162 | 60,2 |
| 1000+ | 50+ | 6 | 4 | 66,7 |

**Retención por tramo Fan-In**

| Nivel | N en A | Retenidos | % |
| :--- | ---: | ---: | ---: |
| 0 | 3.382.680 | 2.394.077 | 70,8 |
| 1-9 | 630.654 | 277.928 | 44,1 |
| 10-99 | 55.208 | 28.486 | 51,6 |
| 100-999 | 9.734 | 7.052 | 72,4 |
| 1000+ | 2.021 | 1.625 | 80,4 |

**Retención por tramo Fan-Out**

| Nivel | N en A | Retenidos | % |
| :--- | ---: | ---: | ---: |
| 0 | 1.485.442 | 1.034.247 | 69,6 |
| 1-2 | 1.211.130 | 780.509 | 64,4 |
| 3-9 | 1.029.409 | 666.604 | 64,8 |
| 10-49 | 336.791 | 215.424 | 64,0 |
| 50+ | 17.525 | 12.384 | 70,7 |

**Retención por celda de ceros**

| Nivel | N en A | Retenidos | % |
| :--- | ---: | ---: | ---: |
| Aislado (Fan-In 0, Fan-Out 0) | 1.297.827 | 939.787 | 72,4 |
| Consumidor (Fan-In 0, Fan-Out mayor a 0) | 2.084.853 | 1.454.290 | 69,8 |
| Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | 187.615 | 94.460 | 50,3 |
| Con ambas conexiones | 510.002 | 220.631 | 43,3 |

**Retención por año de creación**

| Nivel | N en A | Retenidos | % |
| :--- | ---: | ---: | ---: |
| 2010 | 109 | 109 | 100,0 |
| 2011 | 4.879 | 4.879 | 100,0 |
| 2012 | 13.124 | 13.124 | 100,0 |
| 2013 | 31.488 | 31.488 | 100,0 |
| 2014 | 61.124 | 61.124 | 100,0 |
| 2015 | 103.235 | 100.958 | 97,8 |
| 2016 | 159.303 | 148.609 | 93,3 |
| 2017 | 201.138 | 176.114 | 87,6 |
| 2018 | 244.602 | 187.179 | 76,5 |
| 2019 | 278.313 | 188.954 | 67,9 |
| 2020 | 293.956 | 194.478 | 66,2 |
| 2021 | 327.560 | 211.955 | 64,7 |
| 2022 | 364.983 | 206.782 | 56,7 |
| 2023 | 365.976 | 235.603 | 64,4 |
| 2024 | 610.430 | 447.959 | 73,4 |
| 2025 | 365.965 | 212.680 | 58,1 |
| 2026 | 654.112 | 287.173 | 43,9 |

**Retención por scoped**

| Nivel | N en A | Retenidos | % |
| :--- | ---: | ---: | ---: |
| scoped | 1.603.427 | 232.298 | 14,5 |
| unscoped | 2.476.870 | 2.476.870 | 100,0 |

**Los que salen vs los que se quedan**

| Métrica | Salen (familia) | Se quedan |
| :--- | ---: | ---: |
| N | 1.371.129 | 2.709.168 |
| med_n_versions | 4,0 | 2,0 |
| med_n_maintainers | 1,0 | 1,0 |
| med_age_years | 2,7 | 4,5 |
| pct_nonzero_n_keywords | 48,8 | 52,1 |
| pct_nonzero_n_peer | 30,7 | 15,8 |
| pct_nonzero_n_opt | 3,4 | 0,7 |
| pct_nonzero_fan_in_dev | 8,8 | 4,1 |
| pct_nonzero_fan_out_dev | 62,6 | 55,8 |
| pct_fi_gt0 | 27,9 | 11,6 |
| p90_fi | 2,000 | 1,000 |
| p99_fi | 20,000 | 16,000 |
| pct_fo_gt0 | 67,1 | 61,8 |
| p90_fo | 9,000 | 8,000 |
| p99_fo | 34,000 | 34,000 |
| pct_has_github | 62,2 | 56,1 |
| pct_deprecated | 3,9 | 2,9 |
| pct_scoped | 100,0 | 8,6 |
| by_zero_cell: Aislado (Fan-In 0, Fan-Out 0) | 26,1 | 34,7 |
| by_zero_cell: Consumidor (Fan-In 0, Fan-Out mayor a 0) | 46,0 | 53,7 |
| by_zero_cell: Consumido sin consumir (Fan-In mayor a 0, Fan-Out 0) | 6,8 | 3,5 |
| by_zero_cell: Con ambas conexiones | 21,1 | 8,1 |
| by_fi_tramo: 0 | 72,1 | 88,4 |
| by_fi_tramo: 1-9 | 25,7 | 10,3 |
| by_fi_tramo: 10-99 | 1,9 | 1,1 |
| by_fi_tramo: 100-999 | 0,2 | 0,3 |
| by_fi_tramo: 1000+ | 0,0 | 0,1 |
| by_fo_tramo: 0 | 32,9 | 38,2 |
| by_fo_tramo: 1-2 | 31,4 | 28,8 |
| by_fo_tramo: 3-9 | 26,5 | 24,6 |
| by_fo_tramo: 10-49 | 8,9 | 8,0 |
| by_fo_tramo: 50+ | 0,4 | 0,5 |

*Nota: scoped is 100% for leavers by definition*

## 14. Gráficos

**Grilla conjunta Fan-In × Fan-Out**

![Grilla conjunta Fan-In × Fan-Out](figures/fig01_joint_grid.png)

**Retención B/A por celda de la grilla**

![Retención B/A por celda de la grilla](figures/fig02_retention_B_over_A.png)

**Cambio de tramo A → A externo**

![Cambio de tramo A → A externo](figures/fig03_band_change_A_to_A_external.png)

**ρ de Spearman con Fan-In**

![ρ de Spearman con Fan-In](figures/fig04_rho_fan_in.png)

**ρ de Spearman con Fan-Out**

![ρ de Spearman con Fan-Out](figures/fig05_rho_fan_out.png)

**ρ por grupo**

![ρ por grupo](figures/fig06_rho_by_group.png)

**AUC e información mutua**

![AUC e información mutua](figures/fig07_auc_and_mutual_information.png)

**Importancia por permutación**

![Importancia por permutación](figures/fig08_permutation_importance.png)

**Techo de explicación**

![Techo de explicación](figures/fig09_model_ceiling.png)

**Perfil por tramo Fan-In**

![Perfil por tramo Fan-In](figures/fig10_profile_by_fan_in_band.png)

**Perfil por tramo Fan-Out**

![Perfil por tramo Fan-Out](figures/fig11_profile_by_fan_out_band.png)

**Perfil por celda de ceros**

![Perfil por celda de ceros](figures/fig12_profile_by_zero_cell.png)

**Interno vs externo (A)**

![Interno vs externo (A)](figures/fig13_internal_vs_external_A.png)
