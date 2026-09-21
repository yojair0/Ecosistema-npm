# Estructura interna vs. topologia externa en NPM

Pipeline Recorre el registro de NPM,
extrae dependencias declaradas y calcula metricas de posicion topologica.

## Snapshot

| | |
|---|---|
| Fecha | 18-09-2026 |
| Seq final | 131,412,017 |
| Paquetes activos | 4,405,737 |

## Por que dos pasadas

El plan original usaba include_docs=true en el feed de replicacion para
traer el documento completo de cada paquete en una sola pasada. Cloudflare
lo bloquea (400 Bad Request, verificado en cuatro variantes). Sin ese
parametro el feed solo entrega identidad, no contenidoo.

La extraccion quedo dividida en dos:

| Script | Fuente | Entrega | Tiempo |
|---|---|---|---|
| pasada1.py | replicate.npmjs.com/_changes | nombre, seq, borrado | 6.9 min |
| pasada2.py | registry.npmjs.org/pkg | deps, dev_deps, tarball | 3.5 h |
| pasada3.py | local | aristas, Fan-In, Fan-Out | pendiente |

El cursor seq permite reanudar sin perder
progreso.

## Resultados

Pasada 1 -- feed de replicacion completo desde seq=0

| | |
|---|---|

| Eventos totales | 6,433,267 |
| Paquetes activos | 4,405,737 |
| Paquetes borrados | 2,027,530 (31.5%) |
| Con  @org/ | 1,703,010 (38.7%) |
| Shards | 65 |

Pasada 2 -- contenido por paquete

| | |
|---|---|
| Con version utilizable | 4,394,970 |
| Sin version | 1,280 |
| Despublicados entre pasadas | 9,486 (0.22%) |
| Con tarball | 100% |
| Sin dependencias declaradas | 1,704,447 (38.8%) |
| Shards | 89 |

## Decisiones metodologicas

- repository descartado. No viene en el formato abreviado y traerlo
  duplicaba la transferencia. El tarball si viene y es la ruta acordada
  para obtener codigo fuente.
- deps y dev_deps en campos separados, nunca mezclados. Permite
  calcular ambos grafos sin re-descargar.
- Formato abreviado (Accept: application/vnd.npm.install-v1+json):
  57.8% menos transferencia, medido sobre express (809 KB a 341 KB).
- Recorrido completo desde seq=0, incluyendo historial de borrados.
- 404 no son nodos. Un paquete despublicado no existe; si alguien lo
  declara como dependencia, aparece como referencia colgante.
- sin_version si son nodos. Reciben Fan-In pero no generan Fan-Out.

## Datos

Los shards no estan en el repositorio (~2 GB). Descarga:

    [https://drive.google.com/drive/folders/1P4nBb1kxQjd_7do0P_UITV4nXLhzqcTQ?usp=sharing]

Descomprimir en data/ manteniendo la estructura data/pasada1/ y
data/pasada2/.

## Pendiente

- pasada3.py -- construir aristas, normalizar nombres, detectar colgantes,
  calcular Fan-In/Fan-Out global
- Validar contra Wittern et al. (2016): Fan-In=0 a 72.5%, Fan-In>=6 a 4.9%,
  con >=1 dependencia a 81.3%
- Corregir la cifra de la Introduccion del Charter: dice "mas de 2 millones"
  citando npm; medimos 4,405,737

## Uso

    python3 pasada1.py
    python3 pasada2.py
    python3 pasada3.py

Ambas pasadas guardan checkpoint atomico. Si se cortan, volver a correr
el mismo comando retoma donde quedo.
