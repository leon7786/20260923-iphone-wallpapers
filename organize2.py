#!/usr/bin/env python3
"""Phase C: repair/verify downloads, build the unified Apple-Wallpapers tree, prune junk."""
import os, re, json, shutil, hashlib, subprocess, zipfile
from collections import defaultdict
from PIL import Image

BASE = "/root/Projects/20260922-iphone-wallpapers"
STAGE = os.path.join(BASE, "staging2")
EXTR = os.path.join(STAGE, "_extracted")
ZIPS = os.path.join(STAGE, "_zips")
OUT = os.path.join(BASE, "Apple-Wallpapers")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
OK_EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp"}

PLAT_ORDER = [("iphone", "01-iPhone"), ("ipad", "02-iPad"), ("mac", "03-Mac"),
              ("ios", "04-iOS-generic"), ("special", "05-Special")]

# ---------- 1. verify every downloaded zip; re-fetch the broken ones ----------
assets = json.load(open(os.path.join(BASE, "recon/assets.json")))
zmap = defaultdict(list)
for f in os.listdir(ZIPS):
    m = re.match(r"^(\d+)-", f)
    if m:
        zmap[m.group(1)].append(os.path.join(ZIPS, f))

bad = []
for f in sorted(os.listdir(ZIPS)):
    p = os.path.join(ZIPS, f)
    try:
        with zipfile.ZipFile(p) as zf:
            if zf.testzip() is not None:
                raise RuntimeError("crc")
        n = len(zipfile.ZipFile(p).namelist())
        print(f"OK    {os.path.getsize(p)/1048576:7.1f}MB  {n:4} entries  {f}")
    except Exception as e:
        print(f"BAD   {os.path.getsize(p)/1048576:7.1f}MB  {f}  ({e})")
        bad.append(f)

for f in bad:                       # serial re-fetch, kinder to the origin
    aid = re.match(r"^(\d+)-", f).group(1)
    idx = int(re.search(r"-(\d+)\.zip$", f).group(1))
    url = assets[aid]["zips"][idx]
    print("refetch", f)
    os.remove(os.path.join(ZIPS, f))
    subprocess.run(["curl", "-sL", "-A", UA, "-o", os.path.join(ZIPS, f), url,
                    "--max-time", "1800", "--retry", "3", "--retry-delay", "10"], check=False)
    p = os.path.join(ZIPS, f)
    try:
        with zipfile.ZipFile(p) as zf:
            assert zf.testzip() is None
        print("  repaired", os.path.getsize(p) / 1048576, "MB")
    except Exception as e:
        print("  STILL BAD", f, e)

# ---------- 2. extract into the unified tree ----------
def slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-")

def safe_name(b):
    b = b.replace("\u200b", "")
    b = re.sub(r"[^A-Za-z0-9._\-()\[\]+& ]+", "_", b)
    return b.strip() or "image"

plat_dir = dict(PLAT_ORDER)
index = []          # {platform, folder, group, file, kb, ext, w, h}
seen_hash = {}

def add_file(plat, group, folder, src_bytes, name, src_path=None):
    ext = os.path.splitext(name)[1].lower()
    if ext not in OK_EXT:
        return False
    try:
        if src_path:
            with open(src_path, "rb") as fh:
                data = fh.read()
        else:
            data = src_bytes
    except Exception:
        return False
    if len(data) < 20_000:                      # thumbnails / sprites / icons
        return False
    h = hashlib.md5(data).hexdigest()
    key = (plat, group, h)
    if key in seen_hash:                        # duplicate inside the same set
        return False
    seen_hash[key] = name
    dst_dir = os.path.join(OUT, plat_dir[plat], folder)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, name)
    i = 2
    while os.path.exists(dst):
        stem, e = os.path.splitext(name)
        dst = os.path.join(dst_dir, f"{stem}-{i}{e}")
        i += 1
    with open(dst, "wb") as fh:
        fh.write(data)
    w = hgt = 0
    try:
        with Image.open(dst) as im:
            w, hgt = im.size
        if w < 1000 and hgt < 1000:             # screenshots / inline graphics
            os.remove(dst)
            return False
    except Exception:
        os.remove(dst)
        return False
    index.append({"platform": plat, "folder": folder, "group": group,
                  "file": os.path.relpath(dst, BASE).replace(os.sep, "/"),
                  "kb": round(len(data) / 1024, 1), "ext": ext.lstrip("."),
                  "w": w, "h": hgt})
    return True

def kind(aid):
    return assets[aid]["platform"], assets[aid]["group"]

# 2a. zips
for aid in sorted(assets):
    plat, group = kind(aid)
    folder = f'{slug(group)}'
    for f in sorted(zmap.get(aid, [])):
        try:
            with zipfile.ZipFile(f) as zf:
                for m in zf.namelist():
                    b = os.path.basename(m)
                    if not b or b.startswith("._") or b == ".DS_Store" or "__MACOSX" in m:
                        continue
                    if os.path.splitext(b)[1].lower() not in OK_EXT:
                        continue
                    add_file(plat, group, folder, zf.read(m), safe_name(b))
        except Exception as e:
            print("extract fail", f, e)

# 2b. loose images (files fetched directly)
for root, dirs, files in os.walk(EXTR):
    for f in files:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, EXTR)
        parts = rel.split(os.sep)
        if len(parts) < 3:
            continue
        plat, group = parts[0], parts[1]
        add_file(plat, group, slug(group), b"", safe_name(f), src_path=p)

# ---------- 3. write index ----------
json.dump(index, open(os.path.join(BASE, "recon/other_index.json"), "w"), ensure_ascii=False, indent=1)
by_plat = defaultdict(lambda: defaultdict(lambda: {"files": 0, "mb": 0.0}))
for r in index:
    s = by_plat[r["platform"]][r["group"]]
    s["files"] += 1
    s["mb"] += r["kb"] / 1024
tot = 0
print("\n=== organised tree ===")
for plat, _ in PLAT_ORDER:
    if plat not in by_plat:
        continue
    sub = by_plat[plat]
    pf = sum(v["files"] for v in sub.values())
    pm = sum(v["mb"] for v in sub.values())
    tot += pm
    print(f'\n[{plat}]  {pf} files  {pm:.0f} MB')
    for g, v in sorted(sub.items()):
        print(f'   {g:34} {v["files"]:4} files  {v["mb"]:6.0f} MB')
print(f"\nTOTAL {len(index)} files, {tot/1024:.2f} GB")
