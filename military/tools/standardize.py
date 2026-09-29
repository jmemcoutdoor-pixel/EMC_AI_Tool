#!/usr/bin/env python3
"""
Step 1 of the rate-card pipeline.

Reads the raw export of Box > Military > Master Grid > "MasterMilitaryOnBaseList 12.2.25 NS.xlsx"
(data/source_master_export_12.2.25.json, one object per line item as exported from Box)
and writes the standardized rate card: data/rate_card.csv

One row per media option on a base. Vendor (net) cost is the source of truth; client price
is computed later (Excel formulas / app) from the margin setting, so it is NOT stored here.
"""
import csv, json, re, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
SRC = os.path.join(DATA, 'source_master_export_12.2.25.json')
OUT = os.path.join(DATA, 'rate_card.csv')

# Base populations (Active Duty, Dependents) as listed in
# Box > Military > "Military - National Digital Inventory Master 6.3.26.xlsx".  Reference only;
# David/Chelsea are re-sourcing these from Military OneSource + the DoD demographics report.
POP = {
 'Eielson AFB':(1958,2424),'JBER - Elmendorf AFB':(5504,7035),'JBER - Fort Richardson':(5141,5991),
 'Fort Jonathan Wainwright':(6117,6995),'Fort Rucker':(3860,5945),'Maxwell AFB':(3012,5336),
 'Redstone Arsenal':(588,1518),'Little Rock AFB':(3536,4572),'Davis-Monthan AFB':(5995,6924),
 'Fort Huachuca':(4139,5163),'Luke AFB':(4607,5689),'Yuma MCAS':(4946,4702),'Camp Pendleton':(39690,31010),
 'MCAS Miramar':(7535,7007),'Travis AFB':(6675,7960),'Buckley AFB':(2540,3106),'Fort Carson':(24520,32953),
 'Peterson AFB':(3645,6210),'Schriever AFB':(1853,2679),'USAF Academy':(2070,3209),
 'New London NAVSUBBASE (Groton)':(6385,7471),'JB Anacostia-Bolling':(2491,3654),'NSA Washington':(3100,5435),
 'Fort Lesley J McNair':(975,2391),'Marine Barracks, Washington, D.C.':(1424,1774),'Dover AFB':(3484,4234),
 'Eglin AFB':(9243,12793),'Hurlburt Field':(8185,10597),'Jacksonville NAS':(6967,9499),'MacDill AFB':(5705,10061),
 'Pensacola NAS':(8595,6512),'Whiting Field NAS':(1145,1022),'Homestead ARB':(429,718),'Key West NAS':(797,986),
 'Mayport NAVSTA':(10442,14571),'Panama City NSA':(615,615),'NOTU Cape Canaveral':(163,340),'Patrick AFB':(1733,2550),
 'Tyndall AFB':(1633,2089),'US Army Garrison Miami Southern Command':(1370,2226),'Albany MCLB':(318,571),
 'Fort Benning':(24305,22480),'Fort Gordon':(11220,14416),'Fort Stewart':(19476,25826),'Kings Bay NAVSUBBASE':(2918,3953),
 'Moody AFB':(4562,5322),'Robins AFB':(3313,4707),'MCB Hawaii':(9157,7201),'Pearl Harbor - Hickam':(5561,7473),
 'Mountain Home AFB':(3387,3784),'Scott AFB':(4610,7686),'Naval Station Great Lakes':(15726,6149),
 'Rock Island Arsenal':(371,920),'Fort Leavenworth':(3438,7470),'Fort Riley':(15214,18081),'McConnell AFB':(2899,3577),
 'Fort Campbell':(26824,36153),'Fort Knox':(4842,7088),'Barksdale AFB':(5175,6715),'Fort Polk':(7783,9601),
 'New Orleans NAS JRB':(463,1132),'Hanscom AFB':(833,1124),'Westover ARB':(168,247),'Andrews AFB':(4312,5760),
 'Annapolis NS (Incl. USNA)':(1447,1918),'Fort Meade':(11140,14901),'Aberdeen Proving Ground':(831,1841),
 'Fort Detrick':(991,1873),'Indian Head NAV ORD STA':(584,620),'Patuxent River NAS':(2267,4150),
 'Walter Reed NNMC Bethesda':(4322,5945),'Portsmouth Naval Shipyard':(959,1105),'Fort Leonard Wood':(12218,11261),
 'Whiteman AFB':(3831,4381),'Keesler AFB':(5162,4425),'Camp Shelby':(393,1039),'Columbus AFB':(1520,1404),
 'Gulfport NCBC':(2906,3970),'Meridian NAS':(1126,680),'Camp Lejeune MCB':(38706,33400),'Fort Bragg':(45055,64046),
 'Grand Forks AFB':(1659,1901),'Minot AFB':(5625,5406),'Joint Base Lakehurst - McGuire - Dix':(5701,7607),
 'Cannon AFB':(4633,4353),'Holloman AFB':(4076,4386),'Kirtland AFB':(3386,4316),'Nellis AFB':(10168,11769),
 'Fort Drum':(15195,16816),'Fort Hamilton':(211,434),'Saratoga Springs Naval Support Unit':(3196,3752),
 'West Point':(1527,2890),'Naval Station Newport':(3269,3922),'Fort Hood':(36697,47118),'Fort Sam Houston':(10721,14934),
 'Lackland AFB':(22220,20301),'Randolph AFB':(2813,4802),'Fort Belvoir':(4614,8875),'Fort Eustis':(5645,8490),
 'Fort Lee':(8469,9316),'JBMHH - Fort Myer':(2133,2650),'JBMHH - Henderson Hall':(1424,1774),'Langley AFB':(7243,9549),
 'Quantico':(8409,10876),'Joint Base Lewis - McChord':(29453,39953),'Naval Air Station North Island':(8809,10776),
 'Naval Amphibious Base':(6057,8027),'Naval Base San Diego':(32983,33574),'Naval Medical Center San Diego':(4028,4686),
 'Fort Shafter':(2584,4653),'Schofield Barracks':(15057,18965),'Tripler Army Medical Center':(1765,2730),
 'Dam Neck Annex':(3838,5859),'JEB - Fort Story':(8790,12949),'JEB - Little Creek':(1045,887),'NAS Oceana':(5711,6755),
 'Naval Station Norfolk':(47368,53525),'Norfolk Naval Shipyard':(637,1084),'WPNSTA Yorktown':(1311,1405),
 'Naval Air Station Whidbey Island':(7304,8306),'Naval Base Kitsap-Bangor':(5845,7325),'Naval Base Kitsap-Bremerton':(6892,6386),
 'Naval Station Everett':(2576,2846),'Cherry Point MCAS':(5973,6547),'Seymour Johnson AFB':(4100,6000),
 'Fort Bliss':(33638,41000),'JB San Antonio':(35754,40037),'Corpus Christi NAS':(2836,7090),'JRB Fort Worth NAS':(4725,10500),
 'Kingsville NAS':(4500,0),'Hill AFB':(26000,0),'Wright Patterson AFB':(38000,0),'Tinker AFB':(30000,0),'Fort Sill':(20000,33000),
 'Carlisle Barracks':(744,1172),'Fort Jackson':(3500,12000),'Beaufort MCAS':(4100,1600),'Mid-South NAS':(6500,0),
 'Crane Naval Support Activity':(3600,0),'Earle NWS':(2000,0),'Picatinny Arsenal':(100,350),'Fort AP Hill':(750,0),
 'NSW Dahlgren':(9500,3350),'Columbus Def Depot':(9000,0),'Defense Distribution Depot Susquehanna':(5632,0),
 'NSA Mechanicsburg':(4300,0),'Fort Buchanan':(130000,0),'Fort Greely':(407,0),
}

CATEGORY_RULES = [
  # (category, ordered keyword regexes). First match wins; large format checked before standard.
  ('Digital',            r'digital|monitor|kiosk|marquee|\btv\b|television|screen|bowling|theat|cinema|movie|commercial|video|\bled\b|scoreboard|jumbotron|qubica|sweeper|lane'),
  ('Large Format',       r'large|\bxl\b|gate|field|wrap|cling|scape|billboard|road ?side|masking|bus|vehicle|fence|wall|window|floor|building|exterior|mural|panel'),
  ('Web & Email',        r'e-?news|email|e-mail|web|website|online|social|facebook|instagram|app\b'),
  ('Print & Publications', r'magazine|newsletter|guide|map|calendar|scorecard|score card|directory|newspaper|publication|insert|program|book|flyer|brochure'),
  ('Standard Media',     r'banner|poster|table tent|tent|counter card|tee|bench|gas pump|pump top|mouse|placemat|cup|napkin|coaster|sign|display|standee|pop.?up|vertical|retract|easel|rack|card'),
]
CATEGORY_ORDER = ['Digital','Standard Media','Large Format','Print & Publications','Web & Email','Sponsorship & Other']

def categorize(media, desc):
    text = (media + ' ' + desc).lower()
    m = media.lower()
    for cat, rx in CATEGORY_RULES:
        if re.search(rx, m):
            return cat
    for cat, rx in CATEGORY_RULES:
        if re.search(rx, text):
            return cat
    return 'Sponsorship & Other'

def num(v):
    return v if isinstance(v, (int, float)) else None

def norm_base(b):
    b = re.sub(r'\s+', ' ', b).strip()
    b = re.sub(r'\s+\(formerly.*?\)', '', b, flags=re.I)
    return b

# Current name -> former / alternate names (searchable in the app, shown as "aka").
AKA = {
 'Fort Liberty': 'Fort Bragg', 'Fort Eisenhower': 'Fort Gordon', 'Fort Novosel': 'Fort Rucker',
 'Fort Gregg-Adams': 'Fort Lee', 'Fort Johnson': 'Fort Polk', 'Fort George G. Meade': 'Fort Meade',
 'JBLM': 'Joint Base Lewis-McChord / Fort Lewis', 'JBLM - McChord AFB': 'Joint Base Lewis-McChord',
 'Hickam AFB': 'JB Pearl Harbor-Hickam', 'Pearl Harbor NS': 'JB Pearl Harbor-Hickam',
 'JBAB Anacostia NS': 'JB Anacostia-Bolling', 'JBER - Elmendorf AFB': 'Joint Base Elmendorf-Richardson',
 'Fort Stewart / Hunter Army Airfield': 'Fort Stewart', 'NOTU Cape Cape Canaveral': 'NOTU Cape Canaveral',
 'Nav Coastal Systems Ctr Panama City NSA': 'NSA Panama City', 'NSA Mid South': 'NAS Mid-South (Millington)',
 'Fort Sam Houston': 'JB San Antonio', 'Lackland AFB': 'JB San Antonio', 'Randolph AFB': 'JB San Antonio',
 'Washington NAVDIST HQ': 'Naval District Washington / Washington Navy Yard', 'Camp Williams': 'Utah National Guard',
 'USAG Hawaii': 'Schofield Barracks / Fort Shafter / Wheeler AAF', 'MCB Hawaii': 'Kaneohe Bay',
 'Point Loma': 'Naval Base Point Loma (San Diego)', 'China Lake NAVWEAPCEN': 'NAWS China Lake',
 'NBVC Port Hueneme NCBC': 'Naval Base Ventura County', 'Yorktown Navy Weapon Station': 'WPNSTA Yorktown',
 'Maxwell AFB (Incl. Gunter)': 'Maxwell-Gunter AFB', 'Aberdeen Proving Ground/ Edgewood Area': 'APG',
}
POP_ALIAS = {
 'Fort Liberty': 'Fort Bragg', 'Fort Eisenhower': 'Fort Gordon', 'Fort Novosel': 'Fort Rucker',
 'Fort Gregg-Adams': 'Fort Lee', 'Fort Johnson': 'Fort Polk', 'Fort George G. Meade': 'Fort Meade',
 'JBLM': 'Joint Base Lewis - McChord', 'JBLM - McChord AFB': 'Joint Base Lewis - McChord',
 'Hickam AFB': 'Pearl Harbor - Hickam', 'Pearl Harbor NS': 'Pearl Harbor - Hickam',
 'JBAB Anacostia NS': 'JB Anacostia-Bolling', 'Fort Stewart / Hunter Army Airfield': 'Fort Stewart',
 'NOTU Cape Cape Canaveral': 'NOTU Cape Canaveral', 'Nav Coastal Systems Ctr Panama City NSA': 'Panama City NSA',
 'NSA Mid South': 'Mid-South NAS', 'Washington NAVDIST HQ': 'NSA Washington', 'MCAS Miramar': 'MCAS Miramar',
 'Maxwell AFB (Incl. Gunter)': 'Maxwell AFB', 'Aberdeen Proving Ground/ Edgewood Area': 'Aberdeen Proving Ground',
 'Homestead AFB': 'Homestead ARB', 'NAS JRB Fort Worth': 'JRB Fort Worth NAS', 'Joint Base Charleston': 'Joint Base Charleston',
 'USAG Hawaii': 'Schofield Barracks', 'Point Loma': 'Naval Base San Diego', 'Yorktown Navy Weapon Station': 'WPNSTA Yorktown',
 'Whiteman AFB': 'Whiteman AFB', 'Crane Naval Support Activity': 'Crane Naval Support Activity',
}
STATE_FIX = {'KY TN': 'KY/TN'}

def main():
    rows = json.load(open(SRC))
    out = []
    counter = collections.Counter()
    for r in rows:
        base = norm_base(r['base'])
        if not base or not r['media']:
            continue
        v = {k: num(r[k]) for k in ('n1','n3','n6','n12','nprod')}
        c = {k: num(r[k]) for k in ('c1','c3','c6','c12','cprod')}
        notes = []
        # vendor cost is the source of truth; if only a client price was listed, derive vendor = client / 2
        for k, ck in (('n1','c1'),('n3','c3'),('n6','c6'),('n12','c12'),('nprod','cprod')):
            if v[k] is None and c[ck] not in (None, 0):
                v[k] = round(c[ck] / 2, 2)
                notes.append('vendor %s derived from listed client price' % k.replace('n',''))
        errs = [k for k in ('n1','n3','n6','n12','c1','c3','c6','c12') if isinstance(r[k], str)]
        if r['notes']:
            notes.insert(0, r['notes'])
        priced = any(v[k] not in (None, 0) for k in ('n1','n3','n6','n12'))
        terms = [t for t, k in ((1,'n1'),(3,'n3'),(6,'n6'),(12,'n12')) if v[k] not in (None, 0)]
        year = r['year'] or ''
        upd = r['updated'] or ''
        if not year and re.search(r'/(\d\d)$', upd):
            yy = int(re.search(r'/(\d\d)$', upd).group(1)); year = str(2000 + yy)
        review = []
        if not priced: review.append('No price on file - inquire')
        if errs: review.append('Source formula errors')
        if year and year.isdigit() and int(year) < 2025: review.append('Rate card older than 2025 - reconfirm')
        counter[base] += 1
        pop = POP.get(base) or POP.get(POP_ALIAS.get(base, ''))
        state = STATE_FIX.get(r['state'], r['state']) or ('CA' if r['metro'] == 'Los Angeles' else r['state'])
        out.append({
            'id': '',
            'base': base, 'aka': AKA.get(base, ''), 'state': state, 'dma': r['metro'], 'zip': r['zip'], 'branch': re.sub(r'\s+',' ',r['branch']).strip(),
            'category': categorize(r['media'], r['desc']), 'media_type': r['media'], 'ad_unit_size': r['size'],
            'description': r['desc'],
            'vendor_1mo': v['n1'] or '', 'vendor_3mo': v['n3'] or '', 'vendor_6mo': v['n6'] or '', 'vendor_12mo': v['n12'] or '',
            'vendor_production': v['nprod'] if v['nprod'] is not None else '',
            'min_term_months': terms[0] if terms else '',
            'active_duty': pop[0] if pop else '', 'dependents': pop[1] if pop and pop[1] else '',
            'rate_card_year': year, 'last_updated': upd, 'notes': '; '.join(notes), 'review': '; '.join(review),
            'source': 'MasterMilitaryOnBaseList 12.2.25 NS.xlsx',
        })
    # stable ids: STATE-BASECODE-NNN
    seq = collections.Counter()
    out.sort(key=lambda x: (x['state'], x['base'], CATEGORY_ORDER.index(x['category']), x['media_type']))
    for o in out:
        code = re.sub(r'[^A-Z0-9]', '', o['base'].upper())[:8]
        seq[(o['state'], code)] += 1
        o['id'] = '%s-%s-%03d' % (o['state'] or 'XX', code, seq[(o['state'], code)])
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print('wrote', OUT, len(out), 'rows,', len(counter), 'bases')
    print(collections.Counter(o['category'] for o in out))
    print('unpriced', sum(1 for o in out if 'No price' in o['review']))

if __name__ == '__main__':
    main()
