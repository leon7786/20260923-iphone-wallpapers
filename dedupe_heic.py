#!/usr/bin/env python3
"""One file per artwork in the Mac sets.

21 pairs were byte-identical (the Apple original was already in the tree under another
name) -> drop the non-canonical copy. Three pairs differ only in encode quality -> keep
the higher-bpp file. Rebuilds index rows so disk == index.
"""
import json, os
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

d = json.load(open('recon/heic_dupes.json'))
removed = []

for o, p in d['identical']:
    os.remove(o); removed.append(o)                       # keep the Apple-* copy

for o, p in d['different']:
    so, sp = os.path.getsize(o), os.path.getsize(p)
    drop = o if so < sp else p                            # keep the bigger encode
    os.remove(drop); removed.append(drop)
    print(f'  {(drop == o and [os.path.basename(o), "ours"] or [os.path.basename(o), "keep"])[0]:26} '
          f'{so/1048576:7.2f} vs {sp/1048576:7.2f} MB  -> kept {os.path.basename(o if drop == p else p)}')

freed = sum(1 for _ in removed)
print(f'\n删除 {freed} 个重复（同一幅画只留一份最高码率）')

idx = json.load(open('recon/index_all.json'))
idx = [r for r in idx if r['platform'] != 'mac']
MAC = 'Apple-Wallpapers/03-Mac'
for s in sorted(os.listdir(MAC)):
    dd = os.path.join(MAC, s)
    if not os.path.isdir(dd):
        continue
    for f in sorted(os.listdir(dd)):
        fp = os.path.join(dd, f)
        if not os.path.isfile(fp):
            continue
        with Image.open(fp) as im:
            w, h = im.size
        idx.append({'platform': 'mac', 'folder': s, 'file': fp,
                    'kb': round(os.path.getsize(fp) / 1024, 1), 'ext': f.rsplit('.', 1)[1].lower(),
                    'w': w, 'h': h})
json.dump(idx, open('recon/index_all.json', 'w'), ensure_ascii=False)
disk = sum(len(fs) for _, _, fs in os.walk('Apple-Wallpapers'))
print(f'index rows: {len(idx)} | disk files: {disk} | Mac 体积: {sum(os.path.getsize(os.path.join(r,f)) for r,_,fs in os.walk(MAC) for f in fs)/1073741824:.2f} GB')
