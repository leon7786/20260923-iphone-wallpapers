#!/usr/bin/env python3
"""Tidy filenames, write README + report.json, build a preview contact sheet."""
import os, re, json, zipfile
from PIL import Image

BASE = "/root/Projects/20260922-iphone-wallpapers"
OUT = os.path.join(BASE, "iPhone-stock-wallpapers-13to18")

RENAMES = [
    (r"^iOS15-iPhone13-Twist-",            "iPhone13-Twist-"),
    (r"^iOS15-iPhone13Pro-LightBeams-",    "iPhone13Pro-LightBeams-"),
    (r"^iPhone-18-Pro-Wallpaper-",         "iPhone18Pro-"),
    (r"^iPhone-Duo-Wallpaper-",            "iPhoneDuo-"),
]

for root, dirs, files in os.walk(OUT):
    for f in files:
        new = f
        for pat, rep in RENAMES:
            new = re.sub(pat, rep, new)
        if new != f:
            os.rename(os.path.join(root, f), os.path.join(root, new))

META = {
    "01-iPhone-13":     ("iPhone 13 / 13 mini", "2021", "Twist（5 色 × 浅色/深色）"),
    "02-iPhone-13-Pro": ("iPhone 13 Pro / Pro Max", "2021", "Light Beams（4 色 × 浅色/深色）"),
    "03-iPhone-14":     ("iPhone 14 / 14 Plus", "2022", "5 色"),
    "04-iPhone-14-Pro": ("iPhone 14 Pro / Pro Max", "2022", "4 色"),
    "05-iPhone-15":     ("iPhone 15 / 15 Plus", "2023", "5 色"),
    "06-iPhone-15-Pro": ("iPhone 15 Pro / Pro Max", "2023", "4 色 × 锁屏/主屏/息屏"),
    "07-iPhone-16":     ("iPhone 16 / 16 Plus", "2024", "5 色"),
    "08-iPhone-16-Pro": ("iPhone 16 Pro / Pro Max", "2024", "4 色"),
    "09-iPhone-16e":    ("iPhone 16e", "2025", "1 款"),
    "10-iPhone-17":     ("iPhone 17", "2025", "5 色 × 锁屏/主屏"),
    "11-iPhone-17-Pro": ("iPhone 17 Pro / Pro Max", "2025", "3 色 × 锁屏/主屏"),
    "12-iPhone-Air":    ("iPhone Air", "2025", "4 色 × 锁屏/主屏"),
    "13-iPhone-17e":    ("iPhone 17e", "2026", "3 色"),
    "14-iPhone-18-Pro": ("iPhone 18 Pro / Pro Max", "2026", "Vitra（4 色 × 锁屏/主屏）"),
    "15-iPhone-Duo":    ("iPhone Duo（折叠）", "2026", "内屏/外屏 × 锁屏/主屏 × 浅色/深色"),
}

report = {}
rows = []
for folder in sorted(META):
    d = os.path.join(OUT, folder)
    items = []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        entry = {"file": f, "kb": round(os.path.getsize(p) / 1024)}
        try:
            with Image.open(p) as im:
                entry["w"], entry["h"], entry["format"] = im.width, im.height, im.format
        except Exception:
            entry["w"] = entry["h"] = 0
            entry["format"] = os.path.splitext(f)[1].lstrip(".").upper()
        items.append(entry)
    report[folder] = items
    res = sorted({(i["w"], i["h"]) for i in items if i["w"]})
    fmts = sorted({i["format"] for i in items})
    jpgs = len([i for i in items if i["format"] == "JPEG"])
    rows.append((folder, META[folder], len(items), jpgs, res, fmts,
                 round(sum(i["kb"] for i in items) / 1024)))

with open(os.path.join(BASE, "report.json"), "w") as fh:
    json.dump(report, fh, indent=1, ensure_ascii=False)

total = sum(r[2] for r in rows)
total_mb = sum(r[6] for r in rows)

lines = []
lines.append("# iPhone 13 – 18 官方跟机壁纸（原件）\n")
lines.append(f"共 **{total}** 个文件，约 **{total_mb} MB**，全部为 Apple 官方原图，未做任何缩放或压缩。\n")
lines.append("来源：iClarified 从 Apple 官方素材 / iOS 固件中提取并整理的原尺寸包（原始 ZIP 保留在 `../zips/`）。\n")
lines.append("\n## 目录\n")
lines.append("| 文件夹 | 机型 | 年份 | 内容 | 文件数 | 主要分辨率 |")
lines.append("|---|---|---|---|---|---|")
for folder, (model, year, desc), n, jpgs, res, fmts, mb in rows:
    rs = " / ".join(f"{w}×{h}" for w, h in res)
    lines.append(f"| `{folder}` | {model} | {year} | {desc} | {n} | {rs} |")
lines.append(f"\n**合计 {total} 个文件 / {total_mb} MB**\n")
lines.append("""
## 说明

- **原图**：均为官方提供方给出的最大尺寸（多数大于屏幕本身的逻辑分辨率，因为 Apple 的原生壁纸素材本身留了视差余量）。例如 iPhone 13 为 1404×3040、iPhone 13 Pro 为 1542×3334、iPhone 18 Pro 为 1320×2868。
- **格式**：`.jpg` 可直接任何设备使用；`.heic` 是 Apple 原生格式（iOS/macOS 可直接设为壁纸，画质更好、体积更小）。同一张图同时提供两种格式时都在，按需取用。
- **锁屏 / 主屏**：Pro 机型官方素材区分 Lock Screen 与 Home Screen（无时钟、无小组件的干净版本）。
- **浅色 / 深色**：13 系列与 Duo 区分 Light / Dark 两套。
- **2026 年阵容**：Apple 2026 年 9 月只发布了 iPhone 18 Pro / 18 Pro Max 与首款折叠机 iPhone Duo，没有标准版 iPhone 18，因此 18 代包含 Pro 与 Duo。
- **一键下载**：`iPhone-stock-wallpapers-13to18.zip` 为全部文件的打包。

## 来源页面

- iPhone 13 系列 / iOS 15：https://www.iclarified.com/84267/
- iPhone 14 系列：https://www.iclarified.com/87374/
- iPhone 15 系列：https://www.iclarified.com/91483/
- iPhone 16 系列：https://www.iclarified.com/94911/
- iPhone 16e：https://www.iclarified.com/96469/
- iPhone 17 / 17 Pro：https://www.iclarified.com/98545/
- iPhone Air：https://www.iclarified.com/98546/
- iPhone 17e：https://www.iclarified.com/100084/
- iPhone 18 Pro：https://www.iclarified.com/102105/
- iPhone Duo：https://www.iclarified.com/102102/
""")
with open(os.path.join(OUT, "README.md"), "w") as fh:
    fh.write("\n".join(lines))

# ZIP
zpath = os.path.join(BASE, "iPhone-stock-wallpapers-13to18.zip")
if os.path.exists(zpath):
    os.remove(zpath)
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(OUT):
        for f in files:
            p = os.path.join(root, f)
            zf.write(p, os.path.relpath(p, OUT))

# preview contact sheet (one JPG per model family)
picks = [
    ("01-iPhone-13", "iPhone13-Twist-Blue-Light.jpg"),
    ("02-iPhone-13-Pro", "iPhone13Pro-LightBeams-Gold-Light.jpg"),
    ("03-iPhone-14", "iPhone14-Purple.jpg"),
    ("04-iPhone-14-Pro", "iPhone14Pro-DeepPurple.jpg"),
    ("05-iPhone-15", "iPhone15-Green.jpg"),
    ("06-iPhone-15-Pro", "iPhone15Pro-BlueTitanium-LockScreen.jpg"),
    ("07-iPhone-16", "iPhone16-Ultramarine.jpg"),
    ("08-iPhone-16-Pro", "iPhone16Pro-DesertTitanium.jpg"),
    ("09-iPhone-16e", "iPhone16e-Official.jpg"),
    ("10-iPhone-17", "iPhone17-Sage-Lockscreen.jpg"),
    ("11-iPhone-17-Pro", "iPhone17Pro-CosmicOrange-Lockscreen.jpg"),
    ("12-iPhone-Air", "iPhoneAir-SkyBlue-LockScreen.jpg"),
    ("13-iPhone-17e", "iPhone17e-SoftPink.jpg"),
    ("14-iPhone-18-Pro", "iPhone18Pro-Burgundy-Lock-Screen.jpg"),
    ("15-iPhone-Duo", "iPhoneDuo-Inner-Lock-Screen-Light.jpg"),
]
TH, GAP = 420, 10
thumbs = []
for folder, fn in picks:
    p = os.path.join(OUT, folder, fn)
    im = Image.open(p).convert("RGB")
    w = max(1, round(im.width * TH / im.height))
    thumbs.append(im.resize((w, TH), Image.LANCZOS))
cols = 8
rowsN = (len(thumbs) + cols - 1) // cols
W = cols * (max(t.width for t in thumbs) + GAP) + GAP
H = rowsN * (TH + GAP) + GAP
sheet = Image.new("RGB", (W, H), (18, 18, 20))
x, y = GAP, GAP
for i, t in enumerate(thumbs):
    if i and i % cols == 0:
        x, y = GAP, y + TH + GAP
    sheet.paste(t, (x, y))
    x += t.width + GAP
sheet.save(os.path.join(BASE, "preview.jpg"), quality=88)

print(f"TOTAL {total} files, {total_mb} MB")
print("zip:", zpath, round(os.path.getsize(zpath) / 1024 / 1024, 1), "MB")
for r in rows:
    print(r[0], r[2], r[3], r[4], r[5], f"{r[6]}MB")
