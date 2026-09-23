#!/usr/bin/env python3
"""Refresh the Mac rows of recon/index_all.json from disk (disk == index)."""
import json, os
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

MAC = 'Apple-Wallpapers/03-Mac'
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
        idx.append({'platform': 'mac', 'folder': s, 'file': fp,
                    'kb': round(os.path.getsize(fp) / 1024, 1), 'ext': f.rsplit('.', 1)[1].lower(),
                    'w': w, 'h': h})
json.dump(idx, open('recon/index_all.json', 'w'), ensure_ascii=False)
disk = sum(len(fs) for _, _, fs in os.walk('Apple-Wallpapers'))
print(f'index rows: {len(idx)} | disk files: {disk} | mac rows: {sum(1 for r in idx if r["platform"]=="mac")}')
