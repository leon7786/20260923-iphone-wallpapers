#!/usr/bin/env python3
"""Generate 480px thumbnails + data.json for the GitHub Pages gallery."""
import os, json, re
from PIL import Image

BASE = "/root/Projects/20260922-iphone-wallpapers"
OUT = os.path.join(BASE, "iPhone-stock-wallpapers-13to18")
THUMBS = os.path.join(BASE, "thumbs")
PREVIEW = os.path.join(BASE, "preview")
OUTNAME = os.path.basename(OUT)

MODELS = [
    ("01-iPhone-13",     "iPhone 13 / 13 mini",          "iPhone 13",      2021, 13, "Twist 5 色 × 浅色 / 深色",  "iPhone13-",       "Twist"),
    ("02-iPhone-13-Pro", "iPhone 13 Pro / Pro Max",      "iPhone 13 Pro",  2021, 13, "Light Beams 4 色 × 浅色 / 深色", "iPhone13Pro-", "LightBeams"),
    ("03-iPhone-14",     "iPhone 14 / 14 Plus",          "iPhone 14",      2022, 14, "官方 5 色",                  "iPhone14-",     ""),
    ("04-iPhone-14-Pro", "iPhone 14 Pro / Pro Max",      "iPhone 14 Pro",  2022, 14, "官方 4 色",                  "iPhone14Pro-",  ""),
    ("05-iPhone-15",     "iPhone 15 / 15 Plus",          "iPhone 15",      2023, 15, "官方 5 色",                  "iPhone15-",     ""),
    ("06-iPhone-15-Pro", "iPhone 15 Pro / Pro Max",      "iPhone 15 Pro",  2023, 15, "4 色 × 锁屏 / 主屏 / 息屏",    "iPhone15Pro-",  ""),
    ("07-iPhone-16",     "iPhone 16 / 16 Plus",          "iPhone 16",      2024, 16, "官方 5 色",                  "iPhone16-",     ""),
    ("08-iPhone-16-Pro", "iPhone 16 Pro / Pro Max",      "iPhone 16 Pro",  2024, 16, "官方 4 色",                  "iPhone16Pro-",  ""),
    ("09-iPhone-16e",    "iPhone 16e",                   "iPhone 16e",     2025, 16, "官方 1 款",                  "iPhone16e-",    ""),
    ("10-iPhone-17",     "iPhone 17",                    "iPhone 17",      2025, 17, "5 色 × 锁屏 / 主屏",         "iPhone17-",     ""),
    ("11-iPhone-17-Pro", "iPhone 17 Pro / Pro Max",      "iPhone 17 Pro",  2025, 17, "3 色 × 锁屏 / 主屏",         "iPhone17Pro-",  ""),
    ("12-iPhone-Air",    "iPhone Air",                   "iPhone Air",     2025, 17, "4 色 × 锁屏 / 主屏",         "iPhoneAir-",    ""),
    ("13-iPhone-17e",    "iPhone 17e",                   "iPhone 17e",     2026, 17, "官方 3 色",                  "iPhone17e-",    ""),
    ("14-iPhone-18-Pro", "iPhone 18 Pro / Pro Max",      "iPhone 18 Pro",  2026, 18, "Vitra 4 色 × 锁屏 / 主屏",    "iPhone18Pro-",  ""),
    ("15-iPhone-Duo",    "iPhone Duo（折叠机）",           "iPhone Duo",     2026, 18, "内屏 / 外屏 × 锁屏 / 主屏 × 浅 / 深", "iPhoneDuo-", ""),
]

ZH = [
    ("AlwaysOnDisplaytoLockScreen-1", "息屏→锁屏 1"),
    ("AlwaysOnDisplaytoLockScreen-2", "息屏→锁屏 2"),
    ("AlwaysOnDisplaytoLockScreen", "息屏→锁屏"),
    ("AlwaysOnDisplay", "息屏显示"),
    ("LockScreen", "锁屏"), ("Lockscreen", "锁屏"),
    ("HomeScreen", "主屏"), ("Homescreen", "主屏"),
    ("Lock-Screen", "锁屏"), ("Home-Screen", "主屏"),
    ("Inner", "内屏"), ("Outer", "外屏"),
    ("LightBeams", "光带"), ("Light Beams", "光带"),
    ("Light", "浅色"), ("Dark", "深色"),
]
COLOR_ZH = {
    "Black": "黑色", "White": "白色", "Blue": "蓝色", "Pink": "粉色", "Red": "红色",
    "Green": "绿色", "Yellow": "黄色", "Purple": "紫色", "Midnight": "午夜", "Starlight": "星光",
    "Teal": "青色", "Ultramarine": "群青", "Sage": "鼠尾草绿", "Lavender": "薰衣草", "MistBlue": "雾蓝",
    "CloudWhite": "云白", "LightGold": "浅金", "SkyBlue": "天蓝", "SpaceBlack": "太空黑",
    "DeepPurple": "深紫", "Gold": "金色", "Silver": "银色", "DeepBlue": "深蓝",
    "CosmicOrange": "宇宙橙", "Burgundy": "勃艮第红", "Glacier": "冰川蓝",
    "NaturalTitanium": "原色钛金属", "BlueTitanium": "蓝色钛金属", "BlackTitanium": "黑色钛金属",
    "WhiteTitanium": "白色钛金属", "DesertTitanium": "沙漠色钛金属",
    "SoftPink": "柔粉", "Soft Pink": "柔粉", "Official": "官方",
    "DarkGray": "深灰",
}

def label(stem, prefix):
    s = stem
    if prefix and s.startswith(prefix):
        s = s[len(prefix):]
    s = s.strip("-")
    parts = [p for p in s.split("-") if p]
    out = []
    i = 0
    while i < len(parts):
        p = parts[i]
        # merge two-word keys
        merged = False
        if i + 1 < len(parts):
            two = p + parts[i + 1]
            for en, zh in ZH:
                if two == en:
                    out.append(zh); i += 2; merged = True; break
        if merged:
            continue
        if p in COLOR_ZH:
            out.append(COLOR_ZH[p])
        else:
            hit = False
            for en, zh in ZH:
                if p == en:
                    out.append(zh); hit = True; break
            if not hit:
                out.append(p)
        i += 1
    return " · ".join(out) if out else "官方壁纸"

data = {"release": "https://github.com/leon7786/20260923-iphone-wallpapers/releases/download/v1.0/iPhone-stock-wallpapers-13to18.zip",
        "repo": "https://github.com/leon7786/20260923-iphone-wallpapers",
        "models": []}

n_thumb = 0
total_files = 0
total_mb = 0.0
for folder, model, short, year, gen, desc, prefix, _x in MODELS:
    d = os.path.join(OUT, folder)
    groups = {}
    for f in sorted(os.listdir(d)):
        stem, ext = os.path.splitext(f)
        groups.setdefault(stem, []).append((ext.lstrip(".").lower(), f))
    tdir = os.path.join(THUMBS, folder)
    os.makedirs(tdir, exist_ok=True)
    items = []
    for stem, files in groups.items():
        exts = [e for e, _ in files]
        src = None
        for pref_ext in ("jpg", "png"):
            for e, fn in files:
                if e == pref_ext:
                    src = os.path.join(d, fn)
        if not src:
            continue
        tpath = os.path.join(tdir, stem + ".jpg")
        pdir = os.path.join(PREVIEW, folder)
        os.makedirs(pdir, exist_ok=True)
        ppath = os.path.join(pdir, stem + ".jpg")
        try:
            im = Image.open(src).convert("RGB")
            w = 480
            h = max(1, round(im.height * w / im.width))
            im.resize((w, h), Image.LANCZOS).save(tpath, "JPEG", quality=82, optimize=True)
            pw = 800
            ph = max(1, round(im.height * pw / im.width))
            im.resize((pw, ph), Image.LANCZOS).save(ppath, "JPEG", quality=80, optimize=True)
            n_thumb += 1
        except Exception as e:
            print("thumb fail", src, e)
            continue
        with Image.open(src) as im:
            fw, fh = im.width, im.height
        fl = []
        for e, fn in sorted(files):
            kb = round(os.path.getsize(os.path.join(d, fn)) / 1024)
            total_files += 1
            total_mb += kb / 1024
            fl.append({"ext": e.upper(), "file": f"{OUTNAME}/{folder}/{fn}", "kb": kb})
        items.append({"label": label(stem, prefix), "stem": stem,
                      "thumb": f"thumbs/{folder}/{stem}.jpg",
                      "preview": f"preview/{folder}/{stem}.jpg",
                      "w": fw, "h": fh, "files": fl})
    data["models"].append({"folder": folder, "model": model, "short": short,
                           "year": year, "gen": gen, "desc": desc,
                           "count": len(items), "items": items})

data["total_files"] = total_files
data["total_mb"] = round(total_mb)
data["total_thumbs"] = n_thumb

with open(os.path.join(BASE, "data.json"), "w") as fh:
    json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))

print(f"models={len(data['models'])} thumbs={n_thumb} files={total_files} ~{round(total_mb)}MB")
for m in data["models"]:
    print(f"  {m['short']:16} items={m['count']:3}  e.g. {m['items'][0]['label']}")
