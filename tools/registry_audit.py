#!/usr/bin/env python3
"""
Registry audit on a seeded random sample of the reference list.

Fetches the full registry document of each sampled package and answers
three questions, with criteria fixed before looking at the results:

  A. Does `modified` reflect publishing activity? It is compared with the
     date of the most recent version. If most packages last modified in
     April-June 2022 show a gap above 30 days, `modified` there records
     registry-side changes rather than releases.
  B. Do a few accounts publish a large share of the registry? Publisher of
     the latest version, with a 95% interval. Any account above 0.5% of the
     registry is investigated.
  C. Which accounts concentrate each creation year, and how much flagged
     spam they hold.

Only account names are kept; e-mail addresses are never stored. The fetch
runs once; later runs reuse the saved sample and only rebuild the report.

Input : data/names_sorted.json             reference list, 2026-09-18
        data/07_strata_analysis/strata_table.parquet  optional, for spam flags
Output: data/audit_sample.jsonl
        data/07_strata_analysis/audit_report.md
"""
import json
import math
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

NAMES = "data/names_sorted.json"
STRATA = "data/07_strata_analysis/strata_table.parquet"
OUT_JSONL = "data/audit_sample.jsonl"
OUT_MD = "data/07_strata_analysis/audit_report.md"
N_SAMPLE = 10_000
SEED = 42
WORKERS = 16
POPULATION = 4_405_737
GAP_DAYS = 30
PUBLISHER_SHARE = 0.005
HDR = {"User-Agent": "UCN-research/1.0 (+https://github.com/yojair0/Ecosistema-npm)",
       "Accept": "application/json"}


def fetch(name):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@")
    doc = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=60) as r:
                doc = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"name": name, "status": "gone"}
            if attempt == 2:
                return {"name": name, "status": f"http_{e.code}"}
        except Exception:
            if attempt == 2:
                return {"name": name, "status": "network_error"}
        time.sleep(2 + attempt * 3)

    versions = doc.get("versions") or {}
    if not versions:
        return {"name": name, "status": "no_versions"}
    t = doc.get("time") or {}
    latest = (doc.get("dist-tags") or {}).get("latest")
    publish_times = [v for k, v in t.items() if k in versions and isinstance(v, str)]
    user = (versions.get(latest) or {}).get("_npmUser")
    return {
        "name": name,
        "status": "ok",
        "created": t.get("created"),
        "modified": t.get("modified"),
        "last_publish": max(publish_times) if publish_times else None,
        "publisher": user.get("name") if isinstance(user, dict) else None,
        "maintainers": [m.get("name") for m in doc.get("maintainers") or []
                        if isinstance(m, dict)],
        "n_versions": len(versions),
    }


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def interval(k, n):
    p = k / n
    h = 1.96 * math.sqrt(p * (1 - p) / n)
    return p, max(p - h, 0.0), p + h


def report(df):
    lines = []
    w = lines.append
    ok = df[df["status"] == "ok"].copy()
    n = len(ok)

    w("# Registry audit\n")
    w(f"Seeded random sample (seed {SEED}) of {len(df):,} packages from the "
      f"reference list of {POPULATION:,}. Usable records: {n:,}.\n")
    w(table(["Status", "Packages"],
            [[k, f"{v:,}"] for k, v in df["status"].value_counts().items()]))

    for c in ("created", "modified", "last_publish"):
        ok[c] = pd.to_datetime(ok[c], utc=True, errors="coerce")
    ok["gap_days"] = (ok["modified"] - ok["last_publish"]).dt.days
    window = ok["modified"].between(pd.Timestamp("2022-04-01", tz="UTC"),
                                    pd.Timestamp("2022-07-01", tz="UTC"),
                                    inclusive="left")

    spam_known = os.path.exists(STRATA)
    if spam_known:
        st = pd.read_parquet(STRATA, columns=["package", "spam_suspect",
                                              "spam_propagated"])
        flag = dict(zip(st["package"], st["spam_suspect"] | st["spam_propagated"]))
        ok["spam"] = ok["name"].str.strip().str.lower().map(flag)

    # ---------------------------------------------------------------- A
    w("## A. Does `modified` reflect publishing?\n")
    w(f"Gap: days between the last modification and the most recent version. "
      f"Criterion fixed in advance: if most packages modified in April-June "
      f"2022 show a gap above {GAP_DAYS} days, `modified` there records "
      f"registry-side changes rather than releases.\n")
    rows = []
    for label, m in [("modified April-June 2022", window),
                     ("modified at any other time", ~window)]:
        g = ok.loc[m, "gap_days"].dropna()
        rows.append([label, f"{len(g):,}",
                     f"{(g > GAP_DAYS).mean() * 100:.1f}%",
                     f"{g.median():,.0f}"])
    w(table(["Group", "n", f"gap > {GAP_DAYS} days", "median gap (days)"], rows))
    share = (ok.loc[window, "gap_days"].dropna() > GAP_DAYS).mean()
    w("Criterion **met**: in that window `modified` does not reflect "
      "releases; the date of the last version is the alternative.\n"
      if share > 0.5 else
      "Criterion **not met**: `modified` cannot be discarded on this basis.\n")

    # ---------------------------------------------------------------- B
    w("## B. Publisher concentration\n")
    w(f"Publisher: account that published the latest version. Estimated "
      f"packages: share of the sample times the reference list, with a 95% "
      f"interval. Criterion fixed in advance: any account above "
      f"{PUBLISHER_SHARE:.1%} of the registry is investigated.\n")
    counts = ok["publisher"].value_counts()
    rows = []
    for pub, k in counts.head(20).items():
        p, lo, hi = interval(k, n)
        row = [pub, k, f"{p * 100:.2f}%",
               f"{lo * POPULATION:,.0f} – {hi * POPULATION:,.0f}"]
        if spam_known:
            row.append(f"{ok.loc[ok['publisher'] == pub, 'spam'].mean() * 100:.0f}%")
        rows.append(row)
    header = ["Publisher", "in sample", "share", "estimated packages (95%)"]
    w(table(header + (["flagged spam"] if spam_known else []), rows))
    above = int((counts / n > PUBLISHER_SHARE).sum())
    w(f"Top 20 accounts publish {counts.head(20).sum() / n * 100:.1f}% of the "
      f"sample. Accounts above {PUBLISHER_SHARE:.1%}: **{above}**.\n")

    # ---------------------------------------------------------------- C
    w("## C. Creation year\n")
    ok["year"] = ok["created"].dt.year
    rows = []
    for yr, g in ok.dropna(subset=["year"]).groupby("year"):
        top = g["publisher"].value_counts().head(5)
        row = [int(yr), f"{len(g):,}", f"{top.sum() / len(g) * 100:.1f}%",
               ", ".join(f"{p} ({c})" for p, c in top.head(3).items())]
        if spam_known:
            row.append(f"{g['spam'].mean() * 100:.1f}%")
        rows.append(row)
    header = ["Year", "n", "share of top 5 accounts", "top 3 accounts"]
    w(table(header + (["flagged spam"] if spam_known else []), rows))

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {OUT_MD}")


def main():
    if os.path.exists(OUT_JSONL):
        print(f"Reusing {OUT_JSONL}")
        df = pd.read_json(OUT_JSONL, lines=True)
    else:
        with open(NAMES, encoding="utf-8") as f:
            names = json.load(f)
        sample = random.Random(SEED).sample(names, N_SAMPLE)
        rows = []
        with ThreadPoolExecutor(WORKERS) as pool:
            for i, rec in enumerate(pool.map(fetch, sample), 1):
                rows.append(rec)
                if i % 1000 == 0:
                    print(f"  {i:,}/{N_SAMPLE:,}", flush=True)
        with open(OUT_JSONL, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        df = pd.DataFrame(rows)
    os.makedirs("data/07_strata_analysis", exist_ok=True)
    report(df)


if __name__ == "__main__":
    main()