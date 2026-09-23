#!/usr/bin/env python3
"""Robust range-based downloader. The iClarified origin truncates large GETs at random
offsets (content-length 76 MB, delivered 4-14 MB) but serves correct 206 range responses,
so fetch big files in fixed chunks, retrying each chunk until it is complete."""
import os, re, subprocess, time

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
CHUNK = 4 * 1024 * 1024


def head(url, timeout=30):
    r = subprocess.run(["curl", "-sI", "-A", UA, url, "--max-time", str(timeout)],
                       capture_output=True, text=True)
    code = re.search(r"HTTP/\S+ (\d{3})", r.stdout)
    ln = re.search(r"[Cc]ontent-[Ll]ength:\s*(\d+)", r.stdout)
    return (code.group(1) if code else "000"), (int(ln.group(1)) if ln else 0)


def grab_range(url, start, end, tries=6):
    """Return bytes for [start,end] or None."""
    want = end - start + 1
    for t in range(tries):
        r = subprocess.run(["curl", "-s", "-A", UA, "-r", f"{start}-{end}", url,
                            "--max-time", "180", "--retry", "2", "--retry-all-errors"],
                           capture_output=True)
        data = r.stdout
        if len(data) == want:
            return data
        if len(data) > want:               # server ignored Range and sent more
            return None
        time.sleep(1 + t)
    return None


def fetch(url, dst, expect=None, log=print):
    """Download url -> dst using ranges. Returns (ok, size, size_expected)."""
    code, total = head(url)
    if code != "200" or total <= 0:
        if code not in ("200", "206") or total <= 0:      # fall back to a plain GET
            subprocess.run(["curl", "-sL", "-A", UA, "-o", dst, url, "--max-time", "600"],
                           check=False)
            sz = os.path.getsize(dst) if os.path.exists(dst) else 0
            return (sz > 1024 and (expect is None or abs(sz - expect) < 4096)), sz, expect or sz
    if expect is None:
        expect = total
    if os.path.exists(dst) and os.path.getsize(dst) == expect:
        return True, expect, expect
    if os.path.exists(dst):
        os.remove(dst)
    with open(dst, "wb") as fh:
        for start in range(0, total, CHUNK):
            end = min(start + CHUNK - 1, total - 1)
            data = grab_range(url, start, end)
            if data is None:
                log(f"  chunk {start}-{end} FAILED for {os.path.basename(dst)}")
                return False, os.path.getsize(dst), total
            fh.write(data)
            fh.flush()
    sz = os.path.getsize(dst)
    return sz == total, sz, total


if __name__ == "__main__":
    import json, zipfile, sys
    BASE = "/root/Projects/20260922-iphone-wallpapers"
    ZIPS = os.path.join(BASE, "staging2/_zips")
    assets = json.load(open(os.path.join(BASE, "recon/assets.json")))

    todo = []
    for f in sorted(os.listdir(ZIPS)):
        p = os.path.join(ZIPS, f)
        ok = False
        try:
            with zipfile.ZipFile(p) as zf:
                ok = zf.testzip() is None
        except Exception:
            ok = False
        if not ok:
            todo.append(f)
    print(f"broken zips to fetch with ranges: {len(todo)}", flush=True)

    for f in todo:
        aid = re.match(r"^(\d+)-", f).group(1)
        idx = int(re.search(r"-(\d+)\.zip$", f).group(1))
        url = assets[aid]["zips"][idx]
        p = os.path.join(ZIPS, f)
        t0 = time.time()
        ok, sz, exp = fetch(url, p)
        good = False
        if ok:
            try:
                with zipfile.ZipFile(p) as zf:
                    good = zf.testzip() is None
            except Exception:
                good = False
        print(f"{'OK  ' if good else 'FAIL'} {f:38} {sz/1048576:7.1f}/{exp/1048576:7.1f} MB "
              f"{time.time()-t0:5.0f}s", flush=True)
        if not good:
            print("     url:", url, flush=True)

    tot = sum(os.path.getsize(os.path.join(ZIPS, x)) for x in os.listdir(ZIPS))
    print(f"\nzip cache: {len(os.listdir(ZIPS))} files, {tot/1048576:.0f} MB", flush=True)
