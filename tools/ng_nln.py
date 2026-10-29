"""NLN DSpace discovery: python -X utf8 ng_nln.py "query" -> titles, dates, item uuids."""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ng_get
for q in sys.argv[1:]:
    u = 'https://nigeriareposit.nln.gov.ng/server/api/discover/search/objects?' + urllib.parse.urlencode({'query': q, 'dsoType': 'ITEM', 'size': 40})
    b = ng_get.get(u)
    if not b: print('no answer', q); continue
    j = json.loads(b)
    sr = j['_embedded']['searchResult']
    print(f'== {q}: {sr["page"]["totalElements"]} hits')
    for o in sr['_embedded']['objects']:
        it = o['_embedded']['indexableObject']; m = it['metadata']
        g = lambda k: (m.get(k) or [{'value': ''}])[0]['value']
        print(' ', it['uuid'], g('dc.date.issued'), '|', g('dc.title')[:110], '|', g('dc.publisher')[:40])
