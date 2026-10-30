# Post-check, local phase

Generated 2026-10-29 22:20.

## L1. Name collisions

- Names that collide in lower case: 787; flagged by the rule: 787.
- Of them, groups where two or more spellings have a version (two real packages): 785.
- Names that appear twice with the same spelling: 0.
- Every spelling is listed in `l1_collisions.csv`.

## L2. Versions that mention "security"

Matched by the pattern: 155,722. Not matched: 1,200.

| Version | Packages | Matched |
|---|---|---|
| 0.0.1-security.1 | 74,237 | yes |
| 0.0.1-security | 63,193 | yes |
| 0.0.1-security.0 | 14,538 | yes |
| 0.0.1-security.4 | 884 | yes |
| 0.0.1-security.2 | 879 | yes |
| 1.0.2-security | 725 | **no** |
| 0.0.1-security.7 | 375 | yes |
| 0.0.1-security.3 | 304 | yes |
| 0.0.1-security.5 | 236 | yes |
| 0.0.1-security.10 | 184 | yes |
| 0.0.1-security.6 | 141 | yes |
| 0.0.1-security.9 | 134 | yes |
| 1.0.0-security | 124 | **no** |
| 0.0.1-security.19 | 101 | yes |
| 0.0.1-security.15 | 69 | yes |
| 0.0.2-security | 63 | yes |
| 0.0.1-security.14 | 51 | yes |
| 0.0.1-security.8 | 49 | yes |
| 1.0.1-security.2 | 49 | **no** |
| 1.0.1-security.0 | 46 | **no** |
| 1.0.1-security.1 | 46 | **no** |
| 0.0.1-security.13 | 39 | yes |
| 0.0.1-security.12 | 37 | yes |
| 1.0.1-security | 37 | **no** |
| 0.0.1-security.17 | 36 | yes |
| 1.0.1-security.3 | 34 | **no** |
| 0.0.1-security.16 | 33 | yes |
| 1.0.1-security.4 | 30 | **no** |
| 0.0.1-security.18 | 25 | yes |
| 0.0.0-security | 24 | yes |
| 1.0.1-security.7 | 20 | **no** |
| 0.0.1-security.11 | 15 | yes |
| 1.0.1-security.5 | 15 | **no** |
| 0.0.1-security.20 | 14 | yes |
| 0.0.1-security.24 | 12 | yes |
| 1.0.1-security.6 | 11 | **no** |
| 1.0.1-security.9 | 10 | **no** |
| 1.0.2-security.0 | 9 | **no** |
| 0.0.1-security.21 | 8 | yes |
| 0.1.0-security.0 | 6 | **no** |

Packages in population A whose version mentions "security": 1,200.

| Package | Version | Fan-in |
|---|---|---|
| brasil | 1.0.0-security | 5 |
| @dwing/common | 10.0.1-security | 5 |
| crypit | 1.0.10-security | 3 |
| ui_checkboxhard | 1.0.0-security | 0 |
| votifier-test-tool | 1.0.0-security | 0 |
| vue-app-transition | 1.0.0-security | 0 |
| vuee | 1.0.0-security | 0 |
| vueh | 1.0.0-security | 0 |
| vuej | 1.0.0-security | 0 |
| vuek | 1.0.0-security | 0 |
| vuen | 1.0.0-security | 0 |
| vueu | 1.0.0-security | 0 |
| vuev | 1.0.0-security | 0 |
| vuew | 1.0.0-security | 0 |
| wangeditor2 | 3.1.0-security | 0 |
| watchmen-plugin-email | 1.0.0-security | 0 |
| watchmen-plugin-hipchat | 1.0.0-security | 0 |
| wc-angular-dashboard-framework | 1.0.0-security | 0 |
| @malware-test-amaze-prows-prank-zeals/test-mlw3-amaze-prows-prank-zeals | 1.0.2-security | 0 |
| @malware-test-amici-ochre-ronde-soles/test-mlw3-amici-ochre-ronde-soles | 1.0.2-security | 0 |
| @malware-test-amour-wicca-soggy-palsy/test-mlw3-amour-wicca-soggy-palsy | 1.0.1-security.3 | 0 |
| @malware-test-ample-hones-owari-waged/test-mlw3-ample-hones-owari-waged | 1.0.2-security | 0 |
| @malware-test-antre-pings-unaus-malva/test-mlw3-antre-pings-unaus-malva | 1.0.2-security | 0 |
| @malware-test-anvil-tzars-groma-bible/test-mlw3-anvil-tzars-groma-bible | 1.0.2-security | 0 |
| @malware-test-apace-dhows-blank-doucs/test-mlw3-apace-dhows-blank-doucs | 1.0.2-security | 0 |
| @malware-test-apace-squat-wongi-blads/test-mlw3-apace-squat-wongi-blads | 1.0.2-security | 0 |
| @malware-test-appuy-oleos-wizen-incur/test-mlw3-appuy-oleos-wizen-incur | 1.0.2-security | 0 |
| @malware-test-armil-teils-kakas-courb/test-mlw3-armil-teils-kakas-courb | 1.0.2-security | 0 |
| @malware-test-arris-tices-scans-yelps/test-mlw3-arris-tices-scans-yelps | 1.0.2-security | 0 |
| @malware-test-ataxy-nisse-locks-bells/test-mlw3-ataxy-nisse-locks-bells | 1.0.2-security.0 | 0 |

## L3. Platform binaries by family

Flagged: 56,007. Families: 7,098. Columns: packages, and how many match the system-processor pattern (the rest match a Rust target).

| Family | Packages | System-processor pattern |
|---|---|---|
| @haybarn | 3,756 | 3,756 |
| @rustbin | 2,979 | 0 |
| @napi-rs | 390 | 377 |
| node | 208 | 208 |
| @farmfe | 199 | 199 |
| opencode | 141 | 141 |
| farm | 136 | 136 |
| wickra | 130 | 130 |
| @loongdotjs | 113 | 110 |
| @node-rs | 109 | 103 |
| sqlite | 105 | 105 |
| @swc | 91 | 91 |
| oh | 87 | 87 |
| agent | 86 | 86 |
| @gjsify | 76 | 76 |
| @khaf | 74 | 74 |
| codex | 72 | 72 |
| @fateforge | 72 | 72 |
| @sylphx | 70 | 70 |
| @kreuzberg | 68 | 68 |
| @loong64 | 67 | 67 |
| @skastr0 | 66 | 66 |
| @depup | 66 | 65 |
| napi | 65 | 64 |
| rust | 65 | 64 |
| @hackolade | 64 | 64 |
| @ruvector | 64 | 64 |
| @shined | 64 | 63 |
| fast | 63 | 62 |
| @camera.ui | 62 | 62 |
| @microsoft | 62 | 62 |
| @svg-toolkit | 60 | 60 |
| @parcel | 59 | 59 |
| create | 56 | 56 |
| farmfe | 54 | 54 |
| @w5 | 52 | 52 |
| rusty | 49 | 48 |
| @sqliteai | 49 | 49 |
| @speedy-js | 49 | 49 |
| @brokkai | 49 | 49 |

Rust-pattern matches outside @rustbin: 466.

| Package |
|---|
| @3-/blake3-wasm32-wasi |
| @agent-transcripts/aarch64-apple-darwin |
| @agent-transcripts/aarch64-unknown-linux-gnu |
| @agent-transcripts/x86_64-apple-darwin |
| @agent-transcripts/x86_64-pc-windows-msvc |
| @agent-transcripts/x86_64-unknown-linux-gnu |
| @alex-wine/napi-test-wasm32-wasi |
| @alexstep/doc-extract-wasm32-wasi |
| @alidade/query-parser-wasm32-wasi |
| @anymon/aarch64-apple-darwin |
| @anymon/aarch64-pc-windows-msvc |
| @anymon/aarch64-unknown-linux-gnu |
| @anymon/x86_64-apple-darwin |
| @anymon/x86_64-pc-windows-msvc |
| @anymon/x86_64-unknown-linux-gnu |
| @aqarios/luna-model-wasm32-wasi |
| @arkts/project-detector-wasm32-wasi |
| @astrojs/compiler-binding-wasm32-wasi |
| @avsystem/openapi-ng-wasm32-wasi |
| @baicie/napi-wasm32-wasi |
| @bennyblader/ddk-ts-wasm32-wasi |
| @bika.ai/license-wasm32-wasi |
| @bin-release/deno-aarch64-apple-darwin |
| @bin-release/deno-x86_64-apple-darwin |
| @bin-release/deno-x86_64-pc-windows-msvc |
| @bin-release/deno-x86_64-unknown-linux-gnu |
| @binraries/deno-x86_64-apple-darwin |
| @blazen-dev/blazen-wasm32-wasi |
| @blazen-dev/blazen-wasm32-wasi-tiktoken |
| @bratel/rollup-linux-loongarch64-gnu |
| @bruits/satteri-wasm32-wasi |
| @build-qube/papyra-native-wasm32-wasi |
| @build-qube/takeoff-calculator-wasm32-wasi |
| @bun-gpu/dawn-aarch64-linux-gnu |
| @bun-gpu/dawn-aarch64-linux-musl |
| @bun-gpu/dawn-x86_64-linux-gnu |
| @bun-gpu/dawn-x86_64-linux-musl |
| @buntui/native-wasm32-wasi |
| @chainsafe/lodestar-z-aarch64-apple-darwin |
| @chainsafe/lodestar-z-aarch64-unknown-linux-gnu |

## L4. Failed queries in pass 2

Failed queries: 9,487; with at least one dependent: 21; dependents in total: 443.

| Package | Dependents |
|---|---|
| @rabiepenpm/libero-nisi-voluptatem | 145 |
| @f1stnpm2/officiis-cumque-dolor-ducimus | 114 |
| @npmtuanmap/ex-vel-expedita-impedit | 50 |
| @npmtuanmap/psychic-guide | 50 |
| @npmtuanmap/velit-esse-velit-magnam | 50 |
| @npmtea2024/at-sapiente-minima-nesciunt | 3 |
| @npmtea2024/deleniti-iure-ratione-natus | 3 |
| @npmtea2024/expedita-reiciendis-dolore-quidem | 3 |
| @npmtea2024/iste-ut-quibusdam-in | 3 |
| @npmtea2024/modi-dicta-asperiores-nam | 3 |
| @npmtea2024/nobis-recusandae-est-quo | 3 |
| @npmtea2024/recusandae-necessitatibus-nesciunt-cupiditate | 3 |
| @npmtea2024/velit-impedit-omnis-nam | 3 |
| @datagica/parse-dates | 3 |
| @dramaorg/fuga-vel-natus | 1 |
| @patrtorg/illum-sapiente-quos | 1 |
| @patrtorg/libero-doloribus-omnis | 1 |
| @patrtorg/libero-voluptas-sequi | 1 |
| @patrtorg/maiores-quidem-quo | 1 |
| @patrtorg/porro-labore-eos | 1 |
| @patrtorg/sapiente-exercitationem-sit | 1 |
| rulesthatvalidnpmpackagenameshouldconformtopackagenamelengthshouldbegreaterthanzeroallthecharactersinthepackagenamemustbelowercasenouppercaseormixedcasenamesareallowedpackagenamecanconsistofhyphenspackagenamemustn | 0 |
| rulesthatvalidnpmpackagenameshouldconformtopackagenamelengthshouldbegreaterthanzeroallthecharactersinthepackagenamemustbelowercasenouppercaseormixedcasenamesareallowedpackagenamecanconsistofhyphenspackagenamemustno | 0 |
| senovtlab6 | 0 |
| skeleton-react-single-page-app | 0 |
| thelongestpackagenamemadebykexohknownforitsinnovativesoftwaresolutionshasbecomeatopicofinterestamongdevelopersworldwidesoicantputmoreword | 0 |
| thelongestpackagenamemadebykexohknownforitsinnovativesoftwaresolutionshasbecomeatopicofinterestamongdevelopersworldwidesoicantputmoreword2 | 0 |
| thelongestpackagenamemadebykexohknownforitsinnovativesoftwaresolutionshasbecomeatopicofinterestamongdevelopersworldwidesoicantputmoreword222 | 0 |
| thelongestpackagenamemadebykexohknownforitsinnovativesoftwaresolutionshasbecomeatopicofinterestamongdevelopersworldwidesoicantputmoreword333 | 0 |
| toggleable-circle | 0 |

## L5. Packages the corrections keep

| Reason | Packages |
|---|---|
| Only because failed queries now count as existing | 15 |
| Only because fs and http no longer count as bad | 13,272 |
| Both | 0 |

Network phase lists: errors.txt, placeholders.txt, binaries.txt.

