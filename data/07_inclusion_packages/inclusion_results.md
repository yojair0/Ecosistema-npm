# Inclusion population results

## 1. Rules and parameters

- Snapshot date: 2026-09-18
- Family minimum size: 2
- Security pattern: `^0\.0\.\d+-security`
- Node built-ins not counted as bad dependencies: fs, http
- Platform binary patterns: `(linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)-(x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)` and the Rust targets

| Criterion | Description |
| --- | --- |
| no_graph | Not in dependency graph (expected 0) |
| no_profile | No profile extracted |
| name_collision | Two different names become equal in lower case |
| no_version | No dist-tags.latest or version missing |
| pre2010 | Created before 2010-01-01 |
| no_date | Has profile but no parseable creation date |
| post_snapshot | Created after 2026-09-18 |
| types_only | Name starts with @types/ |
| platform_binary | Name matches OS-architecture pattern or a Rust target |
| security_placeholder | Latest version is 0.0.x-security |
| bad_dependency | >=1 production dep missing, or a security placeholder other than the Node built-ins fs and http |
| family | Scope with >= 2 packages |

## 2. Totals

| Measure | Value |
| --- | --- |
| Rows read from pasada2 | 4,405,737 |
| Case-duplicate rows removed | 799 |
| Errors in pasada2 (outside universe) | 9,487 |
| Universe (unique names) | 4,395,451 |
| Graph nodes | 4,395,451 |
| Packages with profile | 4,389,236 |
| Packages without profile | 6,215 |
| Dataset A (with families) | 4,081,497 |
| Dataset B (without families) | 2,710,352 |
| Removed by family rule (A minus B) | 1,371,145 |

## 3. By criterion

| Criterion | Fail | Only this | % univ | Reference | Diff |
| --- | --- | --- | --- | --- | --- |
| no_graph | 0 | 0 | 0.00% | 0 | +0 |
| no_profile | 6,215 | 5,035 | 0.14% | 6,215 | +0 |
| name_collision | 787 | 764 | 0.02% | corrected rule |  |
| no_version | 1,279 | 7 | 0.03% | 1,279 | +0 |
| pre2010 | 1 | 1 | 0.00% | 1 | +0 |
| no_date | 0 | 0 | 0.00% | 0 | +0 |
| post_snapshot | 941 | 626 | 0.02% | 941 | +0 |
| types_only | 11,401 | 11,396 | 0.26% | 11,401 | +0 |
| platform_binary | 56,007 | 55,673 | 1.27% | corrected rule |  |
| security_placeholder | 155,341 | 154,636 | 3.53% | corrected rule |  |
| bad_dependency | 83,954 | 83,866 | 1.91% | corrected rule |  |
| family | 1,457,318 | 1,371,145 | 33.16% | 1,457,318 | +0 |

## 4. Funnel

| Step | Remain A | Lost A | Remain B | Lost B |
| --- | --- | --- | --- | --- |
| (start) | 4,395,451 |  | 4,395,451 |  |
| no_graph | 4,395,451 | -0 | 4,395,451 | -0 |
| no_profile | 4,389,236 | -6,215 | 4,389,236 | -6,215 |
| name_collision | 4,388,449 | -787 | 4,388,449 | -787 |
| no_version | 4,388,173 | -276 | 4,388,173 | -276 |
| pre2010 | 4,388,172 | -1 | 4,388,172 | -1 |
| no_date | 4,388,172 | -0 | 4,388,172 | -0 |
| post_snapshot | 4,387,235 | -937 | 4,387,235 | -937 |
| types_only | 4,375,834 | -11,401 | 4,375,834 | -11,401 |
| platform_binary | 4,320,001 | -55,833 | 4,320,001 | -55,833 |
| security_placeholder | 4,165,363 | -154,638 | 4,165,363 | -154,638 |
| bad_dependency | 4,081,497 | -83,866 | 4,081,497 | -83,866 |
| family | 4,081,497 | (skip) | 2,710,352 | -1,371,145 |

## 5. Impact of the family rule

### 5a. Scope size thresholds

| Min size | Scopes | Packages | % universe |
| --- | --- | --- | --- |
| 2 | 186,872 | 1,457,318 | 33.16% |
| 5 | 66,150 | 1,143,673 | 26.02% |
| 10 | 27,350 | 893,931 | 20.34% |
| 20 | 10,176 | 667,406 | 15.18% |
| 50 | 2,515 | 443,723 | 10.10% |
| 100 | 862 | 334,194 | 7.60% |
| 500 | 96 | 196,968 | 4.48% |

### 5b. 30 largest families removed by the rule

| Scope | Packages |
| --- | --- |
| @hyper.fun | 30,273 |
| @citation | 10,530 |
| @alifd | 8,459 |
| @openfonts | 6,768 |
| @semi-bot | 5,987 |
| @arco-themes | 5,617 |
| @stdlib | 5,555 |
| @iflow-mcp | 5,192 |
| @gitmyabi | 3,457 |
| @pipedream | 3,435 |
| @mindyartera | 3,134 |
| @datafire | 2,260 |
| @depup | 2,127 |
| @fontsource | 2,126 |
| @react-shimeji | 2,022 |
| @expo-google-fonts | 2,006 |
| @n8n-dev | 1,826 |
| @heartlandone | 1,818 |
| @ohos-ports | 1,752 |
| @wix | 1,675 |
| @wemnyelezxnpm | 1,638 |
| @ryancavanaugh | 1,626 |
| @electron-fonts | 1,612 |
| @haybarn | 1,611 |
| @watheia | 1,562 |
| @ryniaubenpm | 1,518 |
| @compai | 1,457 |
| @alicloud | 1,427 |
| @gitmyabi-stg | 1,420 |
| @phoenix-plugin-registry | 1,380 |

### 5c. @hyper.fun

- Packages in universe: 30,273
- In A: 30,273
- In B: 0

### 5d. fan_in and fan_out comparison (A, A_ext, B)

A_ext: population A, counting only dependents from other scopes.

| Metric | Set | Mean | Median | p90 | p99 | Max | % zero |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fan_in | A | 3.68 | 0 | 1 | 18 | 195,952 | 82.9% |
| fan_in | A_ext | 3.36 | 0 | 1 | 13 | 195,952 | 89.8% |
| fan_in | B | 4.33 | 0 | 1 | 16 | 195,952 | 88.4% |
| fan_out | A | 3.61 | 1 | 9 | 34 | 1,000 | 36.4% |
| fan_out | B | 3.56 | 1 | 8 | 34 | 1,000 | 38.2% |

### 5e. Distribution by fan_in and fan_out bands

**fan_in**

| Band | A | % A | A_ext | % A_ext | B | % B |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 3,383,865 | 82.9% | 3,665,927 | 89.8% | 2,395,260 | 88.4% |
| 1-9 | 630,657 | 15.5% | 365,383 | 9.0% | 277,929 | 10.3% |
| 10-99 | 55,217 | 1.4% | 39,423 | 1.0% | 28,486 | 1.1% |
| 100-999 | 9,737 | 0.2% | 8,868 | 0.2% | 7,052 | 0.3% |
| 1000+ | 2,021 | 0.0% | 1,896 | 0.0% | 1,625 | 0.1% |

**fan_out**

| Band | A | % A | B | % B |
| --- | --- | --- | --- | --- |
| 0 | 1,486,620 | 36.4% | 1,035,424 | 38.2% |
| 1-2 | 1,211,133 | 29.7% | 780,510 | 28.8% |
| 3-9 | 1,029,424 | 25.2% | 666,610 | 24.6% |
| 10-49 | 336,795 | 8.3% | 215,424 | 7.9% |
| 50+ | 17,525 | 0.4% | 12,384 | 0.5% |

## 6. By creation year

| Year | Universe | A | B | % B/univ |
| --- | --- | --- | --- | --- |
| 1970 | 1 | 0 | 0 | 0.0% |
| 2010 | 110 | 109 | 109 | 99.1% |
| 2011 | 4,985 | 4,879 | 4,879 | 97.9% |
| 2012 | 13,261 | 13,124 | 13,124 | 99.0% |
| 2013 | 31,683 | 31,488 | 31,488 | 99.4% |
| 2014 | 61,493 | 61,127 | 61,127 | 99.4% |
| 2015 | 103,962 | 103,238 | 100,961 | 97.1% |
| 2016 | 164,819 | 159,321 | 148,627 | 90.2% |
| 2017 | 204,505 | 201,252 | 176,227 | 86.2% |
| 2018 | 247,888 | 244,604 | 187,181 | 75.5% |
| 2019 | 281,559 | 278,317 | 188,955 | 67.1% |
| 2020 | 297,169 | 293,956 | 194,478 | 65.4% |
| 2021 | 343,242 | 327,560 | 211,955 | 61.8% |
| 2022 | 376,351 | 366,027 | 207,826 | 55.2% |
| 2023 | 380,193 | 365,976 | 235,603 | 62.0% |
| 2024 | 707,057 | 610,442 | 447,959 | 63.4% |
| 2025 | 465,790 | 365,965 | 212,680 | 45.7% |
| 2026 | 705,168 | 654,112 | 287,173 | 40.7% |
| NA | 6,215 | 0 | 0 | 0.0% |

## 7. Dependencies

### 7a. Packages by number of missing or placeholder deps

| Bad deps | Packages |
| --- | --- |
| 1 | 44,823 |
| 2 | 13,099 |
| 3-9 | 8,740 |
| 10+ | 17,292 |
| Total | 83,954 |

### 7b. Packages that declare Node built-ins (fs, http)

Kept: npm holds security placeholders under those names, but Node loads its own built-in module. Packages declaring them: 13,531; in A: 13,253.

| Year | Packages declaring fs or http |
| --- | --- |
| 2012 | 7 |
| 2013 | 7 |
| 2014 | 71 |
| 2015 | 394 |
| 2016 | 719 |
| 2017 | 958 |
| 2018 | 1,195 |
| 2019 | 1,290 |
| 2020 | 1,244 |
| 2021 | 1,504 |
| 2022 | 1,435 |
| 2023 | 1,453 |
| 2024 | 2,084 |
| 2025 | 903 |
| 2026 | 252 |

### 7c. Top 20 security placeholders declared as dependencies

| Placeholder | Packages declaring it |
| --- | --- |
| fs | 11,955 |
| pubteahy | 9,925 |
| http | 2,012 |
| astralamber | 1,543 |
| cosmicchorus | 1,534 |
| luminouslab | 1,534 |
| stellarscribe | 1,534 |
| ciphersage | 1,534 |
| vividvortex | 1,534 |
| nebulanomad | 1,534 |
| api-chatfb | 808 |
| api-chatfb-test | 801 |
| api-chat-fanpage-facebook | 800 |
| @oraliepham/api-chat-fanpage-facebook | 800 |
| @oraliepham/api-facebooknew | 800 |
| api-facebooknew | 797 |
| @scdb/simple-http | 789 |
| @utilcode/simple-http | 789 |
| seblakkuah | 711 |
| vndrabnb | 698 |

## 8. Notes

- The fan_in and fan_out of datasets A and B come from the full dependency graph and count dependents that may have been excluded from the population.
- Scope size is counted over the universe before applying any other criterion.
- Packages with errors in pasada2 are not part of the universe, but a dependency on one of them counts as existing.
- fan_in_internal counts dependents from the package's own scope, read from pasada2; fan_in_external is fan_in minus fan_in_internal.
- Dependency lists are not stored (only dep_hash and counts). Peer and optional dependency lists are also not stored (only n_peer and n_opt).
