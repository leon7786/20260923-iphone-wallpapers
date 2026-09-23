#!/usr/bin/env python3
"""Final range downloader.

Fixes two traps found earlier:
  1. the origin truncates long GETs at random offsets -> fetch in 2 MB ranges;
  2. preallocating the target made a zero-filled, wrong file look "complete" ->
     write chunks into <name>.part at explicit offsets and only rename after the
     archive verifies. Never treat an existing file as cached unless its CRC passes.
"""
import os, re, json, time, zipfile, subprocess
import concurrent.futures as cf

BASE = "/root/Projects/20260922-iphone-wallpapers"
ZIPS = os.path.join(BASE, "staging2/_zips")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
CHUNK = 2 * 1024 * 1024


def head(url):
    r = subprocess.run(["curl", "-sI", "-A", UA, url, "--max-time", "30"],
                       capture_output=True, text=True)
    c = re.search(r"HTTP/\S+ (\d{3})", r.stdout)
    ln = re.search(r"[Cc]ontent-[Ll]ength:\s*(\d+)", r.stdout)
    return (c.group(1) if c else "000"), (int(ln.group(1)) if ln else 0)


def grab(url, start, end, tries=8):
    want = end - start + 1
    last = ""
    for t in range(tries):
        r = subprocess.run(["curl", "-s", "-A", UA, "-r", f"{start}-{end}", url,
                            "--max-time", "300", "--retry", "2", "--retry-all-errors",
                            "--retry-delay", "2"], capture_output=True)
        d = r.stdout
        if len(d) == want:
            return d, "ok"
        last = f"{len(d)}/{want}"
        time.sleep(min(2 + t * 2, 12))
    return None, last


def valid_zip(p):
    try:
        with zipfile.ZipFile(p) as zf:
            return zf.testzip() is None
    except Exception:
        return False


def fetch(url, dst, log=print):
    if os.path.exists(dst) and valid_zip(dst):
        return True, "cached", os.path.getsize(dst), os.path.getsize(dst)
    if os.path.exists(dst):
        os.remove(dst)
    code, total = head(url)
    if code not in ("200", "206") or total <= 0:
        return False, f"head {code}", 0, 0
    part = dst + ".part"
    if os.path.exists(part):
        os.remove(part)
    done = set()
    offsets = list(range(0, total, CHUNK))
    diag = ""
    with open(part, "wb+") as fh:
        for pass_no in (1, 2, 3):
            left = [o for o in offsets if o not in done]
            if not left:
                break
            for start in left:
                end = min(start + CHUNK - 1, total - 1)
                d, why = grab(url, start, end, tries=6 if pass_no == 1 else 4)
                if d is None:
                    diag = f"@{start} {why}"
                    continue
                fh.seek(start)
                fh.write(d)
                done.add(start)
            if pass_no < 3:
                time.sleep(2)
    sz = os.path.getsize(part)
    if len(done) != len(offsets) or sz != total:
        return False, f"incomplete {len(done)}/{len(offsets)} chunks sz={sz}/{total} {diag}", sz, total
    os.rename(part, dst)
    ok = valid_zip(dst)
    return ok, "ok" if ok else "crc-fail", os.path.getsize(dst), total


def work(f):
    assets = json.load(open(os.path.join(BASE, "recon/assets.json")))
    aid = re.match(r"^(\d+)-", f).group(1)
    idx = int(re.search(r"-(\d+)\.zip$", f).group(1))
    url = assets[aid]["zips"][idx]
    p = os.path.join(ZIPS, f)
    t0 = time.time()
    ok, why, sz, exp = fetch(url, p)
    return f"{'OK  ' if ok else 'FAIL'} {f:38} {sz/1048576:7.1f}/{exp/1048576:7.1f} MB {time.time()-t0:5.0f}s {why}"


if __name__ == "__main__":
    broken = [f for f in sorted(os.listdir(ZIPS))
              if not valid_zip(os.path.join(ZIPS, f)) and not f.endswith(".part")]
    print(f"to fetch/repair: {len(broken)}", flush=True)
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for line in ex.map(work, broken):
            print(line, flush=True)
    tot = sum(os.path.getsize(os.path.join(ZIPS, x)) for x in os.listdir(ZIPS) if x.endswith(".zip"))
    n = sum(1 for x in os.listdir(ZIPS) if x.endswith(".zip"))
    print(f"\n{n} zips, {tot/1048576:.0f} MB, {time.time()-t0:.0f}s", flush=True)
    print("still bad:", [f for f in sorted(os.listdir(ZIPS))
                         if f.endswith(".zip") and not valid_zip(os.path.join(ZIPS, f))], flush=True)
