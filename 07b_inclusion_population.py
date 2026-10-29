import collections
import hashlib
import json
import os
import warnings
from datetime import date
from pathlib import Path

import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────
SNAPSHOT_DATE = date(2026, 9, 18)
PLATFORM_BINARY_RE = (
    r"(linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)"
)
SECURITY_PREFIX = "0.0.1-security"
FAMILY_MIN_SIZE = 2
NODE_PLACEHOLDER_NAMES = {"fs", "http"}

# ── Helpers ───────────────────────────────────────────────────────────
def dep_list_hash(deps):
    key = ",".join(sorted(deps))
    return hashlib.md5(key.encode()).hexdigest()[:16]

def scope_of(name):
    return name.split("/")[0] if name.startswith("@") else ""

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

def flag_family(scope_size):
    return scope_size >= FAMILY_MIN_SIZE

# ── Path constants ───────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
DIR_PASADA2 = BASE / "data" / "pasada2"
GRAPH_CSV = BASE / "data" / "03_dependency_graph" / "graph_metrics.csv"
DIR_PROFILE_1 = BASE / "data" / "04_profile" / "part1"
DIR_PROFILE_2 = BASE / "data" / "04_profile" / "part2"

# ── Data loaders ─────────────────────────────────────────────────────
def load_universe():
    # Returns (df, collision_names, rows_read, n_dupes, n_errors).
    p2_dir = str(DIR_PASADA2)
    p2_files = sorted(f for f in os.listdir(p2_dir) if f.endswith(".jsonl"))
    col_name = []
    col_sinver = []
    col_latest = []
    col_tarball = []
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
                col_tarball.append(rec.get("tarball") or "")
                deps_raw = rec.get("deps", [])
                if deps_raw:
                    col_hash.append(dep_list_hash(
                        sorted(d.strip().lower() for d in deps_raw)))
                else:
                    col_hash.append("")
        if (fi + 1) % 20 == 0 or fi + 1 == len(p2_files):
            print(f"  pasada2: {fi + 1}/{len(p2_files)} shards, "
                  f"{len(col_name):,} live, {n_errors:,} errors")
    rows_read = len(col_name) + n_errors
    df = pd.DataFrame({
        "name": col_name,
        "sin_version": pd.array(col_sinver, dtype="int8"),
        "latest_p2": col_latest,
        "tarball": col_tarball,
        "dep_hash": col_hash,
    })
    del col_name, col_sinver, col_latest, col_tarball, col_hash
    dup_mask = df.duplicated(subset="name", keep=False)
    collision_names = set(df.loc[dup_mask, "name"])
    n_before = len(df)
    df = df.drop_duplicates(subset="name", keep="first")
    n_dupes = n_before - len(df)
    return df, collision_names, rows_read, n_dupes, n_errors

def load_graph():
    gm = pd.read_csv(
        str(GRAPH_CSV),
        usecols=["paquete", "fan_in", "fan_out", "fan_in_dev", "fan_out_dev"],
        dtype={"paquete": str, "fan_in": "int32", "fan_out": "int32",
               "fan_in_dev": "int32", "fan_out_dev": "int32"},
        keep_default_na=False,
        na_values=[],
    )
    gm.rename(columns={"paquete": "name"}, inplace=True)
    gm["name"] = gm["name"].str.strip().str.lower()
    return gm

def load_profile():
    # Returns (prof, prof_dup_names, n_dupes).
    prof_dirs = [str(DIR_PROFILE_1), str(DIR_PROFILE_2)]
    col_name = []
    col_latest = []
    col_created = []
    col_modified = []
    col_nver = []
    col_nmaint = []
    col_nkw = []
    col_keywords = []
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
                    col_modified.append(rec.get("modified", ""))
                    col_nver.append(int(rec.get("n_versions", 0)))
                    col_nmaint.append(int(rec.get("n_maintainers", 0)))
                    col_nkw.append(int(rec.get("n_keywords", 0)))
                    col_keywords.append(rec.get("keywords") or [])
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
    prof = pd.DataFrame({
        "name": col_name,
        "latest_profile": col_latest,
        "created": col_created,
        "modified": col_modified,
        "n_versions": pd.array(col_nver, dtype="int32"),
        "n_maintainers": pd.array(col_nmaint, dtype="int32"),
        "n_keywords": pd.array(col_nkw, dtype="int32"),
        "keywords": col_keywords,
        "n_peer": pd.array(col_npeer, dtype="int32"),
        "n_opt": pd.array(col_nopt, dtype="int32"),
        "has_github": pd.array(col_github, dtype="bool"),
        "file_count": col_fc,
        "unpacked": col_unpacked,
        "deprecated": pd.array(col_depr, dtype="bool"),
    })
    del (col_name, col_latest, col_created, col_modified, col_nver,
         col_nmaint, col_nkw, col_keywords, col_npeer, col_nopt,
         col_github, col_fc, col_unpacked, col_depr)
    prof["name"] = prof["name"].str.strip().str.lower()
    # created — exact conversion from 07
    created_ts = pd.to_datetime(prof["created"].str[:19], errors="coerce")
    prof["created_date"] = created_ts.dt.date
    prof["created_year"] = created_ts.dt.year.astype("Int32")
    prof.drop(columns=["created"], inplace=True)
    prof.drop(columns=["modified"], inplace=True)
    # file_count, unpacked — exact conversion from 07
    prof["file_count"] = pd.to_numeric(prof["file_count"], errors="coerce")
    prof["unpacked"] = pd.to_numeric(prof["unpacked"], errors="coerce")
    # dedup
    dup_mask = prof.duplicated(subset="name", keep=False)
    prof_dup_names = set(prof.loc[dup_mask, "name"])
    n_before = len(prof)
    prof = prof.drop_duplicates(subset="name", keep="first")
    n_dupes = n_before - len(prof)
    return prof, prof_dup_names, n_dupes

def load_dependency_check(universe_names, security_names):
    # Returns (dep_issues, placeholder_counter).
    # dep_issues: dict name -> (n_missing, n_placeholder, only_node_placeholders)
    # placeholder_counter: Counter placeholder_name -> n_packages declaring it
    p2_dir = str(DIR_PASADA2)
    p2_files = sorted(f for f in os.listdir(p2_dir) if f.endswith(".jsonl"))
    dep_issues = {}
    placeholder_counter = collections.Counter()
    for fi, fname in enumerate(p2_files):
        with open(os.path.join(p2_dir, fname), encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                if rec.get("error"):
                    continue
                deps_raw = rec.get("deps", [])
                if not deps_raw:
                    continue
                name = rec["name"].strip().lower()
                n_missing = 0
                n_placeholder = 0
                pkg_placeholders = set()
                for d in deps_raw:
                    dn = d.strip().lower()
                    if dn not in universe_names:
                        n_missing += 1
                    elif dn in security_names:
                        n_placeholder += 1
                        pkg_placeholders.add(dn)
                if n_missing > 0 or n_placeholder > 0:
                    only_node = (n_missing == 0
                                 and pkg_placeholders <= NODE_PLACEHOLDER_NAMES)
                    dep_issues[name] = (n_missing, n_placeholder, only_node)
                for pn in pkg_placeholders:
                    placeholder_counter[pn] += 1
        if (fi + 1) % 20 == 0 or fi + 1 == len(p2_files):
            print(f"  dep_check: {fi + 1}/{len(p2_files)} shards, "
                  f"{len(dep_issues):,} with issues")
    return dep_issues, placeholder_counter

# ── Additional imports for main ──────────────────────────────────────
import gc
import time as _time

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# ── Output path ──────────────────────────────────────────────────────
DIR_OUT = BASE / "data" / "07_inclusion_packages"

# ── Criteria (funnel order) ──────────────────────────────────────────
CRITERIA = [
    "no_graph", "no_profile", "name_collision", "no_version",
    "pre2010", "no_date", "post_snapshot", "types_only",
    "platform_binary", "security_placeholder", "bad_dependency", "family",
]
CRITERIA_NO_FAMILY = [c for c in CRITERIA if c != "family"]

CRITERION_DESC = {
    "no_graph":              "Not in dependency graph (expected 0)",
    "no_profile":            "No profile extracted",
    "name_collision":        "Normalized name appears more than once",
    "no_version":            "No dist-tags.latest or version missing",
    "pre2010":               "Created before 2010-01-01",
    "no_date":               "Has profile but no parseable creation date",
    "post_snapshot":         f"Created after {SNAPSHOT_DATE}",
    "types_only":            "Name starts with @types/",
    "platform_binary":       "Name matches OS-architecture pattern",
    "security_placeholder":  f"Latest starts with \"{SECURITY_PREFIX}\"",
    "bad_dependency":        ">=1 production dep missing or is a security placeholder",
    "family":                f"Scope with >= {FAMILY_MIN_SIZE} packages",
}

# ── Markdown stubs ───────────────────────────────────────────────────
def md_table(f, headers, rows):
    f.write("| " + " | ".join(headers) + " |\n")
    f.write("| " + " | ".join("---" for _ in headers) + " |\n")
    for row in rows:
        f.write("| " + " | ".join(str(v) for v in row) + " |\n")
    f.write("\n")

def md_part1(f, flags, ctx):
    p = ctx["params"]
    criteria = ctx["criteria"]
    n_u = ctx["n_universe"]
    # ── 1. Rules and parameters ──────────────────────────────────
    f.write("# Inclusion population results\n\n")
    f.write("## 1. Rules and parameters\n\n")
    f.write(f"- Snapshot date: {p['SNAPSHOT_DATE']}\n")
    f.write(f"- Family minimum size: {p['FAMILY_MIN_SIZE']}\n")
    f.write(f"- Security prefix: `{p['SECURITY_PREFIX']}`\n")
    f.write(f"- Node placeholder names: "
            f"{', '.join(sorted(p['NODE_PLACEHOLDER_NAMES']))}\n")
    f.write(f"- Platform binary pattern: `{p['PLATFORM_BINARY_RE']}`\n\n")
    rule_rows = []
    for c in criteria:
        rule_rows.append((c, CRITERION_DESC[c]))
    md_table(f, ["Criterion", "Description"], rule_rows)
    # ── 2. Totals ────────────────────────────────────────────────
    f.write("## 2. Totals\n\n")
    n_A = ctx["n_A"]
    n_B = ctx["n_B"]
    totals = [
        ("Rows read from pasada2", f"{ctx['rows_read']:,}"),
        ("Case-duplicate rows removed", f"{ctx['dup_removed']:,}"),
        ("Errors in pasada2 (outside universe)", f"{ctx['errors_p2']:,}"),
        ("Universe (unique names)", f"{n_u:,}"),
        ("Graph nodes", f"{ctx['n_graph']:,}"),
        ("Packages with profile", f"{ctx['n_with_profile']:,}"),
        ("Packages without profile", f"{ctx['n_without_profile']:,}"),
        ("Dataset A (with families)", f"{n_A:,}"),
        ("Dataset B (without families)", f"{n_B:,}"),
        ("Removed by family rule (A minus B)", f"{n_A - n_B:,}"),
    ]
    md_table(f, ["Measure", "Value"], totals)
    # ── 3. By criterion ──────────────────────────────────────────
    f.write("## 3. By criterion\n\n")
    refs = {
        "no_profile": 6_215,
        "name_collision": 787,
        "pre2010": 1,
        "no_date": 0,
        "post_snapshot": 941,
        "no_version": 1_279,
        "types_only": 11_401,
        "platform_binary": 52_562,
        "security_placeholder": 155_248,
        "family": 1_457_318,
    }
    # compute only_this from flags
    fail_count = flags[criteria].sum(axis=1)
    only_this = {}
    for c in criteria:
        only_this[c] = int((flags[c] & (fail_count == 1)).sum())
    del fail_count
    crit_rows = []
    for c in criteria:
        n_fail = int(flags[c].sum())
        ot = only_this[c]
        pct = f"{100 * n_fail / n_u:.2f}%"
        if c == "bad_dependency":
            ref_str = "~97,216"
            diff_str = ""
        elif c == "no_graph":
            ref_str = "0"
            diff = n_fail - 0
            mark = " !!!" if abs(diff) > 0 else ""
            diff_str = f"{diff:+,}{mark}"
        elif c in refs:
            ref = refs[c]
            diff = n_fail - ref
            pct_diff = abs(diff) / max(ref, 1) * 100
            mark = " !!!" if pct_diff > 1.0 else ""
            diff_str = f"{diff:+,}{mark}"
            ref_str = f"{ref:,}"
        else:
            ref_str = ""
            diff_str = ""
        crit_rows.append((c, f"{n_fail:,}", f"{ot:,}", pct,
                          ref_str, diff_str))
    md_table(f, ["Criterion", "Fail", "Only this", "% univ",
                 "Reference", "Diff"], crit_rows)
    # ── 4. Funnel ────────────────────────────────────────────────
    f.write("## 4. Funnel\n\n")
    # For A: apply all criteria except family in order
    # For B: apply all criteria in order
    remain_a = flags.copy()
    remain_b = flags.copy()
    funnel_rows = []
    prev_a = n_u
    prev_b = n_u
    funnel_rows.append(("(start)", f"{n_u:,}", "", f"{n_u:,}", ""))
    for c in criteria:
        if c != "family":
            remain_a = remain_a[~remain_a[c]]
        remain_b = remain_b[~remain_b[c]]
        cur_a = len(remain_a)
        cur_b = len(remain_b)
        lost_a = prev_a - cur_a if c != "family" else "-"
        lost_b = prev_b - cur_b
        fa = f"{lost_a:,}" if isinstance(lost_a, int) else lost_a
        funnel_rows.append((
            c,
            f"{cur_a:,}", f"-{fa}" if isinstance(lost_a, int) else "(skip)",
            f"{cur_b:,}", f"-{lost_b:,}",
        ))
        if c != "family":
            prev_a = cur_a
        prev_b = cur_b
    del remain_a, remain_b
    md_table(f, ["Step", "Remain A", "Lost A",
                 "Remain B", "Lost B"], funnel_rows)

def md_part2(f, flags, ctx):
    n_u = ctx["n_universe"]
    dep_info = ctx["dep_info"]
    pc = ctx["placeholder_counter"]
    # ── 5. Family impact ─────────────────────────────────────────
    f.write("## 5. Impact of the family rule\n\n")
    # 5a. Scope size thresholds
    f.write("### 5a. Scope size thresholds\n\n")
    scoped = flags[flags["scope_size"] > 0]
    thresh_rows = []
    for t in [2, 5, 10, 20, 50, 100, 500]:
        sub = scoped[scoped["scope_size"] >= t]
        n_scopes = sub["scope"].nunique()
        n_pkgs = len(sub)
        thresh_rows.append((t, f"{n_scopes:,}", f"{n_pkgs:,}",
                            f"{100 * n_pkgs / n_u:.2f}%"))
    md_table(f, ["Min size", "Scopes", "Packages", "% universe"],
             thresh_rows)
    del scoped
    # 5b. 30 largest families removed
    f.write("### 5b. 30 largest families removed by the rule\n\n")
    removed = flags[flags["family"] & flags["in_A"]]
    fam_sizes = removed.groupby("scope").size().sort_values(ascending=False)
    top30 = fam_sizes.head(30)
    fam_rows = []
    for scope, cnt in top30.items():
        fam_rows.append((scope, f"{cnt:,}"))
    md_table(f, ["Scope", "Packages"], fam_rows)
    del removed
    # 5c. @hyper.fun
    f.write("### 5c. @hyper.fun\n\n")
    hf = flags[flags["scope"] == "@hyper.fun"]
    hf_total = len(hf)
    hf_in_a = int(hf["in_A"].sum())
    hf_in_b = int(hf["in_B"].sum())
    f.write(f"- Packages in universe: {hf_total:,}\n")
    f.write(f"- In A: {hf_in_a:,}\n")
    f.write(f"- In B: {hf_in_b:,}\n\n")
    del hf
    # 5d. fan_in / fan_out comparison A vs B
    f.write("### 5d. fan_in and fan_out comparison (A vs B)\n\n")
    a = flags[flags["in_A"]]
    b = flags[flags["in_B"]]
    stat_rows = []
    for col in ["fan_in", "fan_out"]:
        for label, sub, n_sub in [("A", a, ctx["n_A"]),
                                  ("B", b, ctx["n_B"])]:
            s = sub[col]
            stat_rows.append((
                col, label,
                f"{s.mean():.2f}", f"{s.median():.0f}",
                f"{int(s.quantile(0.90)):,}",
                f"{int(s.quantile(0.99)):,}",
                f"{int(s.max()):,}",
                f"{100 * (s == 0).sum() / n_sub:.1f}%",
            ))
    md_table(f, ["Metric", "Set", "Mean", "Median", "p90", "p99",
                 "Max", "% zero"], stat_rows)
    # 5e. Distribution by band
    f.write("### 5e. Distribution by fan_in and fan_out bands\n\n")
    fi_bands = [("0", lambda s: s == 0), ("1-9", lambda s: s.between(1, 9)),
                ("10-99", lambda s: s.between(10, 99)),
                ("100-999", lambda s: s.between(100, 999)),
                ("1000+", lambda s: s >= 1000)]
    fo_bands = [("0", lambda s: s == 0), ("1-2", lambda s: s.between(1, 2)),
                ("3-9", lambda s: s.between(3, 9)),
                ("10-49", lambda s: s.between(10, 49)),
                ("50+", lambda s: s >= 50)]
    for col, bands in [("fan_in", fi_bands), ("fan_out", fo_bands)]:
        f.write(f"**{col}**\n\n")
        band_rows = []
        for label, cond in bands:
            na = int(cond(a[col]).sum())
            nb = int(cond(b[col]).sum())
            band_rows.append((label, f"{na:,}",
                              f"{100 * na / ctx['n_A']:.1f}%",
                              f"{nb:,}",
                              f"{100 * nb / ctx['n_B']:.1f}%"))
        md_table(f, ["Band", "A", "% A", "B", "% B"], band_rows)
    del a, b
    # ── 6. By creation year ──────────────────────────────────────
    f.write("## 6. By creation year\n\n")
    year_rows = []
    for yr in sorted(flags["created_year"].dropna().unique()):
        yr_int = int(yr)
        m = flags["created_year"] == yr
        n_yr = int(m.sum())
        n_yr_a = int((m & flags["in_A"]).sum())
        n_yr_b = int((m & flags["in_B"]).sum())
        pct_b = f"{100 * n_yr_b / n_yr:.1f}%" if n_yr > 0 else "0.0%"
        year_rows.append((yr_int, f"{n_yr:,}", f"{n_yr_a:,}",
                          f"{n_yr_b:,}", pct_b))
    m_na = flags["created_year"].isna()
    if m_na.any():
        n_na = int(m_na.sum())
        n_na_a = int((m_na & flags["in_A"]).sum())
        n_na_b = int((m_na & flags["in_B"]).sum())
        pct_b = f"{100 * n_na_b / n_na:.1f}%" if n_na > 0 else "0.0%"
        year_rows.append(("NA", f"{n_na:,}", f"{n_na_a:,}",
                          f"{n_na_b:,}", pct_b))
    md_table(f, ["Year", "Universe", "A", "B", "% B/univ"], year_rows)
    # ── 7. Dependencies ──────────────────────────────────────────
    f.write("## 7. Dependencies\n\n")
    # 7a. Distribution by number of bad deps
    f.write("### 7a. Packages by number of missing or placeholder deps\n\n")
    band_dep = {"1": 0, "2": 0, "3-9": 0, "10+": 0}
    for name, (nm, np_, _) in dep_info.items():
        total = nm + np_
        if total == 1:
            band_dep["1"] += 1
        elif total == 2:
            band_dep["2"] += 1
        elif total <= 9:
            band_dep["3-9"] += 1
        else:
            band_dep["10+"] += 1
    dep_band_rows = []
    for k in ["1", "2", "3-9", "10+"]:
        dep_band_rows.append((k, f"{band_dep[k]:,}"))
    dep_band_rows.append(("Total", f"{len(dep_info):,}"))
    md_table(f, ["Bad deps", "Packages"], dep_band_rows)
    # 7b. Packages failing only because of fs/http
    f.write("### 7b. Packages failing only due to Node builtins "
            "(fs, http)\n\n")
    only_node = {name for name, (_, _, on) in dep_info.items() if on}
    f.write(f"Packages with only_node_placeholders = true: "
            f"{len(only_node):,}\n\n")
    # year distribution of only_node
    on_mask = flags["name"].isin(only_node)
    on_years = flags.loc[on_mask, "created_year"].dropna()
    if len(on_years) > 0:
        yr_counts = on_years.astype(int).value_counts().sort_index()
        on_year_rows = []
        for yr, cnt in yr_counts.items():
            on_year_rows.append((yr, f"{cnt:,}"))
        md_table(f, ["Year", "Packages (only node builtins)"],
                 on_year_rows)
    del only_node, on_mask
    # 7c. Top 20 placeholders
    f.write("### 7c. Top 20 security placeholders declared "
            "as dependencies\n\n")
    top20 = pc.most_common(20)
    ph_rows = []
    for name, cnt in top20:
        ph_rows.append((name, f"{cnt:,}"))
    md_table(f, ["Placeholder", "Packages declaring it"], ph_rows)
    # ── 8. Notes ─────────────────────────────────────────────────
    f.write("## 8. Notes\n\n")
    f.write("- The fan_in and fan_out of datasets A and B come from the "
            "full dependency graph and count dependents that may have been "
            "excluded from the population.\n")
    f.write("- Scope size is counted over the universe before applying "
            "any other criterion.\n")
    f.write("- Packages with errors in pasada2 are not part of the "
            "universe.\n")
    f.write("- Dependency lists are not stored (only dep_hash and "
            "counts). Peer and optional dependency lists are also not "
            "stored (only n_peer and n_opt).\n")

def write_results_md(flags, ctx):
    os.makedirs(str(DIR_OUT), exist_ok=True)
    with open(str(DIR_OUT / "inclusion_results.md"), "w", encoding="utf-8") as f:
        md_part1(f, flags, ctx)
        md_part2(f, flags, ctx)

# ── Parquet chunked writer ───────────────────────────────────────────
def write_parquet_chunked(df, path, chunk_size=500_000):
    n = len(df)
    first_end = min(chunk_size, n)
    first_table = pa.Table.from_pandas(
        df.iloc[:first_end], preserve_index=False)
    schema = first_table.schema
    if "keywords" in df.columns:
        idx = schema.get_field_index("keywords")
        schema = schema.set(idx, pa.field("keywords", pa.list_(pa.string())))
    with pq.ParquetWriter(str(path), schema) as writer:
        writer.write_table(first_table.cast(schema))
        del first_table
        for start in range(chunk_size, n, chunk_size):
            end = min(start + chunk_size, n)
            chunk = pa.Table.from_pandas(
                df.iloc[start:end], preserve_index=False).cast(schema)
            writer.write_table(chunk)
            del chunk

# ── Main ─────────────────────────────────────────────────────────────
def main():
    started = _time.strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 60)
    print("07b_inclusion_population.py")
    print("=" * 60)

    # ── 1. Load data ─────────────────────────────────────────────
    print("\n[1] Loading universe (pasada2 shards) ...")
    universe, collision_names, rows_read, n_univ_dupes, n_errors = (
        load_universe())

    print("\n[2] Loading graph_metrics.csv ...")
    graph = load_graph()
    n_graph = len(graph)
    print(f"  Graph nodes: {n_graph:,}")

    print("\n[3] Loading profile shards ...")
    profile, prof_dup_names, n_prof_dupes = load_profile()
    n_prof_unique = len(profile)
    print(f"  Profile: {n_prof_unique:,} unique")

    collision_names = collision_names | prof_dup_names
    n_collision = len(collision_names)
    del prof_dup_names

    # ── 2. Verify and merge ──────────────────────────────────────
    n_universe = len(universe)
    if n_universe != n_graph:
        print(f"  WARNING: universe ({n_universe:,}) != graph ({n_graph:,})")
    else:
        print(f"  Universe matches graph: {n_universe:,}")

    print("\n[4] Merging ...")
    df = universe.merge(graph, on="name", how="left")
    del universe; gc.collect()

    df["no_graph"] = df["fan_in"].isna()
    n_no_graph = int(df["no_graph"].sum())
    if n_no_graph > 0:
        print(f"  WARNING: no_graph = {n_no_graph:,}")

    for col in ["fan_in", "fan_out", "fan_in_dev", "fan_out_dev"]:
        df[col] = df[col].fillna(0).astype("int32")

    df["has_profile"] = df["name"].isin(profile["name"])
    n_with_profile = int(df["has_profile"].sum())
    n_without_profile = n_universe - n_with_profile

    df = df.merge(profile, on="name", how="left")
    del graph, profile; gc.collect()

    # Fill NaN for profile columns on packages without profile
    df["latest_profile"] = df["latest_profile"].fillna("")
    for col in ["n_versions", "n_maintainers", "n_keywords", "n_peer", "n_opt"]:
        df[col] = df[col].fillna(0).astype("int32")
    df["has_github"] = df["has_github"].fillna(False)
    df["deprecated"] = df["deprecated"].fillna(False)
    df["keywords"] = [
        kw if isinstance(kw, list) else [] for kw in df["keywords"]]

    # Scope and scope_size
    df["scope"] = df["name"].map(scope_of)
    scope_counts = df.loc[df["scope"] != "", "scope"].value_counts()
    df["scope_size"] = df["scope"].map(scope_counts).fillna(0).astype("int32")

    mem_mb = df.memory_usage(deep=True).sum() / 1024**2
    print(f"  Merged table: {len(df):,} rows, {mem_mb:,.0f} MB")

    # ── 3. Security names and dependency check ───────────────────
    print("\n[5] Dependency check ...")
    sec_mask = flag_security_placeholder(df["latest_profile"])
    security_names = set(df.loc[sec_mask, "name"])
    universe_names = set(df["name"])
    dep_issues, placeholder_counter = load_dependency_check(
        universe_names, security_names)
    del universe_names

    # ── 4. Apply criteria ────────────────────────────────────────
    print("\n[6] Applying criteria ...")
    # no_graph already computed above
    df["no_profile"] = ~df["has_profile"]
    df["name_collision"] = df["name"].isin(collision_names)
    df["no_version"] = df["sin_version"] == 1
    df["pre2010"] = flag_pre2010(df["created_date"]).fillna(False)
    df["no_date"] = flag_no_date(df["created_date"], df["has_profile"])
    df["post_snapshot"] = flag_post_snapshot(df["created_date"]).fillna(False)
    df["types_only"] = flag_types_only(df["name"])
    df["platform_binary"] = flag_platform_binary(df["name"])
    df["security_placeholder"] = sec_mask
    df["bad_dependency"] = df["name"].isin(dep_issues)
    df["family"] = flag_family(df["scope_size"])
    del sec_mask, collision_names

    # in_A: passes every criterion except family
    df["in_A"] = True
    for c in CRITERIA_NO_FAMILY:
        df["in_A"] = df["in_A"] & ~df[c]
    # in_B: in_A and not family
    df["in_B"] = df["in_A"] & ~df["family"]

    n_A = int(df["in_A"].sum())
    n_B = int(df["in_B"].sum())

    # only_this (packages failing exactly one criterion)
    fail_count = df[CRITERIA].sum(axis=1)
    only_this = {}
    for c in CRITERIA:
        only_this[c] = int((df[c] & (fail_count == 1)).sum())
    del fail_count

    # ── 5. Console output ────────────────────────────────────────
    print("\n" + "=" * 70)
    print("[A] INCLUSION RULES")
    print("=" * 70)
    for c in CRITERIA:
        print(f"  {c:<25s}  {CRITERION_DESC[c]}")

    print("\n" + "=" * 70)
    print("[B] POPULATION")
    print("=" * 70)
    print(f"  Rows read from pasada2:          {rows_read:>12,}")
    print(f"  Case-duplicate rows removed:     {n_univ_dupes:>12,}")
    print(f"  Errors in pasada2 (not in univ): {n_errors:>12,}")
    print(f"  Universe (unique names):         {n_universe:>12,}")
    print(f"  Graph nodes:                     {n_graph:>12,}")
    print(f"  Packages with profile:           {n_with_profile:>12,}")
    print(f"  Packages without profile:        {n_without_profile:>12,}")
    print(f"  Dataset A (with families):       {n_A:>12,}")
    print(f"  Dataset B (without families):    {n_B:>12,}")

    print("\n" + "=" * 70)
    print("[C] BY CRITERION")
    print("=" * 70)
    hdr = (f"  {'criterion':<25s} {'fail':>10s} "
           f"{'only_this':>10s} {'%univ':>7s}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for c in CRITERIA:
        n_fail = int(df[c].sum())
        pct = 100 * n_fail / n_universe
        print(f"  {c:<25s} {n_fail:>10,} "
              f"{only_this[c]:>10,} {pct:>6.2f}%")
    print("  " + "-" * (len(hdr) - 2))
    total_fail_a = n_universe - n_A
    print(f"  {'FAIL_ANY (excl family)':<25s} {total_fail_a:>10,} "
          f"{'':>10s} {100 * total_fail_a / n_universe:>6.2f}%")
    print(f"  {'IN_A':<25s} {n_A:>10,} {'':>10s} "
          f"{100 * n_A / n_universe:>6.2f}%")
    print(f"  {'IN_B':<25s} {n_B:>10,} {'':>10s} "
          f"{100 * n_B / n_universe:>6.2f}%")

    # ── 6. Write outputs ─────────────────────────────────────────
    os.makedirs(str(DIR_OUT), exist_ok=True)

    # Columns for population parquets (A and B)
    pop_cols = [
        "name", "scope", "scope_size", "created_date", "created_year",
        "latest_profile", "latest_p2", "tarball",
        "dep_hash", "fan_in", "fan_out", "fan_in_dev", "fan_out_dev",
        "n_versions", "n_maintainers", "deprecated", "has_github",
        "n_keywords", "keywords", "n_peer", "n_opt",
        "file_count", "unpacked",
    ]

    print("\n[7] Writing population_with_families.parquet ...")
    df_a = df.loc[df["in_A"], pop_cols].rename(
        columns={"latest_profile": "latest"})
    write_parquet_chunked(df_a, DIR_OUT / "population_with_families.parquet")
    cols_a = list(df_a.columns)
    del df_a; gc.collect()

    print("[8] Writing population_without_families.parquet ...")
    df_b = df.loc[df["in_B"], pop_cols].rename(
        columns={"latest_profile": "latest"})
    write_parquet_chunked(df_b, DIR_OUT / "population_without_families.parquet")
    cols_b = list(df_b.columns)
    del df_b; gc.collect()

    # inclusion_flags.parquet
    print("[9] Writing inclusion_flags.parquet ...")
    flags_cols = (["name", "scope", "scope_size", "created_year",
                   "fan_in", "fan_out"] + CRITERIA + ["in_A", "in_B"])
    flags = df[flags_cols].copy()
    write_parquet_chunked(flags, DIR_OUT / "inclusion_flags.parquet")
    del df; gc.collect()

    # run_metadata.json
    print("[10] Writing run_metadata.json ...")
    metadata = {
        "executed_at": started,
        "params": {
            "SNAPSHOT_DATE": str(SNAPSHOT_DATE),
            "FAMILY_MIN_SIZE": FAMILY_MIN_SIZE,
            "NODE_PLACEHOLDER_NAMES": sorted(NODE_PLACEHOLDER_NAMES),
            "PLATFORM_BINARY_RE": PLATFORM_BINARY_RE,
            "SECURITY_PREFIX": SECURITY_PREFIX,
        },
        "paths": {
            "pasada2": str(DIR_PASADA2),
            "graph_csv": str(GRAPH_CSV),
            "profile_part1": str(DIR_PROFILE_1),
            "profile_part2": str(DIR_PROFILE_2),
        },
        "counts": {
            "rows_read": rows_read,
            "dup_removed": n_univ_dupes,
            "errors_p2": n_errors,
            "collision_names": n_collision,
            "profile_dups": n_prof_dupes,
            "n_universe": n_universe,
            "n_graph": n_graph,
            "n_with_profile": n_with_profile,
            "n_without_profile": n_without_profile,
            "n_A": n_A,
            "n_B": n_B,
        },
        "columns_A": cols_a,
        "columns_B": cols_b,
        "versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "pyarrow": pa.__version__,
        },
    }
    with open(str(DIR_OUT / "run_metadata.json"), "w",
              encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, ensure_ascii=False)

    # ── 7. Build ctx and write md ────────────────────────────────
    ctx = {
        "params": metadata["params"],
        "rows_read": rows_read,
        "dup_removed": n_univ_dupes,
        "errors_p2": n_errors,
        "collision_n": n_collision,
        "profile_dups": n_prof_dupes,
        "n_graph": n_graph,
        "n_universe": n_universe,
        "n_with_profile": n_with_profile,
        "n_without_profile": n_without_profile,
        "n_A": n_A,
        "n_B": n_B,
        "criteria": CRITERIA,
        "dep_info": dep_issues,
        "placeholder_counter": placeholder_counter,
    }

    print("[11] Writing inclusion_results.md ...")
    write_results_md(flags, ctx)

    print("\nDone.")


if __name__ == "__main__":
    main()
