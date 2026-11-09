# Curvas de cortes por Fan-In

Generado 2026-11-09 14:23. Cada grupo conserva los paquetes con el Fan-In igual o mayor que el corte. Los cortes vienen de los deciles de cada población, es decir, quedarse con el 90%, 80%… de arriba (columna Corte pedido por deciles), y de la escala 1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000. Se omiten los cortes con menos de 2.000 paquetes.

Si varios cortes pedidos caen en la misma fila, es por los empates: no se puede quedar justo con ese porcentaje, y la columna De la población dice cuánto queda en realidad.

Cómo leer cada variable: si su correlación sube al sacar a los de abajo, esos paquetes eran ruido; si baja desde el principio, no lo eran; si queda plana, el corte no cambia la conclusión.

Omitidas, porque falta su columna (corre la versión de check_fanin_clean.py que separa el Fan-In externo): g2_clean.

## Inicio de la cola (xmin)

Valor del Fan-In desde el que la distribución entra en su cola larga, estimado con el método de Clauset, Shalizi y Newman (2009): se ajusta una ley de potencia discreta sobre cada candidato y se elige el de menor distancia de Kolmogorov-Smirnov. Se agrega como un corte más, marcado con xmin. No se corre la prueba de bondad de ajuste por bootstrap: es un punto de referencia, no una prueba de que la cola sea una ley de potencia. Si la cola deja menos de 2.000 paquetes, ese corte no aparece en las tablas de la curva, porque la correlación sería poco confiable.

| Población | xmin | Exponente | Distancia KS | Paquetes en la cola | De la población |
|---|---|---|---|---|---|
| G1, con familias, Fan-In del registro | 13 | 1,75 | 0,013 | 53.613 | 7,9% |
| G1, con familias, Fan-In limpio | 2 | 1,85 | 0,014 | 326.394 | 48,8% |
| G2, solo vínculos externos, Fan-In del registro | 10 | 1,67 | 0,013 | 50.142 | 12,5% |
| G3, sin familias, Fan-In del registro | 1 | 1,73 | 0,013 | 300.348 | 100,0% |
| G3, sin familias, Fan-In limpio | 1 | 1,74 | 0,011 | 295.069 | 100,0% |

## G1, con familias, Fan-In del registro

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-Out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 1 | 90% a 50% de arriba | 680.373 | 100,0% | 348.087 | 0,224 | 0,106 | 0,138 | 0,125 | 0,064 | 0,321 | 0,063 | 0,057 |
| ≥ 2 | 40% de arriba | 332.286 | 48,8% | 115.131 | 0,172 | 0,151 | 0,115 | 0,130 | 0,081 | 0,365 | 0,066 | 0,055 |
| ≥ 3 | 30% de arriba | 217.155 | 31,9% | 53.631 | 0,141 | 0,177 | 0,098 | 0,133 | 0,092 | 0,387 | 0,068 | 0,048 |
| ≥ 4 | 20% de arriba | 163.524 | 24,0% | 31.660 | 0,130 | 0,185 | 0,102 | 0,144 | 0,096 | 0,402 | 0,071 | 0,034 |
| ≥ 5 |  | 131.864 | 19,4% | 53.519 | 0,126 | 0,197 | 0,103 | 0,164 | 0,108 | 0,415 | 0,065 | 0,009 |
| ≥ 9 | 10% de arriba | 78.345 | 11,5% | 11.433 | 0,195 | 0,269 | 0,127 | 0,269 | 0,148 | 0,465 | -0,003 | -0,137 |
| ≥ 10 |  | 66.912 | 9,8% | 13.299 | 0,049 | 0,168 | 0,047 | 0,173 | 0,100 | 0,417 | 0,060 | 0,013 |
| ≥ 13 (xmin) |  | 53.613 | 7,9% | 15.739 | 0,029 | 0,160 | 0,030 | 0,168 | 0,088 | 0,410 | 0,053 | 0,008 |
| ≥ 20 |  | 37.874 | 5,6% | 18.628 | 0,022 | 0,145 | 0,018 | 0,165 | 0,068 | 0,393 | 0,048 | -0,001 |
| ≥ 50 |  | 19.246 | 2,8% | 7.491 | 0,045 | 0,139 | 0,021 | 0,112 | 0,002 | 0,350 | 0,036 | -0,032 |
| ≥ 100 |  | 11.755 | 1,7% | 4.353 | 0,047 | 0,113 | 0,031 | 0,055 | 0,031 | 0,312 | 0,052 | -0,047 |
| ≥ 200 |  | 7.402 | 1,1% | 3.667 | 0,078 | 0,129 | 0,040 | 0,046 | 0,068 | 0,310 | 0,081 | -0,004 |
| ≥ 500 |  | 3.735 | 0,5% | 1.714 | 0,097 | 0,093 | 0,029 | 0,039 | 0,018 | 0,311 | 0,039 | 0,010 |
| ≥ 1000 |  | 2.021 | 0,3% | 2.021 | 0,219 | 0,160 | 0,116 | 0,042 | 0,090 | 0,371 | 0,090 | 0,026 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,224 | 0,224 | 0,219 | Plana |
| Edad | 0,106 | 0,269 | 0,160 | Sube al cortar: máximo en ≥ 9 |
| Mantenedores | 0,138 | 0,138 | 0,116 | Plana |
| En GitHub | 0,125 | 0,269 | 0,042 | Sube al cortar: máximo en ≥ 9 |
| Palabras clave | 0,064 | 0,148 | 0,090 | Sube al cortar: máximo en ≥ 9 |
| Dependientes de desarrollo | 0,321 | 0,465 | 0,371 | Sube al cortar: máximo en ≥ 9 |
| Dependencias de desarrollo | 0,063 | 0,090 | 0,090 | Plana |
| Fan-Out | 0,057 | 0,057 | 0,026 | Plana |

## G1, con familias, Fan-In limpio

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-Out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 1 | 90% a 50% de arriba | 668.424 | 100,0% | 342.030 | 0,225 | 0,106 | 0,137 | 0,122 | 0,061 | 0,324 | 0,065 | 0,056 |
| ≥ 2 (xmin) | 40% de arriba | 326.394 | 48,8% | 113.195 | 0,180 | 0,156 | 0,117 | 0,126 | 0,076 | 0,368 | 0,068 | 0,052 |
| ≥ 3 | 30% de arriba | 213.199 | 31,9% | 52.937 | 0,153 | 0,185 | 0,104 | 0,130 | 0,088 | 0,394 | 0,072 | 0,043 |
| ≥ 4 | 20% de arriba | 160.262 | 24,0% | 31.366 | 0,147 | 0,196 | 0,110 | 0,139 | 0,091 | 0,412 | 0,076 | 0,026 |
| ≥ 5 |  | 128.896 | 19,3% | 52.794 | 0,144 | 0,210 | 0,111 | 0,160 | 0,104 | 0,427 | 0,070 | -0,000 |
| ≥ 9 | 10% de arriba | 76.102 | 11,4% | 11.377 | 0,228 | 0,294 | 0,144 | 0,269 | 0,144 | 0,490 | 0,004 | -0,154 |
| ≥ 10 |  | 64.725 | 9,7% | 28.762 | 0,085 | 0,197 | 0,066 | 0,169 | 0,095 | 0,446 | 0,071 | -0,004 |
| ≥ 20 |  | 35.963 | 5,4% | 18.101 | 0,054 | 0,176 | 0,036 | 0,168 | 0,075 | 0,429 | 0,065 | -0,008 |
| ≥ 50 |  | 17.862 | 2,7% | 6.933 | 0,038 | 0,142 | 0,020 | 0,116 | 0,032 | 0,379 | 0,053 | -0,012 |
| ≥ 100 |  | 10.929 | 1,6% | 4.004 | 0,043 | 0,114 | 0,024 | 0,044 | 0,035 | 0,331 | 0,062 | -0,034 |
| ≥ 200 |  | 6.925 | 1,0% | 3.463 | 0,087 | 0,124 | 0,039 | 0,047 | 0,047 | 0,337 | 0,076 | -0,001 |
| ≥ 500 |  | 3.462 | 0,5% | 3.462 | 0,100 | 0,101 | 0,022 | 0,046 | 0,028 | 0,336 | 0,034 | 0,002 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,225 | 0,228 | 0,100 | Baja al cortar |
| Edad | 0,106 | 0,294 | 0,101 | Sube al cortar: máximo en ≥ 9 |
| Mantenedores | 0,137 | 0,144 | 0,022 | Baja al cortar |
| En GitHub | 0,122 | 0,269 | 0,046 | Sube al cortar: máximo en ≥ 9 |
| Palabras clave | 0,061 | 0,144 | 0,028 | Sube al cortar: máximo en ≥ 9 |
| Dependientes de desarrollo | 0,324 | 0,490 | 0,336 | Sube al cortar: máximo en ≥ 9 |
| Dependencias de desarrollo | 0,065 | 0,076 | 0,034 | Plana |
| Fan-Out | 0,056 | 0,056 | 0,002 | Baja al cortar |

## G2, solo vínculos externos, Fan-In del registro

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-Out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 1 | 90% a 50% de arriba | 402.326 | 100,0% | 210.069 | 0,229 | 0,154 | 0,178 | 0,159 | 0,100 | 0,416 | 0,111 | 0,049 |
| ≥ 2 | 40% de arriba | 192.257 | 47,8% | 59.117 | 0,160 | 0,086 | 0,148 | 0,139 | 0,084 | 0,440 | 0,079 | 0,050 |
| ≥ 3 | 30% de arriba | 133.140 | 33,1% | 43.791 | 0,141 | 0,082 | 0,129 | 0,128 | 0,075 | 0,448 | 0,067 | 0,036 |
| ≥ 5 | 20% de arriba | 89.349 | 22,2% | 39.207 | 0,148 | 0,120 | 0,121 | 0,167 | 0,088 | 0,464 | 0,044 | -0,025 |
| ≥ 10 (xmin) |  | 50.142 | 12,5% | 8.388 | 0,062 | 0,079 | 0,055 | 0,123 | 0,053 | 0,435 | 0,032 | 0,016 |
| ≥ 13 | 10% de arriba | 41.754 | 10,4% | 10.448 | 0,058 | 0,082 | 0,052 | 0,128 | 0,047 | 0,423 | 0,027 | 0,014 |
| ≥ 20 |  | 31.306 | 7,8% | 14.175 | 0,066 | 0,097 | 0,049 | 0,114 | 0,039 | 0,406 | 0,034 | -0,003 |
| ≥ 50 |  | 17.131 | 4,3% | 6.367 | 0,073 | 0,115 | 0,047 | 0,076 | 0,005 | 0,368 | 0,019 | -0,011 |
| ≥ 100 |  | 10.764 | 2,7% | 3.872 | 0,054 | 0,094 | 0,033 | 0,036 | 0,017 | 0,324 | 0,036 | -0,027 |
| ≥ 200 |  | 6.892 | 1,7% | 3.330 | 0,072 | 0,111 | 0,036 | 0,028 | 0,057 | 0,311 | 0,070 | 0,021 |
| ≥ 500 |  | 3.562 | 0,9% | 3.562 | 0,104 | 0,098 | 0,032 | 0,019 | 0,022 | 0,333 | 0,039 | 0,002 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,229 | 0,229 | 0,104 | Baja al cortar |
| Edad | 0,154 | 0,154 | 0,098 | Baja al cortar |
| Mantenedores | 0,178 | 0,178 | 0,032 | Baja al cortar |
| En GitHub | 0,159 | 0,167 | 0,019 | Baja al cortar |
| Palabras clave | 0,100 | 0,100 | 0,022 | Baja al cortar |
| Dependientes de desarrollo | 0,416 | 0,464 | 0,333 | Baja al cortar |
| Dependencias de desarrollo | 0,111 | 0,111 | 0,039 | Baja al cortar |
| Fan-Out | 0,049 | 0,050 | 0,002 | Plana |

## G3, sin familias, Fan-In del registro

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-Out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 1 (xmin) | 90% a 50% de arriba | 300.348 | 100,0% | 154.779 | 0,222 | 0,152 | 0,182 | 0,156 | 0,114 | 0,409 | 0,125 | 0,055 |
| ≥ 2 | 40% de arriba | 145.569 | 48,5% | 44.961 | 0,140 | 0,093 | 0,156 | 0,131 | 0,088 | 0,429 | 0,095 | 0,069 |
| ≥ 3 | 30% de arriba | 100.608 | 33,5% | 33.204 | 0,121 | 0,094 | 0,144 | 0,124 | 0,083 | 0,436 | 0,082 | 0,050 |
| ≥ 5 | 20% de arriba | 67.404 | 22,4% | 30.283 | 0,151 | 0,138 | 0,151 | 0,179 | 0,102 | 0,453 | 0,046 | -0,034 |
| ≥ 10 |  | 37.121 | 12,4% | 5.958 | 0,078 | 0,064 | 0,100 | 0,130 | 0,052 | 0,416 | 0,037 | 0,017 |
| ≥ 13 | 10% de arriba | 31.163 | 10,4% | 7.474 | 0,079 | 0,068 | 0,094 | 0,130 | 0,045 | 0,404 | 0,031 | 0,014 |
| ≥ 20 |  | 23.689 | 7,9% | 10.203 | 0,104 | 0,077 | 0,098 | 0,108 | 0,032 | 0,389 | 0,038 | -0,008 |
| ≥ 50 |  | 13.486 | 4,5% | 4.809 | 0,121 | 0,115 | 0,104 | 0,075 | -0,008 | 0,354 | 0,021 | -0,019 |
| ≥ 100 |  | 8.677 | 2,9% | 2.975 | 0,087 | 0,082 | 0,082 | 0,042 | 0,011 | 0,309 | 0,038 | -0,024 |
| ≥ 200 |  | 5.702 | 1,9% | 2.681 | 0,101 | 0,114 | 0,068 | 0,021 | 0,065 | 0,303 | 0,082 | 0,029 |
| ≥ 500 |  | 3.021 | 1,0% | 3.021 | 0,131 | 0,107 | 0,047 | 0,007 | 0,033 | 0,326 | 0,045 | 0,015 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,222 | 0,222 | 0,131 | Baja al cortar |
| Edad | 0,152 | 0,152 | 0,107 | Plana |
| Mantenedores | 0,182 | 0,182 | 0,047 | Baja al cortar |
| En GitHub | 0,156 | 0,179 | 0,007 | Baja al cortar |
| Palabras clave | 0,114 | 0,114 | 0,033 | Baja al cortar |
| Dependientes de desarrollo | 0,409 | 0,453 | 0,326 | Baja al cortar |
| Dependencias de desarrollo | 0,125 | 0,125 | 0,045 | Baja al cortar |
| Fan-Out | 0,055 | 0,069 | 0,015 | Plana |

## G3, sin familias, Fan-In limpio

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-Out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 1 (xmin) | 90% a 50% de arriba | 295.069 | 100,0% | 152.472 | 0,227 | 0,156 | 0,184 | 0,154 | 0,113 | 0,412 | 0,127 | 0,055 |
| ≥ 2 | 40% de arriba | 142.597 | 48,3% | 44.141 | 0,153 | 0,108 | 0,160 | 0,123 | 0,084 | 0,438 | 0,100 | 0,062 |
| ≥ 3 | 30% de arriba | 98.456 | 33,4% | 32.951 | 0,144 | 0,115 | 0,153 | 0,120 | 0,082 | 0,450 | 0,091 | 0,040 |
| ≥ 5 | 20% de arriba | 65.505 | 22,2% | 29.889 | 0,179 | 0,166 | 0,163 | 0,176 | 0,101 | 0,477 | 0,056 | -0,047 |
| ≥ 10 |  | 35.616 | 12,1% | 5.865 | 0,127 | 0,111 | 0,121 | 0,134 | 0,057 | 0,459 | 0,053 | -0,003 |
| ≥ 13 | 10% de arriba | 29.751 | 10,1% | 7.507 | 0,126 | 0,114 | 0,115 | 0,133 | 0,048 | 0,452 | 0,048 | -0,007 |
| ≥ 20 |  | 22.244 | 7,5% | 9.762 | 0,130 | 0,106 | 0,109 | 0,118 | 0,040 | 0,432 | 0,056 | -0,008 |
| ≥ 50 |  | 12.482 | 4,2% | 4.429 | 0,126 | 0,122 | 0,109 | 0,071 | 0,020 | 0,391 | 0,052 | -0,006 |
| ≥ 100 |  | 8.053 | 2,7% | 2.784 | 0,097 | 0,094 | 0,082 | 0,015 | 0,031 | 0,343 | 0,059 | -0,021 |
| ≥ 200 |  | 5.269 | 1,8% | 2.501 | 0,097 | 0,097 | 0,061 | 0,020 | 0,034 | 0,329 | 0,066 | 0,035 |
| ≥ 500 |  | 2.768 | 0,9% | 2.768 | 0,122 | 0,095 | 0,032 | 0,016 | 0,025 | 0,343 | 0,023 | 0,024 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,227 | 0,227 | 0,122 | Baja al cortar |
| Edad | 0,156 | 0,166 | 0,095 | Baja al cortar |
| Mantenedores | 0,184 | 0,184 | 0,032 | Baja al cortar |
| En GitHub | 0,154 | 0,176 | 0,016 | Baja al cortar |
| Palabras clave | 0,113 | 0,113 | 0,025 | Baja al cortar |
| Dependientes de desarrollo | 0,412 | 0,477 | 0,343 | Sube al cortar: máximo en ≥ 5 |
| Dependencias de desarrollo | 0,127 | 0,127 | 0,023 | Baja al cortar |
| Fan-Out | 0,055 | 0,062 | 0,024 | Plana |

## Comparación entre poblaciones, por variable

Cortes de la escala presentes en todas las poblaciones. Cada celda es la correlación con el Fan-In en ese corte.

**Versiones:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,224 | 0,225 | 0,229 | 0,222 | 0,227 |
| ≥ 2 | 0,172 | 0,180 | 0,160 | 0,140 | 0,153 |
| ≥ 3 | 0,141 | 0,153 | 0,141 | 0,121 | 0,144 |
| ≥ 5 | 0,126 | 0,144 | 0,148 | 0,151 | 0,179 |
| ≥ 10 | 0,049 | 0,085 | 0,062 | 0,078 | 0,127 |
| ≥ 20 | 0,022 | 0,054 | 0,066 | 0,104 | 0,130 |
| ≥ 50 | 0,045 | 0,038 | 0,073 | 0,121 | 0,126 |
| ≥ 100 | 0,047 | 0,043 | 0,054 | 0,087 | 0,097 |
| ≥ 200 | 0,078 | 0,087 | 0,072 | 0,101 | 0,097 |
| ≥ 500 | 0,097 | 0,100 | 0,104 | 0,131 | 0,122 |

**Edad:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,106 | 0,106 | 0,154 | 0,152 | 0,156 |
| ≥ 2 | 0,151 | 0,156 | 0,086 | 0,093 | 0,108 |
| ≥ 3 | 0,177 | 0,185 | 0,082 | 0,094 | 0,115 |
| ≥ 5 | 0,197 | 0,210 | 0,120 | 0,138 | 0,166 |
| ≥ 10 | 0,168 | 0,197 | 0,079 | 0,064 | 0,111 |
| ≥ 20 | 0,145 | 0,176 | 0,097 | 0,077 | 0,106 |
| ≥ 50 | 0,139 | 0,142 | 0,115 | 0,115 | 0,122 |
| ≥ 100 | 0,113 | 0,114 | 0,094 | 0,082 | 0,094 |
| ≥ 200 | 0,129 | 0,124 | 0,111 | 0,114 | 0,097 |
| ≥ 500 | 0,093 | 0,101 | 0,098 | 0,107 | 0,095 |

**Mantenedores:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,138 | 0,137 | 0,178 | 0,182 | 0,184 |
| ≥ 2 | 0,115 | 0,117 | 0,148 | 0,156 | 0,160 |
| ≥ 3 | 0,098 | 0,104 | 0,129 | 0,144 | 0,153 |
| ≥ 5 | 0,103 | 0,111 | 0,121 | 0,151 | 0,163 |
| ≥ 10 | 0,047 | 0,066 | 0,055 | 0,100 | 0,121 |
| ≥ 20 | 0,018 | 0,036 | 0,049 | 0,098 | 0,109 |
| ≥ 50 | 0,021 | 0,020 | 0,047 | 0,104 | 0,109 |
| ≥ 100 | 0,031 | 0,024 | 0,033 | 0,082 | 0,082 |
| ≥ 200 | 0,040 | 0,039 | 0,036 | 0,068 | 0,061 |
| ≥ 500 | 0,029 | 0,022 | 0,032 | 0,047 | 0,032 |

**En GitHub:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,125 | 0,122 | 0,159 | 0,156 | 0,154 |
| ≥ 2 | 0,130 | 0,126 | 0,139 | 0,131 | 0,123 |
| ≥ 3 | 0,133 | 0,130 | 0,128 | 0,124 | 0,120 |
| ≥ 5 | 0,164 | 0,160 | 0,167 | 0,179 | 0,176 |
| ≥ 10 | 0,173 | 0,169 | 0,123 | 0,130 | 0,134 |
| ≥ 20 | 0,165 | 0,168 | 0,114 | 0,108 | 0,118 |
| ≥ 50 | 0,112 | 0,116 | 0,076 | 0,075 | 0,071 |
| ≥ 100 | 0,055 | 0,044 | 0,036 | 0,042 | 0,015 |
| ≥ 200 | 0,046 | 0,047 | 0,028 | 0,021 | 0,020 |
| ≥ 500 | 0,039 | 0,046 | 0,019 | 0,007 | 0,016 |

**Palabras clave:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,064 | 0,061 | 0,100 | 0,114 | 0,113 |
| ≥ 2 | 0,081 | 0,076 | 0,084 | 0,088 | 0,084 |
| ≥ 3 | 0,092 | 0,088 | 0,075 | 0,083 | 0,082 |
| ≥ 5 | 0,108 | 0,104 | 0,088 | 0,102 | 0,101 |
| ≥ 10 | 0,100 | 0,095 | 0,053 | 0,052 | 0,057 |
| ≥ 20 | 0,068 | 0,075 | 0,039 | 0,032 | 0,040 |
| ≥ 50 | 0,002 | 0,032 | 0,005 | -0,008 | 0,020 |
| ≥ 100 | 0,031 | 0,035 | 0,017 | 0,011 | 0,031 |
| ≥ 200 | 0,068 | 0,047 | 0,057 | 0,065 | 0,034 |
| ≥ 500 | 0,018 | 0,028 | 0,022 | 0,033 | 0,025 |

**Dependientes de desarrollo:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,321 | 0,324 | 0,416 | 0,409 | 0,412 |
| ≥ 2 | 0,365 | 0,368 | 0,440 | 0,429 | 0,438 |
| ≥ 3 | 0,387 | 0,394 | 0,448 | 0,436 | 0,450 |
| ≥ 5 | 0,415 | 0,427 | 0,464 | 0,453 | 0,477 |
| ≥ 10 | 0,417 | 0,446 | 0,435 | 0,416 | 0,459 |
| ≥ 20 | 0,393 | 0,429 | 0,406 | 0,389 | 0,432 |
| ≥ 50 | 0,350 | 0,379 | 0,368 | 0,354 | 0,391 |
| ≥ 100 | 0,312 | 0,331 | 0,324 | 0,309 | 0,343 |
| ≥ 200 | 0,310 | 0,337 | 0,311 | 0,303 | 0,329 |
| ≥ 500 | 0,311 | 0,336 | 0,333 | 0,326 | 0,343 |

**Dependencias de desarrollo:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,063 | 0,065 | 0,111 | 0,125 | 0,127 |
| ≥ 2 | 0,066 | 0,068 | 0,079 | 0,095 | 0,100 |
| ≥ 3 | 0,068 | 0,072 | 0,067 | 0,082 | 0,091 |
| ≥ 5 | 0,065 | 0,070 | 0,044 | 0,046 | 0,056 |
| ≥ 10 | 0,060 | 0,071 | 0,032 | 0,037 | 0,053 |
| ≥ 20 | 0,048 | 0,065 | 0,034 | 0,038 | 0,056 |
| ≥ 50 | 0,036 | 0,053 | 0,019 | 0,021 | 0,052 |
| ≥ 100 | 0,052 | 0,062 | 0,036 | 0,038 | 0,059 |
| ≥ 200 | 0,081 | 0,076 | 0,070 | 0,082 | 0,066 |
| ≥ 500 | 0,039 | 0,034 | 0,039 | 0,045 | 0,023 |

**Fan-Out:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 1 | 0,057 | 0,056 | 0,049 | 0,055 | 0,055 |
| ≥ 2 | 0,055 | 0,052 | 0,050 | 0,069 | 0,062 |
| ≥ 3 | 0,048 | 0,043 | 0,036 | 0,050 | 0,040 |
| ≥ 5 | 0,009 | -0,000 | -0,025 | -0,034 | -0,047 |
| ≥ 10 | 0,013 | -0,004 | 0,016 | 0,017 | -0,003 |
| ≥ 20 | -0,001 | -0,008 | -0,003 | -0,008 | -0,008 |
| ≥ 50 | -0,032 | -0,012 | -0,011 | -0,019 | -0,006 |
| ≥ 100 | -0,047 | -0,034 | -0,027 | -0,024 | -0,021 |
| ≥ 200 | -0,004 | -0,001 | 0,021 | 0,029 | 0,035 |
| ≥ 500 | 0,010 | 0,002 | 0,002 | 0,015 | 0,024 |

Claves: g1_reg = G1, con familias, Fan-In del registro; g1_clean = G1, con familias, Fan-In limpio; g2_reg = G2, solo vínculos externos, Fan-In del registro; g3_reg = G3, sin familias, Fan-In del registro; g3_clean = G3, sin familias, Fan-In limpio.
