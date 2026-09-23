#!/usr/bin/env python3
"""macOS 27 quality fix:
   - the 'macOS-27-Sunset-and-Night' set held iClarified's low-bitrate re-encodes
     (2.93 / 3.49 MB); replace them with the high-bitrate copies already archived in
     'macOS-27-Golden-Gate' (5.26 / 3.90 MB, same artwork, same 4096x2160);
   - add Apple's own desktop-picture files pulled from a macOS 27 install:
     Default.heic (bridge photo, 4096x2160) and DefaultDark.heic (6K abstract dark).
   Keeps recon/index_all.json in sync so disk == index == site.
"""
import os, json, shutil
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

BASE = 'Apple-Wallpapers/03-Mac'
SUN = f'{BASE}/macOS-27-Sunset-and-Night'
GG = f'{BASE}/macOS-27-Golden-Gate'

# 1. drop the low-bitrate re-encodes
for f in ['macOS-27-Sunset-and-Night-479298.jpg', 'macOS-27-Sunset-and-Night-479300.jpg']:
    p = os.path.join(SUN, f)
    if os.path.exists(p):
        os.remove(p)
        print('removed', f)

# 2. high-bitrate replacements (same artwork) + Apple native files
plan = [
    (f'{GG}/macOS-27-Golden-Gate-Sunset-Wallpaper.jpg', f'{SUN}/macOS-27-Sunset.jpg'),
    (f'{GG}/macOS-27-Golden-Gate-Night-Wallpaper.jpg', f'{SUN}/macOS-27-Night.jpg'),
    ('staging3/Default.heic', f'{SUN}/macOS-27-Default.heic'),
    ('staging3/DefaultDark.heic', f'{GG}/macOS-27-Golden-Gate-DefaultDark-6K.heic'),
]
for src, dst in plan:
    if not os.path.exists(src):
        print('MISSING SOURCE', src); continue
    shutil.copy2(src, dst)
    with Image.open(dst) as im:
        print(f'added {os.path.basename(dst):45} {im.size[0]}x{im.size[1]}  {os.path.getsize(dst)/1048576:.2f} MB  {im.format}')

# 3. rebuild index rows for the two sets from what is now on disk
idx = json.load(open('recon/index_all.json'))
keep = [r for r in idx if '/macOS-27-Sunset-and-Night/' not in r['file'] and '/macOS-27-Golden-Gate/' not in r['file']]
rows = []
for pdir, plat, folder, group in [(SUN, 'mac', 'macOS-27-Sunset-and-Night', 'macOS 27 Sunset / Night'),
                                  (GG, 'mac', 'macOS-27-Golden-Gate', 'macOS 27 Golden Gate')]:
    for f in sorted(os.listdir(pdir)):
        fp = os.path.join(pdir, f)
        with Image.open(fp) as im:
            w, h = im.size
        rows.append({'platform': plat, 'folder': folder, 'group': group, 'file': fp,
                     'kb': round(os.path.getsize(fp) / 1024, 1), 'ext': f.rsplit('.', 1)[1].lower(),
                     'w': w, 'h': h})
idx = keep + rows
json.dump(idx, open('recon/index_all.json', 'w'), ensure_ascii=False)
print(f'index rows: {len(idx)} (was {len(keep)} + {len(rows)} rebuilt)')
