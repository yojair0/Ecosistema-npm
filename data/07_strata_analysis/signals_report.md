# Network signals report

Generated 2026-10-21 03:33 over 4,395,451 nodes and 16,333,670 edges.

## Verification

- Fan-in recomputed from the edges differs from pass 03 in 866 packages.
- Pass 03 fan-out equals declared dependencies in 100.00% of packages, and dependencies that exist in 98.48%.

## Rules

| Rule | Packages |
|---|---|
| spam_declarer | 15,540 |
| spam_propagated | 688 |
| types_only | 11,401 |
| platform_binary (all) | 55,300 |
| platform_binary (Rust format only) | 2,738 |
| security_placeholder | 155,255 |
| coordinated_core | 6,796 |
| colluded_dependent | 206,316 |
| excluded_any | 440,409 |

## Strata under each fan-in

| Stratum | Raw | Clean | Clean, out of scope |
|---|---|---|---|
| 0a isolated | 1,511,103 | 1,511,955 | 1,582,284 |
| 0b consumer | 2,161,382 | 2,164,418 | 2,381,221 |
| 1-9 | 650,820 | 651,597 | 381,589 |
| 10-99 | 58,678 | 56,910 | 40,888 |
| 100-999 | 11,351 | 8,782 | 7,805 |
| >=1000 | 2,117 | 1,789 | 1,664 |

## Reference packages (must all be False)

| Package | spam_declarer | spam_propagated | coordinated_core | colluded_dependent |
|---|---|---|---|---|
| react | False | False | False | False |
| lodash | False | False | False | False |
| chalk | False | False | False | False |
| cors | False | False | False | False |
| ms | False | False | False | False |
| strip-ansi | False | False | False | False |
| debug | False | False | False | False |
| express | False | False | False | False |
| axios | False | False | False | False |
| commander | False | False | False | False |
| tslib | False | False | False | False |
| @babel/core | False | False | False | False |
| @stdlib/math-base-special-pow | False | False | False | False |

## Sensitivity grid

| rule | params | flagged | flagged_fan_in_100_plus | half_a | half_b | references_flagged |
|---|---|---|---|---|---|---|
| spam_declarer | share>0.3, deps>=5 | 20042 | 133 | 10083 | 9959 | none |
| spam_declarer | share>0.3, deps>=10 | 16913 | 110 | 8518 | 8395 | none |
| spam_declarer | share>0.3, deps>=15 | 16134 | 107 | 8116 | 8018 | none |
| spam_declarer | share>0.5, deps>=5 | 16274 | 93 | 8189 | 8085 | none |
| spam_declarer | share>0.5, deps>=10 | 15540 | 76 | 7834 | 7706 | none |
| spam_declarer | share>0.5, deps>=15 | 15080 | 75 | 7613 | 7467 | none |
| spam_declarer | share>0.7, deps>=5 | 14536 | 79 | 7309 | 7227 | none |
| spam_declarer | share>0.7, deps>=10 | 14195 | 70 | 7144 | 7051 | none |
| spam_declarer | share>0.7, deps>=15 | 13869 | 70 | 6993 | 6876 | none |
| coordinated_core | deps>=10, span<=60d, recent<=0.005 | 6797 | 2435 | 3350 | 3447 | none |
| coordinated_core | deps>=10, span<=60d, recent<=0.02 | 6798 | 2436 | 3350 | 3448 | none |
| coordinated_core | deps>=10, span<=120d, recent<=0.005 | 8588 | 3115 | 4232 | 4356 | none |
| coordinated_core | deps>=10, span<=120d, recent<=0.02 | 8589 | 3116 | 4232 | 4357 | none |
| coordinated_core | deps>=10, span<=180d, recent<=0.005 | 8904 | 3139 | 4389 | 4515 | none |
| coordinated_core | deps>=10, span<=180d, recent<=0.02 | 8909 | 3144 | 4393 | 4516 | none |
| coordinated_core | deps>=20, span<=60d, recent<=0.005 | 5296 | 2435 | 2590 | 2706 | none |
| coordinated_core | deps>=20, span<=60d, recent<=0.02 | 5297 | 2436 | 2590 | 2707 | none |
| coordinated_core | deps>=20, span<=120d, recent<=0.005 | 6796 | 3115 | 3317 | 3479 | none |
| coordinated_core | deps>=20, span<=120d, recent<=0.02 | 6797 | 3116 | 3317 | 3480 | none |
| coordinated_core | deps>=20, span<=180d, recent<=0.005 | 6960 | 3139 | 3400 | 3560 | none |
| coordinated_core | deps>=20, span<=180d, recent<=0.02 | 6965 | 3144 | 3404 | 3561 | none |
| coordinated_core | deps>=50, span<=60d, recent<=0.005 | 3669 | 2411 | 1789 | 1880 | none |
| coordinated_core | deps>=50, span<=60d, recent<=0.02 | 3670 | 2412 | 1789 | 1881 | none |
| coordinated_core | deps>=50, span<=120d, recent<=0.005 | 4659 | 3091 | 2264 | 2395 | none |
| coordinated_core | deps>=50, span<=120d, recent<=0.02 | 4660 | 3092 | 2264 | 2396 | none |
| coordinated_core | deps>=50, span<=180d, recent<=0.005 | 4719 | 3115 | 2294 | 2425 | none |
| coordinated_core | deps>=50, span<=180d, recent<=0.02 | 4724 | 3120 | 2298 | 2426 | none |
| colluded_dependent | share>=0.3 | 211064 | 0 | 105825 | 105239 | none |
| colluded_dependent | share>=0.5 | 206316 | 0 | 103465 | 102851 | none |
| colluded_dependent | share>=0.7 | 189917 | 0 | 95214 | 94703 | none |

## Triage: 801 packages in strata 100+ with no out-of-scope dependents

| Scope | Packages | Share flagged by any rule | Share with one version | Max fan-in |
|---|---|---|---|---|
| @saovietproject | 155.0 | 0% | 100% | 510.0 |
| @trivikr-test | 91.0 | 0% | 66% | 394.0 |
| @lbnqduy180500 | 88.0 | 1% | 100% | 300.0 |
| @stdlib | 42.0 | 0% | 0% | 1,220.0 |
| @ffras4vnpm | 30.0 | 0% | 100% | 1,737.0 |
| @saoviettest | 29.0 | 0% | 100% | 166.0 |
| @wemnyelezxnpm | 27.0 | 0% | 100% | 1,736.0 |
| @crabas0npm | 27.0 | 0% | 100% | 1,066.0 |
| @a-2-c-2-anpm | 25.0 | 0% | 100% | 151.0 |
| @hoangcung1804npm | 25.0 | 0% | 100% | 150.0 |
| @bobyzgirlllnpm | 25.0 | 0% | 100% | 152.0 |
| @omegion1npm | 23.0 | 0% | 100% | 147.0 |
| @ryniaubenpm | 22.0 | 0% | 100% | 1,586.0 |
| @saovietcompany | 17.0 | 0% | 100% | 168.0 |
| @ryniaubenpm2 | 15.0 | 0% | 100% | 114.0 |
| @aws-sdk | 14.0 | 0% | 0% | 368.0 |
| @girs | 11.0 | 0% | 0% | 436.0 |
| @saovietgmetrix | 8.0 | 0% | 100% | 135.0 |
| @hanzo | 5.0 | 0% | 0% | 345.0 |
| @v-act | 5.0 | 0% | 0% | 238.0 |
| @opentinyvue | 4.0 | 0% | 0% | 242.0 |
| @agnocon | 4.0 | 0% | 100% | 763.0 |
| @renyii | 4.0 | 0% | 25% | 232.0 |
| @autohive | 3.0 | 0% | 100% | 257.0 |
| @digitranslab | 3.0 | 0% | 100% | 257.0 |
