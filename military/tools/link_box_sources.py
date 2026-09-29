#!/usr/bin/env python3
"""
Step 1c: attach the Box source to every rate-card row.

Uses audit/box_listing_<date>.json (the per-base folder listing pulled from Box) to fill three columns
in data/rate_card.csv for each base:
  box_folder_url   - the base's folder in Box > Military > 2 Military Installations
  box_source_file  - the newest pricing-looking file in that folder (rate card / media kit / price sheet)
  box_source_url   - link to that file
Rows keep whatever link was already set (e.g. typed in the app), so re-running never overwrites a manual link.
"""
import csv, json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
from box_audit import ALIAS, norm, PRICE_RX, POC_RX
CSV = os.path.join(ROOT, 'data', 'rate_card.csv')
DATE = sys.argv[1] if len(sys.argv) > 1 else '2026-09-28'
LISTING = os.path.join(ROOT, 'audit', f'box_listing_{DATE}.json')
NEW = ['box_folder_url', 'box_source_file', 'box_source_url']
# bases whose rate card lives in a regional / parent folder in Box
PARENT = {'Southeast Naval Region': ['Jacksonville NAS', 'Mayport NAVSTA', 'Pensacola NAS', 'Key West NAS', 'Whiting Field NAS', 'Kings Bay NAVSUBBASE', 'Gulfport NCBC', 'Meridian NAS', 'Corpus Christi NAS', 'Kingsville NAS', 'New Orleans NAS JRB', 'NSA Mid South', 'Nav Coastal Systems Ctr Panama City NSA', 'NOTU Cape Cape Canaveral', 'Homestead AFB'],
          'Mid Atlantic Naval Region': ['Naval Station Norfolk', 'NAS Oceana', 'JEB - Little Creek', 'Dam Neck Annex', 'Cheatham Annex', 'WPNSTA Yorktown', 'NSW Dahlgren', 'Patuxent River NAS', 'Indian Head NAV ORD STA', 'Annapolis NS (Incl. USNA)', 'Walter Reed NNMC Bethesda', 'Portsmouth Naval Shipyard', 'Saratoga Springs Naval Support Unit'],
          'NorthWest Naval Region': ['Naval AIr Station Whidbey Island', 'Naval Base Kitsap-Bangor', 'Naval Base Kitsap-Bremerton'],
          'USAG Alaska': ['Fort Greely', 'Fort Jonathan Wainwright'], 'USAG Hawaii': ['Fort Shafter', 'Wheeler Army Airfield'], 'JB Pearl Harbor Hickman': ['Hickam AFB'], 'MCB Hawaii': ['MCB Hawaii'], 'Pacific Missile Range Facility': ['Pacific Missile Range Facilty (Barking Sands)'],
          'JB San Antonio': ['Lackland AFB', 'Randolph AFB'], 'JB Myer Henderson Hall Mcnair': ['JBMHH - Henderson Hall'], 'JB Lewis McChord': ['JBLM - McChord AFB'], 'Beaufort and Parris Island MCB': ['Parris Island MCRD'], 'Defense Logistic Agency': ['Defense Distribution Depot Susquehanna']}

def main():
    rows = list(csv.DictReader(open(CSV)))
    fields = list(rows[0].keys())
    for k in NEW:
        if k not in fields: fields.insert(fields.index('source') + 1, k) if 'source' in fields else fields.append(k)
    for r in rows:
        for k in NEW: r.setdefault(k, '')
    listing = json.load(open(LISTING))
    bases = sorted(set(r['base'] for r in rows))
    mnorm = {norm(b): b for b in bases}
    folder_for = {}
    for fo in listing:
        f = fo['folder']; mb = ALIAS.get(f)
        if mb not in bases:
            n = norm(f); mb = mnorm.get(n)
            if not mb:
                for k, b in mnorm.items():
                    if len(n) > 3 and (n in k or k in n): mb = b; break
        if not mb: continue
        d = lambda x: (x.get('content_modified_at') or x.get('modified_at') or '')[:10]
        pricing = [x for x in fo['files'] if PRICE_RX.search(x['name']) and not POC_RX.search(x['name'])]
        newest = max(pricing, key=d, default=None)
        folder_for.setdefault(mb, (f"https://wilkinsmedia.app.box.com/folder/{fo['folder_id']}", newest['name'] if newest else '', f"https://wilkinsmedia.app.box.com/file/{newest['id']}" if newest else ''))
    byname = {fo['folder']: fo for fo in listing}
    for fname, kids in PARENT.items():
        fo = byname.get(fname)
        if not fo: continue
        d = lambda x: (x.get('content_modified_at') or x.get('modified_at') or '')[:10]
        pricing = [x for x in fo['files'] if PRICE_RX.search(x['name']) and not POC_RX.search(x['name'])]
        newest = max(pricing, key=d, default=None)
        for kid in kids:
            folder_for.setdefault(kid, (f"https://wilkinsmedia.app.box.com/folder/{fo['folder_id']}", newest['name'] if newest else '', f"https://wilkinsmedia.app.box.com/file/{newest['id']}" if newest else ''))
    n = 0
    for r in rows:
        if r['box_folder_url']: continue
        hit = folder_for.get(r['base'])
        if hit: r['box_folder_url'], r['box_source_file'], r['box_source_url'] = hit; n += 1
    with open(CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    linked = sum(1 for r in rows if r['box_folder_url']); files = sum(1 for r in rows if r['box_source_url'])
    print(f'linked {linked}/{len(rows)} rows to a Box folder ({files} with a specific file); bases without a folder link:', [b for b in bases if b not in folder_for])

if __name__ == '__main__':
    main()
