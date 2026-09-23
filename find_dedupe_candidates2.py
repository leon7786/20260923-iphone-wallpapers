#!/usr/bin/env python3
"""Colour-aware duplicate matcher: Apple-*.heic  vs  existing JPEGs in the Mac sets.

dHash (grayscale) merges hue variants, so pair it with a 4x4 mean-RGB signature:
a candidate must match structurally (dHash <= 2) AND in colour (mean |dRGB| <= 10).
"""
import os, json, glob
from PIL import Image, ImageOps, ImageDraw
import pillow_heif
pillow_heif.register_heif_opener()

MAC = 'Apple-Wallpapers/03-Mac'

def sig(path):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        small = im.resize((8, 8), Image.LANCZOS)
        px = list(small.getdata())
        gray = im.convert('L').resize((9, 8), Image.LANCZOS)
        gp = list(gray.getdata())
        bits = 0
        for r in range(8):
            for c in range(8):
                bits = (bits << 1) | (1 if gp[r * 9 + c] > gp[r * 9 + c + 1] else 0)
        return bits, px                                  # (structure, 64 RGB triples)

def hamming(a, b):
    return bin(a ^ b).count('1')

def colour_dist(pa, pb):
    return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) for a, b in zip(pa, pb)) / (len(pa) * 3)

natives = glob.glob(f'{MAC}/*/Apple-*.heic')
jpgs = glob.glob(f'{MAC}/*/*.jpg') + glob.glob(f'{MAC}/*/*.jpeg')
print(f'Apple 原版 {len(natives)} / JPEG {len(jpgs)}')

ns = {p: sig(p) for p in natives}
cands = []
for j in jpgs:
    jb, jp = sig(j)
    best, bd, bc = None, 99, 999
    for p, (pb, pp) in ns.items():
        d = hamming(jb, pb)
        if d > 2:
            continue
        c = colour_dist(jp, pp)
        if c < bc:
            best, bd, bc = p, d, c
    if best and bc <= 10:
        cands.append({'jpg': j, 'apple': best, 'dist': bd, 'cdist': round(bc, 1),
                      'jpg_mb': round(os.path.getsize(j) / 1048576, 2),
                      'apple_mb': round(os.path.getsize(best) / 1048576, 2)})

cands.sort(key=lambda c: (c['cdist'], -c['apple_mb']))
print(f'候选: {len(cands)} 对\n')
for c in cands:
    print(f"  d={c['dist']} cd={c['cdist']:5.1f}  {c['jpg'].split('/')[-2]:22} {c['jpg'].split('/')[-1][:36]:38} {c['jpg_mb']:7.2f}MB → {os.path.basename(c['apple'])[:36]:38} {c['apple_mb']:7.2f}MB")
json.dump(cands, open('recon/dedupe_candidates2.json', 'w'), ensure_ascii=False, indent=1)

if cands:
    CW = CH = 260
    rows = len(cands)
    sheet = Image.new('RGB', (CW * 2 + 30, (CH + 20) * rows + 10), (252, 252, 252))
    d = ImageDraw.Draw(sheet)
    for i, c in enumerate(cands):
        for k, p in enumerate([c['jpg'], c['apple']]):
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im).convert('RGB')
                sheet.paste(ImageOps.fit(im, (CW, CH), Image.LANCZOS), (10 + k * (CW + 10), 10 + i * (CH + 20)))
        d.text((10, 12 + i * (CH + 20) + CH),
               f"{os.path.basename(c['jpg'])[:44]} ({c['jpg_mb']}MB)  |  {os.path.basename(c['apple'])[:40]} ({c['apple_mb']}MB)",
               fill=(10, 10, 10))
    sheet.save('/tmp/dedupe_sheet2.jpg', 'JPEG', quality=88)
    print('\n对比图 -> /tmp/dedupe_sheet2.jpg')
print(f'可释放: {sum(c["jpg_mb"] for c in cands):.1f} MB')
