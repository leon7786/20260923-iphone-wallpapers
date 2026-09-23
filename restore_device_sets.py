#!/usr/bin/env python3
"""Move the byte-identical Apple copies back to their original device sets.

The 21 identical pairs proved the collection already held Apple's natives under the
device-set names; keeping the copy in the new Apple set hollowed those sets out
(iMac-2023, MacBook-Air-2022/2023, MacBook-Pro-2023/M3-2023) and left one empty.
So: recreate the original path from the surviving Apple copy, then drop the Apple copy.
"""
import json, os, shutil

d = json.load(open('recon/heic_dupes.json'))
APPSET = 'macOS-Apple-Device-Themes'
restored = 0
for o, p in d['identical']:
    if os.path.dirname(p) != f'Apple-Wallpapers/03-Mac/{APPSET}':
        continue                                   # only the Apple-set copies move
    if not os.path.exists(p):
        continue
    if os.path.exists(o):                          # original survived -> just drop the copy
        os.remove(p); continue
    os.makedirs(os.path.dirname(o), exist_ok=True)
    shutil.move(p, o)
    os.chmod(o, 0o644)
    restored += 1

empty = []
MAC = 'Apple-Wallpapers/03-Mac'
for s in sorted(os.listdir(MAC)):
    dd = os.path.join(MAC, s)
    if os.path.isdir(dd) and not any(os.path.isfile(os.path.join(dd, f)) for f in os.listdir(dd)):
        empty.append(dd)
print(f'放回机型套装: {restored} 个 | Apple 套装剩余: {len(os.listdir(os.path.join(MAC, APPSET)))} 个')
print(f'空套装: {empty}')
