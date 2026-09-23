#!/usr/bin/env python3
"""macOS cleanup:
   1. delete the 48 low-bitrate JPEG copies of artworks now held as Apple originals;
   2. split the 49-file 'macOS-Apple-Desktop-Pictures' dump into a nature set and a
      device-theme set (keeps every Release ZIP well under 1 GB);
   3. rebuild index rows for all touched sets so disk == index.
"""
import os, json, shutil
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

MAC = 'Apple-Wallpapers/03-Mac'
OLD = os.path.join(MAC, 'macOS-Apple-Desktop-Pictures')

NATURE = ('The Lake', 'The Cliffs', 'The Desert', 'The Beach', 'Dome', 'Valley',
          'Peak', 'Tree', 'Solar Gradients', 'Iridescence')
SETS = {'macOS-Apple-Nature': ('Apple 官方桌面图 · 自然风景', NATURE),
        'macOS-Apple-Device-Themes': ('Apple 官方桌面图 · 机型与渐变主题', None)}

# 1. drop weak duplicates
cands = json.load(open('recon/dedupe_candidates2.json'))
removed = 0
for c in cands:
    if os.path.exists(c['jpg']):
        os.remove(c['jpg']); removed += 1
print(f'删除低码率重复副本: {removed} 个文件, 释放 {sum(c["jpg_mb"] for c in cands):.1f} MB')

# 2. split
moved = {}
for f in sorted(os.listdir(OLD)):
    src = os.path.join(OLD, f)
    if not os.path.isfile(src):
        continue
    base = f[:-5].replace('Apple-', '').replace('-', ' ')
    target = 'macOS-Apple-Device-Themes'
    for kw in NATURE:
        if kw.lower() in base.lower():
            target = 'macOS-Apple-Nature'; break
    os.makedirs(os.path.join(MAC, target), exist_ok=True)
    shutil.move(src, os.path.join(MAC, target, f))
    moved[target] = moved.get(target, 0) + 1
os.rmdir(OLD)
for s, n in moved.items():
    d = os.path.join(MAC, s)
    print(f'{s:30} {n:2} 张  {sum(os.path.getsize(os.path.join(d,x)) for x in os.listdir(d))/1048576:7.1f} MB')

# 3. rebuild index for every Mac set (cheap, keeps rows exactly in sync)
idx = json.load(open('recon/index_all.json'))
idx = [r for r in idx if r['platform'] != 'mac']
for s in sorted(os.listdir(MAC)):
    d = os.path.join(MAC, s)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        fp = os.path.join(d, f)
        if not os.path.isfile(fp):
            continue
        with Image.open(fp) as im:
            w, h = im.size
        row = {'platform': 'mac', 'folder': s, 'file': fp,
               'kb': round(os.path.getsize(fp) / 1024, 1), 'ext': f.rsplit('.', 1)[1].lower(),
               'w': w, 'h': h}
        idx.append(row)
json.dump(idx, open('recon/index_all.json', 'w'), ensure_ascii=False)
disk = sum(len(fs) for _, _, fs in os.walk('Apple-Wallpapers'))
print(f'\nindex rows: {len(idx)} | disk files: {disk}')
