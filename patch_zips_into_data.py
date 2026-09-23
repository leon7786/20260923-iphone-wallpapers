#!/usr/bin/env python3
"""Add per-set ZIP (GitHub Release asset) info to data.json."""
import json, urllib.parse

REPO = 'https://github.com/leon7786/20260923-iphone-wallpapers'
TAG = {'01-iPhone': 'v2.0-iphone', '02-iPad': 'v2.0-ipad', '03-Mac': 'v2.0-mac',
       '04-iOS-generic': 'v2.0-ios', '05-Special': 'v2.0-special'}
PDIR = {'iphone': '01-iPhone', 'ipad': '02-iPad', 'mac': '03-Mac',
        'ios': '04-iOS-generic', 'special': '05-Special'}

zips = {f"{z['platform']}__{z['set']}.zip": z for z in json.load(open('recon/zips_out.json'))}
d = json.load(open('data.json'))
missing = []
for p in d['platforms']:
    pdir = PDIR[p['id']]
    tag = TAG[pdir]
    for s in p['sets']:
        name = f"{pdir}__{s['id']}.zip"
        z = zips.get(name)
        if not z:
            missing.append(f"{p['id']}/{s['id']}")
            continue
        s['zip'] = name
        s['zip_mb'] = z['mb']
        s['zip_url'] = f"{REPO}/releases/download/{tag}/{urllib.parse.quote(name)}"
d['releases'] = {v: f"{REPO}/releases/tag/{v}" for v in TAG.values()}
json.dump(d, open('data.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('sets with zip:', sum(1 for p in d['platforms'] for s in p['sets'] if 'zip' in s))
print('missing:', missing)
print('stats:', d['stats'])
for p in d['platforms']:
    print(f"  {p['id']:8} sets={len(p['sets']):2} zip_mb={sum(s.get('zip_mb',0) for s in p['sets']):7.1f}")
