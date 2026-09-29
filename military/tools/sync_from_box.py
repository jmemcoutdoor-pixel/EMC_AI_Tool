#!/usr/bin/env python3
"""
Pull the MASTER rate card from Box and rebuild the app from it (Box -> app direction of the sync).

Runs in GitHub Actions on a schedule (see .github/workflows/sync-rate-card.yml) and can be run locally.

Box authentication: a Box "Custom App" with Server Authentication (Client Credentials Grant).
  BOX_CLIENT_ID, BOX_CLIENT_SECRET  - from the app's Configuration tab
  BOX_SUBJECT_TYPE = "enterprise" and BOX_SUBJECT_ID = <enterprise id>   (or "user" + a user id)
  BOX_FOLDER_ID                      - the folder that holds the master (default: Jon's "Military Rate Card Tool")
  BOX_FILE_NAME                      - default "Wilkins Military Rate Card - MASTER.xlsx"
The app must be authorized once by a Box admin (Admin Console > Apps > Custom Apps Manager) and must have
access to the folder (invite the app's service account e-mail to the folder as Viewer).

Exit code 0 and prints CHANGED=true/false so the workflow knows whether to commit.
"""
import os, sys, json, hashlib, subprocess, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
FOLDER = os.environ.get('BOX_FOLDER_ID', '422333003231')
NAME = os.environ.get('BOX_FILE_NAME', 'Wilkins Military Rate Card - MASTER.xlsx')
DEST = os.path.join(ROOT, NAME)
STAMP = os.path.join(ROOT, 'data', 'box_sync.json')

def token():
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials', 'client_id': os.environ['BOX_CLIENT_ID'], 'client_secret': os.environ['BOX_CLIENT_SECRET'],
        'box_subject_type': os.environ.get('BOX_SUBJECT_TYPE', 'enterprise'), 'box_subject_id': os.environ['BOX_SUBJECT_ID'],
    }).encode()
    with urllib.request.urlopen(urllib.request.Request('https://api.box.com/oauth2/token', data=data)) as r:
        return json.load(r)['access_token']

def api(tok, url):
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok})
    return urllib.request.urlopen(req)

def main():
    tok = token()
    items = json.load(api(tok, f'https://api.box.com/2.0/folders/{FOLDER}/items?fields=id,name,sha1,modified_at,modified_by&limit=1000'))['entries']
    f = next((i for i in items if i['type'] == 'file' and i['name'].lower() == NAME.lower()), None)
    if not f:
        print(f'No file named "{NAME}" in Box folder {FOLDER}; nothing to sync.'); print('CHANGED=false'); return
    prev = json.load(open(STAMP)) if os.path.exists(STAMP) else {}
    if prev.get('sha1') == f.get('sha1'):
        print('Box master unchanged since last sync', prev.get('synced_at')); print('CHANGED=false'); return
    with api(tok, f'https://api.box.com/2.0/files/{f["id"]}/content') as r, open(DEST, 'wb') as out:
        out.write(r.read())
    print('downloaded', NAME, f['modified_at'], 'by', (f.get('modified_by') or {}).get('name'))
    run = lambda *a: subprocess.check_call([sys.executable, os.path.join(HERE, a[0])] + list(a[1:]))
    run('xlsx_to_csv.py', DEST)
    run('build_rate_card.py')
    run('build_standalone.py')
    json.dump({'sha1': f.get('sha1'), 'file_id': f['id'], 'modified_at': f['modified_at'], 'modified_by': (f.get('modified_by') or {}).get('name'),
               'synced_at': __import__('datetime').datetime.utcnow().isoformat(timespec='seconds') + 'Z'}, open(STAMP, 'w'), indent=1)
    print('CHANGED=true')

if __name__ == '__main__':
    main()
