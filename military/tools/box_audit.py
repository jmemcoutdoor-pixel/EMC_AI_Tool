#!/usr/bin/env python3
"""
Compare the Box > Military > "2 Military Installations" folders against the standardized rate card.

Input : audit/box_listing_<date>.json  (folder listings pulled from Box, one entry per base folder)
        data/rate_card.csv
Output: audit/Box vs Master rate card audit <date>.xlsx, audit/README.md

Verdict per folder: does Box hold pricing-looking files newer than the rate card's source date, is the
base priced in the rate card at all, and who uploaded the newer files.
"""
import json, re, csv, collections, datetime, sys, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
DATE = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
MASTER_DATE = '2025-12-02'   # MasterMilitaryOnBaseList 12.2.25
LISTING = os.path.join(ROOT, 'audit', f'box_listing_{DATE}.json')
OUT = os.path.join(ROOT, 'audit', f'Box vs Master rate card audit {DATE}.xlsx')

ALIAS = {'Fort Bragg (formely Fort Liberty)': 'Fort Liberty', 'Fort Gordon (formerly Fort Eisenhower)': 'Fort Eisenhower', 'Fort Rucker (formerly Fort Novosel)': 'Fort Novosel', 'Fort Lee (formerly Fort Gregg-Adams)': 'Fort Gregg-Adams', 'Fort Polk (formerly Fort Johnson)': 'Fort Johnson', 'Fort Meade': 'Fort George G. Meade', 'JB Lewis McChord': 'JBLM', 'JB Pearl Harbor Hickman': 'Pearl Harbor NS', 'JB Anacostia Bolling': 'JBAB Anacostia NS', 'JB Elmendorf Richardson': 'JBER - Elmendorf AFB', 'Fort Stewart': 'Fort Stewart / Hunter Army Airfield', 'Naval District Washington': 'Washington NAVDIST HQ', 'Camp Williams - Utah National Guard': 'Camp Williams', 'Maxwell AFB': 'Maxwell AFB (Incl. Gunter)', 'Aberdeen Proving Grounds': 'Aberdeen Proving Ground/ Edgewood Area', 'JB San Antonio': 'Fort Sam Houston', 'Camp Lejeune & New River MC': 'New River MCAS', 'Fort Hood (formerly Fort Cavazos)': 'Fort Hood', 'Fort A.P. Hill (formerly Fort Walker)': 'Fort AP Hill', 'China Lake NWS': 'China Lake NAVWEAPCEN', 'Ventura Naval Bases': 'NBVC Port Hueneme NCBC', 'Miramar MCAS': 'MCAS Miramar', 'Crane NWS': 'Crane Naval Support Activity', 'Camp Elmore MCCS Hampton Roads': 'Camp Elmore', '29 Palms MCAGCC': '29 Palms MC Air/Ground Combat Center', 'Southwest Naval Region': 'Point Loma', 'NorthWest Naval Region': 'Naval Station Everett', 'USCG Base Yorktown Training Center': 'Yorktown Navy Weapon Station', 'Fort Benning (formerly Fort Moore)': 'Fort Benning', 'JB Myer Henderson Hall Mcnair': 'JBMHH - Fort Myer', 'Great Lakes NS': 'Naval Station Great Lakes', 'New London SUBASE': 'New London NAVSUBBASE (Groton)', 'Newport NS': 'Naval Station Newport', 'Coast Guard Academy': 'US Coast Guard Academy', 'USCG Base Portsmouth': 'Portsmouth Coast Guard Integrated Support Command', 'Frances E Warren AFB': 'Francis E Warren AFB', 'Wright Patterson AFB': 'Wright Patterson Air Force Base', 'Davis-Monthan AFB': 'Davis-Monthan Air Force Base', 'Nellis AFB': 'Nellis Air Force Base', 'Fort Sill': 'Fort Sill', 'Quantico MCB': 'Quantico', 'Beaufort and Parris Island MCB': 'Beaufort MCAS', 'JB McGuire Dix Lakehurst': 'Joint Base Lakehurst - McGuire - Dix', 'Langley AFB': 'Langley Air Force Base', 'Kirtland AFB': 'Kirtland AFB', 'Mid Atlantic Naval Region': 'Hampton Roads Network', 'Defense Logistic Agency': 'Columbus Def Depot', 'Fort Huachuca': 'Fort Huachuca', 'Offutt AFB': 'Offutt AFB', 'Vance AFB': 'Vance AFB'}
STOP = r'\b(formerly|formely|and|the|of|mc|us|usag|jb|joint base|base|naval|region|air force|afb|sfb|arb|ars|nas|ncbc|nws|nsa|ns|mcas|mclb|mcb|mcrd|mcagcc|army|fort|ft|camp|station|center|training|force|incl)\b'
def norm(s): s = re.sub(r'\(.*?\)', '', s.lower()); s = re.sub(STOP, ' ', s); return ' '.join(re.findall(r'[a-z0-9]+', s))
PRICE_RX = re.compile(r'rate|pric|advertis|sponsor|media ?kit|guide|option|asset|spec|menu|cost|quote|proposal|sheet|card|packag|opportunit|fy2|\b20(2[5-9])\b', re.I)
POC_RX = re.compile(r'\bpoc\b|contact', re.I)
IMG = {'jpg', 'jpeg', 'png', 'heic'}

def main():
    allf = json.load(open(LISTING))
    rc = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'rate_card.csv'))))
    bases = collections.defaultdict(lambda: {'rows': 0, 'years': set(), 'sources': set()})
    for r in rc:
        b = bases[r['base']]; b['rows'] += 1; b['sources'].add(r['source'][:22])
        if r['rate_card_year']: b['years'].add(r['rate_card_year'])
    mnorm = {norm(b): b for b in bases}
    def match(folder):
        if folder in ALIAS and ALIAS[folder] in bases: return ALIAS[folder]
        n = norm(folder)
        if n in mnorm: return mnorm[n]
        for k, b in mnorm.items():
            if len(n) > 3 and (n in k or k in n): return b
        return None
    summary, detail = [], []
    for fo in allf:
        files = fo['files']
        d = lambda x: (x.get('content_modified_at') or x.get('modified_at') or '')[:10]
        newer = [x for x in files if d(x) > MASTER_DATE]
        pricing_newer = [x for x in newer if PRICE_RX.search(x['name']) and not POC_RX.search(x['name'])]
        img_newer = [x for x in newer if (x.get('extension') or '').lower() in IMG]
        newest = max(files, key=d, default=None)
        newest_price = max([x for x in files if PRICE_RX.search(x['name']) and not POC_RX.search(x['name'])], key=d, default=None)
        mb = match(fo['folder']); m = bases.get(mb) if mb else None
        years = ', '.join(sorted(m['years'])) if m else ''
        if not files: verdict = 'Box folder is empty'
        elif not m: verdict = 'Not priced in rate card' + (' (pricing files in Box to enter)' if pricing_newer or newest_price else '')
        elif pricing_newer: verdict = 'Box has newer pricing than rate card: review and update'
        elif img_newer: verdict = 'Only new photos/screenshots since master: check whether they are rate cards'
        elif newer: verdict = 'Only new POC/other files since master'
        else: verdict = 'Nothing newer than master'
        uploaders = collections.Counter(x.get('modified_by') or '' for x in newer)
        summary.append({'verdict': verdict, 'folder': fo['folder'], 'files_newer': len(newer), 'pricing_newer': len(pricing_newer), 'photos_newer': len(img_newer),
            'newest_pricing_file': newest_price['name'] if newest_price else '', 'newest_pricing_date': d(newest_price) if newest_price else '',
            'newest_file': newest['name'] if newest else '', 'newest_date': d(newest) if newest else '', 'newest_by': (newest or {}).get('modified_by', ''),
            'newer_by': ', '.join(f'{k} ({v})' for k, v in uploaders.most_common()), 'master_base': mb or '', 'master_rows': m['rows'] if m else 0, 'master_years': years,
            'master_sources': ', '.join(sorted(m['sources'])) if m else '', 'box_url': f"https://wilkinsmedia.app.box.com/folder/{fo['folder_id']}"})
        for x in newer:
            detail.append({'folder': fo['folder'], 'subfolder': x.get('path') or '', 'file': x['name'], 'type': (x.get('extension') or '').lower(), 'modified': d(x), 'by': x.get('modified_by') or '',
                           'pricing': 'yes' if PRICE_RX.search(x['name']) and not POC_RX.search(x['name']) else '', 'url': f"https://wilkinsmedia.app.box.com/file/{x['id']}"})
    order = ['Box has newer pricing than rate card: review and update', 'Not priced in rate card (pricing files in Box to enter)', 'Only new photos/screenshots since master: check whether they are rate cards', 'Not priced in rate card', 'Only new POC/other files since master', 'Nothing newer than master', 'Box folder is empty']
    summary.sort(key=lambda s: (order.index(s['verdict']) if s['verdict'] in order else 9, -int((s['newest_pricing_date'] or s['newest_date'] or '0000-00-00').replace('-', ''))))
    detail.sort(key=lambda x: (x['modified'], x['folder']), reverse=True)
    counts = collections.Counter(s['verdict'] for s in summary)
    # workbook
    NAVY = '1F2A44'; H = Font(bold=True, color='FFFFFF'); F = PatternFill('solid', fgColor=NAVY); T = Side(style='thin', color='D1D5DB'); B = Border(left=T, right=T, top=T, bottom=T)
    wb = Workbook(); ws = wb.active; ws.title = 'Summary'
    ws['A1'] = 'Box "2 Military Installations" folders vs. the standardized rate card'; ws['A1'].font = Font(bold=True, size=14, color=NAVY)
    ws['A2'] = f'Audited {DATE}. Rate card sources: MasterMilitaryOnBaseList 12.2.25 (Dec 2, 2025) + Digital/Publication Inventory Masters (June 2026). "Newer than master" = Box file modified after {MASTER_DATE}. Pricing-looking = name mentions rate, pricing, advertising, sponsorship, media kit, guide, options, specs, FY.'; ws['A2'].font = Font(italic=True, color='6B7280')
    cols = [('verdict', 'Verdict', 44), ('folder', 'Box folder', 34), ('files_newer', 'Files newer than master', 12), ('pricing_newer', 'of which pricing-looking', 12), ('photos_newer', 'of which photos', 10), ('newest_pricing_file', 'Newest pricing-looking file', 44), ('newest_pricing_date', 'Date', 12), ('newest_file', 'Newest file (any)', 40), ('newest_date', 'Date', 12), ('newest_by', 'Uploaded by', 18), ('newer_by', 'Who uploaded the newer files', 28), ('master_base', 'Base in rate card', 30), ('master_rows', 'Rate card rows', 10), ('master_years', 'Rate card year(s)', 14), ('master_sources', 'Rate card source(s)', 24), ('box_url', 'Box link', 40)]
    for i, (k, h, w) in enumerate(cols, 1):
        c = ws.cell(4, i, h); c.font = H; c.fill = F; c.alignment = Alignment(wrap_text=True, vertical='center'); c.border = B; ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[4].height = 32
    VF = {order[0]: 'FEF3C7', order[1]: 'FEE2E2', order[2]: 'FEF9C3', order[3]: 'FEE2E2', order[4]: 'F8FAFC', order[5]: 'ECFDF5', order[6]: 'F1F5F9'}
    for ri, s in enumerate(summary, 5):
        for i, (k, h, w) in enumerate(cols, 1):
            c = ws.cell(ri, i, s[k]); c.border = B; c.alignment = Alignment(wrap_text=k in ('verdict', 'folder', 'newest_pricing_file', 'newest_file', 'newer_by', 'master_base', 'master_sources'), vertical='top')
            if k == 'box_url': c.hyperlink = s[k]; c.font = Font(color='0092E4', underline='single')
        ws.cell(ri, 1).fill = PatternFill('solid', fgColor=VF.get(s['verdict'], 'FFFFFF'))
    ws.freeze_panes = 'C5'; ws.auto_filter.ref = f'A4:{get_column_letter(len(cols))}{4 + len(summary)}'
    wd = wb.create_sheet('Newer files detail')
    dcols = [('folder', 'Box folder', 34), ('subfolder', 'Subfolder', 22), ('file', 'File', 50), ('type', 'Type', 7), ('modified', 'Modified', 12), ('by', 'By', 18), ('pricing', 'Pricing-looking?', 10), ('url', 'Box link', 40)]
    for i, (k, h, w) in enumerate(dcols, 1):
        c = wd.cell(1, i, h); c.font = H; c.fill = F; c.border = B; wd.column_dimensions[get_column_letter(i)].width = w
    for ri, x in enumerate(detail, 2):
        for i, (k, h, w) in enumerate(dcols, 1):
            c = wd.cell(ri, i, x[k]); c.border = B
            if k == 'url': c.hyperlink = x[k]; c.font = Font(color='0092E4', underline='single')
    wd.freeze_panes = 'A2'; wd.auto_filter.ref = f'A1:{get_column_letter(len(dcols))}{1 + len(detail)}'
    wb.save(OUT)
    top = [s for s in summary if s['verdict'] == order[0]]
    unp = [s for s in summary if s['verdict'].startswith('Not priced')]
    md = [f'# Box installation folders vs. the rate card', '', f'Audited {DATE}. Rate card = MasterMilitaryOnBaseList 12.2.25 plus the June 2026 Digital and Publication Inventory Masters. {len(summary)} Box base folders; {len(detail)} files are newer than the Dec 2, 2025 master.', '', '| Verdict | Folders |', '|---|---|']
    md += [f'| {k} | {v} |' for k, v in counts.most_common()]
    md += ['', f'## Box has newer pricing than the rate card ({len(top)})', '', '| Base folder | Newest pricing-looking file | Date | By | Rate card year(s) |', '|---|---|---|---|---|']
    md += [f"| {s['folder']} | {s['newest_pricing_file']} | {s['newest_pricing_date']} | {s['newest_by']} | {s['master_years'] or 'none recorded'} |" for s in top]
    md += ['', f'## Box folders with no pricing in the rate card ({len(unp)})', '', '| Base folder | Newest pricing-looking file | Date | By |', '|---|---|---|---|']
    md += [f"| {s['folder']} | {s['newest_pricing_file']} | {s['newest_pricing_date']} | {s['newest_by']} |" for s in unp]
    open(os.path.join(ROOT, 'audit', 'README.md'), 'w').write('\n'.join(md) + '\n')
    print('wrote', OUT); print(counts)
    print('unmatched folders:', [s['folder'] for s in summary if not s['master_base'] and s['files_newer']])

if __name__ == '__main__':
    main()
