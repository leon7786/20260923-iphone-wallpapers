#!/usr/bin/env python3
"""Download Apple's own macOS Desktop Picture assets (mesu MobileAsset catalog).

Catalog : https://mesu.apple.com/assets/macos/com_apple_MobileAsset_DesktopPicture/com_apple_MobileAsset_DesktopPicture.xml
Each asset: {__BaseURL}{__RelativePath} -> ZIP containing AssetData/<Name>.heic (native 6016x6016 etc.)
"""
import plistlib, subprocess, os, json, sys, time

CAT = 'https://mesu.apple.com/assets/macos/com_apple_MobileAsset_DesktopPicture/com_apple_MobileAsset_DesktopPicture.xml'
OUT = 'staging4/_dps'
os.makedirs(OUT, exist_ok=True)

if not os.path.exists('staging4/dp_catalog.xml'):
    subprocess.run(['curl', '-s', CAT, '-o', 'staging4/dp_catalog.xml'], check=True)
d = plistlib.load(open('staging4/dp_catalog.xml', 'rb'))
assets = d['Assets']
print(f'assets: {len(assets)}  total {sum(a["_DownloadSize"] for a in assets)/1073741824:.2f} GB', flush=True)

ok = fail = skip = 0
for i, a in enumerate(sorted(assets, key=lambda x: -x['_DownloadSize']), 1):
    url = a['__BaseURL'] + a['__RelativePath']
    name = a['__RelativePath'].split('/')[-1]
    dst = os.path.join(OUT, name)
    if os.path.exists(dst) and os.path.getsize(dst) == a['_DownloadSize']:
        skip += 1
        print(f'[{i:2}/{len(assets)}] skip {name}', flush=True)
        continue
    t = time.time()
    r = subprocess.run(['curl', '-sL', '--retry', '3', '--retry-delay', '3',
                        '--max-time', '600', url, '-o', dst], capture_output=True)
    sz = os.path.getsize(dst) if os.path.exists(dst) else 0
    if r.returncode == 0 and sz == a['_DownloadSize']:
        ok += 1
        print(f'[{i:2}/{len(assets)}] ok   {name}  {sz/1048576:6.1f} MB  {time.time()-t:.0f}s', flush=True)
    else:
        fail += 1
        print(f'[{i:2}/{len(assets)}] FAIL {name}  rc={r.returncode} got={sz} want={a["_DownloadSize"]}', flush=True)
        if os.path.exists(dst):
            os.remove(dst)

json.dump([{'zip': a['__RelativePath'].split('/')[-1], 'id': a.get('DesktopPictureID'),
            'build': a.get('Build'), 'bytes': a['_DownloadSize']} for a in assets],
          open('staging4/dp_assets.json', 'w'), ensure_ascii=False, indent=1)
print(f'\ndone: ok={ok} skip={skip} fail={fail}')
