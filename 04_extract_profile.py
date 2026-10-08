#!/usr/bin/env python3
"""
Phase 1 -- Profile extraction over the registry.

MODE = "latest"  -> ~3 KB/pkg, ~3 h, no creation date, no version count
MODE = "full"    -> ~51 KB/pkg, ~37 h, everything

Non-usable packages are classified during the walk and written to
data/profile_problems.jsonl, so no separate filtering pass is needed.

Input : data/pasada2/*.jsonl
Output: data/profile/shard_NNNNN.jsonl   (usable only)
        data/profile_problems.jsonl      (everything else)
State : data/checkpoint_profile.json
"""
import json, os, time, glob, signal, sys
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor

MODE     = "full"          # "latest" or "full"

IN_DIR   = "data/pasada1"
OUT_DIR  = "data/profile"
PROBLEMS = "data/profile_problems.jsonl"
CKPT     = "data/checkpoint_profile.json"
NAMES    = "data/names_sorted.json"

SHARD_N  = 50_000
WORKERS  = 16
PAUSE    = 0.03

os.makedirs(OUT_DIR, exist_ok=True)
HDR = {"User-Agent": "UCN-research/1.0 (jairo.vergara@alumnos.ucn.cl)"}

_stop = False
def _handler(sig, frame):
    global _stop
    if _stop:
        sys.exit(1)
    _stop = True
    print("\n  Ctrl+C -- flushing shard and saving checkpoint...")
signal.signal(signal.SIGINT, _handler)


def load_names():
    """Live package names from phase 1 (feed ingest).

    Phase 1 records use "id" and "deleted"; phase 2 used "name".
    Reading phase 1 directly avoids re-running phase 2 on a new machine,
    since the profile pass already collects dependency data.
    """
    if os.path.exists(NAMES):
        return json.load(open(NAMES, encoding="utf-8"))
    print("Building name list...")
    n = []
    for f in sorted(glob.glob(f"{IN_DIR}/*.jsonl")):
        for line in open(f, encoding="utf-8"):
            d = json.loads(line)
            if not d.get("deleted"):
                n.append(d["id"])
    n.sort()
    json.dump(n, open(NAMES, "w", encoding="utf-8"))
    print(f"  {len(n):,} names cached")
    return n

def load_ckpt():
    if os.path.exists(CKPT):
        c = json.load(open(CKPT))
        c["start"] = time.time()
        return c
    return {"idx": 0, "shard": 0, "mode": MODE,
            "start": time.time(), "began": time.strftime("%Y-%m-%d %H:%M"),
            "counts": {}}


def save_ckpt(c):
    tmp = CKPT + ".tmp"
    json.dump(c, open(tmp, "w"))
    os.replace(tmp, CKPT)


def has_github(repo):
    if not repo:
        return False
    url = repo.get("url", "") if isinstance(repo, dict) else str(repo)
    return "github.com" in url.lower()


def request(url):
    """Returns (doc, status, extra). status 'ok' means doc is valid."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HDR)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r), "ok", None
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None, "gone", e.code          # no retry
            if attempt == 2:
                return None, "http_error", e.code
            time.sleep(1 + attempt * 2)
        except Exception as e:
            if attempt == 2:
                return None, "network_error", str(e)[:60]
            time.sleep(1 + attempt * 2)
    return None, "network_error", "exhausted"


def project(name, v, root=None):
    """Build the output record from a version manifest (+ root doc if full)."""
    dist = v.get("dist") or {}
    src = root if root else v
    kw = src.get("keywords") or v.get("keywords") or []
    if not isinstance(kw, list):
        kw = []
    mt = src.get("maintainers") or v.get("maintainers") or []

    rec = {
        "name":          name,
        "status":        "ok",
        "scoped":        name.startswith("@"),
        "latest":        v.get("version"),
        "n_prod":        len(v.get("dependencies") or {}),
        "n_dev":         len(v.get("devDependencies") or {}),
        "n_peer":        len(v.get("peerDependencies") or {}),
        "n_opt":         len(v.get("optionalDependencies") or {}),
        "peer":          sorted((v.get("peerDependencies") or {}).keys()),
        "opt":           sorted((v.get("optionalDependencies") or {}).keys()),
        "n_maintainers": len(mt) if isinstance(mt, list) else 0,
        "deprecated":    "deprecated" in v,
        "keywords":      kw[:30],
        "n_keywords":    len(kw),
        "has_github":    has_github(src.get("repository") or v.get("repository")),
        "file_count":    dist.get("fileCount"),
        "unpacked":      dist.get("unpackedSize"),
    }

    if root is not None:                       # full mode only
        t = root.get("time") or {}
        rec["created"]    = t.get("created")
        rec["modified"]   = t.get("modified")
        rec["n_versions"] = len(root.get("versions") or {})
    else:
        rec["created"] = rec["modified"] = None
        rec["n_versions"] = None

    return rec


def fetch_latest(name):
    url = ("https://registry.npmjs.org/"
           + urllib.parse.quote(name, safe="@/") + "/latest")
    d, st, extra = request(url)
    if st != "ok":
        return {"name": name, "status": st, "detail": extra}
    if not d or not d.get("version"):
        return {"name": name, "status": "no_latest_tag"}
    return project(name, d)


def fetch_full(name):
    url = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@/")
    d, st, extra = request(url)
    if st != "ok":
        return {"name": name, "status": st, "detail": extra}

    vs = d.get("versions") or {}
    latest = (d.get("dist-tags") or {}).get("latest")
    if not vs:
        return {"name": name, "status": "no_versions"}
    if not latest:
        return {"name": name, "status": "no_latest_tag", "n_versions": len(vs)}
    if latest not in vs:
        return {"name": name, "status": "latest_missing",
                "latest": latest, "n_versions": len(vs)}
    return project(name, vs[latest], root=d)


FETCH = fetch_latest if MODE == "latest" else fetch_full


def work(name):
    time.sleep(PAUSE)
    return FETCH(name)


def flush(buf, shard):
    good = [b for b in buf if b.get("status") == "ok"]
    bad  = [b for b in buf if b.get("status") != "ok"]

    path = f"{OUT_DIR}/shard_{shard:05d}.jsonl"
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for b in good:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    os.replace(tmp, path)

    if bad:
        with open(PROBLEMS, "a", encoding="utf-8") as f:
            for b in bad:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")


def main():
    names = load_names()
    c = load_ckpt()
    total = len(names)

    if c.get("mode") and c["mode"] != MODE:
        print(f"WARNING: checkpoint was written in mode '{c['mode']}', "
              f"now running '{MODE}'. Delete {CKPT} to restart cleanly.")
        return

    print(f"\n{'='*60}")
    print(f"  Mode      : {MODE}")
    print(f"  Total     : {total:,}")
    print(f"  Resuming  : index {c['idx']:,}")
    print(f"  Remaining : {total - c['idx']:,}")
    print(f"  Workers   : {WORKERS}")
    print(f"{'='*60}\n")

    if c["idx"] >= total:
        print("Already complete.")
        return

    buf, shard = [], c["shard"]
    pending = names[c["idx"]:]

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, res in enumerate(pool.map(work, pending), 1):
            buf.append(res)
            st = res.get("status", "unknown")
            c["counts"][st] = c["counts"].get(st, 0) + 1

            if len(buf) >= SHARD_N or _stop:
                flush(buf, shard)
                shard += 1
                c["shard"] = shard
                c["idx"] += len(buf)
                buf = []
                save_ckpt(c)
                if _stop:
                    print(f"  Saved at index {c['idx']:,}. Re-run to continue.")
                    return

            if i % 10_000 == 0:
                done = c["idx"] + len(buf)
                el = time.time() - c["start"]
                rate = i / el
                eta = (total - done) / rate / 3600
                ok = c["counts"].get("ok", 0)
                print(f"  {done:>9,}/{total:,} | {done/total*100:5.1f}% | "
                      f"ok={ok:>9,} | {rate:5.1f}/s | ETA {eta:5.1f}h")

    if buf:
        flush(buf, shard)
        c["shard"] = shard + 1
        c["idx"] += len(buf)
    save_ckpt(c)

    print(f"\n{'='*60}")
    for k, v in sorted(c["counts"].items(), key=lambda x: -x[1]):
        print(f"  {k:<16}: {v:>12,}")
    print(f"  {'shards':<16}: {c['shard']:>12,}")
    print(f"  {'elapsed':<16}: {(time.time()-c['start'])/3600:>12.1f} h")
    print(f"{'='*60}")
    print(f"\n  Usable  -> {OUT_DIR}/")
    print(f"  Problems-> {PROBLEMS}")


if __name__ == "__main__":
    main()