#!/usr/bin/env python3
"""Phase B2: serially repair truncated ZIPs with resume + retry until CRC-valid."""
import os, re, json, subprocess, zipfile, time

BASE = "/root/Projects/20260922-iphone-wallpapers"
REC = os.path.join(BASE, "recon")
ZIPS = os.path.join(BASE, "staging2/_zips")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
assets = json.load(open(os.path.join(REC, "assets.json")))

def valid(p, expect=None):
    try:
        with zipfile.ZipFile(p) as zf:
            if zf.testzip() is not None:
                return False, "crc"
        sz = os.path.getsize(p)
        if expect and abs(sz - expect) / expect > 0.02:
            return False, f"size {sz/1048576:.1f} vs {expect/1048576:.1f}"
        return True, os.path.getsize(p) / 1048576
    except Exception as e:
        return False, type(e).__name__

todo = []
for f in sorted(os.listdir(ZIPS)):
    p = os.path.join(ZIPS, f)
    ok, why = valid(p)
    if not ok:
        todo.append((f, p, why))
print(f"to repair: {len(todo)}", flush=True)

for f, p, why in todo:
    aid = re.match(r"^(\d+)-", f).group(1)
    idx = int(re.search(r"-(\d+)\.zip$", f).group(1))
    url = assets[aid]["zips"][idx]
    ok = False
    for attempt in range(1, 6):
        sz0 = os.path.getsize(p) if os.path.exists(p) else 0
        subprocess.run(["curl", "-sL", "-C", "-", "-A", UA, "-o", p, url,
                        "--max-time", "2400", "--retry", "10", "--retry-all-errors",
                        "--retry-delay", "5", "--speed-time", "60", "--speed-limit", "2048"],
                       check=False)
        ok, info = valid(p)
        print(f"{f:36} try{attempt} {sz0/1048576:7.1f} -> "
              f"{(os.path.getsize(p)/1048576 if os.path.exists(p) else 0):7.1f} MB  {info}",
              flush=True)
        if ok:
            break
        time.sleep(5)
    if not ok:
        print(f"GIVE UP {f} ({info})", flush=True)

print("REPAIR DONE", flush=True)
tot = sum(os.path.getsize(os.path.join(ZIPS, x)) for x in os.listdir(ZIPS))
print(f"zip cache total: {tot/1048576:.0f} MB in {len(os.listdir(ZIPS))} files", flush=True)
