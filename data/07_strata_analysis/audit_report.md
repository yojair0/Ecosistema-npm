# Registry audit

Seeded random sample (seed 42) of 10,000 packages from the reference list of 4,405,737. Usable records: 9,967.

| Status | Packages |
|---|---|
| ok | 9,967 |
| gone | 24 |
| no_versions | 9 |

## A. Does `modified` reflect publishing?

Gap: days between the last modification and the most recent version. Criterion fixed in advance: if most packages modified in April-June 2022 show a gap above 30 days, `modified` there records registry-side changes rather than releases.

| Group | n | gap > 30 days | median gap (days) |
|---|---|---|---|
| modified April-June 2022 | 3,619 | 95.2% | 973 |
| modified at any other time | 6,348 | 8.5% | 0 |

Criterion **met**: in that window `modified` does not reflect releases; the date of the last version is the alternative.

## B. Publisher concentration

Publisher: account that published the latest version. Estimated packages: share of the sample times the reference list, with a 95% interval. Criterion fixed in advance: any account above 0.5% of the registry is investigated.

| Publisher | in sample | share | estimated packages (95%) | flagged spam |
|---|---|---|---|---|
| GitHub Actions | 385 | 3.86% | 153,514 – 186,851 | 0% |
| npm | 342 | 3.43% | 135,430 – 166,920 | 0% |
| terryfei | 65 | 0.65% | 21,770 – 35,694 | 0% |
| mayangsario | 26 | 0.26% | 7,081 – 15,905 | 0% |
| rajhsinggg | 21 | 0.21% | 5,317 – 13,249 | 0% |
| bedlaj | 18 | 0.18% | 4,284 – 11,629 | 0% |
| ayowel | 18 | 0.18% | 4,284 – 11,629 | 0% |
| types | 17 | 0.17% | 3,945 – 11,084 | 0% |
| ryliefrey | 16 | 0.16% | 3,610 – 10,535 | 0% |
| stdlib-bot | 16 | 0.16% | 3,610 – 10,535 | 0% |
| miptaa02 | 15 | 0.15% | 3,278 – 9,983 | 0% |
| burakcevik101 | 15 | 0.15% | 3,278 – 9,983 | 0% |
| semi-bot | 13 | 0.13% | 2,625 – 8,868 | 0% |
| mipppp | 13 | 0.13% | 2,625 – 8,868 | 0% |
| mipta19 | 12 | 0.12% | 2,305 – 8,304 | 0% |
| mindyartera | 12 | 0.12% | 2,305 – 8,304 | 0% |
| wix-ci-publisher | 12 | 0.12% | 2,305 – 8,304 | 0% |
| wanzaty | 11 | 0.11% | 1,990 – 7,734 | 0% |
| chatflowdev | 11 | 0.11% | 1,990 – 7,734 | 0% |
| arcodesign-bot | 10 | 0.10% | 1,682 – 7,159 | 0% |

Top 20 accounts publish 10.5% of the sample. Accounts above 0.5%: **3**.

## C. Creation year

| Year | n | share of top 5 accounts | top 3 accounts | flagged spam |
|---|---|---|---|---|
| 2011 | 9 | 55.6% | jnordberg (1), alexyoung (1), felixge (1) | 0.0% |
| 2012 | 24 | 20.8% | lemonlwz (1), GitHub Actions (1), taterbase (1) | 0.0% |
| 2013 | 71 | 8.5% | jdalton (2), doowb (1), herco (1) | 0.0% |
| 2014 | 151 | 7.3% | manvalls (3), kgryte (3), cjus (2) | 0.0% |
| 2015 | 223 | 4.5% | jonschlinkert (2), ctxhou (2), kikobeats (2) | 0.0% |
| 2016 | 367 | 4.9% | ryancavanaugh (5), retyped (4), types (3) | 0.0% |
| 2017 | 471 | 2.5% | ehsalazar (3), types (3), felixrieseberg (2) | 0.0% |
| 2018 | 558 | 3.0% | GitHub Actions (5), types (5), sobear (3) | 0.0% |
| 2019 | 605 | 4.0% | GitHub Actions (7), no-repeat (6), bedlaj (5) | 0.0% |
| 2020 | 671 | 3.4% | GitHub Actions (11), datafire (3), afeiship (3) | 0.0% |
| 2021 | 843 | 6.6% | npm (25), wix-ci-publisher (10), stdlib-bot (8) | 0.0% |
| 2022 | 856 | 12.5% | terryfei (65), GitHub Actions (18), npm (13) | 0.0% |
| 2023 | 871 | 7.5% | npm (25), GitHub Actions (18), wizardforcel (10) | 0.0% |
| 2024 | 1,574 | 9.5% | npm (69), mayangsario (26), rajhsinggg (21) | 2.3% |
| 2025 | 1,057 | 24.8% | npm (201), GitHub Actions (45), shirshak (6) | 0.0% |
| 2026 | 1,616 | 18.1% | GitHub Actions (254), bedlaj (13), npm (9) | 0.0% |
