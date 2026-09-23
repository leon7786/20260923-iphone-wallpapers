#!/usr/bin/env python3
"""Same resumable range downloader as chunk_dl2, but runs 3 files in parallel
(each file still fetched sequentially in 2 MB ranges)."""
import os, re, json, time, zipfile
import concurrent.futures as cf
from chunk_dl2 import fetch, ZIPS, BASE

assets = json.load(open(os.path.join(BASE, "recon/assets.json")))


def is_broken(f):
    p = os.path.join(ZIPS, f)
    try:
        with zipfile.ZipFile(p) as zf:
            return zf.testzip() is not None
    except Exception:
        return True


broken = [f for f in sorted(os.listdir(ZIPS)) if is_broken(f)]
print(f"broken: {len(broken)}", flush=True)


def job(f):
    aid = re.match(r"^(\d+)-", f).group(1)
    idx = int(re.search(r"-(\d+)\.zip$", f).group(1))
    url = assets[aid]["zips"][idx]
    p = os.path.join(ZIPS, f)
    t0 = time.time()
    ok, why, sz, exp = fetch(url, p)
    good = False
    if ok:
        try:
            with zipfile.ZipFile(p) as zf:
                good = zf.testzip() is None
        except Exception as e:
            why = type(e).__name__
    return f"{'OK  ' if good else 'FAIL'} {f:38} {sz/1048576:7.1f}/{exp/1048576:7.1f} MB {time.time()-t0:5.0f}s {why}"


with cf.ThreadPoolExecutor(max_workers=3) as ex:
    for line in ex.map(job, broken):
        print(line, flush=True)

tot = sum(os.path.getsize(os.path.join(ZIPS, x)) for x in os.listdir(ZIPS))
print(f"\nzip cache: {len(os.listdir(ZIPS))} files, {tot/1048576:.0f} MB", flush=True)
print("still broken:", [f for f in sorted(os.listdir(ZIPS)) if is_broken(f)], flush=True)
