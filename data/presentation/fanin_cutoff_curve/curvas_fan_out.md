# Curvas de cortes por Fan-Out

Generado 2026-11-09 14:23. Cada grupo conserva los paquetes con el Fan-Out igual o mayor que el corte. Los cortes vienen de los deciles de cada población, es decir, quedarse con el 90%, 80%… de arriba (columna Corte pedido por deciles), y de la escala 0, 1, 2, 3, 5, 10, 20, 50, 100. Se omiten los cortes con menos de 2.000 paquetes.

Si varios cortes pedidos caen en la misma fila, es por los empates: no se puede quedar justo con ese porcentaje, y la columna De la población dice cuánto queda en realidad.

Cómo leer cada variable: si su correlación sube al sacar a los de abajo, esos paquetes eran ruido; si baja desde el principio, no lo eran; si queda plana, el corte no cambia la conclusión.

Omitidas, porque falta su columna (corre la versión de check_fanin_clean.py que separa el Fan-In externo): g2_clean.

## Inicio de la cola (xmin)

Valor del Fan-Out desde el que la distribución entra en su cola larga, estimado con el método de Clauset, Shalizi y Newman (2009): se ajusta una ley de potencia discreta sobre cada candidato y se elige el de menor distancia de Kolmogorov-Smirnov. Se agrega como un corte más, marcado con xmin. No se corre la prueba de bondad de ajuste por bootstrap: es un punto de referencia, no una prueba de que la cola sea una ley de potencia. Si la cola deja menos de 2.000 paquetes, ese corte no aparece en las tablas de la curva, porque la correlación sería poco confiable.

| Población | xmin | Exponente | Distancia KS | Paquetes en la cola | De la población |
|---|---|---|---|---|---|
| G1, con familias, Fan-In del registro | 18 | 3,22 | 0,016 | 25.663 | 3,8% |
| G1, con familias, Fan-In limpio | 18 | 3,26 | 0,017 | 25.214 | 3,8% |
| G2, solo vínculos externos, Fan-In del registro | 18 | 3,22 | 0,023 | 16.433 | 4,1% |
| G3, sin familias, Fan-In del registro | 18 | 3,24 | 0,030 | 13.827 | 4,6% |
| G3, sin familias, Fan-In limpio | 18 | 3,31 | 0,029 | 13.552 | 4,6% |

## G1, con familias, Fan-In del registro

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-In |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 0 | 90% a 80% de arriba | 680.373 | 100,0% | 188.092 | 0,189 | -0,042 | 0,131 | -0,004 | -0,060 | -0,003 | 0,152 | 0,057 |
| ≥ 1 | 70% a 60% de arriba | 492.281 | 72,4% | 131.641 | 0,162 | -0,014 | 0,106 | -0,001 | -0,031 | 0,031 | 0,168 | 0,081 |
| ≥ 2 | 50% a 40% de arriba | 360.640 | 53,0% | 90.880 | 0,126 | -0,013 | 0,075 | -0,028 | -0,032 | 0,036 | 0,138 | 0,087 |
| ≥ 3 | 30% de arriba | 269.760 | 39,6% | 111.494 | 0,123 | -0,018 | 0,072 | -0,038 | -0,025 | 0,042 | 0,117 | 0,100 |
| ≥ 5 | 20% de arriba | 158.266 | 23,3% | 84.485 | 0,007 | -0,065 | 0,005 | -0,050 | -0,060 | 0,013 | 0,112 | 0,107 |
| ≥ 9 | 10% de arriba | 73.781 | 10,8% | 10.208 | -0,078 | -0,083 | -0,046 | -0,060 | -0,046 | -0,005 | 0,088 | 0,135 |
| ≥ 10 |  | 63.573 | 9,3% | 37.910 | -0,083 | -0,081 | -0,055 | -0,061 | -0,043 | 0,001 | 0,086 | 0,139 |
| ≥ 18 (xmin) |  | 25.663 | 3,8% | 5.559 | 0,121 | 0,068 | 0,049 | 0,038 | 0,059 | 0,066 | -0,056 | -0,038 |
| ≥ 20 |  | 20.104 | 3,0% | 17.613 | 0,079 | 0,041 | 0,024 | 0,088 | 0,063 | 0,051 | -0,049 | -0,005 |
| ≥ 50 |  | 2.491 | 0,4% | 2.491 | -0,214 | -0,017 | -0,105 | 0,081 | 0,075 | -0,138 | -0,174 | 0,116 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,189 | 0,189 | -0,214 | Baja al cortar |
| Edad | -0,042 | 0,068 | -0,017 | Sube al cortar: máximo en ≥ 18 |
| Mantenedores | 0,131 | 0,131 | -0,105 | Baja al cortar |
| En GitHub | -0,004 | 0,088 | 0,081 | Sube al cortar: máximo en ≥ 20 |
| Palabras clave | -0,060 | 0,075 | 0,075 | Sube al cortar: máximo en ≥ 50 |
| Dependientes de desarrollo | -0,003 | 0,066 | -0,138 | Sube al cortar: máximo en ≥ 18 |
| Dependencias de desarrollo | 0,152 | 0,168 | -0,174 | Baja al cortar |
| Fan-In | 0,057 | 0,139 | 0,116 | Sube al cortar: máximo en ≥ 10 |

## G1, con familias, Fan-In limpio

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-In |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 0 | 90% a 80% de arriba | 668.424 | 100,0% | 184.355 | 0,189 | -0,042 | 0,131 | -0,005 | -0,062 | -0,001 | 0,150 | 0,056 |
| ≥ 1 | 70% a 60% de arriba | 484.069 | 72,4% | 129.878 | 0,165 | -0,014 | 0,106 | 0,000 | -0,032 | 0,031 | 0,166 | 0,081 |
| ≥ 2 | 50% a 40% de arriba | 354.191 | 53,0% | 89.115 | 0,130 | -0,014 | 0,075 | -0,026 | -0,035 | 0,035 | 0,136 | 0,087 |
| ≥ 3 | 30% de arriba | 265.076 | 39,7% | 109.444 | 0,123 | -0,020 | 0,072 | -0,039 | -0,026 | 0,042 | 0,117 | 0,099 |
| ≥ 5 | 20% de arriba | 155.632 | 23,3% | 82.985 | 0,005 | -0,068 | 0,003 | -0,052 | -0,060 | 0,011 | 0,115 | 0,106 |
| ≥ 9 | 10% de arriba | 72.647 | 10,9% | 10.075 | -0,078 | -0,088 | -0,046 | -0,061 | -0,047 | -0,006 | 0,091 | 0,141 |
| ≥ 10 |  | 62.572 | 9,4% | 37.358 | -0,082 | -0,087 | -0,054 | -0,062 | -0,045 | 0,001 | 0,087 | 0,146 |
| ≥ 18 (xmin) |  | 25.214 | 3,8% | 5.485 | 0,124 | 0,059 | 0,052 | 0,038 | 0,059 | 0,073 | -0,060 | -0,034 |
| ≥ 20 |  | 19.729 | 3,0% | 17.383 | 0,082 | 0,026 | 0,026 | 0,088 | 0,066 | 0,062 | -0,055 | 0,006 |
| ≥ 50 |  | 2.346 | 0,4% | 2.346 | -0,195 | -0,083 | -0,088 | 0,088 | 0,065 | -0,117 | -0,194 | 0,182 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,189 | 0,189 | -0,195 | Baja al cortar |
| Edad | -0,042 | 0,059 | -0,083 | Sube al cortar: máximo en ≥ 18 |
| Mantenedores | 0,131 | 0,131 | -0,088 | Baja al cortar |
| En GitHub | -0,005 | 0,088 | 0,088 | Sube al cortar: máximo en ≥ 20 |
| Palabras clave | -0,062 | 0,066 | 0,065 | Sube al cortar: máximo en ≥ 20 |
| Dependientes de desarrollo | -0,001 | 0,073 | -0,117 | Sube al cortar: máximo en ≥ 18 |
| Dependencias de desarrollo | 0,150 | 0,166 | -0,194 | Baja al cortar |
| Fan-In | 0,056 | 0,182 | 0,182 | Sube al cortar: máximo en ≥ 50 |

## G2, solo vínculos externos, Fan-In del registro

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-In |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 0 | 90% a 70% de arriba | 402.326 | 100,0% | 136.164 | 0,110 | -0,041 | 0,054 | -0,011 | -0,061 | -0,005 | 0,197 | 0,049 |
| ≥ 1 | 60% a 50% de arriba | 266.162 | 66,2% | 77.973 | 0,109 | -0,089 | 0,054 | -0,007 | -0,035 | 0,022 | 0,209 | 0,092 |
| ≥ 2 | 40% de arriba | 188.189 | 46,8% | 48.556 | 0,082 | -0,113 | 0,043 | -0,087 | -0,052 | 0,020 | 0,159 | 0,103 |
| ≥ 3 | 30% de arriba | 139.633 | 34,7% | 59.101 | 0,097 | -0,095 | 0,049 | -0,107 | -0,027 | 0,028 | 0,115 | 0,132 |
| ≥ 5 | 20% de arriba | 80.532 | 20,0% | 34.518 | -0,077 | -0,210 | -0,029 | -0,122 | -0,108 | -0,039 | 0,093 | 0,153 |
| ≥ 8 | 10% de arriba | 46.014 | 11,4% | 11.372 | -0,147 | -0,228 | -0,059 | -0,126 | -0,099 | -0,052 | 0,043 | 0,194 |
| ≥ 10 |  | 34.642 | 8,6% | 18.209 | -0,156 | -0,203 | -0,071 | -0,122 | -0,078 | -0,050 | 0,019 | 0,190 |
| ≥ 18 (xmin) |  | 16.433 | 4,1% | 3.772 | 0,162 | 0,142 | 0,094 | 0,054 | 0,107 | 0,081 | -0,141 | -0,037 |
| ≥ 20 |  | 12.661 | 3,1% | 12.661 | 0,108 | 0,088 | 0,059 | 0,144 | 0,106 | 0,061 | -0,144 | 0,017 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,110 | 0,162 | 0,108 | Sube al cortar: máximo en ≥ 18 |
| Edad | -0,041 | 0,142 | 0,088 | Sube al cortar: máximo en ≥ 18 |
| Mantenedores | 0,054 | 0,094 | 0,059 | Plana |
| En GitHub | -0,011 | 0,144 | 0,144 | Sube al cortar: máximo en ≥ 20 |
| Palabras clave | -0,061 | 0,107 | 0,106 | Sube al cortar: máximo en ≥ 18 |
| Dependientes de desarrollo | -0,005 | 0,081 | 0,061 | Sube al cortar: máximo en ≥ 18 |
| Dependencias de desarrollo | 0,197 | 0,209 | -0,144 | Baja al cortar |
| Fan-In | 0,049 | 0,194 | 0,017 | Sube al cortar: máximo en ≥ 8 |

## G3, sin familias, Fan-In del registro

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-In |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 0 | 90% a 70% de arriba | 300.348 | 100,0% | 94.867 | 0,124 | -0,106 | 0,089 | -0,013 | -0,068 | -0,012 | 0,189 | 0,055 |
| ≥ 1 | 60% a 50% de arriba | 205.481 | 68,4% | 58.659 | 0,114 | -0,130 | 0,074 | -0,007 | -0,039 | 0,017 | 0,207 | 0,120 |
| ≥ 2 | 40% de arriba | 146.822 | 48,9% | 36.895 | 0,073 | -0,153 | 0,050 | -0,101 | -0,060 | 0,009 | 0,149 | 0,133 |
| ≥ 3 | 30% de arriba | 109.927 | 36,6% | 47.122 | 0,081 | -0,123 | 0,050 | -0,126 | -0,024 | 0,020 | 0,099 | 0,165 |
| ≥ 5 | 20% de arriba | 62.805 | 20,9% | 31.489 | -0,124 | -0,276 | -0,033 | -0,139 | -0,134 | -0,048 | 0,078 | 0,199 |
| ≥ 9 | 10% de arriba | 31.316 | 10,4% | 3.717 | -0,216 | -0,280 | -0,077 | -0,147 | -0,108 | -0,073 | 0,006 | 0,230 |
| ≥ 10 |  | 27.599 | 9,2% | 13.772 | -0,209 | -0,260 | -0,073 | -0,142 | -0,094 | -0,065 | -0,006 | 0,222 |
| ≥ 18 (xmin) |  | 13.827 | 4,6% | 3.292 | 0,168 | 0,173 | 0,080 | 0,059 | 0,128 | 0,088 | -0,193 | -0,027 |
| ≥ 20 |  | 10.535 | 3,5% | 10.535 | 0,120 | 0,106 | 0,049 | 0,174 | 0,130 | 0,058 | -0,200 | 0,033 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,124 | 0,168 | 0,120 | Plana |
| Edad | -0,106 | 0,173 | 0,106 | Sube al cortar: máximo en ≥ 18 |
| Mantenedores | 0,089 | 0,089 | 0,049 | Plana |
| En GitHub | -0,013 | 0,174 | 0,174 | Sube al cortar: máximo en ≥ 20 |
| Palabras clave | -0,068 | 0,130 | 0,130 | Sube al cortar: máximo en ≥ 20 |
| Dependientes de desarrollo | -0,012 | 0,088 | 0,058 | Sube al cortar: máximo en ≥ 18 |
| Dependencias de desarrollo | 0,189 | 0,207 | -0,200 | Baja al cortar |
| Fan-In | 0,055 | 0,230 | 0,033 | Sube al cortar: máximo en ≥ 9 |

## G3, sin familias, Fan-In limpio

| Corte | Corte pedido por deciles | Paquetes | De la población | Hasta el siguiente corte | Versiones | Edad | Mantenedores | En GitHub | Palabras clave | Dependientes de desarrollo | Dependencias de desarrollo | Fan-In |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ≥ 0 | 90% a 70% de arriba | 295.069 | 100,0% | 93.049 | 0,124 | -0,107 | 0,089 | -0,015 | -0,071 | -0,013 | 0,188 | 0,055 |
| ≥ 1 | 60% a 50% de arriba | 202.020 | 68,5% | 57.751 | 0,114 | -0,131 | 0,074 | -0,009 | -0,041 | 0,017 | 0,207 | 0,118 |
| ≥ 2 | 40% de arriba | 144.269 | 48,9% | 36.305 | 0,074 | -0,155 | 0,051 | -0,102 | -0,061 | 0,008 | 0,149 | 0,134 |
| ≥ 3 | 30% de arriba | 107.964 | 36,6% | 46.359 | 0,082 | -0,126 | 0,051 | -0,128 | -0,025 | 0,019 | 0,100 | 0,166 |
| ≥ 5 | 20% de arriba | 61.605 | 20,9% | 30.828 | -0,127 | -0,284 | -0,034 | -0,141 | -0,133 | -0,052 | 0,080 | 0,204 |
| ≥ 9 | 10% de arriba | 30.777 | 10,4% | 3.666 | -0,218 | -0,289 | -0,078 | -0,150 | -0,109 | -0,075 | 0,008 | 0,253 |
| ≥ 10 |  | 27.111 | 9,2% | 13.559 | -0,210 | -0,269 | -0,074 | -0,145 | -0,095 | -0,066 | -0,006 | 0,249 |
| ≥ 18 (xmin) |  | 13.552 | 4,6% | 3.255 | 0,168 | 0,162 | 0,081 | 0,058 | 0,130 | 0,098 | -0,204 | -0,015 |
| ≥ 20 |  | 10.297 | 3,5% | 10.297 | 0,119 | 0,084 | 0,051 | 0,174 | 0,137 | 0,079 | -0,216 | 0,056 |

Resumen (orientativo: un cambio cuenta si supera 0,05 y el margen de azar del grupo, que crece cuando quedan menos paquetes):

| Variable | Con todos | Máximo | En el último corte | Qué hace al cortar |
|---|---|---|---|---|
| Versiones | 0,124 | 0,168 | 0,119 | Plana |
| Edad | -0,107 | 0,162 | 0,084 | Sube al cortar: máximo en ≥ 18 |
| Mantenedores | 0,089 | 0,089 | 0,051 | Plana |
| En GitHub | -0,015 | 0,174 | 0,174 | Sube al cortar: máximo en ≥ 20 |
| Palabras clave | -0,071 | 0,137 | 0,137 | Sube al cortar: máximo en ≥ 20 |
| Dependientes de desarrollo | -0,013 | 0,098 | 0,079 | Sube al cortar: máximo en ≥ 18 |
| Dependencias de desarrollo | 0,188 | 0,207 | -0,216 | Baja al cortar |
| Fan-In | 0,055 | 0,253 | 0,056 | Sube al cortar: máximo en ≥ 9 |

## Comparación entre poblaciones, por variable

Cortes de la escala presentes en todas las poblaciones. Cada celda es la correlación con el Fan-Out en ese corte.

**Versiones:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | 0,189 | 0,189 | 0,110 | 0,124 | 0,124 |
| ≥ 1 | 0,162 | 0,165 | 0,109 | 0,114 | 0,114 |
| ≥ 2 | 0,126 | 0,130 | 0,082 | 0,073 | 0,074 |
| ≥ 3 | 0,123 | 0,123 | 0,097 | 0,081 | 0,082 |
| ≥ 5 | 0,007 | 0,005 | -0,077 | -0,124 | -0,127 |
| ≥ 10 | -0,083 | -0,082 | -0,156 | -0,209 | -0,210 |
| ≥ 20 | 0,079 | 0,082 | 0,108 | 0,120 | 0,119 |

**Edad:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | -0,042 | -0,042 | -0,041 | -0,106 | -0,107 |
| ≥ 1 | -0,014 | -0,014 | -0,089 | -0,130 | -0,131 |
| ≥ 2 | -0,013 | -0,014 | -0,113 | -0,153 | -0,155 |
| ≥ 3 | -0,018 | -0,020 | -0,095 | -0,123 | -0,126 |
| ≥ 5 | -0,065 | -0,068 | -0,210 | -0,276 | -0,284 |
| ≥ 10 | -0,081 | -0,087 | -0,203 | -0,260 | -0,269 |
| ≥ 20 | 0,041 | 0,026 | 0,088 | 0,106 | 0,084 |

**Mantenedores:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | 0,131 | 0,131 | 0,054 | 0,089 | 0,089 |
| ≥ 1 | 0,106 | 0,106 | 0,054 | 0,074 | 0,074 |
| ≥ 2 | 0,075 | 0,075 | 0,043 | 0,050 | 0,051 |
| ≥ 3 | 0,072 | 0,072 | 0,049 | 0,050 | 0,051 |
| ≥ 5 | 0,005 | 0,003 | -0,029 | -0,033 | -0,034 |
| ≥ 10 | -0,055 | -0,054 | -0,071 | -0,073 | -0,074 |
| ≥ 20 | 0,024 | 0,026 | 0,059 | 0,049 | 0,051 |

**En GitHub:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | -0,004 | -0,005 | -0,011 | -0,013 | -0,015 |
| ≥ 1 | -0,001 | 0,000 | -0,007 | -0,007 | -0,009 |
| ≥ 2 | -0,028 | -0,026 | -0,087 | -0,101 | -0,102 |
| ≥ 3 | -0,038 | -0,039 | -0,107 | -0,126 | -0,128 |
| ≥ 5 | -0,050 | -0,052 | -0,122 | -0,139 | -0,141 |
| ≥ 10 | -0,061 | -0,062 | -0,122 | -0,142 | -0,145 |
| ≥ 20 | 0,088 | 0,088 | 0,144 | 0,174 | 0,174 |

**Palabras clave:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | -0,060 | -0,062 | -0,061 | -0,068 | -0,071 |
| ≥ 1 | -0,031 | -0,032 | -0,035 | -0,039 | -0,041 |
| ≥ 2 | -0,032 | -0,035 | -0,052 | -0,060 | -0,061 |
| ≥ 3 | -0,025 | -0,026 | -0,027 | -0,024 | -0,025 |
| ≥ 5 | -0,060 | -0,060 | -0,108 | -0,134 | -0,133 |
| ≥ 10 | -0,043 | -0,045 | -0,078 | -0,094 | -0,095 |
| ≥ 20 | 0,063 | 0,066 | 0,106 | 0,130 | 0,137 |

**Dependientes de desarrollo:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | -0,003 | -0,001 | -0,005 | -0,012 | -0,013 |
| ≥ 1 | 0,031 | 0,031 | 0,022 | 0,017 | 0,017 |
| ≥ 2 | 0,036 | 0,035 | 0,020 | 0,009 | 0,008 |
| ≥ 3 | 0,042 | 0,042 | 0,028 | 0,020 | 0,019 |
| ≥ 5 | 0,013 | 0,011 | -0,039 | -0,048 | -0,052 |
| ≥ 10 | 0,001 | 0,001 | -0,050 | -0,065 | -0,066 |
| ≥ 20 | 0,051 | 0,062 | 0,061 | 0,058 | 0,079 |

**Dependencias de desarrollo:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | 0,152 | 0,150 | 0,197 | 0,189 | 0,188 |
| ≥ 1 | 0,168 | 0,166 | 0,209 | 0,207 | 0,207 |
| ≥ 2 | 0,138 | 0,136 | 0,159 | 0,149 | 0,149 |
| ≥ 3 | 0,117 | 0,117 | 0,115 | 0,099 | 0,100 |
| ≥ 5 | 0,112 | 0,115 | 0,093 | 0,078 | 0,080 |
| ≥ 10 | 0,086 | 0,087 | 0,019 | -0,006 | -0,006 |
| ≥ 20 | -0,049 | -0,055 | -0,144 | -0,200 | -0,216 |

**Fan-In:**

| Corte | g1_reg | g1_clean | g2_reg | g3_reg | g3_clean |
|---|---|---|---|---|---|
| ≥ 0 | 0,057 | 0,056 | 0,049 | 0,055 | 0,055 |
| ≥ 1 | 0,081 | 0,081 | 0,092 | 0,120 | 0,118 |
| ≥ 2 | 0,087 | 0,087 | 0,103 | 0,133 | 0,134 |
| ≥ 3 | 0,100 | 0,099 | 0,132 | 0,165 | 0,166 |
| ≥ 5 | 0,107 | 0,106 | 0,153 | 0,199 | 0,204 |
| ≥ 10 | 0,139 | 0,146 | 0,190 | 0,222 | 0,249 |
| ≥ 20 | -0,005 | 0,006 | 0,017 | 0,033 | 0,056 |

Claves: g1_reg = G1, con familias, Fan-In del registro; g1_clean = G1, con familias, Fan-In limpio; g2_reg = G2, solo vínculos externos, Fan-In del registro; g3_reg = G3, sin familias, Fan-In del registro; g3_clean = G3, sin familias, Fan-In limpio.
