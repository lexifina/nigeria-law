"""WIPO Lex: Nigeria's legislation listed on its member profile (a secondary source).

python -I tools/wipo.py   fetch each legislation details page and the English text PDF it links; writes cache/wipo/items.json"""
import json, os, re, sys, time, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from fetch import get, log  # noqa: E402

D = os.path.join(ROOT, "cache", "wipo")


def main():
    s = open(os.path.join(D, "ng.html"), encoding="utf-8", errors="replace").read()
    rows = {}
    for u, t in re.findall(r'href="(/wipolex/en/legislation/details/(\d+))"', s):
        rows[t] = None
    items = []
    for lid in sorted(rows, key=int):
        fn = os.path.join(D, "details", f"{lid}.html")
        get(f"https://www.wipo.int/wipolex/en/legislation/details/{lid}", fn, 2000); time.sleep(1)
        if not os.path.exists(fn):
            continue
        p = open(fn, encoding="utf-8", errors="replace").read()
        title = html.unescape(re.sub(r"\s+", " ", (re.search(r"<title>(.*?)</title>", p, re.S) or [None, ""])[1])).strip()
        pdfs = sorted(set(html.unescape(u) for u in re.findall(r'(https://wipolex-res\.wipo\.int/edocs/lexdocs/laws/en/ng/[^"\'\s]+?\.pdf\?[^"\'\s]+)', p)))
        meta = {}
        for k, v in re.findall(r'<div[^>]*class="[^"]*label[^"]*"[^>]*>\s*([^<]{3,60}?)\s*</div>\s*<div[^>]*>\s*(.*?)</div>', p, re.S):
            meta[html.unescape(k).strip()] = html.unescape(re.sub(r"<[^>]+>", " ", v)).strip()
        it = {"id": lid, "title": title, "pdfs": pdfs, "meta": meta, "url": f"https://www.wipo.int/wipolex/en/legislation/details/{lid}"}
        for u in pdfs[:2]:
            get(u, os.path.join(D, "pdf", os.path.basename(u.split("?")[0])), 1000); time.sleep(1)
        items.append(it)
    json.dump(items, open(os.path.join(D, "items.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"wipo: {len(items)} Nigeria items, {sum(1 for i in items if i['pdfs'])} with an English PDF")


if __name__ == "__main__":
    main()
