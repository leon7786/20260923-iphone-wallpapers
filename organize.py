#!/usr/bin/env python3
# Extract the iClarified zips and organise iPhone 13-18 stock wallpapers.
# Files are attributed to a folder by (source zip, filename predicate) so a
# generic predicate cannot pull in files from other zips.
import os, re, shutil, zipfile, json
from PIL import Image

BASE = "/root/Projects/20260922-iphone-wallpapers"
ZIPS = os.path.join(BASE, "zips")
OUT = os.path.join(BASE, "iPhone-stock-wallpapers-13to18")

LAYOUT = [
    ("01-iPhone-13",      "iClarified-iOS15-iPhone-Wallpaper.zip",  lambda n: "iPhone13-" in n),
    ("02-iPhone-13-Pro",  "iClarified-iOS15-iPhone-Wallpaper.zip",  lambda n: "iPhone13Pro-" in n),
    ("03-iPhone-14",      "iClarified-iPhone14-Wallpaper.zip",      lambda n: n.startswith("iClarified-iPhone14-")),
    ("04-iPhone-14-Pro",  "iClarified-iPhone14-Wallpaper.zip",      lambda n: "iPhone14Pro-" in n),
    ("05-iPhone-15",      "iClarified-iPhone15-Wallpaper.zip",      lambda n: re.match(r"iClarified-iPhone15-[A-Z]", n) is not None),
    ("06-iPhone-15-Pro",  "iClarified-iPhone15-Wallpaper.zip",      lambda n: "iPhone15Pro-" in n),
    ("07-iPhone-16",      "iClarified-iPhone16-Wallpaper.zip",      lambda n: re.match(r"iClarified-iPhone16-[A-Z]", n) is not None),
    ("08-iPhone-16-Pro",  "iClarified-iPhone16-Wallpaper.zip",      lambda n: "iPhone16Pro-" in n),
    ("09-iPhone-16e",     None,                                     None),
    ("10-iPhone-17",      "iClarified-iPhone17-Wallpaper.zip",      lambda n: re.match(r"iClarified-iPhone17-[A-Z]", n) is not None),
    ("11-iPhone-17-Pro",  "iClarified-iPhone17-Wallpaper.zip",      lambda n: "iPhone17Pro-" in n),
    ("12-iPhone-Air",     "iClarified-iPhoneAir-Wallpaper.zip",     lambda n: "iPhoneAir-" in n),
    ("13-iPhone-17e",     None,                                     None),
    ("14-iPhone-18-Pro",  "iClarified-iPhone-18-Pro-Wallpaper.zip", lambda n: n.startswith("iClarified-iPhone-18-Pro-Wallpaper-")),
    ("15-iPhone-Duo",     "iClarified-iPhone-Duo-Wallpaper.zip",    lambda n: n.startswith("iClarified-iPhone-Duo-Wallpaper-")),
]

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

# open every zip, keep {basename: (zipname, member)}
members = {}
for z in sorted(os.listdir(ZIPS)):
    if not z.endswith(".zip"):
        continue
    with zipfile.ZipFile(os.path.join(ZIPS, z)) as zf:
        for m in zf.namelist():
            b = os.path.basename(m)
            if not b or b.startswith("._") or b == ".DS_Store" or "__MACOSX" in m:
                continue
            members[b] = (z, m, os.path.join(ZIPS, z))

def extract(zpath, member, dst):
    with zipfile.ZipFile(zpath) as zf, zf.open(member) as src, open(dst, "wb") as out:
        shutil.copyfileobj(src, out)

report = {}
for folder, zname, pred in LAYOUT:
    d = os.path.join(OUT, folder)
    os.makedirs(d, exist_ok=True)
    if zname is None:
        if folder == "09-iPhone-16e":
            pairs = [("staging/iPhone-16e-Official.jpg", "iPhone16e-Official.jpg")]
        else:
            pairs = [("staging/iPhone-17e-Soft-Pink.jpg", "iPhone17e-SoftPink.jpg"),
                     ("staging/iPhone-17e-White.jpg", "iPhone17e-White.jpg"),
                     ("staging/iPhone-17e-Black.jpg", "iPhone17e-Black.jpg")]
        for s, n in pairs:
            shutil.copy2(os.path.join(BASE, s), os.path.join(d, n))
    else:
        for b, (z, m, zp) in sorted(members.items()):
            if z != zname or not pred(b):
                continue
            extract(zp, m, os.path.join(d, re.sub(r"^iClarified-", "", b)))

    info = []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        try:
            with Image.open(p) as im:
                info.append({"file": f, "w": im.width, "h": im.height,
                             "format": im.format, "kb": round(os.path.getsize(p)/1024)})
        except Exception as e:
            info.append({"file": f, "w": 0, "h": 0,
                         "format": os.path.splitext(f)[1].lstrip(".").upper() + "?",
                         "note": str(e)[:60],
                         "kb": round(os.path.getsize(p)/1024)})
    report[folder] = info

with open(os.path.join(BASE, "report.json"), "w") as fh:
    json.dump(report, fh, indent=1, ensure_ascii=False)

for k, v in report.items():
    sizes = sorted({(i.get("w") or 0, i.get("h") or 0) for i in v})
    fmts = sorted({i.get("format") for i in v})
    print(f"{k}: {len(v)} files  res={sizes}  fmt={fmts}")
    for i in v:
        print("    ", i["file"], i.get("w", "?"), "x", i.get("h", "?"), i.get("format"), f'{i["kb"]}KB')
print("TOTAL", sum(len(v) for v in report.values()), "files")
