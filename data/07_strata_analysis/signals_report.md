# Network signals report

Generated 2026-10-22 02:21 over 4,395,451 nodes and 16,332,311 edges.

## Verification

- Records repeated in pass 2, read once: 253.
- Fan-in recomputed from the edges differs from pass 03 in 1,000 packages.
- Pass 03 fan-out equals declared dependencies in 99.99% of packages, and dependencies that exist in 98.47%.

## Rules

| Rule | Packages |
|---|---|
| spam_declarer | 15,540 |
| spam_propagated | 688 |
| types_only | 11,401 |
| platform_binary (all) | 55,867 |
| platform_binary (Rust format only) | 3,305 |
| security_placeholder | 155,255 |
| coordinated_burst (core or victim) | 6,796 |
| coordinated_core (excluded) | 6,695 |
| burst_victim (kept, fan-in cleaned) | 101 |
| colluded_dependent | 206,309 |
| excluded_any | 440,870 |

## Sampling frame (strata by stratum_clean_out_of_scope)

Each excluded package is counted once, under its first reason in this order: security_placeholder, platform_binary, types_only, spam_declarer, spam_propagated, coordinated_core, colluded_dependent. Eligible: not excluded and at least 365 days old at the snapshot.

| stratum | packages | security_placeholder | platform_binary | types_only | spam_declarer | spam_propagated | coordinated_core | colluded_dependent | excluded | pct_excluded | under_one_year | eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0a isolated | 1582291 | 154475 | 53712 | 2298 | 0 | 94 | 368 | 0 | 210947 | 13.3 | 300134 | 1071210 |
| 0b consumer | 2381259 | 113 | 469 | 4245 | 15513 | 407 | 1565 | 196727 | 219039 | 9.2 | 445862 | 1716358 |
| 1-9 | 381588 | 550 | 1534 | 3488 | 23 | 8 | 1331 | 0 | 6934 | 1.8 | 33226 | 341428 |
| 10-99 | 40855 | 69 | 10 | 1113 | 3 | 2 | 2271 | 0 | 3468 | 8.5 | 970 | 36417 |
| 100-999 | 7797 | 46 | 0 | 232 | 1 | 0 | 159 | 0 | 438 | 5.6 | 56 | 7303 |
| >=1000 | 1661 | 2 | 0 | 25 | 0 | 0 | 17 | 0 | 44 | 2.6 | 6 | 1611 |

## Eligible packages under each fan-in

| Stratum | raw | clean | clean_out_of_scope |
|---|---|---|---|
| 0a isolated | 1,030,381 | 1,030,443 | 1,071,210 |
| 0b consumer | 1,571,539 | 1,572,119 | 1,716,358 |
| 1-9 | 513,543 | 513,408 | 341,428 |
| 10-99 | 48,865 | 48,448 | 36,417 |
| 100-999 | 8,258 | 8,182 | 7,303 |
| >=1000 | 1,741 | 1,727 | 1,611 |

## Largest burst victims (kept in the frame)

Victims by creation year: 2013: 3, 2014: 2, 2015: 5, 2016: 5, 2017: 8, 2018: 9, 2019: 2, 2020: 4, 2021: 20, 2022: 29, 2023: 14

Fan-in for strata: without spam sources, same-scope dependents or the burst.

| Package | Created | Fan-in raw | Burst dependents | From spam sources | Fan-in for strata | Burst arrived after (years) |
|---|---|---|---|---|---|---|
| unique-names-generator | 2018 | 14,044 | 13,786 | 12,697 | 254 | 6.3 |
| pdfjs-dist-signature-bt | 2021 | 3,848 | 3,848 | 537 | 0 | 2.7 |
| @pipedream/platform | 2021 | 2,428 | 129 | 331 | 1 | 1.1 |
| insta-fetcher | 2021 | 2,326 | 2,313 | 2,312 | 13 | 3.1 |
| are-objects | 2017 | 1,928 | 1,925 | 1,303 | 1 | 6.9 |
| are-arrays | 2017 | 1,925 | 1,922 | 1,303 | 1 | 6.9 |
| @dext7r/cz-config | 2022 | 1,689 | 1,689 | 1,684 | 0 | 1.7 |
| zhouqjtest | 2018 | 1,498 | 1,498 | 1,497 | 0 | 5.7 |
| @h7ml/badwords | 2023 | 1,407 | 1,407 | 1,407 | 0 | 1.3 |
| @h7ml/deletenodemodules | 2023 | 1,172 | 1,172 | 1,172 | 0 | 1.2 |
| confidence | 2013 | 1,017 | 971 | 1 | 46 | 10.7 |
| @dext7r/commitlint-config | 2022 | 888 | 888 | 888 | 0 | 1.7 |
| vue-amis-editor | 2022 | 888 | 888 | 888 | 0 | 2.1 |
| @dext7r/prettier | 2022 | 888 | 888 | 888 | 0 | 1.7 |
| @dext7r/init | 2022 | 519 | 518 | 513 | 0 | 1.7 |
| h7ui | 2020 | 518 | 518 | 513 | 0 | 4.1 |
| telebot | 2015 | 461 | 443 | 7 | 16 | 8.9 |
| create-initer | 2023 | 422 | 422 | 416 | 0 | 1.1 |
| @femm/prettier | 2023 | 421 | 421 | 416 | 0 | 1.3 |
| create-femm | 2023 | 421 | 421 | 416 | 0 | 1.1 |

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
| spam_declarer | share>0.3, deps>=5 | 20043 | 133 | 10083 | 9960 | none |
| spam_declarer | share>0.3, deps>=10 | 16913 | 110 | 8518 | 8395 | none |
| spam_declarer | share>0.3, deps>=15 | 16134 | 107 | 8116 | 8018 | none |
| spam_declarer | share>0.5, deps>=5 | 16274 | 93 | 8189 | 8085 | none |
| spam_declarer | share>0.5, deps>=10 | 15540 | 76 | 7834 | 7706 | none |
| spam_declarer | share>0.5, deps>=15 | 15080 | 75 | 7613 | 7467 | none |
| spam_declarer | share>0.7, deps>=5 | 14536 | 79 | 7309 | 7227 | none |
| spam_declarer | share>0.7, deps>=10 | 14195 | 70 | 7144 | 7051 | none |
| spam_declarer | share>0.7, deps>=15 | 13869 | 70 | 6993 | 6876 | none |
| coordinated_burst | deps>=10, span<=60d, recent<=0.005 | 6796 | 2435 | 3350 | 3446 | none |
| coordinated_burst | deps>=10, span<=60d, recent<=0.02 | 6797 | 2436 | 3350 | 3447 | none |
| coordinated_burst | deps>=10, span<=120d, recent<=0.005 | 8588 | 3115 | 4232 | 4356 | none |
| coordinated_burst | deps>=10, span<=120d, recent<=0.02 | 8589 | 3116 | 4232 | 4357 | none |
| coordinated_burst | deps>=10, span<=180d, recent<=0.005 | 8903 | 3139 | 4389 | 4514 | none |
| coordinated_burst | deps>=10, span<=180d, recent<=0.02 | 8908 | 3144 | 4393 | 4515 | none |
| coordinated_burst | deps>=20, span<=60d, recent<=0.005 | 5295 | 2435 | 2590 | 2705 | none |
| coordinated_burst | deps>=20, span<=60d, recent<=0.02 | 5296 | 2436 | 2590 | 2706 | none |
| coordinated_burst | deps>=20, span<=120d, recent<=0.005 | 6796 | 3115 | 3317 | 3479 | none |
| coordinated_burst | deps>=20, span<=120d, recent<=0.02 | 6797 | 3116 | 3317 | 3480 | none |
| coordinated_burst | deps>=20, span<=180d, recent<=0.005 | 6959 | 3139 | 3400 | 3559 | none |
| coordinated_burst | deps>=20, span<=180d, recent<=0.02 | 6964 | 3144 | 3404 | 3560 | none |
| coordinated_burst | deps>=50, span<=60d, recent<=0.005 | 3669 | 2411 | 1789 | 1880 | none |
| coordinated_burst | deps>=50, span<=60d, recent<=0.02 | 3670 | 2412 | 1789 | 1881 | none |
| coordinated_burst | deps>=50, span<=120d, recent<=0.005 | 4659 | 3091 | 2264 | 2395 | none |
| coordinated_burst | deps>=50, span<=120d, recent<=0.02 | 4660 | 3092 | 2264 | 2396 | none |
| coordinated_burst | deps>=50, span<=180d, recent<=0.005 | 4719 | 3115 | 2294 | 2425 | none |
| coordinated_burst | deps>=50, span<=180d, recent<=0.02 | 4724 | 3120 | 2298 | 2426 | none |
| coordinated_core | burst, not a victim (lag<180d) | 6662 | 3038 | 3244 | 3418 | none |
| coordinated_core | burst, not a victim (lag<365d) | 6695 | 3054 | 3260 | 3435 | none |
| coordinated_core | burst, not a victim (lag<730d) | 6731 | 3080 | 3281 | 3450 | none |
| colluded_dependent | share>=0.3 | 211054 | 0 | 105821 | 105233 | none |
| colluded_dependent | share>=0.5 | 206309 | 0 | 103462 | 102847 | none |
| colluded_dependent | share>=0.7 | 189912 | 0 | 95212 | 94700 | none |

## @rustbin coverage

2,986 packages, 147 not flagged as platform binaries.

## Triage: 801 packages in strata 100+ with no out-of-scope dependents

| Scope | Packages | Share flagged by any rule | Share with one version | Max fan-in |
|---|---|---|---|---|
| @saovietproject | 155 | 0% | 100% | 510 |
| @trivikr-test | 91 | 0% | 66% | 394 |
| @lbnqduy180500 | 88 | 1% | 100% | 300 |
| @stdlib | 42 | 0% | 0% | 1,220 |
| @ffras4vnpm | 30 | 0% | 100% | 1,737 |
| @saoviettest | 29 | 0% | 100% | 166 |
| @wemnyelezxnpm | 27 | 0% | 100% | 1,736 |
| @crabas0npm | 27 | 0% | 100% | 1,066 |
| @a-2-c-2-anpm | 25 | 0% | 100% | 151 |
| @hoangcung1804npm | 25 | 0% | 100% | 150 |
| @bobyzgirlllnpm | 25 | 0% | 100% | 152 |
| @omegion1npm | 23 | 0% | 100% | 147 |
| @ryniaubenpm | 22 | 0% | 100% | 1,586 |
| @saovietcompany | 17 | 0% | 100% | 168 |
| @ryniaubenpm2 | 15 | 0% | 100% | 114 |
| @aws-sdk | 14 | 0% | 0% | 368 |
| @girs | 11 | 0% | 0% | 436 |
| @saovietgmetrix | 8 | 0% | 100% | 135 |
| @hanzo | 5 | 0% | 0% | 345 |
| @v-act | 5 | 0% | 0% | 238 |
| @opentinyvue | 4 | 0% | 0% | 242 |
| @agnocon | 4 | 0% | 100% | 763 |
| @renyii | 4 | 0% | 25% | 232 |
| @autohive | 3 | 0% | 100% | 257 |
| @digitranslab | 3 | 0% | 100% | 257 |

## Figures

- `data/07_strata_analysis/figures/fig1_exclusions_by_stratum.png`
- `data/07_strata_analysis/figures/fig2_coordinated_baseline.png`
- `data/07_strata_analysis/figures/fig3_missing_share.png`
- `data/07_strata_analysis/figures/fig4_new_rules_by_year.png`
- `data/07_strata_analysis/figures/fig5_eligible_by_fan_in.png`
