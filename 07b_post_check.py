#!/usr/bin/env python3
"""
07b_post_check.py -- Checks the inclusion rules against independent evidence.

Phase "local" (data on this machine, minutes):
  L1 name collisions: the spellings behind each collided name
  L2 security placeholders: every latest version that mentions "security",
     and whether the pattern 0.0.x-security misses any
  L3 platform binaries: the flagged names grouped by family, and the
     Rust-pattern matches outside @rustbin
  L4 pass 2 errors: how many packages depend on each failed query
  L5 effect of two corrections: packages that the corrected rules keep and
     the previous ones excluded, because of fs or http or of failed queries
  It also writes the name lists that the network phase checks.

Phase "network" (asks the npm registry; about an hour and a half; resumable
with Ctrl+C, and run again to continue or to rewrite the report):
  N1 failed queries: whether each package exists, and has a version
  N2 placeholders: whether npm's text "security holding package" or its
     account is there
  N3 binaries: whether the latest version declares the systems (os) or
     processors (cpu) it runs on. Some families, such as @rustbin, do not
     declare them; the report groups the results by family for that reason.

Phase "lists" (only where pass 2 is not available, such as the notebook):
  writes the placeholder and binary lists from the 07b network signals, so
  that the network phase can start. The placeholder list follows the earlier
  rule (0.0.1-security only), so it lacks a few dozen variants, and there is
  no list of failed queries. On the PC, the local phase later writes the
  exact lists, and the network phase checks only the names still missing.

Usage, from the repository root:
    python 07b_post_check.py local      (PC)
    python 07b_post_check.py lists      (notebook, instead of local)
    python 07b_post_check.py network

Input : data/pasada2/*.jsonl
        data/07_inclusion_packages/inclusion_flags.parquet
        data/07_inclusion_packages/population_with_families.parquet
Output: data/07_inclusion_packages/post_check/
"""
import collections
import glob
import json
import os
import re
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

PASS2 = "data/pasada2/*.jsonl"
INCLUSION = "data/07_inclusion_packages"
OUT = f"{INCLUSION}/post_check"
WORKERS = 16
CHUNK = 2_000
USER_AGENT = "UCN-research/1.0 (jairo.vergara@alumnos.ucn.cl)"
NODE_BUILTINS = {"fs", "http"}
SECURITY_RE = re.compile(r"^0\.0\.\d+-security")
OS_ARCH = re.compile(
    r"(?:linux|darwin|win32|windows|freebsd|openbsd|netbsd|android|sunos|aix)"
    r"-(?:x64|x86|ia32|arm|arm64|ppc64|s390x|riscv64|loong64|mips64el|universal)")
_RUST_LONG = (r"x86_64|aarch64|i686|i586|armv7a|armv7r|armv7|arm64ec|riscv64gc|riscv64imac|"
              r"powerpc64le|s390x|loongarch64|wasm32v1|wasm32")
_RUST_SHORT = (r"arm|armv5te|armebv7r|thumbv\w+(?:\.\w+)?|powerpc64|powerpc|mips\w*|sparc\w*|"
               r"riscv32\w*|nvptx64")
RUST = re.compile(rf"(?:^|[-_/.])(?:(?:{_RUST_LONG})-|(?:{_RUST_SHORT})-"
                  rf"(?:unknown|apple|pc|none|sun|linux|wrs|nvidia)-)")
SIGNALS = "data/07_strata_analysis/signals.parquet"

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def md_table(header, rows):
    out = ["| " + " | ".join(str(h) for h in header) + " |", "|" + "---|" * len(header)]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


def family_of(name):
    """Scope for scoped names, first word otherwise: esbuild-linux-x64 -> esbuild."""
    return name.split("/")[0] if name.startswith("@") else re.split(r"[-_.]", name)[0]


# ======================================================================
# Local phase
# ======================================================================

def read_pass2():
    records, spellings, errors = {}, collections.defaultdict(list), set()
    for path in sorted(glob.glob(PASS2)):
        with open(path, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                low = d["name"].strip().lower()
                if d.get("error"):
                    errors.add(low)
                    continue
                spellings[low].append(d["name"])
                status = "no_version" if d.get("sin_version") else "ok"
                records.setdefault(low, []).append(
                    {"spelling": d["name"], "status": status, "latest": d.get("latest") or "",
                     "deps": [x.strip().lower() for x in (d.get("deps") or [])]})
    errors -= set(records)
    return records, spellings, errors


def phase_local():
    os.makedirs(OUT, exist_ok=True)
    log("reading pass 2")
    records, spellings, errors = read_pass2()
    flags = pd.read_parquet(f"{INCLUSION}/inclusion_flags.parquet",
                            columns=["name", "fan_in", "security_placeholder", "platform_binary",
                                     "name_collision", "in_A"])
    placeholders = set(flags.loc[flags.security_placeholder, "name"])
    universe = set(records)

    # L1 collisions
    coll_rows, n_same_twice = [], 0
    for low, names in spellings.items():
        if len(names) > 1:
            if len(set(names)) < len(names):
                n_same_twice += 1
            if len(set(names)) > 1:
                for r in records[low]:
                    coll_rows.append({"name": low, "spelling": r["spelling"], "status": r["status"],
                                      "latest": r["latest"], "n_deps": len(r["deps"])})
    coll = pd.DataFrame(coll_rows, columns=["name", "spelling", "status", "latest", "n_deps"])
    coll.to_csv(f"{OUT}/l1_collisions.csv", index=False)
    groups = coll.groupby("name")
    both_versions = int(groups.apply(lambda g: (g.status == "ok").sum() >= 2,
                                     include_groups=False).sum()) if len(coll) else 0

    # L2 placeholder versions
    versions = collections.Counter()
    for recs in records.values():
        v = recs[0]["latest"]
        if "security" in v.lower():
            versions[v] += 1
    ver_rows = [[v, f"{c:,}", "yes" if SECURITY_RE.search(v) else "**no**"]
                for v, c in versions.most_common(40)]
    missed = sum(c for v, c in versions.items() if not SECURITY_RE.search(v))
    pop = pd.read_parquet(f"{INCLUSION}/population_with_families.parquet",
                          columns=["name", "latest", "fan_in"])
    kept_security = pop[pop["latest"].fillna("").str.contains("security", case=False)]
    kept_security = kept_security.sort_values("fan_in", ascending=False)

    # L3 binaries
    binaries = flags[flags.platform_binary].copy()
    binaries["family"] = binaries["name"].map(family_of)
    binaries["by_os_arch"] = binaries["name"].str.contains(OS_ARCH)
    fam = binaries.groupby("family").agg(packages=("name", "size"),
                                         os_arch_pattern=("by_os_arch", "sum"))
    fam = fam.sort_values("packages", ascending=False)
    rust_outside = binaries[~binaries.by_os_arch & (binaries.family != "@rustbin")]

    # L4 errors and L5 effect of the corrections
    dependents = collections.Counter()
    saved_errors = saved_builtins = saved_both = 0
    for recs in records.values():
        r = recs[0]
        if r["status"] != "ok" or not r["deps"]:
            continue
        missing_old = missing_new = holders_old = holders_new = 0
        for x in set(r["deps"]):
            if x in errors:
                dependents[x] += 1
                missing_old += 1
            elif x not in universe:
                missing_old += 1
                missing_new += 1
            elif x in placeholders:
                holders_old += 1
                holders_new += x not in NODE_BUILTINS
        bad_old = missing_old + holders_old > 0
        bad_new = missing_new + holders_new > 0
        if bad_old and not bad_new:
            by_errors = missing_old > missing_new
            by_builtins = holders_old > holders_new
            saved_both += by_errors and by_builtins
            saved_errors += by_errors and not by_builtins
            saved_builtins += by_builtins and not by_errors
    err = pd.DataFrame({"name": sorted(errors)})
    err["dependents"] = err["name"].map(dependents).fillna(0).astype(int)
    err = err.sort_values("dependents", ascending=False)
    err.to_csv(f"{OUT}/l4_errors.csv", index=False)

    # lists for the network phase
    for fname, names in [("errors.txt", err["name"]), ("placeholders.txt", sorted(placeholders)),
                         ("binaries.txt", binaries["name"])]:
        with open(f"{OUT}/{fname}", "w", encoding="utf-8") as f:
            f.write("\n".join(names) + "\n")

    lines = [
        "# Post-check, local phase\n",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')}.\n",
        "## L1. Name collisions\n",
        f"- Names that collide in lower case: {coll['name'].nunique():,}; flagged by the rule: "
        f"{int(flags.name_collision.sum()):,}.",
        f"- Of them, groups where two or more spellings have a version (two real packages): "
        f"{both_versions:,}.",
        f"- Names that appear twice with the same spelling: {n_same_twice:,}.",
        f"- Every spelling is listed in `l1_collisions.csv`.\n",
        "## L2. Versions that mention \"security\"\n",
        f"Matched by the pattern: {sum(versions.values()) - missed:,}. Not matched: {missed:,}.\n",
        md_table(["Version", "Packages", "Matched"], ver_rows),
        f"Packages in population A whose version mentions \"security\": {len(kept_security):,}.\n",
        md_table(["Package", "Version", "Fan-in"],
                 [[r.name, r.latest, f"{int(r.fan_in):,}"] for r in kept_security.head(30).itertuples()]),
        "## L3. Platform binaries by family\n",
        f"Flagged: {len(binaries):,}. Families: {len(fam):,}. Columns: packages, and how many "
        "match the system-processor pattern (the rest match a Rust target).\n",
        md_table(["Family", "Packages", "System-processor pattern"],
                 [[f_, f"{int(r.packages):,}", f"{int(r.os_arch_pattern):,}"]
                  for f_, r in fam.head(40).iterrows()]),
        f"Rust-pattern matches outside @rustbin: {len(rust_outside):,}.\n",
        md_table(["Package"], [[n] for n in rust_outside["name"].head(40)]),
        "## L4. Failed queries in pass 2\n",
        f"Failed queries: {len(err):,}; with at least one dependent: "
        f"{int((err.dependents > 0).sum()):,}; dependents in total: {int(err.dependents.sum()):,}.\n",
        md_table(["Package", "Dependents"],
                 [[r.name, f"{r.dependents:,}"] for r in err.head(30).itertuples()]),
        "## L5. Packages the corrections keep\n",
        md_table(["Reason", "Packages"],
                 [["Only because failed queries now count as existing", f"{saved_errors:,}"],
                  ["Only because fs and http no longer count as bad", f"{saved_builtins:,}"],
                  ["Both", f"{saved_both:,}"]]),
        "Network phase lists: errors.txt, placeholders.txt, binaries.txt.\n",
    ]
    with open(f"{OUT}/local_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"done: {OUT}/local_report.md")


def phase_lists():
    os.makedirs(OUT, exist_ok=True)
    log("reading the 07b network signals")
    sig = pd.read_parquet(SIGNALS, columns=["name", "security_placeholder"])
    names = sig["name"]
    binary = (names.str.contains(OS_ARCH) | names.str.contains(RUST)).to_numpy()
    lists = {"placeholders.txt": names[sig["security_placeholder"].to_numpy()],
             "binaries.txt": names[binary]}
    for fname, values in lists.items():
        with open(f"{OUT}/{fname}", "w", encoding="utf-8") as f:
            f.write("\n".join(values) + "\n")
        log(f"  {fname}: {len(values):,} names")
    log("no list of failed queries: it needs pass 2, so the PC writes it")


# ======================================================================
# Network phase
# ======================================================================

_stop = False


def _on_sigint(sig, frame):
    global _stop
    if _stop:
        sys.exit(1)
    _stop = True
    print("\n  Ctrl+C: finishing the current batch, then saving.", flush=True)


def fetch(name, abbreviated):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@/")
    headers = {"User-Agent": USER_AGENT}
    if abbreviated:
        headers["Accept"] = "application/vnd.npm.install-v1+json"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                        timeout=30) as r:
                return "ok", json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "not_found", None
            if attempt == 2:
                return "error", None
        except Exception:
            if attempt == 2:
                return "error", None
        time.sleep(1 + 2 * attempt)


def check_error(name):
    status, d = fetch(name, True)
    if status != "ok":
        return {"name": name, "result": status}
    latest = (d.get("dist-tags") or {}).get("latest")
    exists = latest and latest in (d.get("versions") or {})
    return {"name": name, "result": "exists" if exists else "no_version"}


def check_placeholder(name):
    status, d = fetch(name, False)
    if status != "ok":
        return {"name": name, "result": status}
    text = f"{d.get('description') or ''} {d.get('readme') or ''}".lower()
    accounts = {m.get("name") for m in d.get("maintainers") or [] if isinstance(m, dict)}
    return {"name": name, "result": "ok", "latest": (d.get("dist-tags") or {}).get("latest"),
            "holding_text": "security holding package" in text,
            "npm_account": bool(accounts & {"npm", "npm-support"})}


def check_binary(name):
    status, d = fetch(name, True)
    if status != "ok":
        return {"name": name, "result": status}
    latest = (d.get("dist-tags") or {}).get("latest")
    v = (d.get("versions") or {}).get(latest) or {}
    return {"name": name, "result": "ok", "os": bool(v.get("os")), "cpu": bool(v.get("cpu"))}


CHECKS = [("errors.txt", "n1_errors.jsonl", check_error),
          ("placeholders.txt", "n2_placeholders.jsonl", check_placeholder),
          ("binaries.txt", "n3_binaries.jsonl", check_binary)]


def phase_network():
    signal.signal(signal.SIGINT, _on_sigint)
    complete = True
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for list_file, out_file, check in CHECKS:
            if not os.path.exists(f"{OUT}/{list_file}"):
                log(f"{list_file}: not found, skipped")
                complete = False
                continue
            names = [x for x in open(f"{OUT}/{list_file}", encoding="utf-8").read().split("\n") if x]
            path = f"{OUT}/{out_file}"
            done = set()
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    done = {json.loads(line)["name"] for line in f if line.strip()}
            todo = [x for x in names if x not in done]
            log(f"{list_file}: {len(names):,} names, {len(done):,} done, {len(todo):,} left")
            start_t = time.time()
            with open(path, "a", encoding="utf-8") as out:
                for start in range(0, len(todo), CHUNK):
                    for res in ex.map(check, todo[start:start + CHUNK]):
                        out.write(json.dumps(res) + "\n")
                    out.flush()
                    finished = start + min(CHUNK, len(todo) - start)
                    rate = finished / max(time.time() - start_t, 1)
                    log(f"  {finished:,}/{len(todo):,}, {rate:.0f}/s, about "
                        f"{(len(todo) - finished) / max(rate, 0.1) / 60:.0f} min left")
                    if _stop:
                        log("stopped; run the same command again to continue")
                        return
    network_report(complete)


def load_results(name):
    path = f"{OUT}/{name}"
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None
    return pd.read_json(path, lines=True)


def network_report(complete):
    n1, n2, n3 = (load_results("n1_errors.jsonl"), load_results("n2_placeholders.jsonl"),
                  load_results("n3_binaries.jsonl"))
    lines = ["# Post-check, network phase\n", f"Generated {time.strftime('%Y-%m-%d %H:%M')}."
             + ("" if complete else " Partial: a list was missing, see N1.") + "\n"]
    if n1 is not None and os.path.exists(f"{OUT}/l4_errors.csv"):
        n1 = n1.merge(pd.read_csv(f"{OUT}/l4_errors.csv"), on="name", how="left")
        n1_rows = [[k, f"{int((n1.result == k).sum()):,}",
                    f"{int(n1.loc[n1.result == k, 'dependents'].sum()):,}"]
                   for k in ["exists", "no_version", "not_found", "error"]]
        lines += ["## N1. Failed queries, asked again\n",
                  "Dependents: packages that declare it as a production dependency. The corrected "
                  "rule keeps them; those of packages that do not exist should have been excluded.\n",
                  md_table(["Result", "Packages", "Their dependents"], n1_rows)]
    else:
        lines += ["## N1. Failed queries, asked again\n",
                  "Not checked yet: run the local phase on the PC, then this phase again.\n"]
    if n2 is not None:
        lines += placeholder_section(n2)
    if n3 is not None:
        lines += binary_section(n3)
    with open(f"{OUT}/network_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log(f"done: {OUT}/network_report.md")


def placeholder_section(n2):
    ok2 = n2[n2.result == "ok"].astype({"holding_text": bool, "npm_account": bool})
    confirmed = ok2.holding_text | ok2.npm_account
    n2_rows = [["Answered", f"{len(ok2):,}"],
               ["With npm's text", f"{int(ok2.holding_text.sum()):,}"],
               ["With npm's account", f"{int(ok2.npm_account.sum()):,}"],
               ["Confirmed by either", f"{int(confirmed.sum()):,} ({confirmed.mean() * 100:.2f}%)"],
               ["No longer exists", f"{int((n2.result == 'not_found').sum()):,}"],
               ["Query failed", f"{int((n2.result == 'error').sum()):,}"]]
    not_confirmed = ok2[~confirmed]
    return ["## N2. Security placeholders\n", md_table(["Measure", "Packages"], n2_rows),
            "Not confirmed (first 40):\n",
            md_table(["Package", "Version"],
                     [[r.name, r.latest] for r in not_confirmed.head(40).itertuples()])]


def binary_section(n3):
    ok3 = n3[n3.result == "ok"].astype({"os": bool, "cpu": bool})
    ok3["declares"] = ok3["os"] | ok3["cpu"]
    ok3["family"] = ok3["name"].map(family_of)
    fam = ok3.groupby("family").agg(packages=("name", "size"), declares=("declares", "mean"))
    fam = fam.sort_values("packages", ascending=False)
    return [
        "## N3. Platform binaries\n",
        f"Answered: {len(ok3):,}; declare os or cpu: {int(ok3.declares.sum()):,} "
        f"({ok3.declares.mean() * 100:.1f}%). Not found: {int((n3.result == 'not_found').sum()):,}.\n",
        md_table(["Family", "Packages", "Declare os or cpu"],
                 [[f_, f"{int(r.packages):,}", f"{r.declares * 100:.0f}%"]
                  for f_, r in fam.head(40).iterrows()]),
    ]


if __name__ == "__main__":
    phases = {"local": phase_local, "lists": phase_lists, "network": phase_network}
    if len(sys.argv) != 2 or sys.argv[1] not in phases:
        sys.exit("usage: python 07b_post_check.py local|lists|network")
    phases[sys.argv[1]]()