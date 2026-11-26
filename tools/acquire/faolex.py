"""FAOLEX (FAO Legal Database) records for Nigeria: a secondary source for federal Acts and regulations.

python -I tools/faolex.py records   fetch every Nigeria record page listed in FAOLEX's public sitemaps, parse its metadata
python -I tools/faolex.py pdfs      fetch the PDFs of the federal Legislation/Regulation records dated 2003 or later
Records go to cache/faolex/records.json; PDFs to cache/faolex/pdf/. No OCR; text layers only are used by build.py."""
import json, os, re, sys, time, html
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from fetch import get, log  # noqa: E402

D = os.path.join(ROOT, "cache", "faolex")


def paced(job):
    ok = get(*job)
    time.sleep(1.0)
    return ok


def records():
    urls = [u.strip() for u in open(os.path.join(D, "nga.txt"), encoding="utf-8") if u.strip()]
    # federal Acts and regulations after the LFN 2004 revision (as at 2002), and the Constitution; the year is in the slug
    urls = [u for u in urls if re.search(r"-nga-(\d{4})$", u) and (int(u[-4:]) >= 2003 or "constitution" in u)]
    jobs = []
    for u in urls:
        rid = re.search(r"/(LEX-FAOC\d+)/", u).group(1)
        jobs.append((u, os.path.join(D, "rec", rid + ".html"), 2000))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(paced, jobs))
    out = []
    for u, fn, _ in jobs:
        if not os.path.exists(fn):
            continue
        s = open(fn, encoding="utf-8", errors="replace").read()
        m = re.search(r'<script data-prerender type="application/json" id="prerendered-document">(.*?)</script>', s, re.S)
        if not m:
            continue
        doc = json.loads(m.group(1)).get("doc") or {}
        doc.pop("abstract", None)
        doc["_url"] = u
        out.append(doc)
    json.dump(out, open(os.path.join(D, "records.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    log(f"faolex: {len(out)} Nigeria records parsed of {len(jobs)}")


def wanted(r):
    types = {t.get("name") for t in r.get("type_of_text") or []}
    if not types & {"Legislation", "Regulation"}:
        return False
    if r.get("territorial_subdivisions"):
        return False
    d = r.get("date_of_text") or ""
    return d[:4].isdigit() and int(d[:4]) >= 2003 and bool(r.get("links_to_full_text"))


def pdfs():
    recs = json.load(open(os.path.join(D, "records.json"), encoding="utf-8"))
    jobs = []
    for r in recs:
        if not wanted(r):
            continue
        for f in r["links_to_full_text"][:1]:
            if f.lower().endswith(".pdf"):
                jobs.append(("https://faolex.fao.org/docs/pdf/" + f, os.path.join(D, "pdf", f)))
    log(f"faolex: {len(jobs)} PDFs wanted")
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(paced, jobs))
    log("faolex pdfs done")


if __name__ == "__main__":
    for step in (["records", "pdfs"] if sys.argv[1] == "all" else [sys.argv[1]]):
        {"records": records, "pdfs": pdfs}[step]()
