#!/usr/bin/env python3
"""
Pass 5 -- Download counts for every package in the reference list.

A single range request (last-year, daily series) yields the 7-, 30- and
365-day totals at once, instead of one point request per window.

The bulk endpoint accepts up to 128 names but rejects scoped ones, so plain
names go in batches and scoped names one by one; scoped packages dominate
the runtime. Work is split into ordered units (one batch, or one scoped
name) and the checkpoint stores how many units are complete, so a resumed
run neither skips nor repeats packages.

Input : data/names_sept18.json          reference list, 4,405,737 names
Output: data/downloads/shard_NNNNN.jsonl
        data/downloads_problems.jsonl   with the reason for each package
        data/downloads_run_meta.json
State : data/checkpoint_downloads.json  resumable, Ctrl+C once
"""
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    from config import USER_AGENT
except ImportError:
    USER_AGENT = "UCN-research/1.0 (+https://github.com/yojair0/Ecosistema-npm)"

NAMES    = "data/names_sept18.json"
OUT_DIR  = "data/downloads"
PROBLEMS = "data/downloads_problems.jsonl"
CKPT     = "data/checkpoint_downloads.json"
META     = "data/downloads_run_meta.json"

BASE     = "https://api.npmjs.org/downloads/range/last-year"
BATCH    = 128       # bulk endpoint limit
CHUNK    = 2_000     # units in flight at once; bounds memory and Ctrl+C delay
SHARD_N  = 50_000
WORKERS  = 12
PAUSE    = 0.05

HDR = {"User-Agent": USER_AGENT}
RANGE = {}           # first and last day of the series, for the metadata
_stop = False


def _handler(sig, frame):
    global _stop
    if _stop:
        sys.exit(1)
    _stop = True
    print("\n  Ctrl+C -- finishing current units and saving...", flush=True)


def norm(name):
    return name.strip().lower()


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def atomic_json(path, obj, indent=None):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def build_units(names):
    plain = [n for n in names if not n.startswith("@")]
    scoped = [n for n in names if n.startswith("@")]
    units = [plain[i:i + BATCH] for i in range(0, len(plain), BATCH)]
    return units + [[n] for n in scoped], len(plain), len(scoped)


def get(url):
    """Returns (doc, status). Backs off on 429 instead of failing."""
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "no_data"
            if e.code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            if attempt == 4:
                return None, f"http_{e.code}"
        except Exception:
            if attempt == 4:
                return None, "network_error"
        time.sleep(2 + attempt * 3)
    return None, "rate_limited"


def totals(entry):
    days = sorted(entry.get("downloads") or [], key=lambda d: d.get("day", ""))
    if days and not RANGE:
        RANGE.update(start=days[0].get("day"), end=days[-1].get("day"))
    counts = [d.get("downloads") or 0 for d in days]
    return {"dl_7d": sum(counts[-7:]),
            "dl_30d": sum(counts[-30:]),
            "dl_365d": sum(counts)}


def fetch_unit(unit):
    time.sleep(PAUSE)
    try:
        if len(unit) == 1:
            name = unit[0]
            doc, status = get(f"{BASE}/{urllib.parse.quote(name, safe='@/')}")
            if status != "ok" or not isinstance(doc, dict) or "downloads" not in doc:
                reason = status if status != "ok" else "no_data"
                return [{"name": norm(name), "_status": reason}]
            return [{"name": norm(name), **totals(doc), "_status": "ok"}]

        url = f"{BASE}/" + ",".join(urllib.parse.quote(n, safe="@/") for n in unit)
        doc, status = get(url)
        if status != "ok" or not isinstance(doc, dict) or "error" in doc:
            reason = status if status != "ok" else "api_error"
            return [{"name": norm(n), "_status": reason} for n in unit]
        by_name = {k.lower(): v for k, v in doc.items() if isinstance(v, dict)}
        out = []
        for n in unit:
            entry = by_name.get(n.lower())
            if entry and "downloads" in entry:
                out.append({"name": norm(n), **totals(entry), "_status": "ok"})
            else:
                out.append({"name": norm(n), "_status": "no_data"})
        return out
    except Exception as e:
        detail = f"{type(e).__name__}: {str(e)[:60]}"
        return [{"name": norm(n), "_status": "parse_error", "detail": detail}
                for n in unit]


def flush(buf, shard):
    """Usable records to the shard; the rest to the problems file, with reason."""
    good, bad = [], []
    for rec in buf:
        status = rec.pop("_status", None)
        if status == "ok":
            good.append(rec)
        else:
            rec["status"] = status
            bad.append(rec)
    if good:
        path = f"{OUT_DIR}/shard_{shard:05d}.jsonl"
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            for rec in good:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(path + ".tmp", path)
    if bad:
        with open(PROBLEMS, "a", encoding="utf-8") as f:
            for rec in bad:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    signal.signal(signal.SIGINT, _handler)

    if not os.path.exists(NAMES):
        raise SystemExit(f"Missing {NAMES}. The reference list is required.")
    with open(NAMES, encoding="utf-8") as f:
        names = json.load(f)
    units, n_plain, n_scoped = build_units(names)
    n_batches = (n_plain + BATCH - 1) // BATCH

    if os.path.exists(CKPT):
        with open(CKPT, encoding="utf-8") as f:
            c = json.load(f)
    else:
        c = {"unit_idx": 0, "shard": 0, "started_at": stamp(), "counts": {}}
    if c.get("n_units", len(units)) != len(units):
        raise SystemExit(f"{CKPT} comes from a different list. Delete it to restart.")
    c["n_units"] = len(units)

    def save():
        if RANGE:
            c["range"] = dict(RANGE)
        atomic_json(CKPT, c)

    def save_meta(finished):
        atomic_json(META, {
            "source": BASE,
            "windows": {"dl_7d": "last 7 days", "dl_30d": "last 30 days",
                        "dl_365d": "last 365 days"},
            "range": c.get("range"),
            "names": len(names),
            "started_at": c.get("started_at"),
            "finished_at": finished,
            "units_done": c["unit_idx"],
            "counts": c["counts"],
            "shards": c["shard"],
        }, indent=2)

    idx = c["unit_idx"]
    print("=" * 60)
    print(f"  Names    : {len(names):,}")
    print(f"  Plain    : {n_plain:,} in {n_batches:,} batches")
    print(f"  Scoped   : {n_scoped:,} individual requests")
    print(f"  Resuming : unit {idx:,} of {len(units):,}")
    print("=" * 60, flush=True)

    buf, shard = [], c["shard"]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        while idx < len(units) and not _stop:
            t_chunk, consumed = time.time(), 0
            for records in pool.map(fetch_unit, units[idx:idx + CHUNK]):
                consumed += 1
                buf.extend(records)
                for r in records:
                    st = r["_status"]
                    c["counts"][st] = c["counts"].get(st, 0) + 1
                if len(buf) >= SHARD_N or _stop:
                    if buf:
                        flush(buf, shard)
                        shard += 1
                        buf = []
                    c.update(unit_idx=idx + consumed, shard=shard)
                    save()
                    if _stop:
                        break
            idx += consumed
            rate = consumed / max(time.time() - t_chunk, 1e-6)
            eta = ("plain phase" if idx <= n_batches
                   else f"ETA {(len(units) - idx) / rate / 3600:4.1f} h")
            ok = c["counts"].get("ok", 0)
            print(f"  unit {idx:>9,}/{len(units):,} | ok={ok:>9,} | "
                  f"{rate:6.1f} u/s | {eta}", flush=True)

    if buf:
        flush(buf, shard)
        shard += 1
    c.update(unit_idx=idx, shard=shard)
    save()
    finished = stamp() if idx >= len(units) else None
    save_meta(finished)

    print("=" * 60)
    for k, v in sorted(c["counts"].items(), key=lambda x: -x[1]):
        print(f"  {k:<14}: {v:>12,}")
    print(f"  {'shards':<14}: {shard:>12,}")
    print("  Complete." if finished else f"  Stopped at unit {idx:,}. Re-run to continue.")
    print("=" * 60)


if __name__ == "__main__":
    main()