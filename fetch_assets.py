#!/usr/bin/env python3
"""Phase A: fetch every Apple-wallpaper article page and extract its assets."""
import os, re, json, subprocess, concurrent.futures as cf

BASE = "/root/Projects/20260922-iphone-wallpapers"
REC = os.path.join(BASE, "recon")
PAGES = os.path.join(REC, "pages")
os.makedirs(PAGES, exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

# id -> (platform, group, label)
ART = {
    # ---- iPadOS ----
    "84255": ("ipad", "iPadOS 14", "iPadOS 14 官方壁纸"),
    "84264": ("ipad", "iPadOS 14.2", "iPadOS 14.2 官方壁纸"),
    "84270": ("ipad", "iPadOS 15", "iPadOS 15 官方壁纸"),
    "85186": ("ipad", "iPadOS 15.4", "iPadOS 15.4 官方壁纸"),
    "86278": ("ipad", "iPadOS 16", "iPadOS 16 官方壁纸"),
    "90842": ("ipad", "iPadOS 17", "iPadOS 17 官方壁纸"),
    "93901": ("ipad", "iPadOS 18", "iPadOS 18 官方壁纸"),
    "97559": ("ipad", "iPadOS 26", "iPadOS 26 官方壁纸"),
    "101092": ("ipad", "iPadOS 27", "iPadOS 27 官方壁纸"),
    "87924": ("ipad", "iPad 2022 / iPad Pro", "2022 iPad & iPad Pro 跟机壁纸"),
    "93538": ("ipad", "iPad Pro 2024", "2024 iPad Pro 跟机壁纸"),
    "93539": ("ipad", "iPad Air 2024", "2024 iPad Air 跟机壁纸"),
    "28994": ("ipad", "iPad 初代", "初代 iPad 官方壁纸"),
    # ---- macOS ----
    "76415": ("mac", "macOS 11 Big Sur", "macOS 11 Big Sur 官方壁纸"),
    "86274": ("mac", "macOS 12 Monterey", "macOS 12 Monterey 官方壁纸"),
    "86272": ("mac", "macOS 13 Ventura", "macOS 13 Ventura 官方壁纸"),
    "90814": ("mac", "macOS 14 Sonoma", "macOS 14 Sonoma 官方壁纸"),
    "91219": ("mac", "macOS 14 Sonoma Horizon", "Sonoma Horizon 附加壁纸"),
    "93902": ("mac", "macOS 15 Sequoia", "macOS 15 Sequoia 官方壁纸"),
    "94502": ("mac", "macOS 15 Sequoia Sunrise", "Sequoia Sunrise 附加壁纸"),
    "97556": ("mac", "macOS 26 Tahoe", "macOS 26 Tahoe 官方壁纸"),
    "101095": ("mac", "macOS 27 Golden Gate", "macOS 27 Golden Gate 官方壁纸"),
    "101391": ("mac", "macOS 27 Sunset / Night", "Golden Gate Sunset & Night"),
    "101807": ("mac", "macOS 27 Day / Evening", "Golden Gate Day & Evening"),
    "71135": ("mac", "macOS 10.15 Catalina", "macOS 10.15 Catalina 官方壁纸"),
    "86400": ("mac", "MacBook Air 2022", "2022 MacBook Air 跟机壁纸"),
    "88896": ("mac", "MacBook Pro 2023", "2023 MacBook Pro 跟机壁纸"),
    "90856": ("mac", "MacBook Air 2023", "2023 MacBook Air 跟机壁纸"),
    "91914": ("mac", "MacBook Pro M3 2023", "2023 M3 MacBook Pro 跟机壁纸"),
    "91916": ("mac", "iMac 2023", "2023 iMac 跟机壁纸"),
    "95356": ("mac", "iMac M4 2024", "2024 M4 iMac 跟机壁纸"),
    "100111": ("mac", "MacBook Neo", "MacBook Neo 跟机壁纸"),
    # ---- iOS generic ----
    "84237": ("ios", "iOS 12", "iOS 12 官方壁纸（iPhone / iPad / iPod touch）"),
    "71174": ("ios", "iOS 13", "iOS 13 官方壁纸"),
    "84252": ("ios", "iOS 14", "iOS 14 官方壁纸"),
    "84258": ("ios", "iOS 14.1 / iPhone 12", "iOS 14.1（iPhone 12）官方壁纸"),
    "84261": ("ios", "iOS 14.2", "iOS 14.2 官方壁纸"),
    "85110": ("ios", "iOS 15.4", "iOS 15.4 官方壁纸"),
    "86246": ("ios", "iOS 16", "iOS 16 官方壁纸"),
    "90816": ("ios", "iOS 17", "iOS 17 官方壁纸"),
    "93874": ("ios", "iOS 18", "iOS 18 官方壁纸"),
    "97554": ("ios", "iOS 26", "iOS 26 官方壁纸"),
    "97855": ("ios", "iOS 26 Shadow / Halo / Dusk", "iOS 26 beta 3 追加壁纸"),
    "101089": ("ios", "iOS 27", "iOS 27 官方壁纸"),
    # ---- special / event / store ----
    "86618": ("special", "Clownfish 初代 iPhone", "初代 iPhone 小丑鱼壁纸（全分辨率）"),
    "87130": ("special", "Far Out 发布会 2022", "Apple Far Out 发布会壁纸"),
    "91249": ("special", "iPhone 15 发布会 2023", "iPhone 15 发布会壁纸"),
    "90016": ("special", "WWDC 2023", "WWDC 2023 壁纸"),
    "93179": ("special", "WWDC 2024", "WWDC 2024 壁纸"),
    "101020": ("special", "WWDC 2026", "WWDC 2026 壁纸（iPhone / iPad / Mac）"),
    "92575": ("special", "Unity Bloom", "Unity Bloom 壁纸"),
    "93554": ("special", "Pride Radiance 2024", "Pride Radiance 壁纸"),
    "90466": ("special", "Pride 2023", "Pride 2023 壁纸"),
    "100746": ("special", "Pride 2026", "Pride 2026 壁纸"),
    "97776": ("special", "Umeda 店铺", "大阪 Umeda 店铺壁纸"),
    "93022": ("special", "静安店 2023", "上海静安店壁纸"),
    "100037": ("special", "Borivali 店", "Apple Borivali 店铺壁纸"),
    "89764": ("special", "Gangnam 店", "首尔江南店壁纸"),
    "47390": ("special", "Spring Forward 2015", "Spring Forward 发布会壁纸"),
    "49630": ("special", "WWDC 2015", "WWDC 2015 壁纸"),
    "54932": ("special", "地球日", "Apple 地球日壁纸"),
    "58584": ("special", "中国新年", "Apple 中国新年壁纸"),
}

def fetch(aid):
    p = os.path.join(PAGES, aid + ".html")
    if os.path.exists(p) and os.path.getsize(p) > 50000:
        return aid, "cached"
    url = f"https://www.iclarified.com/{aid}/"
    r = subprocess.run(["curl", "-sL", "-A", UA, "-o", p, url, "--max-time", "60"],
                       capture_output=True, text=True)
    return aid, (os.path.getsize(p) if os.path.exists(p) else 0)

with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for aid, size in ex.map(fetch, list(ART)):
        print(aid, size, ART[aid][2][:40])

# ---- parse ----
IMG = re.compile(r'https?://www\.i[Cc]larified\.com/(images/news|files)/([^"\'\s<>]+)', re.I)
res = {}
for aid, meta in ART.items():
    p = os.path.join(PAGES, aid + ".html")
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    zips, imgs = set(), set()
    for m in re.finditer(r'href="(https?://[^"]+\.zip)"', h, re.I):
        zips.add(m.group(1))
    for m in IMG.finditer(h):
        u = f"https://www.iclarified.com/{m.group(1)}/{m.group(2)}"
        if re.search(r'-\d+\.(jpg|jpeg|png|webp)$', u, re.I):   # resized previews
            continue
        if u.lower().endswith((".avif", ".webp")):
            continue
        imgs.add(u)
    res[aid] = {"platform": meta[0], "group": meta[1], "label": meta[2],
                "zips": sorted(zips), "images": sorted(imgs)}

json.dump(res, open(os.path.join(REC, "assets.json"), "w"), indent=1, ensure_ascii=False)
tot_zip = tot_img = 0
print("\n=== parse summary ===")
for aid, d in sorted(res.items(), key=lambda kv: (kv[1]["platform"], kv[1]["group"])):
    print(f'{aid:7} {d["platform"]:8} {d["group"][:26]:28} zips={len(d["zips"])} imgs={len(d["images"]):3}  {d["label"][:34]}')
    tot_zip += len(d["zips"]); tot_img += len(d["images"])
print(f"\narticles={len(res)} total zips={tot_zip} total full-size images={tot_img}")
