#!/usr/bin/env python3
"""Generate thumbs + previews + data.json for the multi-platform gallery.

Reads recon/index_all.json (the organised tree manifest) and writes:
  thumbs/<platform>/<set>/<stem>.jpg   480 px  (grid cards)
  preview/<platform>/<set>/<stem>.jpg 1000 px  (lightbox)
  data.json                             platforms -> sets -> items(files by format)

Set BASE_PREFIX if the originals are served from somewhere other than the site root
('' = same origin, i.e. the files live in this repo).
"""
import os, json, re
from collections import defaultdict
from PIL import Image, ImageOps
try:
    import pillow_heif
    pillow_heif.register_heif_opener()          # so .heic files can be thumbnailed
    HEIF = True
except Exception:
    HEIF = False

BASE = "/root/Projects/20260922-iphone-wallpapers"
OUT = BASE
BASE_PREFIX = ""          # e.g. "https://raw.githubusercontent.com/user/repo/main/"

T = os.path.join(OUT, "thumbs")
P = os.path.join(OUT, "preview")
for d in (T, P):
    os.makedirs(d, exist_ok=True)

PLATFORM_META = [
    ("iphone", "iPhone", "iPhone 13 → 18 原厂跟机壁纸"),
    ("ipad", "iPad", "iPadOS 14 → 27 与 iPad 跟机壁纸"),
    ("mac", "Mac", "macOS 10.15 → 27 与 Mac 跟机壁纸"),
    ("ios", "iOS 通用", "iOS 12 → 27 系统壁纸"),
    ("special", "特别主题", "发布会 / WWDC / Pride / 店铺 / 节日"),
]
PLAT_ORDER = [p for p, _, _ in PLATFORM_META]
PLAT_LABEL = {p: l for p, l, _ in PLATFORM_META}
PLAT_NOTE = {p: n for p, _, n in PLATFORM_META}

rows = json.load(open(os.path.join(BASE, "recon/index_all.json")))

def slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-")

def make(src, dst, box):
    if os.path.exists(dst):
        return True
    try:
        with Image.open(os.path.join(BASE, src)) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            im.thumbnail((box, box), Image.LANCZOS)
            im.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
        return True
    except Exception as e:
        print("  thumb fail", src, type(e).__name__)
        return False


def pick_source(files):
    """Prefer a format Pillow can definitely open; fall back to the largest file."""
    order = {"jpg": 0, "jpeg": 0, "png": 1, "heic": 2}
    return sorted(files, key=lambda f: (order.get(f["ext"], 3), -f["kb"]))[0]

# ---------- group files into items (a wallpaper = same stem across formats) ----------
sets = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for r in rows:
    stem = os.path.splitext(os.path.basename(r["file"]))[0]
    if re.fullmatch(r"\d+", stem):
        stem = r["folder"] + "-" + stem
    sets[r["platform"]][r["folder"]][stem].append(r)

platforms = []
total_files = 0
total_kb = 0
for plat in PLAT_ORDER:
    if plat not in sets:
        continue
    sets_out = []
    for folder in sorted(sets[plat]):
        items = []
        seq = 0
        for stem in sorted(sets[plat][folder]):
            seq += 1
            files = sorted(sets[plat][folder][stem], key=lambda x: x["ext"])
            best = pick_source(files)
            # iClarified stores many sets as bare numeric ids; give those a readable label
            label = stem
            if re.fullmatch(rf"{re.escape(folder)}-\d+", stem) or re.fullmatch(r"\d+", stem):
                label = f"壁纸 {seq:02d}"
            slugp = f"{plat}/{folder}"
            tpath = os.path.join(T, slugp, slug(stem) + ".jpg")
            ppath = os.path.join(P, slugp, slug(stem) + ".jpg")
            os.makedirs(os.path.dirname(tpath), exist_ok=True)
            os.makedirs(os.path.dirname(ppath), exist_ok=True)
            ok_t = make(best["file"], tpath, 480)
            ok_p = make(best["file"], ppath, 1000)
            if not (ok_t and ok_p):
                continue
            items.append({
                "stem": stem,
                "label": label,
                "thumb": os.path.relpath(tpath, OUT).replace(os.sep, "/"),
                "preview": os.path.relpath(ppath, OUT).replace(os.sep, "/"),
                "w": best["w"], "h": best["h"],
                "files": [{"file": BASE_PREFIX + f["file"], "ext": f["ext"],
                           "kb": f["kb"], "w": f["w"], "h": f["h"]} for f in files],
            })
            total_files += len(files)
            total_kb += sum(f["kb"] for f in files)
        if not items:
            continue
        sets_out.append({
            "id": folder, "label": folder.replace("-", " "),
            "files": sum(len(i["files"]) for i in items),
            "mb": round(sum(f["kb"] for i in items for f in i["files"]) / 1024, 1),
            "items": items,
        })
    if not sets_out:
        continue
    platforms.append({
        "id": plat, "label": PLAT_LABEL[plat], "note": PLAT_NOTE[plat],
        "sets": sets_out,
        "files": sum(s["files"] for s in sets_out),
        "mb": round(sum(s["mb"] for s in sets_out), 1),
    })

data = {
    "generated": __import__("time").strftime("%Y-%m-%d %H:%M"),
    "stats": {"platforms": len(platforms),
              "sets": sum(len(p["sets"]) for p in platforms),
              "files": total_files,
              "mb": round(total_kb / 1024, 1)},
    "platforms": platforms,
}
json.dump(data, open(os.path.join(OUT, "data.json"), "w"), ensure_ascii=False, separators=(",", ":"))

print(f"platforms={len(platforms)}  sets={data['stats']['sets']}  "
      f"files={total_files}  {total_kb/1048576:.2f} GB")
for p in platforms:
    print(f"  [{p['id']:8}] {len(p['sets']):2} sets {p['files']:4} files {p['mb']/1024:6.2f} GB")
