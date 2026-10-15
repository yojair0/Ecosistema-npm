# Strata exploration report

Generated 2026-10-14 20:52 from 4,395,451 nodes.

## 1. Exclusions

- **spam_suspect**: more than 50% of declared dependencies point to names absent from the registry, with at least 10 declared. Below that size a single typo would flag a package.
- **spam_propagated**: not a suspect itself, but more than 50% of its fan-in comes from suspects. Spam packages declare one another, so fan-in can be inflated artificially.
- **types_only**: `@types/` packages hold TypeScript declarations, with no executable code.
- **platform_binary**: names with an operating-system and architecture suffix, which ship compiled code.

The last two are name-based pre-filters; whether a package holds analysable JavaScript is settled later on its tarball.

| Criterion | Packages |
|---|---|
| missing share > 50%, any size (reference) | 21,606 |
| spam_suspect | 15,540 |
| spam_propagated | 688 |
| types_only | 11,401 |
| platform_binary | 52,562 |
| excluded by any criterion | 80,178 |

### Exclusions by stratum

| Stratum | spam_suspect | spam_propagated | types_only | platform_binary |
|---|---|---|---|---|
| 0a isolated | 0 | 0 | 2,237 | 48,760 |
| 0b consumer | 15,000 | 0 | 4,078 | 293 |
| 1-9 | 65 | 346 | 3,685 | 3,499 |
| 10-99 | 399 | 231 | 1,139 | 10 |
| 100-999 | 76 | 73 | 237 | 0 |
| >=1000 | 0 | 38 | 25 | 0 |

## 2. Log-decade strata and eligibility

Eligible: has a profile, at least 365 days old at the snapshot, not deprecated, not excluded, and at least 5 published files. Packages without a file count, mostly old ones, are kept and counted separately, since excluding them would bias against older packages.

| Stratum | Packages | Excluded | Eligible | of which file count unknown |
|---|---|---|---|---|
| 0a isolated | 1,511,124 | 50,997 | 667,114 (44.1%) | 152,234 |
| 0b consumer | 2,161,405 | 19,371 | 1,398,979 (64.7%) | 224,814 |
| 1-9 | 650,785 | 7,582 | 421,341 (64.7%) | 77,749 |
| 10-99 | 58,669 | 1,779 | 45,247 (77.1%) | 6,318 |
| 100-999 | 11,351 | 386 | 8,531 (75.2%) | 871 |
| >=1000 | 2,117 | 63 | 1,875 (88.6%) | 96 |

## 3. Clustering on the topological profile

Features: log(x + 1) of fan_in, fan_in_dev, fan_in_peer, fan_in_opt, fan_out, fan_out_dev, fan_out_peer, fan_out_opt, standardised. 3,566,433 packages with a profile; those with every count at zero are excluded, since as a single point they cannot be clustered. k is fixed in advance as the highest silhouette, computed on a random sample of 10,000.

| k | inertia | silhouette |
|---|---|---|
| 2 | 26,052,613 | 0.140 |
| 3 | 21,661,864 | 0.207 |
| 4 | 20,013,706 | 0.214 |
| 5 | 17,110,059 | 0.241 |
| 6 | 15,591,010 | 0.252 |
| 7 | 13,362,548 | 0.266 |
| 8 | 12,293,678 | 0.275 |

Best k = **8**, silhouette **0.275**: weak structure. It sits at the edge of the range, so no natural k emerges.

### Share of packages with each dependency type, by cluster

| cluster | n | fan_in > 0 | fan_in_dev > 0 | fan_in_peer > 0 | fan_in_opt > 0 | fan_out > 0 | fan_out_dev > 0 | fan_out_peer > 0 | fan_out_opt > 0 | excluded |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1,400,494 | 12% | 3% | 0% | 0% | 72% | 46% | 5% | 0% | 0.4% |
| 1 | 966,673 | 11% | 3% | 0% | 0% | 100% | 92% | 7% | 0% | 1.5% |
| 2 | 687,331 | 10% | 4% | 2% | 0% | 58% | 83% | 93% | 0% | 0.0% |
| 3 | 291,942 | 100% | 17% | 2% | 0% | 71% | 70% | 12% | 0% | 0.6% |
| 4 | 88,575 | 60% | 85% | 65% | 0% | 67% | 76% | 46% | 0% | 3.5% |
| 5 | 64,595 | 9% | 3% | 2% | 0% | 38% | 39% | 11% | 100% | 0.1% |
| 6 | 52,802 | 14% | 4% | 2% | 100% | 7% | 7% | 2% | 1% | 87.0% |
| 7 | 14,021 | 98% | 100% | 94% | 29% | 70% | 78% | 41% | 2% | 4.8% |

### Clusters by decade stratum (row %)

| cluster | 0a isolated | 0b consumer | 1-9 | 10-99 | 100-999 | >=1000 |
|---|---|---|---|---|---|---|
| 0 | 23.1% | 64.6% | 12.3% | 0.0% | 0.0% | 0.0% |
| 1 | 0.0% | 89.0% | 11.0% | 0.0% | 0.0% | 0.0% |
| 2 | 38.6% | 51.0% | 10.4% | 0.0% | 0.0% | 0.0% |
| 3 | 0.0% | 0.0% | 85.3% | 13.0% | 1.5% | 0.2% |
| 4 | 15.3% | 25.2% | 42.6% | 15.4% | 1.5% | 0.0% |
| 5 | 59.7% | 31.2% | 8.5% | 0.5% | 0.0% | 0.0% |
| 6 | 83.8% | 2.2% | 11.4% | 2.3% | 0.3% | 0.0% |
| 7 | 0.6% | 1.1% | 9.6% | 38.7% | 38.6% | 11.4% |
