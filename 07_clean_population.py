import gc
import hashlib
import json
import os
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

SNAPSHOT_DATE = date(2026, 9, 18)
DGB_MIN_SIZE = 500
DGB_MAX_WINDOW_DAYS = 30
DGB_MIN_PCT_ONE_VERSION = 100
PLATFORM_BINARY_RE = (
    r"(linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)"
)
SECURITY_PREFIX = "0.0.1-security"

def dep_list_hash(deps):
    key = ",".join(sorted(deps))
    return hashlib.md5(key.encode()).hexdigest()[:16]

# ── Criterion functions ──────────────────────────────────────────────

def flag_pre2010(created_date):
    return created_date < date(2010, 1, 1)

def flag_no_date(created_date, has_profile):
    return has_profile & created_date.isna()

def flag_post_snapshot(created_date):
    return created_date > SNAPSHOT_DATE

def flag_types_only(names):
    return names.str.startswith("@types/")

def flag_platform_binary(names):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*groups.*",
            category=UserWarning,
        )
        return names.str.contains(PLATFORM_BINARY_RE, regex=True, na=False)

def flag_security_placeholder(latest):
    return latest.str.startswith(SECURITY_PREFIX, na=False)

def flag_dgb_500(df):
    # Copied from analysis/explore_exclusion_candidates.py lines 1060-1083.
    # Modified (E): group stats computed only from rows with has_profile=True,
    # but the final isin marks all members including those without profile.
    has_hash = df["dep_hash"] != ""
    hh = df.loc[has_hash & df["has_profile"],
                ["name", "dep_hash", "created_date", "n_versions"]].copy()
    hh["_cd_ts"] = pd.to_datetime(hh["created_date"])
    gs = hh.groupby("dep_hash").agg(
        _sz=("name", "size"),
        _d0=("_cd_ts", "min"),
        _d1=("_cd_ts", "max"),
        _pv=("n_versions", lambda x: 100 * (x == 1).sum() / len(x)),
    ).reset_index()
    gs["_wd"] = (gs["_d1"] - gs["_d0"]).dt.days
    burst_hashes = gs.loc[
        (gs["_sz"] >= DGB_MIN_SIZE)
        & gs["_wd"].notna()
        & (gs["_wd"] <= DGB_MAX_WINDOW_DAYS)
        & (gs["_pv"] >= DGB_MIN_PCT_ONE_VERSION),
        "dep_hash",
    ]
    burst_set = set(burst_hashes)
    return df["dep_hash"].isin(burst_set)

# ── Path constants ───────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
DIR_PASADA2 = BASE / "data" / "pasada2"
GRAPH_CSV = BASE / "data" / "03_dependency_graph" / "graph_metrics.csv"
DIR_PROFILE_1 = BASE / "data" / "04_profile" / "part1"
DIR_PROFILE_2 = BASE / "data" / "04_profile" / "part2"
DIR_OUT = BASE / "data" / "clean_packages"

# ── Data loaders ─────────────────────────────────────────────────────

def load_universe():
    # Returns (df, n_errors, n_univ_dupes, univ_dup_names).
    p2_dir = str(DIR_PASADA2)
    p2_files = sorted(f for f in os.listdir(p2_dir) if f.endswith(".jsonl"))
    col_name = []
    col_sinver = []
    col_latest = []
    col_hash = []
    n_errors = 0
    for fi, fname in enumerate(p2_files):
        with open(os.path.join(p2_dir, fname), encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                if rec.get("error"):
                    n_errors += 1
                    continue
                nm = rec["name"].strip().lower()
                col_name.append(nm)
                col_sinver.append(1 if rec.get("sin_version") else 0)
                col_latest.append(rec.get("latest", ""))
                deps_raw = rec.get("deps", [])
                if deps_raw:
                    col_hash.append(dep_list_hash(
                        sorted(d.strip().lower() for d in deps_raw)))
                else:
                    col_hash.append("")
        if (fi + 1) % 20 == 0 or fi + 1 == len(p2_files):
            print(f"  pasada2: {fi + 1}/{len(p2_files)} shards, "
                  f"{len(col_name):,} live, {n_errors:,} errors")
    df = pd.DataFrame({
        "name": col_name,
        "sin_version": pd.array(col_sinver, dtype="int8"),
        "latest_p2": col_latest,
        "dep_hash": col_hash,
    })
    del col_name, col_sinver, col_latest, col_hash
    dup_mask = df.duplicated(subset="name", keep=False)
    univ_dup_names = set(df.loc[dup_mask, "name"])
    n_before_dedup = len(df)
    df = df.drop_duplicates(subset="name", keep="first")
    n_univ_dupes = n_before_dedup - len(df)
    return df, n_errors, n_univ_dupes, univ_dup_names

def load_graph():
    gm = pd.read_csv(
        str(GRAPH_CSV),
        usecols=["paquete", "fan_in", "fan_out"],
        dtype={"paquete": str, "fan_in": "int32", "fan_out": "int32"},
        keep_default_na=False,
        na_values=[],
    )
    gm.rename(columns={"paquete": "name"}, inplace=True)
    gm["name"] = gm["name"].str.strip().str.lower()
    return gm

def load_profile():
    # Returns (prof, n_dupes, n_empty_created, n_prof_records, prof_dup_names).
    prof_dirs = [str(DIR_PROFILE_1), str(DIR_PROFILE_2)]
    col_name = []
    col_latest = []
    col_created = []
    col_nver = []
    col_nmaint = []
    col_nkw = []
    col_npeer = []
    col_nopt = []
    col_github = []
    col_fc = []
    col_unpacked = []
    col_depr = []
    total_shards = 0
    for pd_dir in prof_dirs:
        if not os.path.isdir(pd_dir):
            continue
        files = sorted(f for f in os.listdir(pd_dir) if f.endswith(".jsonl"))
        for fi, fname in enumerate(files):
            with open(os.path.join(pd_dir, fname), encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    col_name.append(rec["name"])
                    col_latest.append(rec.get("latest", ""))
                    col_created.append(rec.get("created", ""))
                    col_nver.append(int(rec.get("n_versions", 0)))
                    col_nmaint.append(int(rec.get("n_maintainers", 0)))
                    col_nkw.append(int(rec.get("n_keywords", 0)))
                    col_npeer.append(int(rec.get("n_peer", 0)))
                    col_nopt.append(int(rec.get("n_opt", 0)))
                    col_github.append(
                        rec.get("has_github", "False") in (True, "True"))
                    col_fc.append(rec.get("file_count"))
                    col_unpacked.append(rec.get("unpacked"))
                    col_depr.append(
                        rec.get("deprecated", "False") in (True, "True"))
            total_shards += 1
            if total_shards % 20 == 0 or (fi + 1 == len(files)
                                           and pd_dir == prof_dirs[-1]):
                print(f"  profile: {total_shards} shards, "
                      f"{len(col_name):,} records")
    n_prof_records = len(col_name)
    prof = pd.DataFrame({
        "name": col_name,
        "latest_profile": col_latest,
        "created": col_created,
        "n_versions": pd.array(col_nver, dtype="int32"),
        "n_maintainers": pd.array(col_nmaint, dtype="int32"),
        "n_keywords": pd.array(col_nkw, dtype="int32"),
        "n_peer": pd.array(col_npeer, dtype="int32"),
        "n_opt": pd.array(col_nopt, dtype="int32"),
        "has_github": pd.array(col_github, dtype="bool"),
        "file_count": col_fc,
        "unpacked": col_unpacked,
        "deprecated": pd.array(col_depr, dtype="bool"),
    })
    del (col_name, col_latest, col_created, col_nver, col_nmaint, col_nkw,
         col_npeer, col_nopt, col_github, col_fc, col_unpacked, col_depr)
    prof["name"] = prof["name"].str.strip().str.lower()
    created_ts = pd.to_datetime(prof["created"].str[:19], errors="coerce")
    prof["created_date"] = created_ts.dt.date
    prof["created_year"] = created_ts.dt.year.astype("Int32")
    prof["file_count"] = pd.to_numeric(prof["file_count"], errors="coerce")
    prof["unpacked"] = pd.to_numeric(prof["unpacked"], errors="coerce")
    prof.drop(columns=["created"], inplace=True)
    n_empty_created = int(prof["created_date"].isna().sum())
    dup_mask = prof.duplicated(subset="name", keep=False)
    prof_dup_names = set(prof.loc[dup_mask, "name"])
    n_before = len(prof)
    prof = prof.drop_duplicates(subset="name", keep="first")
    n_dupes = n_before - len(prof)
    return prof, n_dupes, n_empty_created, n_prof_records, prof_dup_names

# ── Expected counts ──────────────────────────────────────────────────
EXPECTED = {
    "no_graph":             0,
    "no_profile":           6_215,
    "name_collision":       787,
    "pre2010":              1,
    "no_date":              3,
    "post_snapshot":        941,
    "no_version":           1_280,
    "types_only":           11_401,
    "platform_binary":      52_562,
    "security_placeholder": 155_255,
    "dgb_500":              59_363,
}
CRITERIA = list(EXPECTED.keys())
UNIVERSE_EXPECTED = 4_395_451

# ── Criterion descriptions (for final report) ────────────────────────
CRITERION_DESC = {
    "no_graph":             "Package in universe but missing from dependency graph",
    "no_profile":           "Package in universe but missing from profile extraction",
    "name_collision":       "Normalized name appears more than once in pasada2 or profile shards",
    "pre2010":              "Created before 2010-01-01",
    "no_date":              "Has profile but no parseable creation date",
    "post_snapshot":        f"Created after {SNAPSHOT_DATE} (snapshot date)",
    "no_version":           "No dist-tags.latest or version missing in registry",
    "types_only":           "Name starts with @types/",
    "platform_binary":      "Name contains OS-architecture pattern (e.g. linux-x64, darwin-arm64)",
    "security_placeholder": f"Latest version starts with \"{SECURITY_PREFIX}\"",
    "dgb_500":              (f"Dep-group burst: {DGB_MIN_SIZE}+ packages with identical dependency "
                             f"list, created within {DGB_MAX_WINDOW_DAYS} days, all single-version"),
}

# ── Main ─────────────────────────────────────────────────────────────

def main():
    import time as _time
    started = _time.strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 60)
    print("07_clean_population.py")
    print("=" * 60)

    # ── 1. Load data ─────────────────────────────────────────────
    print("\n[1] Loading universe (pasada2 shards) ...")
    universe, n_errors, n_univ_dupes, univ_dup_names = load_universe()

    print("\n[2] Loading graph_metrics.csv ...")
    graph = load_graph()
    print(f"  Graph nodes: {len(graph):,}")

    print("\n[3] Loading profile shards ...")
    profile, n_dupes, n_empty_created, n_prof_records, prof_dup_names = load_profile()
    print(f"  Profile: {len(profile):,} unique ({n_empty_created:,} with empty created)")

    collision_names = univ_dup_names | prof_dup_names
    del univ_dup_names, prof_dup_names

    # ── 2. Verify universe size ──────────────────────────────────
    n_univ = len(universe)
    n_graph = len(graph)
    if n_univ != n_graph:
        print(f"  WARNING: universe ({n_univ:,}) != graph ({n_graph:,})")
    if n_univ != UNIVERSE_EXPECTED:
        print(f"  WARNING: universe ({n_univ:,}) != expected ({UNIVERSE_EXPECTED:,})")

    # ── 3. Left join: universe + graph + profile ─────────────────
    n_rows_read = n_univ + n_univ_dupes
    df = universe.merge(graph, on="name", how="left")
    del universe; gc.collect()

    df["no_graph"] = df["fan_in"].isna() | df["fan_out"].isna()
    n_no_graph = int(df["no_graph"].sum())
    if n_no_graph > 0:
        sample = df.loc[df["no_graph"], "name"].head(20).tolist()
        print(f"  WARNING: no_graph={n_no_graph:,}, first 20: {sample}")

    df["has_profile"] = df["name"].isin(profile["name"])
    n_with_profile = int(df["has_profile"].sum())
    n_without_profile = n_univ - n_with_profile
    df = df.merge(profile, on="name", how="left")
    del graph, profile; gc.collect()

    df["latest_profile"] = df["latest_profile"].fillna("")
    df["n_versions"] = df["n_versions"].fillna(0).astype("int32")

    # ── 4. Apply exclusion criteria ──────────────────────────────
    df["no_profile"] = ~df["has_profile"]
    df["name_collision"] = df["name"].isin(collision_names)
    del collision_names
    df["pre2010"] = flag_pre2010(df["created_date"]).fillna(False)
    df["no_date"] = flag_no_date(df["created_date"], df["has_profile"])
    df["post_snapshot"] = flag_post_snapshot(df["created_date"]).fillna(False)
    on_snapshot = int((df["created_date"] == SNAPSHOT_DATE).sum())
    print(f"  Created on {SNAPSHOT_DATE}: {on_snapshot:,} (kept)")
    df["no_version"] = df["sin_version"] == 1
    df["types_only"] = flag_types_only(df["name"])
    df["platform_binary"] = flag_platform_binary(df["name"])
    df["security_placeholder"] = flag_security_placeholder(df["latest_profile"])
    sec_p2 = df["latest_p2"].str.startswith(SECURITY_PREFIX, na=False)
    has_prof = df["has_profile"]
    sec_diff = int(((df["security_placeholder"] != sec_p2) & has_prof).sum())
    df["dgb_500"] = flag_dgb_500(
        df[["name", "dep_hash", "created_date", "n_versions", "has_profile"]]
    )
    df["excluded_any"] = False
    for c in CRITERIA:
        df["excluded_any"] = df["excluded_any"] | df[c]

    total_excl = int(df["excluded_any"].sum())
    total_elig = n_univ - total_excl

    # ── 5. Compute only-this-criterion ───────────────────────────
    only_this = {}
    for c in CRITERIA:
        others = False
        for c2 in CRITERIA:
            if c2 != c:
                others = others | df[c2]
        only_this[c] = int((df[c] & ~others).sum())

    # ── 6. Write outputs ─────────────────────────────────────────
    os.makedirs(str(DIR_OUT), exist_ok=True)

    # 6a. population_flags.parquet
    flags_cols = (["name", "fan_in", "fan_out", "created_year"]
                  + CRITERIA + ["excluded_any"])
    df[flags_cols].to_parquet(
        str(DIR_OUT / "population_flags.parquet"), index=False)

    # 6b. population_clean.parquet
    clean = df[~df["excluded_any"]].copy()
    drop_cols = set(CRITERIA + ["excluded_any", "has_profile", "sin_version",
                                "dep_hash", "latest_p2", "latest_profile"])
    keep_cols = [c for c in clean.columns if c not in drop_cols]
    clean[keep_cols].to_parquet(
        str(DIR_OUT / "population_clean.parquet"), index=False)
    del clean; gc.collect()

    # 6c. exclusion_summary.csv
    summary_rows = []
    for c in CRITERIA:
        exp = EXPECTED[c]
        obt = int(df[c].sum())
        summary_rows.append({
            "criterion": c,
            "expected": exp,
            "obtained": obt,
            "difference": obt - exp,
            "only_this_criterion": only_this[c],
            "pct_universe": round(100 * obt / n_univ, 4),
        })
    summary_rows.append({
        "criterion": "TOTAL_EXCLUDED",
        "expected": "",
        "obtained": total_excl,
        "difference": "",
        "only_this_criterion": "",
        "pct_universe": round(100 * total_excl / n_univ, 4),
    })
    summary_rows.append({
        "criterion": "TOTAL_ELIGIBLE",
        "expected": "",
        "obtained": total_elig,
        "difference": "",
        "only_this_criterion": "",
        "pct_universe": round(100 * total_elig / n_univ, 4),
    })
    summary_rows.append({
        "criterion": "UNIVERSE",
        "expected": UNIVERSE_EXPECTED,
        "obtained": n_univ,
        "difference": n_univ - UNIVERSE_EXPECTED,
        "only_this_criterion": "",
        "pct_universe": 100.0,
    })
    pd.DataFrame(summary_rows).to_csv(
        str(DIR_OUT / "exclusion_summary.csv"), index=False)

    # 6d. exclusion_overlaps.csv
    overlap_rows = []
    for i, c1 in enumerate(CRITERIA):
        for c2 in CRITERIA[i + 1:]:
            both = int((df[c1] & df[c2]).sum())
            overlap_rows.append({
                "criterion_a": c1,
                "criterion_b": c2,
                "overlap": both,
            })
    pd.DataFrame(overlap_rows).to_csv(
        str(DIR_OUT / "exclusion_overlaps.csv"), index=False)

    # 6e. exclusion_by_year.csv
    year_rows = []
    for yr in sorted(df["created_year"].dropna().unique()):
        mask_yr = df["created_year"] == yr
        row = {"created_year": int(yr), "packages": int(mask_yr.sum())}
        for c in CRITERIA:
            row[c] = int((mask_yr & df[c]).sum())
        row["excluded_any"] = int((mask_yr & df["excluded_any"]).sum())
        year_rows.append(row)
    mask_noyr = df["created_year"].isna()
    if mask_noyr.any():
        row = {"created_year": "NA", "packages": int(mask_noyr.sum())}
        for c in CRITERIA:
            row[c] = int((mask_noyr & df[c]).sum())
        row["excluded_any"] = int((mask_noyr & df["excluded_any"]).sum())
        year_rows.append(row)
    pd.DataFrame(year_rows).to_csv(
        str(DIR_OUT / "exclusion_by_year.csv"), index=False)

    # 6f. run_metadata.json
    metadata = {
        "executed_at": started,
        "snapshot_date": str(SNAPSHOT_DATE),
        "dgb_params": {
            "min_size": DGB_MIN_SIZE,
            "max_window_days": DGB_MAX_WINDOW_DAYS,
            "min_pct_one_version": DGB_MIN_PCT_ONE_VERSION,
        },
        "platform_binary_re": PLATFORM_BINARY_RE,
        "security_prefix": SECURITY_PREFIX,
        "paths": {
            "pasada2": str(DIR_PASADA2),
            "graph_csv": str(GRAPH_CSV),
            "profile_part1": str(DIR_PROFILE_1),
            "profile_part2": str(DIR_PROFILE_2),
        },
        "profile_duplicates": n_dupes,
        "universe_duplicates": n_univ_dupes,
        "pasada2_errors": n_errors,
        "security_p2_vs_profile_diff": sec_diff,
        "universe_size": n_univ,
        "total_excluded": total_excl,
        "total_eligible": total_elig,
        "versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "pyarrow": None,
        },
    }
    try:
        import pyarrow
        metadata["versions"]["pyarrow"] = pyarrow.__version__
    except ImportError:
        pass
    with open(str(DIR_OUT / "run_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # ── 7. Print final report ────────────────────────────────────
    print("\n" + "=" * 70)
    print("[A] EXCLUSION RULES")
    print("=" * 70)
    for c in CRITERIA:
        print(f"  {c:<25s}  {CRITERION_DESC[c]}")

    print("\n" + "=" * 70)
    print("[B] POPULATION BEFORE AND AFTER")
    print("=" * 70)
    print(f"  Rows read from pasada2:          {n_rows_read:>12,}")
    print(f"  Case-duplicate rows removed:     {n_univ_dupes:>12,}")
    print(f"  Universe (unique names):         {n_univ:>12,}")
    print(f"  Graph nodes:                     {n_graph:>12,}")
    print(f"  Packages with profile:           {n_with_profile:>12,}")
    print(f"  Packages without profile:        {n_without_profile:>12,}")
    print(f"  Profile records read:            {n_prof_records:>12,}")
    print(f"  Profile duplicates removed:      {n_dupes:>12,}")
    print(f"  Total excluded:                  {total_excl:>12,}")
    print(f"  Total eligible:                  {total_elig:>12,}")
    print(f"  Percent excluded:                {100 * total_excl / n_univ:>11.2f}%")

    print("\n" + "=" * 70)
    print("[C] EXCLUSION BY CRITERION")
    print("=" * 70)
    hdr = (f"  {'criterion':<25s} {'excluded':>10s} {'%univ':>7s} "
           f"{'only_this':>10s} {'expected':>10s} {'diff':>10s}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for c in CRITERIA:
        exp = EXPECTED[c]
        obt = int(df[c].sum())
        diff = obt - exp
        pct = 100 * obt / n_univ
        pct_diff = abs(diff) / max(exp, 1) * 100
        mark = " !!!" if pct_diff > 1.0 else ""
        print(f"  {c:<25s} {obt:>10,} {pct:>6.2f}% "
              f"{only_this[c]:>10,} {exp:>10,} {diff:>+10,}{mark}")
    print("  " + "-" * (len(hdr) - 2))
    print(f"  {'TOTAL_EXCLUDED':<25s} {total_excl:>10,} "
          f"{100 * total_excl / n_univ:>6.2f}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
