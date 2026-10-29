"""WordPress media search: python -X utf8 ng_wpmedia.py host term [term ...]"""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ng_get
host = sys.argv[1]
for t in sys.argv[2:]:
    u = f'https://{host}/wp-json/wp/v2/media?' + urllib.parse.urlencode({'search': t, 'per_page': 100})
    try:
        b = ng_get.get(u)
    except Exception as e:
        print('ERR', host, t, e); continue
    if not b: print('none', host, t); continue
    try: j = json.loads(b)
    except Exception: print('notjson', host, t, b[:120]); continue
    print(f'== {host} {t}: {len(j)}')
    for m in j: print(' ', m.get('date', '')[:10], m.get('mime_type'), m.get('source_url'))
