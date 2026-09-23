#!/usr/bin/env python3
"""Phase B: download every zip + loose full-size image, extract, and report."""
import os, re, json, subprocess, zipfile, shutil, sys
import concurrent.futures as cf

BASE = "/root/Projects/20260922-iphone-wallpapers"
REC = os.path.join(BASE, "recon")
STAGE = os.path.join(BASE, "staging2")
ZIPS = os.path.join(STAGE, "_zips")
EXTR = os.path.join(STAGE, "_extracted")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
for d in (ZIPS, EXTR):
    os.makedirs(d, exist_ok=True)

ASSETS = json.load(open(os.path.join(REC, "assets.json")))
log = open(os.path.join(STAGE, "download.log"), "a", buffering=1)

def slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-")

def get(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 1024:
        return "cached", os.path.getsize(dst)
    r = subprocess.run(["curl", "-sL", "-C", "-", "-A", UA, "-o", dst, url,
                        "--max-time", "1800", "--retry", "3", "--retry-delay", "5"],
                       capture_output=True, text=True)
    ok = os.path.exists(dst) and os.path.getsize(dst) > 1024
    return ("ok" if ok else "FAIL"), (os.path.getsize(dst) if os.path.exists(dst) else 0)

# ---------- 1. zips ----------
jobs = []
for aid, x in ASSETS.items():
    for i, z in enumerate(x["zips"]):
        name = f'{aid}-{slug(x["group"])}-{i}.zip'
        jobs.append((aid, x, z, os.path.join(ZIPS, name)))

def dl_zip(j):
    aid, x, url, dst = j
    st, sz = get(url, dst)
    log.write(f"ZIP {st:6} {sz/1048576:7.1f}MB {x['platform']:8} {x['group']}\n")
    return st, sz

print(f"zips to fetch: {len(jobs)}", flush=True)
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(dl_zip, jobs))

# verify + extract
bad = []
for aid, x, url, dst in jobs:
    if not os.path.exists(dst):
        continue
    try:
        with zipfile.ZipFile(dst) as zf:
            if zf.testzip() is not None:
                raise RuntimeError("bad zip entry")
            out = os.path.join(EXTR, f'{x["platform"]}/{slug(x["group"])}')
            os.makedirs(out, exist_ok=True)
            for m in zf.namelist():
                b = os.path.basename(m)
                if not b or b.startswith("._") or b == ".DS_Store" or "__MACOSX" in m:
                    continue
                with zf.open(m) as src, open(os.path.join(out, b), "wb") as fh:
                    shutil.copyfileobj(src, fh)
        log.write(f"EXT ok   {dst}\n")
    except Exception as e:
        bad.append(dst)
        log.write(f"EXT FAIL {dst} {e}\n")

# ---------- 2. loose images ----------
have = set()
for root, dirs, files in os.walk(EXTR):
    for f in files:
        have.add((os.path.basename(root), f.lower()))

img_jobs = []
for aid, x in ASSETS.items():
    grp = slug(x["group"])
    for u in x["images"]:
        b = u.rsplit("/", 1)[-1]
        if re.fullmatch(rf"{aid}(-\d+)?\.(jpg|jpeg|png|heic)", b, re.I):   # article lead image
            continue
        if (grp, b.lower()) in have:
            continue
        img_jobs.append((aid, x, grp, u, b))

def dl_img(j):
    aid, x, grp, u, b = j
    out = os.path.join(EXTR, f'{x["platform"]}/{grp}')
    os.makedirs(out, exist_ok=True)
    st, sz = get(u, os.path.join(out, b))
    log.write(f"IMG {st:6} {sz/1048576:7.2f}MB {x['platform']:8} {x['group']} {b}\n")
    return st, sz

print(f"loose images to fetch: {len(img_jobs)}", flush=True)
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(dl_img, img_jobs))

print("DONE bad_zips=", bad, flush=True)
