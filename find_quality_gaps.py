#!/usr/bin/env python3
"""Find duplicate artwork in the collection and flag bitrate gaps.

bpp alone is content-dependent (smooth gradients compress tiny), so instead:
  1. perceptual hash (dHash) every image -> group near-identical artwork;
  2. within a group, compare bytes-per-pixel of the copies;
  3. a group with a >=1.5x gap means the same artwork is archived twice, once
     noticeably worse (this is how the macOS 27 sunset/night pair was found).
"""
import os, json, sys
from PIL import Image, ImageOps
import pillow_heif
pillow_heif.register_heif_opener()

BASE = 'Apple-Wallpapers'

def dhash(path, size=9):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert('L').resize((size, size - 1), Image.LANCZOS)
        px = list(im.getdata())
    bits = 0
    for r in range(size - 1):
        for c in range(size - 1):
            bits = (bits << 1) | (1 if px[r * size + c] > px[r * size + c + 1] else 0)
    return bits

def hamming(a, b):
    return bin(a ^ b).count('1')

files = []
for root, _, fs in os.walk(BASE):
    for f in fs:
        p = os.path.join(root, f)
        try:
            files.append((p, os.path.getsize(p)))
        except OSError:
            pass
print(f'scanning {len(files)} files...', file=sys.stderr)

hashes = []
for i, (p, sz) in enumerate(files):
    try:
        hashes.append((p, sz, dhash(p)))
    except Exception as e:
        print('skip', p, e, file=sys.stderr)
    if i % 200 == 0:
        print(f'  {i}/{len(files)}', file=sys.stderr)

# group by near-identical hash
groups = []
for p, sz, h in hashes:
    for g in groups:
        if hamming(g[0][2], h) <= 3:
            g.append((p, sz, h))
            break
    else:
        groups.append([(p, sz, h)])

dup = [g for g in groups if len(g) > 1]
print(f'\n相同/近似画面分组: {len(dup)} 组（涉及 {sum(len(g) for g in dup)} 个文件）')

report = []
for g in dup:
    stats = []
    for p, sz, _ in g:
        with Image.open(p) as im:
            w, h = im.size
        stats.append({'p': p, 'mb': sz / 1048576, 'bpp': sz / (w * h), 'wh': f'{w}x{h}'})
    lo = min(stats, key=lambda s: s['bpp']); hi = max(stats, key=lambda s: s['bpp'])
    if lo['bpp'] > 0 and hi['bpp'] / lo['bpp'] >= 1.5:
        report.append((hi['bpp'] / lo['bpp'], lo, hi, len(g)))

report.sort(key=lambda x: -x[0])
print(f'其中码率差 >=1.5 倍的组: {len(report)}\n')
for ratio, lo, hi, n in report[:25]:
    print(f'{ratio:4.1f}x  同一画面 {n} 份')
    print(f'      低: {lo["p"].replace(BASE+"/",""):64} {lo["wh"]:>11} {lo["mb"]:6.2f}MB bpp={lo["bpp"]:.3f}')
    print(f'      高: {hi["p"].replace(BASE+"/",""):64} {hi["wh"]:>11} {hi["mb"]:6.2f}MB bpp={hi["bpp"]:.3f}')
json.dump([{'ratio': r, 'low': l, 'high': h, 'copies': n} for r, l, h, n in report],
          open('recon/dup_bitrate_report.json', 'w'), ensure_ascii=False, indent=1)
print(f'\n完整报告 -> recon/dup_bitrate_report.json ({len(report)} 组)')
