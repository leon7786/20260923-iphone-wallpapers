#!/usr/bin/env python3
"""Resumable range downloader for iClarified zips.
Their origin truncates long GETs at random offsets, so: fixed-size range chunks, positional
writes (so a failure never costs earlier progress), per-chunk retries with backoff, then a
final pass over any offsets still missing."""
import os, re, json, subprocess, time, zipfile, sys

BASE = "/root/Projects/20260922-iphone-wallpapers"
ZIPS = os.path.join(BASE, "staging2/_zips")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
CHUNK = 2 * 1024 * 1024


def head(url):
    r = subprocess.run(["curl", "-sI", "-A", UA, url, "--max-time", "30"],
                       capture_output=True, text=True)
    code = re.search(r"HTTP/\S+ (\d{3})", r.stdout)
    ln = re.search(r"[Cc]ontent-[Ll]ength:\s*(\d+)", r.stdout)
    if not ln:
        cr = re.search(r"[Cc]ontent-[Rr]ange:\s*bytes\s+\d+-\d+/(\d+)", r.stdout)
        ln = cr
    return (code.group(1) if code else "000"), (int(ln.group(1)) if ln else 0)


def grab(url, start, end, tries=8):
    """Fetch [start,end]; return (data|None, diag)."""
    want = end - start + 1
    diag = ""
    for t in range(tries):
        r = subprocess.run(["curl", "-s", "-A", UA, "-r", f"{start}-{end}", url,
                            "--max-time", "300", "--retry", "2", "--retry-all-errors",
                            "--retry-delay", "2"],
                           capture_output=True)
        d = r.stdout
        if len(d) == want:
            return d, "ok"
        diag = f"got {len(d)}/{want} rc={r.returncode}"
        time.sleep(min(2 + t * 2, 12))
    return None, diag


def fetch(url, dst):
    code, total = head(url)
    if code not in ("200", "206") or total <= 0:
        return False, f"head {code}", 0, 0
    if os.path.exists(dst) and os.path.getsize(dst) == total:
        return True, "cached", total, total
    if os.path.exists(dst) and os.path.getsize(dst) > total:
        os.remove(dst)
    size = total
    missing = list(range(0, size, CHUNK))
    diag = ""
    with open(dst, "r+b" if os.path.exists(dst) else "wb") as fh:
        if fh.seek(0, 2) != size:
            fh.truncate(size)                      # preallocate: positional writes stay valid
        for start in missing[:]:
            end = min(start + CHUNK - 1, size - 1)
            d, why = grab(url, start, end)
            if d is None:
                diag = f"chunk@{start} {why}"
                continue
            fh.seek(start)
            fh.write(d)
            missing.remove(start)
        # second pass for whatever failed
        for start in missing[:]:
            end = min(start + CHUNK - 1, size - 1)
            time.sleep(2)
            d, why = grab(url, start, end, tries=6)
            if d is None:
                diag = f"chunk@{start} {why}"
                continue
            fh.seek(start)
            fh.write(d)
            missing.remove(start)
    if missing:
        return False, f"{len(missing)} chunks missing ({diag})", os.path.getsize(dst), total
    return True, "ok", os.path.getsize(dst), total


if __name__ == "__main__":
    assets = json.load(open(os.path.join(BASE, "recon/assets.json")))
    broken = []
    for f in sorted(os.listdir(ZIPS)):
        p = os.path.join(ZIPS, f)
        try:
            with zipfile.ZipFile(p) as zf:
                if zf.testzip() is not None:
                    broken.append(f)
        except Exception:
            broken.append(f)
    print(f"broken zips: {len(broken)}", flush=True)
    for f in broken:
        aid = re.match(r"^(\d+)-", f).group(1)
        idx = int(re.search(r"-(\d+)\.zip$", f).group(1))
        url = assets[aid]["zips"][idx]
        p = os.path.join(ZIPS, f)
        t0 = time.time()
        ok, why, sz, exp = fetch(url, p)
        good = False
        if ok:
            try:
                with zipfile.ZipFile(p) as zf:
                    good = zf.testzip() is None
            except Exception as e:
                why = type(e).__name__
        print(f"{'OK  ' if good else 'FAIL'} {f:38} {sz/1048576:7.1f}/{exp/1048576:7.1f} MB "
              f"{time.time()-t0:5.0f}s  {why}", flush=True)
    tot = sum(os.path.getsize(os.path.join(ZIPS, x)) for x in os.listdir(ZIPS))
    left = sum(1 for x in os.listdir(ZIPS)
               if not (lambda q: (lambda: False)())(x) and False)
    print(f"\nzip cache: {len(os.listdir(ZIPS))} files, {tot/1048576:.0f} MB", flush=True)
