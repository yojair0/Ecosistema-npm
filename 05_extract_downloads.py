#!/usr/bin/env python3
"""
Pass 5 -- Download counts for every package in the index.

The bulk endpoint accepts up to 128 packages per request but rejects scoped
names ("scoped packages are not currently supported in bulk lookups",
verified 2026-10-07), so scoped packages are fetched individually. With
38.7% of the registry scoped, that split dominates the runtime.

Each period costs a full walk: roughly 21,000 batched requests for plain
names plus 1.7 million individual requests for scoped ones, around 10 hours.
PERIODS defaults to one window for that reason; adding more multiplies the
cost linearly. The three windows are expected to correlate above 0.95, so
one suffices for the correlation analysis, and the redundancy can be shown
on a subsample.

Input : data/pasada1/*.jsonl
Output: data/downloads/shard_NNNNN.jsonl
        data/downloads_problems.jsonl
        data/downloads_run_meta.json
State : data/checkpoint_downloads.json  (resumable, Ctrl+C once)
"""
import json
import os
import signal
import sys
import time
import glob
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from config import (SNAPSHOT_SEQ, SNAPSHOT_DATE, NAMES_CACHE,
                    DIR_INDEX, DIR_DOWNLOAD, USER_AGENT)

PERIODS  = ["last-month"]      # add "last-week", "last-year" at ~10 h each

OUT_DIR  = DIR_DOWNLOAD
PROBLEMS = "data/downloads_problems.jsonl"
CKPT     = "data/checkpoint_downloads.json"
META     = "data/downloads_run_meta.json"

BATCH    = 128                 # bulk endpoint limit
SHARD_N  = 50_000
WORKERS  = 12                  # lower than the registry passes: this API
PAUSE    = 0.05                # is stricter about request rate

HDR = {"User-Agent": USER_AGENT}
BASE = "https://api.npmjs.org/downloads/point"

_stop = False


def _handler(sig, frame):
    global _stop
    if _stop:
        sys.exit(1)
    _stop = True
    print("\n  Ctrl+C -- flushing shard and saving checkpoint...")


def norm(name):
    return name.strip().lower()


def load_names():
    """Same cache and same sort order as pass 04, so indices are comparable."""
    if os.path.exists(NAMES_CACHE):
        with open(NAMES_CACHE, encoding="utf-8") as f:
            return json.load(f)

    print("Building name list...")
    names = []
    for path in sorted(glob.glob(f"{DIR_INDEX}/*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if not rec.get("deleted"):
                    names.append(rec["id"])
    names.sort()

    with open(NAMES_CACHE, "w", encoding="utf-8") as f:
        json.dump(names, f)
    print(f"  {len(names):,} names cached in {NAMES_CACHE}")
    return names


def load_ckpt():
    if os.path.exists(CKPT):
        with open(CKPT) as f:
            c = json.load(f)
        c["start"] = time.time()
        return c
    return {
        "plain_idx": 0,
        "scoped_idx": 0,
        "shard": 0,
        "periods": PERIODS,
        "start": time.time(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "counts": {},
    }


def save_ckpt(c):
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(c, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, CKPT)


def save_meta(c, finished):
    meta = {
        "snapshot_seq": SNAPSHOT_SEQ,
        "snapshot_date": SNAPSHOT_DATE,
        "periods": PERIODS,
        "started_at": c.get("started_at"),
        "finished_at": finished,
        "plain_done": c["plain_idx"],
        "scoped_done": c["scoped_idx"],
        "counts": c["counts"],
        "shards": c["shard"],
    }
    tmp = META + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, META)


def get(url, timeout=25):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r), "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "no_data"       # package has no download record
            if attempt == 2:
                return None, f"http_{e.code}"
            time.sleep(2 + attempt * 3)
        except Exception:
            if attempt == 2:
                return None, "network_error"
            time.sleep(2 + attempt * 3)
    return None, "network_error"


def fetch_batch(batch):
    """Plain names, up to BATCH per request, one request per period."""
    out = {n: {"name": norm(n), "_status": "ok"} for n in batch}
    for period in PERIODS:
        url = f"{BASE}/{period}/" + ",".join(batch)
        doc, status = get(url)
        if status != "ok" or not doc:
            for n in batch:
                out[n]["_status"] = status
            continue
        key = period.replace("last-", "dl_")
        for n in batch:
            entry = doc.get(n)
            out[n][key] = entry.get("downloads") if entry else None
        time.sleep(PAUSE)
    return list(out.values())


def fetch_one(name):
    """Scoped names, individually, one request per period."""
    rec = {"name": norm(name), "_status": "ok"}
    for period in PERIODS:
        url = f"{BASE}/{period}/" + urllib.parse.quote(name, safe="@/")
        doc, status = get(url)
        key = period.replace("last-", "dl_")
        if status != "ok" or not doc:
            rec["_status"] = status
            rec[key] = None
        else:
            rec[key] = doc.get("downloads")
        time.sleep(PAUSE)
    return rec


def flush(buf, shard):
    good, bad = [], []
    for rec in buf:
        if rec.pop("_status", None) == "ok":
            good.append(rec)
        else:
            bad.append(rec)

    if good:
        path = f"{OUT_DIR}/shard_{shard:05d}.jsonl"
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for rec in good:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, path)

    if bad:
        with open(PROBLEMS, "a", encoding="utf-8") as f:
            for rec in bad:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_stage(items, worker, c, idx_key, shard_ref, label):
    """Walk one stage (plain or scoped), flushing shards as it goes."""
    buf = []
    pending = items[c[idx_key]:]
    if not pending:
        print(f"  {label}: already complete")
        return shard_ref[0]

    print(f"  {label}: {len(pending):,} remaining")
    unit = BATCH if label == "plain" else 1

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, result in enumerate(pool.map(worker, pending), 1):
            records = result if isinstance(result, list) else [result]
            buf.extend(records)
            for rec in records:
                st = rec.get("_status", "unknown")
                c["counts"][st] = c["counts"].get(st, 0) + 1

            if len(buf) >= SHARD_N or _stop:
                flush(buf, shard_ref[0])
                shard_ref[0] += 1
                c["shard"] = shard_ref[0]
                c[idx_key] += i * unit if label == "plain" else len(buf)
                buf = []
                save_ckpt(c)
                if _stop:
                    save_meta(c, None)
                    print(f"  Saved. Re-run to continue.")
                    sys.exit(0)

            if i % 2_000 == 0:
                rate = i / (time.time() - c["start"])
                print(f"    {label} {i:>8,}/{len(pending):,} | {rate:5.1f}/s")

    if buf:
        flush(buf, shard_ref[0])
        shard_ref[0] += 1
        c["shard"] = shard_ref[0]
        c[idx_key] = len(items)
        save_ckpt(c)
    return shard_ref[0]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    signal.signal(signal.SIGINT, _handler)

    names = load_names()
    c = load_ckpt()

    if c.get("periods") and c["periods"] != PERIODS:
        print(f"WARNING: checkpoint used periods {c['periods']}, "
              f"now running {PERIODS}. Delete {CKPT} to restart cleanly.")
        return

    plain = [n for n in names if not n.startswith("@")]
    scoped = [n for n in names if n.startswith("@")]
    batches = [plain[i:i + BATCH] for i in range(0, len(plain), BATCH)]

    print(f"\n{'=' * 60}")
    print(f"  Periods : {', '.join(PERIODS)}")
    print(f"  Plain   : {len(plain):,} in {len(batches):,} batches")
    print(f"  Scoped  : {len(scoped):,} individual")
    print(f"  Workers : {WORKERS}")
    print(f"{'=' * 60}\n")

    shard_ref = [c["shard"]]
    batch_idx = c["plain_idx"] // BATCH
    c["plain_idx"] = batch_idx * BATCH

    shard_ref[0] = run_stage(batches, fetch_batch, c,
                             "plain_idx", shard_ref, "plain")
    shard_ref[0] = run_stage(scoped, fetch_one, c,
                             "scoped_idx", shard_ref, "scoped")

    save_meta(c, time.strftime("%Y-%m-%dT%H:%M:%S%z"))

    print(f"\n{'=' * 60}")
    for k, v in sorted(c["counts"].items(), key=lambda x: -x[1]):
        print(f"  {k:<16}: {v:>12,}")
    print(f"  {'shards':<16}: {c['shard']:>12,}")
    print(f"  {'elapsed':<16}: {(time.time() - c['start']) / 3600:>12.1f} h")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()