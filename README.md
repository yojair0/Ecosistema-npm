# Internal structure vs. dependency-network position in NPM

Extraction pipeline for the npm registry. Measures each package's position
in the dependency network and collects profile metadata for stratification.

## Snapshot

| | |
|---|---|
| Date | 2026-09-18 |
| Feed sequence | 131,412,017 |
| Active packages | 4,405,737 |

## Execution order

| Script | Reads | Writes | 
|---|---|---|---|
| `tools/preflight_check.py` | `data/pasada1/` | stdout | 
| `01_ingest_registry_index.py` | replication feed | `data/pasada1/` | 
| `02_fetch_dependencies.py` | `data/pasada1/` | `data/pasada2/` | 
| `03_build_dependency_graph.py` | `data/pasada2/` | `data/metricas_externas.csv` | 
| `04_extract_profile.py` | `data/pasada1/` | `data/profile/` | 
| `05_extract_downloads.py` | `data/pasada1/` | `data/downloads/` | 
| `06_build_full_graph.py` | `pasada2/` + `profile/` | full graph table | 
| `07_analyze_profile.py` | all of the above | `results/REPORT.md` | 

Passes 02, 04 and 05 all read the index from 01 and are independent of each
other. Pass 04 does not require 02, which is why it can run on a separate
machine. Pass 06 supersedes 03 by adding peer and optional edge types,
which come from 04.

## Why three sources instead of one

The replication feed supports `include_docs=true`, which would return the
full document for every package in a single paginated walk. Cloudflare
returns 400 for that parameter — verified 2026-09-18 in four variants
(with and without `limit`, reversed order, `limit=1`).

Without it the feed yields only identity, so content is requested per
package from the registry API, and download counts from a third API.

## Methodological decisions

- **Prod/dev dependency counts live only in the graph passes.** Pass 04
  omits them to avoid two versions of the same measure taken on different
  dates.
- **Peer and optional edge lists are kept.** Fan-out follows from a count,
  fan-in does not: it needs to know which package points where.
- **404 responses are not nodes.** A package that no longer exists cannot
  receive fan-in; references to it are recorded as dangling.
- **Packages without a usable version are nodes.** They receive fan-in but
  produce no fan-out.
- **Names are normalised** with `strip().lower()` in every pass, so tables
  join correctly.
- **`deprecated` is truthy-only.** npm un-deprecates by setting an empty
  string, so key presence alone is insufficient.


## Resuming

Passes 02, 04 and 05 write an atomic checkpoint with `fsync` after each
shard. `Ctrl+C` once flushes the current shard and saves; re-running the
same command resumes. Worst case loss is one shard.

## Data

Shards are not in the repository. See release notes for download links.