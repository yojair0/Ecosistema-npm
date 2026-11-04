# Diccionario de CSVs — `explore_exclusion_candidates.py`

## Part 1 — Tiempo y perfil

### 1. `p1_year_month.csv`
Conteos de paquetes creados, pivoteados por año × mes.

| Variable | Significado |
|----------|-------------|
| `year` | Año de creación del paquete |
| `M01`…`M12` | Cantidad de paquetes creados en cada mes del año |
| `total` | Suma anual |

### 2. `p1_daily_counts_raw.csv`
Conteo diario bruto de paquetes creados (incluye días post-snapshot).

| Variable | Significado |
|----------|-------------|
| `created_date` | Fecha de creación |
| `n` | Cantidad de paquetes creados ese día |
| `date` | Igual a `created_date` (redundante) |
| `year` | Año extraído de la fecha |
| `post_snapshot` | `True` si la fecha es posterior al snapshot (2026-09-18) |

### 3. `p1_daily_counts.csv`
Serie temporal diaria (2011–snapshot) con estadísticos de detección de anomalías usando mediana/MAD rolling.

| Variable | Significado |
|----------|-------------|
| `date` | Fecha |
| `n` | Paquetes creados ese día (0-filled) |
| `year` | Año |
| `created_date` | Igual a `date` |
| `med_31/61/91` | Mediana móvil centrada con ventana de 31/61/91 días |
| `mad_31/61/91` | MAD (median absolute deviation) móvil para cada ventana |
| `dev_mad_31/61/91` | Desviación normalizada: `(n − mediana) / MAD`. Valores altos señalan días anómalos |

### 4. `p1_anomalous_days_grid.csv`
Grilla resumen de días anómalos por combinación de ventana y umbral K.

| Variable | Significado |
|----------|-------------|
| `window` | Tamaño de ventana rolling (31, 61, 91 días) |
| `K` | Umbral de desviación (3, 5, 10) — un día es anómalo si `dev_mad > K` |
| `year` | Año |
| `anom_days` | Cantidad de días anómalos en ese año |
| `anom_pkgs` | Paquetes creados en esos días anómalos |
| `year_total` | Total de paquetes creados en el año |
| `pct` | `anom_pkgs / year_total × 100` |

### 5. `p1_top20_days.csv`
Los 20 días con mayor cantidad absoluta de paquetes creados.

| Variable | Significado |
|----------|-------------|
| `date` | Fecha |
| `n` | Cantidad de paquetes creados |
| `year` | Año |

### 6. `p1_anomalous_days_decomposed.csv`
Perfil detallado de cada día anómalo (dev_mad_61 > 5), describiendo qué tipo de paquetes se crearon.

| Variable | Significado |
|----------|-------------|
| `date` | Fecha del día anómalo |
| `n` | Paquetes creados |
| `dev_mad_61` | Desviación MAD con ventana 61 |
| `exceeds_K3/K5/K10` | Booleanos: si supera cada umbral |
| `pct_1ver` | % de paquetes con una sola versión publicada |
| `pct_scoped` | % de paquetes con scope (`@scope/nombre`) |
| `pct_0_maint` | % con 0 maintainers |
| `pct_fo_0` | % con fan_out = 0 (entre elegibles, sin `sin_version`) |
| `med_fc` | Mediana de file_count |
| `pct_top1_dep_group` | % que pertenece al grupo de dep-list más frecuente del día |
| `pct_top3_scopes` | % cubierto por los 3 scopes más comunes del día |
| `pct_top5_pfx_sfx` | % cubierto por los 5 prefijos/sufijos más comunes |
| `n_distinct_combos` | Combinaciones únicas de (n_versions, file_count, n_keywords, has_github, scoped, fan_out) |
| `uses_fan_out` | Siempre `True` (indica que esta tabla usa fan_out) |

### 7. `p1_profile_by_year.csv`
Estadísticos agregados del perfil de paquetes por año de creación.

| Variable | Significado |
|----------|-------------|
| `year` | Año (o bucket: `pre2010`, `no_date`) |
| `packages` | Total de paquetes |
| `pct_1ver` | % con una sola versión |
| `pct_scoped` | % scoped |
| `pct_has_github` | % con repositorio GitHub |
| `pct_no_keywords` | % sin keywords |
| `pct_0_maint` | % con 0 maintainers |
| `pct_fi_0` | % con fan_in = 0 (nadie depende de ellos) |
| `n_sin_version` | Paquetes sin versión publicable (`sin_version = True`) |
| `n_fo_eligible` | Paquetes elegibles para fan_out (con versión) |
| `pct_fo_0` | % elegibles con fan_out = 0 |
| `med_nver` | Mediana de n_versions |
| `med_fo` | Mediana de fan_out (elegibles) |
| `med_fc` | Mediana de file_count |
| `n_with_fc` | Paquetes con file_count disponible |

### 8. `p1_no_maintainers.csv`
Análisis de paquetes con 0 maintainers en formato largo (multi-sección).

| Variable | Significado |
|----------|-------------|
| `section` | Sección: `year_month` (conteos mensuales), `profile` (comparación perfil 0-maint vs resto), `anom_overlap` (solapamiento con días anómalos), `top20_days` (top 20 días con más 0-maint) |
| `key1` | Clave primaria (año, grupo, fecha, o `__TOTAL__`) |
| `key2` | Clave secundaria (mes, año_cat, vacío) |
| `label` | Métrica: `n_0maint`, `pct_0maint`, `med_n_versions`, `med_file_count`, `med_fan_out`, `pct_scoped`, `med_dep_group_size` |
| `value` | Valor numérico |
| `uses_fan_out` | `True` si la métrica usa fan_out |

---

## Part 2 — Duplicación, fingerprints, scopes, nombres

### 9. `p2_dep_groups_by_year.csv`
Distribución del tamaño de "grupos de dep-list" (paquetes con idéntica lista de dependencias) por año.

| Variable | Significado |
|----------|-------------|
| `year` | Año |
| `scope` | `universe` (tamaño global del grupo) o `within_year` (tamaño dentro del año) |
| `bucket` | Rango de tamaño del grupo: `1`, `2-10`, `11-100`, `101-1000`, `>1000` |
| `packages` | Cantidad de paquetes en ese bucket |
| `pct` | Porcentaje sobre el total del año. También hay filas con `bucket=top10_pct` (% de los 10 grupos más grandes) y `bucket=HHI` (índice Herfindahl-Hirschman de concentración) |

### 10. `p2_fingerprints_by_year.csv`
Top 10 valores más frecuentes de file_count, n_keywords y fan_out por año, más HHI.

| Variable | Significado |
|----------|-------------|
| `variable` | `file_count`, `n_keywords`, o `fan_out` |
| `year` | Año |
| `rank` | Posición (1–10); `rank=0` para la fila resumen HHI |
| `value` | El valor concreto de la variable (o HHI en fila resumen) |
| `count` | Cantidad de paquetes con ese valor |
| `pct` | Porcentaje sobre el total del año |

### 11. `p2_scopes_by_year.csv`
Top 20 scopes más frecuentes por año con indicadores de concentración temporal.

| Variable | Significado |
|----------|-------------|
| `year` | Año |
| `scope` | Nombre del scope (ej. `@types`, `@babel`), o `__TOP20_PCT__`/`__TOP50_PCT__` para filas resumen |
| `packages` | Cantidad de paquetes en ese scope/año |
| `pct_1ver` | % con una sola versión |
| `first` | Fecha del primer paquete creado en ese scope/año |
| `last` | Fecha del último |
| `window_days` | Días entre `first` y `last` (ventana temporal de actividad) |

### 12. `p2_name_terms_by_year.csv`
Top 20 prefijos y sufijos de nombres (token antes/después del primer/último guion) por año, solo paquetes no scoped.

| Variable | Significado |
|----------|-------------|
| `year` | Año |
| `kind` | `prefix` o `suffix` |
| `rank` | Posición (1–20) |
| `term` | El token (ej. `react`, `node`, `plugin`) |
| `count` | Cantidad de paquetes con ese prefijo/sufijo |
| `pct` | Porcentaje sobre no-scoped del año |

### 13. `p2_top_combos_by_year.csv`
Top 20 combinaciones de perfil (tupla de 6 variables) más frecuentes por año. Detecta paquetes "idénticos" en su huella.

| Variable | Significado |
|----------|-------------|
| `year` | Año |
| `rank` | Posición (1–20) |
| `n_versions` | Valor de n_versions en la combinación |
| `file_count` | Valor de file_count (vacío si NaN) |
| `n_keywords` | Valor de n_keywords |
| `has_github` | Tiene repo GitHub |
| `scoped` | Es paquete scoped |
| `fan_out` | Valor de fan_out |
| `count` | Paquetes con esa combinación exacta |
| `pct` | % sobre el total del año |
| `hhi` | Índice HHI sobre todas las combinaciones del año |
| `n_total` | Total de paquetes del año |
| `n_distinct_combos` | Combinaciones distintas en el año |
| `fc_available` | Proporción de paquetes con file_count disponible |
| `fc_low_coverage` | `True` si file_count cubre < 90% |
| `uses_fan_out` | Siempre `True` |

### 14. `p2_emergent_name_families.csv`
"Familias" de nombres (por prefijo/sufijo) que aparecen concentradas en un solo año, detectadas con umbrales (R, M).

| Variable | Significado |
|----------|-------------|
| `kind` | `prefix` o `suffix` |
| `term` | El token (ej. `retyped`) |
| `year` | Año pico |
| `R` | Umbral de ratio: conteo en el año pico / máximo en otros años |
| `M` | Umbral mínimo de conteo |
| `n` | Paquetes con ese término en el año pico |
| `first` / `last` | Primera y última fecha de creación |
| `window_days` | Ventana temporal en días |
| `pct_1ver` | % con una sola versión |
| `pct_has_github` | % con GitHub |
| `pct_scoped` | % scoped |
| `pct_0_maint` | % con 0 maintainers |

### 15. `p2_group_profiles_keywords.csv`
Tabla larga multi-sección con perfiles de grupos y análisis de keywords.

| Variable | Significado |
|----------|-------------|
| `section` | `family_profile` (perfiles de familias emergentes), `scope_profile` (top 30 scopes/año), `top30_kw` (top 30 keywords/año), `kw_growth` (crecimiento interanual de keywords) |
| `key1` | Tipo/scope/keyword según sección |
| `key2` | Término/scope/keyword |
| `key3` | Año |
| `label` | Métrica: `n`, `med_n_versions`, `pct_1ver`, `pct_has_github`, etc. |
| `value` | Valor numérico |

---

## Part 3 — Indicadores de exclusión (pendientes de generación)

### 16. `p3_exclusion_candidates.csv` (pendiente)
Resumen de indicadores booleanos de exclusión por fan_in bracket, fan_out bracket, y solapamiento entre pares de indicadores.

### 17. `p3_candidate_counts_by_year.csv` (pendiente)
Conteos de paquetes flaggeados por cada indicador, desglosados por año.

**Indicadores:** `ind_spam`, `ind_sb_*` (scope burst), `ind_dgb_*` (dep-group burst), `ind_enf_*` (emergent name family), `ind_zero_maint`, `ind_types` (@types/\*), `ind_platform_binary` (binarios específicos de plataforma).
