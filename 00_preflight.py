#!/usr/bin/env python3
"""Pre-flight checks. Run before the long extraction."""
import json, time, urllib.request, urllib.parse

HDR = {"User-Agent": "UCN-research/1.0 (jairo.vergara@alumnos.ucn.cl)"}
PKGS = ["express", "@babel/parser", "lodash", "is-odd", "left-pad"]
FIELDS = ["time", "keywords", "maintainers", "versions", "dist-tags"]


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


print("=" * 62)
print("1. FULL METADATA FORMAT")
print("=" * 62)
for p in PKGS:
    url = "https://registry.npmjs.org/" + urllib.parse.quote(p, safe="@/")
    try:
        d = get(url)
        latest = d["dist-tags"]["latest"]
        v = d["versions"][latest]
        missing = [f for f in FIELDS if f not in d]
        print(f"  {p[:22]:24} versions={len(d['versions']):>4} "
              f"keywords={len(d.get('keywords') or []):>2} "
              f"maintainers={len(d.get('maintainers') or []):>2} "
              f"deprecated={'deprecated' in v}")
        if missing:
            print(f"      MISSING: {missing}")
    except Exception as e:
        print(f"  {p[:22]:24} ERROR: {e}")

print()
print("=" * 62)
print("2. DOWNLOADS ENDPOINTS")
print("=" * 62)
for period in ["last-week", "last-month", "last-year"]:
    url = f"https://api.npmjs.org/downloads/point/{period}/express"
    try:
        d = get(url, 15)
        print(f"  {period:<12} OK  -> {d.get('downloads'):,}")
    except Exception as e:
        print(f"  {period:<12} FAIL: {e}")

print()
print("  bulk (no scope):", end=" ")
try:
    d = get("https://api.npmjs.org/downloads/point/last-month/express,lodash,axios", 15)
    print(f"OK  -> {len(d)} packages")
except Exception as e:
    print(f"FAIL: {e}")

print("  bulk (scoped)  :", end=" ")
try:
    d = get("https://api.npmjs.org/downloads/point/last-month/@babel/parser,express", 15)
    print(f"OK  -> {len(d)}")
except Exception as e:
    print(f"EXPECTED FAIL: {str(e)[:50]}")

print()
print("=" * 62)
print("3. THROUGHPUT ESTIMATE (full format, 30 packages)")
print("=" * 62)
import glob
names = []
for f in sorted(glob.glob("data/pasada2/*.jsonl"))[:1]:
    for line in open(f, encoding="utf-8"):
        d = json.loads(line)
        if "error" not in d:
            names.append(d["name"])
        if len(names) >= 30:
            break

t0 = time.time()
ok = 0
total_bytes = 0
for n in names:
    try:
        url = "https://registry.npmjs.org/" + urllib.parse.quote(n, safe="@/")
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            total_bytes += len(raw)
        ok += 1
    except Exception:
        pass

dt = time.time() - t0
rate = ok / dt
print(f"  {ok}/30 OK | {rate:.1f} pkg/s (1 thread) | "
      f"avg {total_bytes/max(ok,1)/1024:.0f} KB/pkg")
print(f"  With 16 workers: ~{rate*16:.0f} pkg/s")
print(f"  4,394,970 packages -> ~{4394970/(rate*16)/3600:.1f} hours")
print(f"  Estimated disk: ~{4394970*0.4/1024:.1f} GB (projected JSONL)")
print("=" * 62)