"""List every item in an NLN collection: python -X utf8 ng_nln_coll.py <collection uuid> > out.tsv"""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ng_get
scope = sys.argv[1]; page = 0
while True:
    u = 'https://nigeriareposit.nln.gov.ng/server/api/discover/search/objects?' + urllib.parse.urlencode(
        {'scope': scope, 'dsoType': 'ITEM', 'size': 100, 'page': page, 'sort': 'dc.date.accessioned,ASC'})
    j = json.loads(ng_get.get(u)); sr = j['_embedded']['searchResult']
    for o in sr['_embedded'].get('objects', []):
        it = o['_embedded']['indexableObject']; m = it['metadata']
        g = lambda k: (m.get(k) or [{'value': ''}])[0]['value'].replace('\t', ' ').replace('\n', ' ')
        print(it['uuid'], g('dc.date.issued'), g('dc.title')[:160], g('dc.publisher')[:50], g('dc.description')[:200], sep='\t', flush=True)
    page += 1
    if page >= sr['page']['totalPages']: break
