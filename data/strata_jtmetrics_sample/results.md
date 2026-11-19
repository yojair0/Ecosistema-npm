# Extracción con JTMetrics: tamaño de muestra por tramo

Generado: 2026-11-18 01:40:46

## Configuración

- Tramos: 6 tramos, con pico (límites 1, 4, 13, 50, 164, 454)
- Meta por tramo: nₕ = K² · p · q · Nₕ / ((Nₕ − 1) · e² + K² · p · q), redondeado hacia arriba
- Parámetros: K = 2, p = 0.5, q = 0.5, e = 0.05
- Semilla 2028; máximo uno por scope y uno por `dep_hash` no vacío
- Válido: JTMetrics terminó y la cobertura es al menos 25 %
- Cobertura: líneas no vacías en .js, .cjs y .ts sobre ese total más .mjs, .mts, .cts, .jsx y .tsx; sin .d.ts ni .min.js
- JTMetrics se ejecuta sin excluir archivos; .d.ts y .min.js se excluyen después, al calcular las métricas por paquete
- Tiempo de la última ejecución: 39,7 min

## Tamaño de muestra por tramo

| Tramo | Fan-In | Nₕ | nₕ | eₕ |
|---|---|---|---|---|
| 1 | 1 a 3 | 516.849 | 400 | 5,00 % |
| 2 | 4 a 12 | 109.911 | 399 | 5,00 % |
| 3 | 13 a 49 | 34.367 | 396 | 5,00 % |
| 4 | 50 a 163 | 10.975 | 386 | 5,00 % |
| 5 | 164 a 453 | 4.179 | 366 | 4,99 % |
| 6 | 454 o más | 4.092 | 365 | 5,00 % |
| Total | | 680.373 | 2.312 | |

## Intentos por tramo

| Tramo | Fan-In | Intentados | Válidos | En la muestra | low_coverage | no_code | download_error | extract_error | jtmetrics_error | timeout | no_tarball_url | script_error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 a 3 | 512 | 462 | 400 | 19 | 28 | 3 | 0 | 0 | 0 | 0 | 0 |
| 2 | 4 a 12 | 510 | 485 | 399 | 16 | 8 | 1 | 0 | 0 | 0 | 0 | 0 |
| 3 | 13 a 49 | 506 | 470 | 396 | 21 | 14 | 1 | 0 | 0 | 0 | 0 | 0 |
| 4 | 50 a 163 | 494 | 457 | 386 | 20 | 16 | 1 | 0 | 0 | 0 | 0 | 0 |
| 5 | 164 a 453 | 468 | 427 | 366 | 18 | 23 | 0 | 0 | 0 | 0 | 0 | 0 |
| 6 | 454 o más | 467 | 410 | 365 | 28 | 28 | 0 | 0 | 0 | 1 | 0 | 0 |

## Cobertura por tramo

Paquetes con código analizable (cobertura calculada).

| Tramo | Paquetes | Mediana | % con 100 % | % entre 25 % y 99 % | % bajo 25 % |
|---|---|---|---|---|---|
| 1 | 481 | 100,0 % | 85,7 % | 10,4 % | 4,0 % |
| 2 | 501 | 100,0 % | 85,8 % | 11,0 % | 3,2 % |
| 3 | 491 | 100,0 % | 82,7 % | 13,0 % | 4,3 % |
| 4 | 477 | 100,0 % | 84,3 % | 11,5 % | 4,2 % |
| 5 | 445 | 100,0 % | 86,1 % | 9,9 % | 4,0 % |
| 6 | 439 | 100,0 % | 82,5 % | 11,2 % | 6,4 % |

## Muestra final

| Tramo | Paquetes | % familia | Mediana Fan-In | Mediana de archivos | % con .d.ts | % con .min.js |
|---|---|---|---|---|---|---|
| 1 | 400 | 55,0 % | 1 | 6 | 51,2 % | 7,8 % |
| 2 | 399 | 53,6 % | 6 | 7 | 60,2 % | 6,5 % |
| 3 | 396 | 45,2 % | 20 | 6 | 60,1 % | 10,1 % |
| 4 | 386 | 30,3 % | 75 | 6 | 52,6 % | 9,8 % |
| 5 | 366 | 19,9 % | 246 | 5 | 57,7 % | 14,5 % |
| 6 | 365 | 13,4 % | 1.080 | 5 | 58,1 % | 12,3 % |

Las columnas de JTMetrics en `attempts.csv` (n_files, internal_edges y otras) incluyen todos los archivos leídos. Las métricas por paquete, sin .d.ts ni .min.js, se calculan después desde `raw/`.
