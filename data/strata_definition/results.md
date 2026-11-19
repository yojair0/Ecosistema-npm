# Tramos de Fan-In por Dalenius-Hodges

Generado: 2026-11-12 11:54:52

## Entradas

- Población: `data\fanin_population\fanin_population.parquet` (G1, Fan-In > 0)
- Paquetes: 680.373
- Fan-In: del registro, sin modificar (máximo 195.952)

## Método

- Regla de Dalenius-Hodges: cortes en partes iguales de la suma acumulada de √f.
- Clases finas: cada entero de 1 a 1.000; sobre 1.000, intervalos que duplican el ancho.
- Sin pico: la frecuencia de Fan-In 9 se reemplaza por √(f(8) · f(10)). Observada: 11.433; esperada: 6.732; exceso: 4.701.
- Los paquetes no cambian: el pico solo se corrige para calcular los cortes; los conteos por tramo usan la población completa.
- Disponibles tras límites: paquetes que quedan en el tramo al dejar como máximo uno por scope y uno por `dep_hash` no vacío (orden aleatorio, semilla 42). Es una cota aproximada de lo que se puede sortear.
- Familia: `scope_size >= 2`.

## Cortes por configuración

| Configuración | Tramos | Límites inferiores |
|---|---|---|
| 6 tramos, con pico | 6 | 1, 4, 13, 50, 164, 454 |
| 6 tramos, sin pico | 6 | 1, 4, 13, 51, 165, 456 |
| 7 tramos, con pico | 7 | 1, 3, 9, 29, 85, 225, 514 |
| 7 tramos, sin pico | 7 | 1, 3, 9, 29, 86, 226, 515 |

## ¿El pico mueve los cortes?

- 6 tramos: los cortes cambian (1, 4, 13, 50, 164, 454 con pico; 1, 4, 13, 51, 165, 456 sin pico).
- 7 tramos: los cortes cambian (1, 3, 9, 29, 85, 225, 514 con pico; 1, 3, 9, 29, 86, 226, 515 sin pico).

## 6 tramos, con pico

| Tramo | Fan-In | Paquetes | % población | Mediana Fan-In | % familia | Con Fan-In 9 | Disponibles tras límites |
|---|---|---|---|---|---|---|---|
| 1 | 1 a 3 | 516.849 | 76,0 % | 1 | 57,3 % | 0 | 245.343 |
| 2 | 4 a 12 | 109.911 | 16,2 % | 6 | 55,7 % | 11.433 | 61.523 |
| 3 | 13 a 49 | 34.367 | 5,1 % | 20 | 48,6 % | 0 | 20.823 |
| 4 | 50 a 163 | 10.975 | 1,6 % | 79 | 34,5 % | 0 | 7.257 |
| 5 | 164 a 453 | 4.179 | 0,6 % | 256 | 28,7 % | 0 | 3.014 |
| 6 | 454 o más | 4.092 | 0,6 % | 980 | 18,8 % | 0 | 3.055 |

## 6 tramos, sin pico

| Tramo | Fan-In | Paquetes | % población | Mediana Fan-In | % familia | Con Fan-In 9 | Disponibles tras límites |
|---|---|---|---|---|---|---|---|
| 1 | 1 a 3 | 516.849 | 76,0 % | 1 | 57,3 % | 0 | 245.343 |
| 2 | 4 a 12 | 109.911 | 16,2 % | 6 | 55,7 % | 11.433 | 61.523 |
| 3 | 13 a 50 | 34.655 | 5,1 % | 21 | 48,5 % | 0 | 20.979 |
| 4 | 51 a 164 | 10.736 | 1,6 % | 80 | 34,2 % | 0 | 7.112 |
| 5 | 165 a 455 | 4.138 | 0,6 % | 257 | 28,7 % | 0 | 2.989 |
| 6 | 456 o más | 4.084 | 0,6 % | 982 | 18,8 % | 0 | 3.051 |

## 7 tramos, con pico

| Tramo | Fan-In | Paquetes | % población | Mediana Fan-In | % familia | Con Fan-In 9 | Disponibles tras límites |
|---|---|---|---|---|---|---|---|
| 1 | 1 a 2 | 463.218 | 68,1 % | 1 | 56,9 % | 0 | 227.435 |
| 2 | 3 a 8 | 138.810 | 20,4 % | 4 | 59,9 % | 0 | 72.890 |
| 3 | 9 a 28 | 49.863 | 7,3 % | 13 | 47,6 % | 11.433 | 31.391 |
| 4 | 29 a 84 | 15.378 | 2,3 % | 44 | 39,8 % | 0 | 10.021 |
| 5 | 85 a 224 | 6.336 | 0,9 % | 129 | 32,8 % | 0 | 4.353 |
| 6 | 225 a 513 | 3.137 | 0,5 % | 320 | 24,8 % | 0 | 2.369 |
| 7 | 514 o más | 3.631 | 0,5 % | 1.114 | 18,9 % | 0 | 2.698 |

## 7 tramos, sin pico

| Tramo | Fan-In | Paquetes | % población | Mediana Fan-In | % familia | Con Fan-In 9 | Disponibles tras límites |
|---|---|---|---|---|---|---|---|
| 1 | 1 a 2 | 463.218 | 68,1 % | 1 | 56,9 % | 0 | 227.435 |
| 2 | 3 a 8 | 138.810 | 20,4 % | 4 | 59,9 % | 0 | 72.890 |
| 3 | 9 a 28 | 49.863 | 7,3 % | 13 | 47,6 % | 11.433 | 31.391 |
| 4 | 29 a 85 | 15.473 | 2,3 % | 44 | 39,7 % | 0 | 10.085 |
| 5 | 86 a 225 | 6.265 | 0,9 % | 130 | 32,9 % | 0 | 4.296 |
| 6 | 226 a 514 | 3.119 | 0,5 % | 321 | 24,7 % | 0 | 2.360 |
| 7 | 515 o más | 3.625 | 0,5 % | 1.118 | 18,9 % | 0 | 2.692 |

