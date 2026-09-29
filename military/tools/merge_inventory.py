#!/usr/bin/env python3
"""
Step 1b of the rate-card pipeline: fold the two June-2026 inventory masters into rate_card.csv.

  data/source_digital_inventory_6.3.26.txt        <- Box > Military > "Military - National Digital Inventory Master 6.3.26.xlsx"
  data/source_publication_inventory_june2026.txt  <- Box > Military > "Military - National Publication Inventory Master_June 2026.xlsx"

Both are newer (June 2026) than the 12.2.25 master and cover bases / media the master never had.
Rule: a base+media that the master already prices is left alone (a note records the inventory value
if it differs); anything the master lacks is added as a new row with source = the inventory file.
Run after standardize.py and before build_rate_card.py.
"""
import csv, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, '..', 'data')
CSV = os.path.join(DATA, 'rate_card.csv')
DIG = os.path.join(DATA, 'source_digital_inventory_6.3.26.txt')
PUB = os.path.join(DATA, 'source_publication_inventory_june2026.txt')

DIG_COLS = [  # (client col, vendor col, screens col, media type, category, description template)
    (11, 17, 18, 'Digital Monitor Network', 'Digital', 'Your ad will appear on the {n}digital monitor network in approved installation facilities.'),
    (12, 19, 20, 'Digital Kiosk Network', 'Digital', 'Your ad will appear on the {n}digital kiosk network in approved installation facilities.'),
    (13, 21, 22, 'Bowling Scoring Monitors', 'Digital', 'Your ad will appear on the {n}scoring monitors in the installation bowling center.'),
    (14, 23, 24, 'Digital Marquee', 'Digital', 'Your ad will appear on the {n}digital marquee(s) on the installation.'),
    (15, 25, 26, 'Movie Theater Ad', 'Digital', 'Your ad will appear on screen before movies at the installation theater ({n}screens).'),
]
PUB_COLS = [
    (11, 19, 'Weekly E-Newsletter Ad', 'Web & Email', 'Your ad will appear in the weekly e-newsletter emailed to the installation community.'),
    (12, 20, 'Monthly E-Newsletter Ad', 'Web & Email', 'Your ad will appear in the monthly e-newsletter emailed to the installation community.'),
    (13, 21, 'Web Ad', 'Web & Email', 'Your ad will appear on the installation MWR / FSS website.'),
    (14, 22, 'Calendar Ad', 'Print & Publications', 'Your ad will appear in the installation events calendar.'),
    (15, 23, 'Magazine Ad', 'Print & Publications', 'Your ad will appear in the installation magazine.'),
    (16, 24, 'Guide / Map Ad', 'Print & Publications', 'Your ad will appear in the installation guide or map.'),
    (17, 25, 'Golf Scorecard Ad', 'Print & Publications', 'Your ad will appear on the golf course scorecard.'),
]
# inventory base name -> master base name (only where normalization alone fails)
ALIAS = {
    'Fort Bragg': 'Fort Liberty', 'Fort Gordon': 'Fort Eisenhower', 'Fort Rucker': 'Fort Novosel', 'Fort Lee': 'Fort Gregg-Adams',
    'Fort Polk': 'Fort Johnson', 'Fort Meade': 'Fort George G. Meade', 'Joint Base Lewis - McChord': 'JBLM',
    'Pearl Harbor - Hickam': 'Pearl Harbor NS', 'JB Pearl Harbor - Hickam': 'Pearl Harbor NS', 'JB Anacostia–Bolling': 'JBAB Anacostia NS',
    'JB Anacostia-Bolling': 'JBAB Anacostia NS', 'NSA Washington': 'Washington NAVDIST HQ', 'Fort Stewart': 'Fort Stewart / Hunter Army Airfield',
    'Maxwell AFB (Incl. Gunter)': 'Maxwell AFB (Incl. Gunter)', 'Aberdeen Proving Ground/ Edgewood Area': 'Aberdeen Proving Ground/ Edgewood Area',
    'Camp Lejeune MCB': 'New River MCAS', 'Camp Lejeune/New River/Albany MCB': 'New River MCAS', 'JB San Antonio': 'Fort Sam Houston',
    'Naval Base San Diego': 'Point Loma', 'San Diego Naval Network': 'Point Loma', 'San Diego Metro Network (Naval Base San Diego/ Naval Air Station North Island/ Naval Amphibious Base/ Naval Base Point Loma-Harbour Drive Annex/ Naval Base Point Loma-SUBASE/ Naval Medical Center San Diego)': 'Point Loma',
    'Northwest Naval Region': 'Naval Station Everett', 'Northwest Navy Network (NAS Whidbey Island/ NB Kitsap-Bangor/ NB Kitsap-Bremerton/ NS Everett)': 'Naval Station Everett',
    'JB Andrews AFB': 'Andrews Air Force Base', 'Tripler Army Medical Center (USAG Hawaii)': 'Tripler Army Medical Center',
    'Whiteman AFB': 'Whiteman AFB', 'Portsmouth Naval Shipyard': 'Portsmouth Naval Shipyard', 'Panama City NSA': 'Nav Coastal Systems Ctr Panama City NSA',
    'NOTU Cape Canaveral': 'NOTU Cape Cape Canaveral', 'Mid-South NAS': 'NSA Mid South', 'Homestead ARB': 'Homestead AFB', 'JRB Fort Worth NAS': 'NAS JRB Fort Worth',
    'Yorktown Coast Guard Training Center': 'Yorktown Navy Weapon Station', 'Fort AP Hill': 'Fort AP Hill', 'Camp Elmore': 'Camp Elmore',
    'USAG Hawaii Network': 'USAG Hawaii', 'USAG Hawaii Network (Aliamanu Military Reservation/ Fort DeRussey/ Fort Shafter/Helemano Military Reservation/Schofield Barracks/Tripler Army Medical Center/Wheeler Army Airfield)': 'USAG Hawaii',
    'Hampton Roads Network': None, 'Hampton Roads Network (Dam Neck Annex / NAS Oceana / JEB Little Creek / JEB Fort Story / Naval Station Norfolk / Norfolk Naval Shipyard / NSA HR-Headquarters / NSA HR-Portsmouth / NSA HR-Northwest Annex / WPNSTA Yorktown / Cheatham Annex / Huntington Hall': None,
    'Hampton Roads Network (Dam Neck Annex / NAS Oceana / JEB Little Creek / JEB Fort Story / Naval Station Norfolk / Norfolk Naval Shipyard / NSA HR-Headquarters / NSA HR-Portsmouth / NSA HR-Northwest Annex / WPNSTA Yorktown / Cheatham Annex / Huntington Hall)': None,
}
STOP = r'\b(air force base|air force|afb|sfb|arb|ars|nas|naval|station|base|joint|jb|fort|ft|camp|mcas|mclb|mcb|mcrd|army|garrison|usag|incl|the|of|and|us|mc|navsta|navsubbase|nws|nsa|ns|jrb|center|centre|training|installation)\b'
def norm(s):
    s = re.sub(r'\(.*?\)', ' ', s.lower()); s = re.sub(STOP, ' ', s); return ' '.join(re.findall(r'[a-z0-9]+', s))

def money(v):
    if isinstance(v, (int, float)): return v if v > 0 else None
    v = (v or '').strip()
    if v in ('', '-', '$0', '$ -', '$   -', 'N/A', 'NA', 'TBD', '??') or v.startswith('Part of') or v.startswith('ERROR'): return None
    m = re.sub(r'[^0-9.]', '', v)
    try: n = float(m); return n if n > 0 else None
    except ValueError: return None

def read_rows(path):
    """Yield lists of cells; folds Excel threaded-comment blocks back into the row they interrupted."""
    lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
    rows, buf, i = [], None, 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('tc={'):
            # skip the comment boilerplate up to 'Comment:' then the comment text line continues the row
            while i < len(lines) and not lines[i].startswith('Comment:'): i += 1
            i += 1
            if i < len(lines) and buf is not None:
                txt = lines[i].strip('\n')
                comment, _, rest = txt.partition('\t')
                buf += ('\t' + rest if rest else '')
                buf += '\t<<note:' + comment.strip() + '>>'
            i += 1; continue
        if re.match(r'^\t\t[A-Z]{2}(/[A-Z]{2})?\t', ln) or re.match(r'^\tXX\t[A-Z]{2}\t', ln):
            if buf is not None: rows.append(buf)
            buf = ln
        elif buf is not None and ln.strip() and not ln.startswith('\t\t') and ln.count('\t') == 0:
            buf += ' ' + ln.strip()          # wrapped cell text ("(USAG Hawaii)")
        elif buf is not None and ln.startswith('\t') and ln.count('\t') > 5 and not re.match(r'^\t\t[A-Z]', ln):
            rows.append(buf); buf = None
        i += 1
    if buf is not None: rows.append(buf)
    out = []
    for r in rows:
        notes = ' '.join(re.findall(r'<<note:(.*?)>>', r))
        r = re.sub(r'\t?<<note:.*?>>', '', r)
        cells = r.split('\t')
        if cells and cells[0] == '' and len(cells) > 1 and cells[1] == 'XX': cells = [''] + cells[1:]
        out.append((cells, notes))
    return out

def term_for(note):
    """Returns (column, multiplier). The inventory columns are 1-month prices unless the note says the
    price itself is quarterly/annual; a 'commitment'/'minimum' note keeps the monthly price but is stored
    as the minimum term's total so the app enforces the minimum."""
    n = (note or '').lower()
    if re.search(r'sold annually|annual price|per year|price for one year|^annual|\bannual\b(?!.*commitment)', n): return 'vendor_12mo', 1
    if re.search(r'sold quarterly|quarterly price|per quarter|per season', n): return 'vendor_3mo', 1
    if re.search(r'annual commitment|12[- ]month (commitment|min)', n): return 'vendor_12mo', 12
    if re.search(r'6[- ]month (commitment|min)', n): return 'vendor_6mo', 6
    if re.search(r'3[- ]month (commitment|min)|three month (commitment|min)', n) and not re.search(r'max', n): return 'vendor_3mo', 3
    if re.search(r'2[- ]month (commitment|min)', n): return 'vendor_3mo', 3
    return 'vendor_1mo', 1

def main():
    master = list(csv.DictReader(open(CSV)))
    fields = list(master[0].keys())
    bybase = collections.defaultdict(list)
    for r in master: bybase[r['base']].append(r)
    mnorm = {norm(b): b for b in bybase}
    def match(name):
        name = re.sub(r'\s+', ' ', name).strip()
        if name in ALIAS: return ALIAS[name]
        n = norm(name)
        if n in mnorm: return mnorm[n]
        for k, b in mnorm.items():
            if len(n) > 4 and (n == k or n in k.split() or k in n.split()): return b
        return None
    added, noted, unmatched, skipped_network = 0, 0, collections.Counter(), 0
    newbases = {}
    def add(base, state, dma, branch, ad, dep, media, cat, desc, vendor, term, note, src, screens=None):
        nonlocal added
        row = {k: '' for k in fields}
        row.update(base=base, state=state, dma=dma, branch=branch, category=cat, media_type=media, description=desc,
                   active_duty=ad or '', dependents=dep or '', rate_card_year=str(re.search(r'20\d\d', note).group(0)) if re.search(r'20\d\d', note) else '2026',
                   last_updated='2026-06', notes=note, source=src, review='')
        row[term] = vendor
        row['min_term_months'] = {'vendor_1mo': 1, 'vendor_3mo': 3, 'vendor_6mo': 6, 'vendor_12mo': 12}[term]
        if screens: row['ad_unit_size'] = f'{screens} screens'
        master.append(row); bybase[base].append(row); added += 1; mnorm.setdefault(norm(base), base)
    def existing(base, media):
        key = re.sub(r'[^a-z]', '', media.lower())[:8]
        return [r for r in bybase.get(base, []) if re.sub(r'[^a-z]', '', r['media_type'].lower()).startswith(key[:6]) or (('monitor' in media.lower() and 'monitor' in r['media_type'].lower() and 'bowl' not in r['media_type'].lower() and 'bowl' not in media.lower()) or ('bowl' in media.lower() and 'bowl' in r['media_type'].lower()) or ('marquee' in media.lower() and 'marquee' in r['media_type'].lower()) or ('kiosk' in media.lower() and 'kiosk' in r['media_type'].lower()) or ('theat' in media.lower() and ('theat' in r['media_type'].lower() or 'movie' in r['media_type'].lower())) or ('web' in media.lower() and 'web' in r['media_type'].lower()) or ('newsletter' in media.lower() and 'news' in r['media_type'].lower()) or ('magazine' in media.lower() and 'magazine' in r['media_type'].lower()) or ('guide' in media.lower() and ('guide' in r['media_type'].lower() or 'map' in r['media_type'].lower())) or ('scorecard' in media.lower() and 'score' in r['media_type'].lower()) or ('calendar' in media.lower() and 'calendar' in r['media_type'].lower()))]
    for path, cols, src in ((DIG, DIG_COLS, 'Military - National Digital Inventory Master 6.3.26.xlsx'), (PUB, PUB_COLS, 'Military - National Publication Inventory Master_June 2026.xlsx')):
        if not os.path.exists(path): print('missing', path); continue
        for cells, cnote in read_rows(path):
            cells += [''] * 30
            state, base, dma, branch = cells[2].strip(), re.sub(r'\s+', ' ', cells[3]).strip(), cells[4].strip(), cells[5].strip()
            if not base: continue
            ad, dep = re.sub(r'[^0-9]', '', cells[7]), re.sub(r'[^0-9]', '', cells[8])
            tail_note = (cells[27] if cols is DIG_COLS else cells[26]).strip()
            note_all = ' '.join(x for x in (tail_note, cnote) if x)
            if any('Part of' in c for c in cells[11:16]): skipped_network += 1
            mb = match(base)
            if mb is None and base in ALIAS and ALIAS[base] is None: continue     # explicitly ignored network umbrella rows
            if mb is not None and mb not in bybase:
                base = mb; mb = None            # alias points at a name we create fresh
            if mb is None:
                nb = norm(base)
                if nb in mnorm: mb = mnorm[nb]; mb = mb if mb in bybase else None
                if mb is None and nb in newbases: base = newbases[nb]
                else: newbases.setdefault(nb, base)
            target = mb or base
            if mb is None: unmatched[base] += 1
            for spec in cols:
                if cols is DIG_COLS:
                    ci, vi, si, media, cat, tmpl = spec; screens = re.sub(r'[^0-9]', '', cells[si]); n = f'{screens}-screen ' if screens else ''
                else:
                    ci, vi, media, cat, tmpl = spec; screens = ''; n = ''
                vendor = money(cells[vi]); client = money(cells[ci])
                if vendor is None and client is not None: vendor = round(client / 2, 2)
                if vendor is None: continue
                term, mult = term_for(note_all)
                vendor = vendor * mult
                ex = existing(target, media) if mb else []
                if ex:
                    have = [money(e['vendor_1mo']) or money(e['vendor_3mo']) for e in ex]
                    if vendor not in have:
                        for e in ex:
                            tag = f'Inventory master 6/2026 lists {media} at ${int(vendor):,} ({term.replace("vendor_", "").replace("mo", " mo")})'
                            if tag not in e['notes']: e['notes'] = (e['notes'] + '; ' if e['notes'] else '') + tag; noted += 1
                    continue
                st = state if mb is None else (bybase[mb][0]['state'] or state)
                dm = dma if mb is None else (bybase[mb][0]['dma'] or dma)
                br = branch if mb is None else (bybase[mb][0]['branch'] or branch)
                add(target, st, dm, br, ad, dep, media, cat, tmpl.format(n=n), vendor, term, note_all, src, screens)
    # ids for new rows
    seq = collections.Counter(r['id'].rsplit('-', 1)[0] for r in master if r['id'])
    for r in master:
        if not r['id']:
            code = f"{r['state'] or 'XX'}-{re.sub(r'[^A-Z0-9]', '', r['base'].upper())[:8]}"
            seq[code] += 1; r['id'] = f'{code}-{seq[code]:03d}'
    master.sort(key=lambda x: (x['state'], x['base'], x['category'], x['media_type']))
    with open(CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(master)
    print(f'added {added} rows, annotated {noted} existing rows, {len(unmatched)} inventory bases not in master (added as new bases):')
    print(sorted(unmatched))
    print('total rows', len(master), 'bases', len(bybase))

if __name__ == '__main__':
    main()
