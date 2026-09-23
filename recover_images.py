#!/usr/bin/env python3
"""Phase B3: recover full-size originals whose only HTML reference was a srcset variant."""
import os, re, json, subprocess
import concurrent.futures as cf

BASE = "/root/Projects/20260922-iphone-wallpapers"
REC = os.path.join(BASE, "recon")
OUT = os.path.join(BASE, "staging2/_extracted")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
assets = json.load(open(os.path.join(REC, "assets.json")))

def slug(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-")

cands = []
for aid, x in assets.items():
    p = os.path.join(REC, "pages", aid + ".html")
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    ids = {}
    for m in re.finditer(rf'/images/news/{aid}/(\d+)/\1-(\d+)\.(jpg|jpeg|png|heic)', h, re.I):
        iid, sz, ext = m.group(1), int(m.group(2)), m.group(3).lower()
        if iid == aid:                     # article lead image
            continue
        ids.setdefault(iid, set()).add(ext)
        ids[iid].add("__max__" + str(sz))
    for iid, exts in ids.items():
        mx = max((int(e[7:]) for e in exts if e.startswith("__max__")), default=0)
        for ext in sorted(e for e in exts if not e.startswith("__")):
            cands.append((aid, x["platform"], slug(x["group"]), iid, ext, mx))

print("candidates:", len(cands), flush=True)

def head(url):
    r = subprocess.run(["curl", "-sI", "-A", UA, url, "--max-time", "25"],
                       capture_output=True, text=True)
    out = r.stdout
    code = re.search(r"HTTP/\S+ (\d{3})", out)
    ln = re.search(r"[Cc]ontent-[Ll]ength:\s*(\d+)", out)
    return (code.group(1) if code else "000"), int(ln.group(1)) if ln else 0

def work(c):
    aid, plat, grp, iid, ext, mx = c
    url = f"https://www.iclarified.com/images/news/{aid}/{iid}/{iid}.{ext}"
    code, ln = head(url)
    if code != "200" or ln < 300_000:      # tiny = icons/avatars, never a wallpaper
        return None
    dst_dir = os.path.join(OUT, plat, grp)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, f"{iid}.{ext}")
    if os.path.exists(dst) and os.path.getsize(dst) == ln:
        return (plat, grp, iid, ext, ln, "cached")
    for _ in range(3):
        subprocess.run(["curl", "-sL", "-A", UA, "-o", dst, url, "--max-time", "600",
                        "--retry", "5", "--retry-all-errors", "--retry-delay", "4"], check=False)
        if os.path.exists(dst) and abs(os.path.getsize(dst) - ln) < 2048:
            return (plat, grp, iid, ext, ln, "ok")
    return (plat, grp, iid, ext, ln, "FAIL")

rows = []
with cf.ThreadPoolExecutor(max_workers=3) as ex:
    for r in ex.map(work, cands):
        if r:
            rows.append(r)
            print(f"{r[5]:6} {r[0]:8} {r[1][:24]:26} {r[2]}.{r[3]}  {r[4]/1048576:6.1f} MB", flush=True)

got = [r for r in rows if r[5] in ("ok", "cached")]
print(f"\nfound {len(rows)} full-size candidates, fetched {len(got)}, "
      f"{sum(r[4] for r in got)/1048576:.0f} MB", flush=True)
