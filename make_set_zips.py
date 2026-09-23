#!/usr/bin/env python3
"""Build one ZIP per wallpaper set (Apple-Wallpapers/<platform>/<set>)."""
import os, subprocess, json, sys, time

BASE = 'Apple-Wallpapers'
OUT = 'zips_out'
os.makedirs(OUT, exist_ok=True)

rows = []
for plat in sorted(os.listdir(BASE)):
    pd = os.path.join(BASE, plat)
    if not os.path.isdir(pd):
        continue
    for st in sorted(os.listdir(pd)):
        sd = os.path.join(pd, st)
        if not os.path.isdir(sd):
            continue
        n = sum(len(fs) for _, _, fs in os.walk(sd))
        if n == 0:
            print('skip empty', sd, flush=True)
            continue
        name = f'{plat}__{st}.zip'
        dst = os.path.join(OUT, name)
        if os.path.exists(dst) and os.path.getsize(dst) > 0:
            print('exists', name, flush=True)
            rows.append({'file': name, 'platform': plat, 'set': st, 'files': n,
                         'mb': round(os.path.getsize(dst) / 1048576, 1)})
            continue
        t = time.time()
        r = subprocess.run(['zip', '-r', '-1', '-q', os.path.abspath(dst), st],
                           cwd=os.path.join(os.getcwd(), pd),
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f'FAIL {name}: rc={r.returncode} stderr={r.stderr.strip()[:200]}', flush=True)
            if os.path.exists(dst):
                os.remove(dst)
            continue
        sz = os.path.getsize(dst) / 1048576
        rows.append({'file': name, 'platform': plat, 'set': st, 'files': n, 'mb': round(sz, 1)})
        print(f'{name:52} {n:3} files {sz:7.1f} MB  {time.time()-t:.0f}s', flush=True)

json.dump(rows, open('recon/zips_out.json', 'w'), ensure_ascii=False, indent=1)
print(f'TOTAL zips {len(rows)}  MB {round(sum(r["mb"] for r in rows), 1)}')
