#!/usr/bin/env python3
"""Phase C: assemble the unified Apple-Wallpapers tree.

Sources: iClarified per-set zips (staging2/_zips) + loose full-size images
(staging2/_extracted) + the earlier iPhone device sets. Drops article marketing renders
(verified visually), dedupes within each set, and requires >=1000 px.
"""
import os, re, json, shutil, hashlib, sys
DEBUG_TRACE = os.environ.get('ORG_TRACE')
def trace(*a):
    if DEBUG_TRACE: print('[trc]', *a, file=sys.stderr)
from collections import defaultdict
from PIL import Image

BASE = "/root/Projects/20260922-iphone-wallpapers"
STAGE = os.path.join(BASE, "staging2")
ZIPS = os.path.join(STAGE, "_zips")
EXTR = os.path.join(STAGE, "_extracted")
OUT = os.path.join(BASE, "Apple-Wallpapers")
OLD_IPHONE = os.path.join(BASE, "iPhone-stock-wallpapers-13to18")

PLAT_DIR = {"iphone": "01-iPhone", "ipad": "02-iPad", "mac": "03-Mac",
            "ios": "04-iOS-generic", "special": "05-Special"}

# group label -> folder name (explicit, so Chinese labels never collapse to bare digits)
FOLDER = {
    # ipad
    "iPadOS 14": "iPadOS-14", "iPadOS 14.2": "iPadOS-14.2", "iPadOS 15": "iPadOS-15",
    "iPadOS 15.4": "iPadOS-15.4", "iPadOS 16": "iPadOS-16", "iPadOS 17": "iPadOS-17",
    "iPadOS 18": "iPadOS-18", "iPadOS 26": "iPadOS-26", "iPadOS 27": "iPadOS-27",
    "iPad 2022 / iPad Pro": "iPad-2022-and-iPad-Pro", "iPad Pro 2024": "iPad-Pro-2024",
    "iPad Air 2024": "iPad-Air-2024", "iPad 初代": "iPad-1st-gen",
    # mac
    "macOS 11 Big Sur": "macOS-11-Big-Sur", "macOS 12 Monterey": "macOS-12-Monterey",
    "macOS 13 Ventura": "macOS-13-Ventura", "macOS 14 Sonoma": "macOS-14-Sonoma",
    "macOS 14 Sonoma Horizon": "macOS-14-Sonoma-Horizon",
    "macOS 15 Sequoia": "macOS-15-Sequoia",
    "macOS 15 Sequoia Sunrise": "macOS-15-Sequoia-Sunrise",
    "macOS 26 Tahoe": "macOS-26-Tahoe", "macOS 27 Golden Gate": "macOS-27-Golden-Gate",
    "macOS 27 Sunset / Night": "macOS-27-Sunset-and-Night",
    "macOS 27 Day / Evening": "macOS-27-Day-and-Evening",
    "macOS 10.15 Catalina": "macOS-10.15-Catalina",
    "MacBook Air 2022": "MacBook-Air-2022", "MacBook Pro 2023": "MacBook-Pro-2023",
    "MacBook Air 2023": "MacBook-Air-2023", "MacBook Pro M3 2023": "MacBook-Pro-M3-2023",
    "iMac 2023": "iMac-2023", "iMac M4 2024": "iMac-M4-2024", "MacBook Neo": "MacBook-Neo",
    # ios
    "iOS 12": "iOS-12", "iOS 13": "iOS-13", "iOS 14": "iOS-14",
    "iOS 14.1 / iPhone 12": "iOS-14.1-iPhone-12", "iOS 14.2": "iOS-14.2",
    "iOS 15.4": "iOS-15.4", "iOS 16": "iOS-16", "iOS 17": "iOS-17", "iOS 18": "iOS-18",
    "iOS 26": "iOS-26", "iOS 26 Shadow / Halo / Dusk": "iOS-26-Shadow-Halo-Dusk",
    "iOS 27": "iOS-27",
    # special
    "Clownfish 初代 iPhone": "Clownfish-Original-iPhone",
    "Far Out 发布会 2022": "Apple-Event-Far-Out-2022",
    "iPhone 15 发布会 2023": "Apple-Event-2023",
    "WWDC 2015": "WWDC-2015", "WWDC 2023": "WWDC-2023", "WWDC 2024": "WWDC-2024",
    "WWDC 2026": "WWDC-2026", "Unity Bloom": "Unity-Bloom",
    "Pride Radiance 2024": "Pride-Radiance-2024", "Pride 2023": "Pride-2023",
    "Pride 2026": "Pride-2026",
    "Umeda 店铺": "Apple-Store-Umeda", "静安店 2023": "Apple-Store-Jingan",
    "Borivali 店": "Apple-Store-Borivali", "Gangnam 店": "Apple-Store-Gangnam",
    "Spring Forward 2015": "Apple-Event-Spring-Forward-2015",
    "地球日": "Earth-Day", "中国新年": "Chinese-New-Year",
}

# display order inside each platform
ORDER = {
    "ipad": ["iPadOS-27", "iPadOS-26", "iPadOS-18", "iPadOS-17", "iPadOS-16",
             "iPadOS-15.4", "iPadOS-15", "iPadOS-14.2", "iPadOS-14",
             "iPad-Pro-2024", "iPad-Air-2024", "iPad-2022-and-iPad-Pro", "iPad-1st-gen"],
    "mac": ["macOS-27-Golden-Gate", "macOS-27-Sunset-and-Night", "macOS-27-Day-and-Evening",
            "macOS-26-Tahoe", "macOS-15-Sequoia", "macOS-15-Sequoia-Sunrise",
            "macOS-14-Sonoma", "macOS-14-Sonoma-Horizon", "macOS-13-Ventura",
            "macOS-12-Monterey", "macOS-11-Big-Sur", "macOS-10.15-Catalina",
            "MacBook-Neo", "iMac-M4-2024", "iMac-2023", "MacBook-Pro-M3-2023",
            "MacBook-Air-2023", "MacBook-Pro-2023", "MacBook-Air-2022"],
    "ios": ["iOS-27", "iOS-26", "iOS-26-Shadow-Halo-Dusk", "iOS-18", "iOS-17", "iOS-16",
            "iOS-15.4", "iOS-14.2", "iOS-14.1-iPhone-12", "iOS-14", "iOS-13", "iOS-12"],
    "special": ["WWDC-2026", "WWDC-2024", "WWDC-2023", "WWDC-2015",
                "Apple-Event-2023", "Apple-Event-Far-Out-2022", "Apple-Event-Spring-Forward-2015",
                "Pride-2026", "Pride-Radiance-2024", "Pride-2023", "Unity-Bloom",
                "Apple-Store-Umeda", "Apple-Store-Jingan", "Apple-Store-Borivali",
                "Apple-Store-Gangnam", "Clownfish-Original-iPhone", "Earth-Day",
                "Chinese-New-Year"],
}

# visually verified marketing renders / composites (not wallpapers)
DROP = {
    ("special", "Gangnam 店", "431012.jpg"), ("special", "Borivali 店", "473969.jpg"),
    ("special", "Pride 2026", "476393.jpg"), ("special", "Pride 2026", "476396.jpg"),
    ("special", "Pride 2023", "433636.jpg"),
    ("mac", "MacBook Pro 2023", "427866.jpg"),
    ("ios", "iOS 26 Shadow / Halo / Dusk", "466584.jpg"),
    ("ios", "iOS 26 Shadow / Halo / Dusk", "466587.jpg"),
    # Apple CgBI-encoded PNGs that no standard decoder (libpng, Pillow, pngcrush) can read
    ("special", "WWDC 2015", "WWDC_2015_iPhone6Plus.png"),
    ("special", "WWDC 2015", "WWDC_2015_iPhone5s.png"),
    ("special", "WWDC 2015", "WWDC_2015_iPhone6.png"),
    ("special", "WWDC 2015", "WWDC_2015_iPad.png"),
}

assets = json.load(open(os.path.join(BASE, "recon/assets.json")))
OK_EXT = {".jpg", ".jpeg", ".png", ".heic"}
index = []
skipped = []


def slug(s):
    return re.sub(r"[^A-Za-z0-9._\-]+", "-", s).strip("-")


def add(plat, group, dst_dir, src_path=None, data=None, orig_name=None):
    folder = FOLDER.get(group, slug(group))
    name = orig_name or os.path.basename(src_path)
    if DEBUG_TRACE and "WWDC-2015" in str(dst_dir): print("[trc] add", name, file=sys.stderr)
    if (plat, group, name) in DROP:
        skipped.append((plat, group, name, "dropped: marketing render"))
        return False
    ext = os.path.splitext(name)[1].lower()
    if ext not in OK_EXT:
        return False
    if data is None:
        with open(src_path, "rb") as fh:
            data = fh.read()
    if len(data) < 20_000:
        return False
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, name)
    with open(dst, "wb") as fh:
        fh.write(data)
    try:
        with Image.open(dst) as im:
            w, h = im.size
        if w < 1000 and h < 1000:
            os.remove(dst)
            skipped.append((plat, group, name, "under-1000px"))
            return False
    except Exception as e:
        if ext != ".heic":
            os.remove(dst)
            skipped.append((plat, group, name, f"unreadable {type(e).__name__}"))
            return False
        w = h = 0
    index.append({"platform": plat, "folder": folder, "group": group,
                  "file": os.path.relpath(dst, BASE).replace(os.sep, "/"),
                  "kb": round(len(data) / 1024, 1), "ext": ext.lstrip("."), "w": w, "h": h})
    return True


# ---------------- 1. iphone sets (copied from the first-stage folder) ----------------
if os.path.isdir(OLD_IPHONE):
    for folder in sorted(os.listdir(OLD_IPHONE)):
        src = os.path.join(OLD_IPHONE, folder)
        if not os.path.isdir(src):
            continue
        dst_dir = os.path.join(OUT, "01-iPhone", folder)
        os.makedirs(dst_dir, exist_ok=True)
        for f in sorted(os.listdir(src)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst_dir, f))
            p = os.path.join(dst_dir, f)
            try:
                with Image.open(p) as im:
                    w, h = im.size
            except Exception:
                w = h = 0
            index.append({"platform": "iphone", "folder": folder, "group": folder,
                          "file": os.path.relpath(p, BASE).replace(os.sep, "/"),
                          "kb": round(os.path.getsize(p) / 1024, 1),
                          "ext": os.path.splitext(f)[1].lstrip(".").lower(),
                          "w": w, "h": h})

# ---------------- 2. zips by article ----------------
zmap = defaultdict(list)
for f in sorted(os.listdir(ZIPS)):
    m = re.match(r"^(\d+)-", f)
    if m:
        zmap[m.group(1)].append(os.path.join(ZIPS, f))

import zipfile
for aid, x in sorted(assets.items()):
    plat, group = x["platform"], x["group"]
    folder = FOLDER.get(group, slug(group))
    dst_dir = os.path.join(OUT, PLAT_DIR[plat], folder)
    files = []
    for z in zmap.get(aid, []):
        try:
            with zipfile.ZipFile(z) as zf:
                if zf.testzip() is not None:
                    print("skip corrupt zip", os.path.basename(z))
                    continue
                for m in zf.namelist():
                    b = os.path.basename(m)
                    if not b or b.startswith("._") or b == ".DS_Store" or "__MACOSX" in m:
                        continue
                    files.append((b, zf.read(m)))
        except Exception as e:
            print("zip read fail", z, e)
    for b, data in files:
        clean = re.sub(r"^iClarified-", "", b)
        add(plat, group, dst_dir, data=data, orig_name=clean)

# ---------------- 3. loose + recovered images ----------------
# image-id -> owning article, for groups whose Chinese-only label collapses to an empty slug
IMG_OWNER = {}
for aid, x in assets.items():
    p = os.path.join(BASE, "recon", "pages", aid + ".html")
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(rf'/images/news/{aid}/(\d+)/\1-\d+\.(?:jpg|jpeg|png|heic)', h, re.I):
        IMG_OWNER.setdefault(m.group(1), (x["platform"], x["group"]))

for root, dirs, fs in os.walk(EXTR):
    for f in sorted(fs):
        p = os.path.join(root, f)
        rel = os.path.relpath(p, EXTR).split(os.sep)
        if len(rel) == 2:                       # stray file whose group slug was empty
            owner = IMG_OWNER.get(os.path.splitext(f)[0])
            if not owner:
                continue
            plat, group = owner
        elif len(rel) >= 3:
            owner = None
            for aid, x in assets.items():
                if x["platform"] == rel[0] and slug(x["group"]) == rel[1]:
                    owner = x
                    break
            if not owner:
                continue
            plat, group = owner["platform"], owner["group"]
        else:
            continue
        folder = FOLDER.get(group, slug(group))
        dst_dir = os.path.join(OUT, PLAT_DIR[plat], folder)
        base_name = f if not re.fullmatch(r"\d+\.(jpg|jpeg|png|heic)", f, re.I) \
            else f"{folder}-{os.path.splitext(f)[0]}.{os.path.splitext(f)[1].lstrip('.')}"
        add(plat, group, dst_dir, src_path=p, orig_name=base_name)

# ---------------- 4. dedupe inside each set, then renumber ----------------
by_set = defaultdict(list)
for r in index:
    by_set[(r["platform"], r["folder"])].append(r)
final = []
for key, rows in sorted(by_set.items()):
    seen = {}
    seen_paths = set()
    for r in rows:
        if r["file"] in seen_paths:          # same path indexed twice (zip entry + loose copy)
            continue
        seen_paths.add(r["file"])
        with open(os.path.join(BASE, r["file"]), "rb") as fh:
            h = hashlib.md5(fh.read()).hexdigest()
        if h in seen:
            if DEBUG_TRACE and "WWDC" in r["file"]: print("[trc] dedupe-remove", r["file"], file=sys.stderr)
            os.remove(os.path.join(BASE, r["file"]))
            skipped.append((r["platform"], r["group"], os.path.basename(r["file"]), "duplicate"))
            continue
        seen[h] = r
        final.append(r)

# renumber files when their names are not descriptive
num_re = re.compile(r"^\d+\.(jpg|jpeg|png|heic)$", re.I)
for key in sorted({(r["platform"], r["folder"]) for r in final}):
    rows = [r for r in final if (r["platform"], r["folder"]) == key]
    rows.sort(key=lambda r: r["file"])
    for i, r in enumerate(rows, 1):
        b = os.path.basename(r["file"])
        if not num_re.match(b):
            continue
        ext = os.path.splitext(b)[1].lower()
        new = f'{r["folder"]}-{i:02d}{ext}'
        old = os.path.join(BASE, r["file"])
        new_abs = os.path.join(os.path.dirname(old), new)
        if os.path.exists(new_abs):
            continue
        if DEBUG_TRACE and "WWDC" in old: print("[trc] rename", old, "->", new_abs, file=sys.stderr)
        os.rename(old, new_abs)
        r["file"] = os.path.relpath(new_abs, BASE).replace(os.sep, "/")

json.dump(final, open(os.path.join(BASE, "recon/index_all.json"), "w"),
          ensure_ascii=False, indent=1)

# ---------------- 5. report ----------------
by_plat = defaultdict(lambda: defaultdict(lambda: {"n": 0, "mb": 0.0, "min": None, "max": None}))
for r in final:
    s = by_plat[r["platform"]][r["folder"]]
    s["n"] += 1
    s["mb"] += r["kb"] / 1024
    area = r["w"] * r["h"]
    s["min"] = area if s["min"] is None else min(s["min"], area)
    s["max"] = area if s["max"] is None else max(s["max"], area)

print("=== Apple-Wallpapers ===")
grand_n = grand_mb = 0
for plat, sub in by_plat.items():
    n = sum(v["n"] for v in sub.values())
    mb = sum(v["mb"] for v in sub.values())
    grand_n += n
    grand_mb += mb
    print(f"\n[{PLAT_DIR[plat]}]  {n} files  {mb/1024:.2f} GB")
    order = ORDER.get(plat, sorted(sub))
    for f in order:
        if f not in sub:
            print(f'   {f:34} -- EMPTY (skipped)')
            continue
        v = sub[f]
        print(f'   {f:34} {v["n"]:4} files  {v["mb"]:7.1f} MB')
    for f in sub:
        if f not in order:
            v = sub[f]
            print(f'   {f:34} {v["n"]:4} files  {v["mb"]:7.1f} MB  (unlisted)')
print(f"\nTOTAL {grand_n} files, {grand_mb/1024:.2f} GB")
print("\nskipped:", len(skipped))
for s in skipped[:40]:
    print("   ", s)
