#!/usr/bin/env python3
"""
Pass 4 -- Package profile extraction over the whole registry.

MODE = "full"    ~51 KB/pkg. Includes creation date, modification date and
                 version count. Required for the age analysis.
MODE = "latest"  ~3 KB/pkg. Much faster, but creation date and version count
                 are unavailable, so the age confounder cannot be measured.

Packages that cannot be profiled are classified during the walk and written
to a separate file, so no later filtering pass is needed.

Input : data/pasada1/*.jsonl          (id, seq, deleted)
Output: data/profile/shard_NNNNN.jsonl
        data/profile_problems.jsonl
        data/profile_run_meta.json
State : data/checkpoint_profile.json  (resumable, Ctrl+C once)
"""
import json
import os
import re
import signal
import sys
import time
import glob
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from config import (SNAPSHOT_SEQ, SNAPSHOT_DATE, NAMES_CACHE,
                    DIR_INDEX, USER_AGENT)

MODE     = "full"

IN_DIR   = DIR_INDEX
OUT_DIR  = "data/profile"
PROBLEMS = "data/profile_problems.jsonl"
CKPT     = "data/checkpoint_profile.json"
META     = "data/profile_run_meta.json"

SHARD_N  = 50_000
WORKERS  = 16
PAUSE    = 0.03

HDR = {"User-Agent": USER_AGENT}

# npm shorthand that resolves to GitHub: "user/repo" with no host.
_SHORTHAND = re.compile(r"^[\w.-]+/[\w.-]+$")

_stop = False


def _handler(sig, frame):
    global _stop
    if _stop:
        sys.exit(1)
    _stop = True
    print("\n  Ctrl+C -- flushing shard and saving checkpoint...")


def norm(name):
    """Same normalisation as the graph pass, so tables join correctly."""
    return name.strip().lower()


def load_names():
    """Live package names from the registry index pass.

    Index records use "id" and "deleted". The sorted order is what makes
    the checkpoint index meaningful across runs, so it must stay stable.
    """
    if os.path.exists(NAMES_CACHE):
        with open(NAMES_CACHE, encoding="utf-8") as f:
            cached = json.load(f)
        if cached:                      # an empty cache means a failed run
            return cached
        print("  Name cache is empty, rebuilding...")

    print("Building name list...")
    names = []
    for path in sorted(glob.glob(f"{IN_DIR}/*.jsonl")):
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
        "idx": 0,
        "shard": 0,
        "mode": MODE,
        "start": time.time(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "counts": {},
    }


def save_ckpt(c):
    """Atomic write with fsync.

    Without the fsync, os.replace can run before the buffer reaches disk,
    which on a multi-hour walk means losing the resume index.
    """
    tmp = CKPT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(c, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, CKPT)


def save_meta(c, finished):
    """Run metadata for the paper: when the data was actually collected."""
    meta = {
        "snapshot_seq": SNAPSHOT_SEQ,
        "snapshot_date": SNAPSHOT_DATE,
        "mode": MODE,
        "started_at": c.get("started_at"),
        "finished_at": finished,
        "packages_processed": c["idx"],
        "counts": c["counts"],
        "shards": c["shard"],
    }
    tmp = META + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, META)


def has_github(repo):
    """True for every form npm accepts that resolves to GitHub.

    Recognised: full URLs containing github.com, the "github:user/repo"
    prefix, and the bare "user/repo" shorthand, which npm resolves to
    GitHub by default. Explicit gitlab: or bitbucket: prefixes are not.
    """
    if not repo:
        return False
    url = repo.get("url", "") if isinstance(repo, dict) else str(repo)
    url = url.strip()
    if not url:
        return False

    low = url.lower()
    if low.startswith(("gitlab:", "bitbucket:", "gist:")):
        return False
    if "github.com" in low:
        return True
    if low.startswith("github:"):
        return True
    return bool(_SHORTHAND.match(url))


def request(url):
    """Returns (doc, status, detail). Status 'ok' means doc is usable."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r), "ok", None
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None, "gone", e.code       # permanent, no retry
            if attempt == 2:
                return None, "http_error", e.code
            time.sleep(1 + attempt * 2)
        except Exception as e:
            if attempt == 2:
                return None, "network_error", str(e)[:60]
            time.sleep(1 + attempt * 2)
    return None, "network_error", "exhausted"


def project(name, v, root=None):
    """Build the output record.

    Dependency counts for prod and dev are deliberately omitted: the graph
    pass already derives them as fan-out from the dependency lists, measured
    on the same snapshot. Peer and optional edge lists are kept because
    fan-in for those types cannot be derived from counts alone.
    """
    dist = v.get("dist") or {}
    src = root if root is not None else v

    kw = src.get("keywords") or v.get("keywords") or []
    if not isinstance(kw, list):
        kw = []

    mt = src.get("maintainers") or v.get("maintainers") or []

    rec = {
        "name":          norm(name),
        "latest":        v.get("version"),
        "n_peer":        len(v.get("peerDependencies") or {}),
        "n_opt":         len(v.get("optionalDependencies") or {}),
        "peer":          sorted(norm(k) for k in (v.get("peerDependencies") or {})),
        "opt":           sorted(norm(k) for k in (v.get("optionalDependencies") or {})),
        "n_maintainers": len(mt) if isinstance(mt, list) else 0,
        # Truthy only: npm un-deprecates by setting an empty string, so the
        # key alone is not enough to call a package deprecated.
        "deprecated":    bool(v.get("deprecated")),
        "keywords":      kw[:30],
        "n_keywords":    len(kw),
        "has_github":    has_github(src.get("repository") or v.get("repository")),
        "file_count":    dist.get("fileCount"),
        "unpacked":      dist.get("unpackedSize"),
    }

    if root is not None:
        t = root.get("time") or {}
        rec["created"]    = t.get("created")
        rec["modified"]   = t.get("modified")
        rec["n_versions"] = len(root.get("versions") or {})
    else:
        rec["created"] = None
        rec["modified"] = None
        rec["n_versions"] = None

    rec["_status"] = "ok"      # routing only, stripped before writing
    return rec


def fetch_latest(name):
    url = ("https://registry.npmjs.org/"
           + urllib.parse.quote(name, safe="@/") + "/latest")
    doc, status, detail = request(url)
    if status != "ok":
        return {"name": name, "_status": status, "detail": detail}
    if not doc or not doc.get("version"):
        return {"name": name, "_status": "no_latest_tag"}
    return project(name, doc)


def fetch_full(name):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@/")
    doc, status, detail = request(url)
    if status != "ok":
        return {"name": name, "_status": status, "detail": detail}

    versions = doc.get("versions") or {}
    latest = (doc.get("dist-tags") or {}).get("latest")
    if not versions:
        return {"name": name, "_status": "no_versions"}
    if not latest:
        return {"name": name, "_status": "no_latest_tag",
                "n_versions": len(versions)}
    if latest not in versions:
        return {"name": name, "_status": "latest_missing",
                "latest": latest, "n_versions": len(versions)}
    return project(name, versions[latest], root=doc)


FETCH = fetch_latest if MODE == "latest" else fetch_full


def work(name):
    time.sleep(PAUSE)
    return FETCH(name)


def flush(buf, shard):
    """Usable records go to the shard, everything else to the problems file."""
    good, bad = [], []
    for rec in buf:
        if rec.pop("_status", None) == "ok":
            good.append(rec)
        else:
            bad.append(rec)

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


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    signal.signal(signal.SIGINT, _handler)

    names = load_names()
    c = load_ckpt()
    total = len(names)

    if c.get("mode") and c["mode"] != MODE:
        print(f"WARNING: checkpoint was written in mode '{c['mode']}', "
              f"now running '{MODE}'. Delete {CKPT} to restart cleanly.")
        return

    print(f"\n{'=' * 60}")
    print(f"  Mode      : {MODE}")
    print(f"  Total     : {total:,}")
    print(f"  Resuming  : index {c['idx']:,}")
    print(f"  Remaining : {total - c['idx']:,}")
    print(f"  Workers   : {WORKERS}")
    print(f"{'=' * 60}\n")

    if c["idx"] >= total:
        print("Already complete.")
        return

    buf, shard = [], c["shard"]
    pending = names[c["idx"]:]

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, rec in enumerate(pool.map(work, pending), 1):
            buf.append(rec)
            st = rec.get("_status", "unknown")
            c["counts"][st] = c["counts"].get(st, 0) + 1

            if len(buf) >= SHARD_N or _stop:
                flush(buf, shard)
                shard += 1
                c["shard"] = shard
                c["idx"] += len(buf)
                buf = []
                save_ckpt(c)
                if _stop:
                    save_meta(c, None)
                    print(f"  Saved at index {c['idx']:,}. Re-run to continue.")
                    return

            if i % 10_000 == 0:
                done = c["idx"] + len(buf)
                rate = i / (time.time() - c["start"])
                eta = (total - done) / rate / 3600
                ok = c["counts"].get("ok", 0)
                print(f"  {done:>9,}/{total:,} | {done / total * 100:5.1f}% | "
                      f"ok={ok:>9,} | {rate:5.1f}/s | ETA {eta:5.1f}h")

    if buf:
        flush(buf, shard)
        c["shard"] = shard + 1
        c["idx"] += len(buf)
    save_ckpt(c)
    save_meta(c, time.strftime("%Y-%m-%dT%H:%M:%S%z"))

    print(f"\n{'=' * 60}")
    for k, v in sorted(c["counts"].items(), key=lambda x: -x[1]):
        print(f"  {k:<16}: {v:>12,}")
    print(f"  {'shards':<16}: {c['shard']:>12,}")
    print(f"  {'elapsed':<16}: {(time.time() - c['start']) / 3600:>12.1f} h")
    print(f"{'=' * 60}")
    print(f"\n  Usable   -> {OUT_DIR}/")
    print(f"  Problems -> {PROBLEMS}")
    print(f"  Run meta -> {META}")


if __name__ == "__main__":
    main()