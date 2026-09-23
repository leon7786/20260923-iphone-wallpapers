#!/usr/bin/env python3
"""Integrate Apple's own macOS Desktop Pictures into the collection.

Naming convention for the added originals: Apple-<Name>.heic
Unambiguous OS names go to their existing set; everything else (device themes,
abstract gradients, dynamic-wallpaper stills) goes to a new set.
"""
import os, json, re, shutil
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

MAC = 'Apple-Wallpapers/03-Mac'
NEW_SET = 'macOS-Apple-Desktop-Pictures'
NEW_LABEL = 'Apple 官方桌面图合集'

RULES = [
    ('Big Sur', 'macOS-11-Big-Sur'),
    ('Catalina', 'macOS-10.15-Catalina'),
    ('Monterey', 'macOS-12-Monterey'),
    ('Ventura', 'macOS-13-Ventura'),
    ('Sonoma', 'macOS-14-Sonoma'),
]

def target(name):
    for kw, s in RULES:
        if kw.lower() in name.lower():
            return s
    return NEW_SET

manifest = json.load(open('staging4/dp_manifest.json'))
os.makedirs(os.path.join(MAC, NEW_SET), exist_ok=True)

added = {}
for r in manifest:
    src = os.path.join('staging4/_extract', r['zip'][:-4], 'AssetData', r['file'])
    stem = re.sub(r'\s+', '-', r['file'][:-5])          # strip .heic, spaces -> dashes
    dst_name = f'Apple-{stem}.heic'
    dest_set = target(r['file'])
    dst = os.path.join(MAC, dest_set, dst_name)
    if os.path.exists(dst):
        print('exists', dst_name); continue
    shutil.copy2(src, dst)
    os.chmod(dst, 0o644)
    added.setdefault(dest_set, []).append(dst)
    print(f'{dest_set:32} {dst_name:44} {r["w"]}x{r["h"]} {r["mb"]:7.2f} MB')

print('\n=== 每个套装新增:')
for s, files in sorted(added.items()):
    tot = sum(os.path.getsize(f) for f in files) / 1048576
    print(f'  {s:32} +{len(files):2} 张  {tot:7.1f} MB')

# rebuild index rows for every touched set
idx = json.load(open('recon/index_all.json'))
touched = set(added) | {s for s in [x for _, x in RULES]}
idx = [r for r in idx if r['folder'] not in touched]
for s in sorted(touched):
    d = os.path.join(MAC, s)
    if not os.path.isdir(d):
        continue
    group = 'Apple 官方桌面图' if s == NEW_SET else None
    for f in sorted(os.listdir(d)):
        fp = os.path.join(d, f)
        with Image.open(fp) as im:
            w, h = im.size
        row = {'platform': 'mac', 'folder': s, 'file': fp,
               'kb': round(os.path.getsize(fp) / 1024, 1), 'ext': f.rsplit('.', 1)[1].lower(),
               'w': w, 'h': h}
        if group:
            row['group'] = group
        idx.append(row)
json.dump(idx, open('recon/index_all.json', 'w'), ensure_ascii=False)
print(f'\nindex rows now: {len(idx)}')
