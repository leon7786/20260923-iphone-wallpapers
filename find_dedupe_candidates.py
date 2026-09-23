#!/usr/bin/env python3
"""Find weak JPEG copies of the Apple desktop pictures inside the macOS sets.

dHash <= 2 only (tight, to avoid merging light/dark variants); every candidate is
rendered into a contact sheet for visual confirmation before anything is deleted.
"""
import os, json, glob
from PIL import Image, ImageOps, ImageDraw
import pillow_heif
pillow_heif.register_heif_opener()

MAC = 'Apple-Wallpapers/03-Mac'

def dhash(path, size=9):
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert('L').resize((size, size - 1), Image.LANCZOS)
        px = list(im.getdata())
    bits = 0
    for r in range(size - 1):
        for c in range(size - 1):
            bits = (bits << 1) | (1 if px[r * size + c] > px[r * size + c + 1] else 0)
    return bits

natives = glob.glob(f'{MAC}/*/Apple-*.heic')
others = [p for p in glob.glob(f'{MAC}/*/*.jpg') + glob.glob(f'{MAC}/*/*.jpeg')]
print(f'Apple 原版 {len(natives)} 张, 待比较 JPEG {len(others)} 张')

n = {p: dhash(p) for p in natives}
cands = []
for j in others:
    jh = dhash(j)
    best, bd = None, 99
    for p, ph in n.items():
        d = bin(jh ^ ph).count('1')
        if d < bd:
            best, bd = p, d
    if bd <= 2:
        mb_j, mb_n = os.path.getsize(j) / 1048576, os.path.getsize(best) / 1048576
        cands.append({'jpg': j, 'apple': best, 'dist': bd, 'jpg_mb': round(mb_j, 2), 'apple_mb': round(mb_n, 2)})

cands.sort(key=lambda c: -c['apple_mb'] / max(c['jpg_mb'], .01))
print(f'候选（dHash<=2）: {len(cands)} 对\n')
for c in cands[:20]:
    print(f"  d={c['dist']}  {c['jpg'].split('/')[-1][:42]:44} {c['jpg_mb']:7.2f}MB  → {os.path.basename(c['apple'])[:38]:40} {c['apple_mb']:7.2f}MB")
json.dump(cands, open('recon/dedupe_candidates.json', 'w'), ensure_ascii=False, indent=1)

# contact sheet: jpg vs apple heic for the top candidates
top = cands[:12]
if top:
    CW, CH = 300, 300
    rows = len(top)
    sheet = Image.new('RGB', (CW * 2 + 30, (CH + 22) * rows + 10), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for i, c in enumerate(top):
        for k, p in enumerate([c['jpg'], c['apple']]):
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im).convert('RGB')
                sheet.paste(ImageOps.fit(im, (CW, CH), Image.LANCZOS), (10 + k * (CW + 10), 10 + i * (CH + 22)))
        d.text((10, 12 + i * (CH + 22) + CH), f"{os.path.basename(c['jpg'])[:40]} ({c['jpg_mb']}MB)  vs  {os.path.basename(c['apple'])[:34]} ({c['apple_mb']}MB)", fill=(10, 10, 10))
    sheet.save('/tmp/dedupe_sheet.jpg', 'JPEG', quality=88)
    print('\n对比图: /tmp/dedupe_sheet.jpg')
