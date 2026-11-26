"""Fetch Nigeria's law text into cache/ (HTML and text-layer PDFs only; no OCR).

python -I tools/fetch.py [lfn|plac|scn|all]
- lfn:  PLAC's Laws of the Federation of Nigeria 2004 (placng.org/lawsofnigeria): index pages, view2.php HTML, laws/*.pdf
- plac: PLAC's Acts collection (WP REST documents, document_type=14): each document page and its PDF
- scn:  Supreme Court of Nigeria judgments API (supreme-cms.supremecourt.gov.ng), by month, and the original PDFs
Up to 4 requests in flight; on 429/5xx back off (30s, 60s, 120s, 240s); on 403 or a challenge page the host stops."""
import json, os, re, subprocess, sys, time, datetime, threading, hashlib
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
CURL = r"C:\Windows\System32\curl.exe"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) lexifina-law-archive"
LOG = os.path.join(ROOT, "progress.log")
STOPPED = set()
lock = threading.RLock()


def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}"
    with lock:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def host(u):
    return re.sub(r"^https?://([^/]+).*", r"\1", u)


def get(url, path, minsize=1):
    if os.path.exists(path) and os.path.getsize(path) >= minsize:
        return True
    h = host(url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for delay in (30, 60, 120, 240, None):
        if h in STOPPED:
            return False
        tmp = path + ".part"
        r = subprocess.run([CURL, "-sS", "-L", "-m", "300", "--connect-timeout", "30", "-y", "60", "-Y", "100", "-A", UA, "-o", tmp, "-w", "%{http_code}", url],
                           capture_output=True, text=True, creationflags=0x08000000)
        code = r.stdout.strip()[-3:]
        if code == "200" and os.path.exists(tmp):
            head = open(tmp, "rb").read(4000).lower()
            if b"cf-chl" in head or b"challenge-platform" in head or b"captcha" in head:
                STOPPED.add(h); log(f"STOP {h}: challenge page at {url}")
                os.remove(tmp); return False
            os.replace(tmp, path)
            return True
        if os.path.exists(tmp):
            os.remove(tmp)
        if code in ("403", "401"):
            STOPPED.add(h); log(f"STOP {h}: HTTP {code} at {url}")
            return False
        if code in ("400", "404", "410"):
            log(f"404 {url}")
            return False
        if delay is None:
            log(f"FAIL {code} {url} {r.stderr.strip()[:200]}")
            return False
        log(f"backoff {delay}s after HTTP {code} {url}")
        time.sleep(delay)
    return False


def pool(jobs, n=4, label=""):
    done = [0]
    def run(j):
        get(*j)
        with lock:
            done[0] += 1
            if done[0] % 50 == 0:
                log(f"{label} fetched {done[0]}/{len(jobs)}")
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(run, jobs))
    log(f"{label} done: {len(jobs)} jobs")


def lfn():
    base = "https://placng.org/lawsofnigeria/"
    cat = []
    for p in range(1, 70):
        fn = os.path.join(CACHE, "lfn", f"index-{p:02d}.html")
        get(f"{base}index.php?page={p}", fn)
        s = open(fn, encoding="utf-8", errors="replace").read()
        for href, t in re.findall(r"<li>\s*<a href='([^']+)'[^>]*>([^<]+)</a>", s):
            cat.append((href, re.sub(r"\s+", " ", t).strip()))
    json.dump(cat, open(os.path.join(CACHE, "lfn", "catalogue.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    jobs = []
    for href, t in cat:
        m = re.match(r"view2\.php\?sn=(\d+)$", href)
        if m:
            jobs.append((base + href, os.path.join(CACHE, "lfn", "html", f"sn-{int(m.group(1)):04d}.html")))
        elif href.lower().endswith(".pdf"):
            jobs.append((base + href.replace(" ", "%20"), os.path.join(CACHE, "lfn", "pdf", os.path.basename(href))))
    log(f"lfn catalogue {len(cat)} entries, {len(jobs)} to fetch")
    pool(jobs, 4, "lfn")


def plac():
    docs = []
    for p in (1, 2, 3):
        fn = os.path.join(CACHE, "plac", f"documents-{p}.json")
        if not get(f"https://placng.org/i/wp-json/wp/v2/documents?document_type=14&per_page=100&page={p}", fn):
            break
        d = json.load(open(fn, encoding="utf-8"))
        if not isinstance(d, list) or not d:
            break
        docs += d
    jobs = []
    for d in docs:
        jobs.append((d["link"], os.path.join(CACHE, "plac", "pages", f"{d['id']}.html")))
    pool(jobs, 4, "plac pages")
    pdfs = []
    for d in docs:
        fn = os.path.join(CACHE, "plac", "pages", f"{d['id']}.html")
        if not os.path.exists(fn):
            continue
        s = open(fn, encoding="utf-8", errors="replace").read()
        links = sorted(set(re.findall(r"https://placng\.org/i/wp-content/uploads/[^\"'<> ]+?\.pdf", s, re.I)))
        d["_pdfs"] = links
        for u in links:
            pdfs.append((u, os.path.join(CACHE, "plac", "pdf", hashlib.sha1(u.encode()).hexdigest()[:12] + ".pdf")))
    json.dump(docs, open(os.path.join(CACHE, "plac", "acts.json"), "w", encoding="utf-8"), indent=0, ensure_ascii=False)
    pool(pdfs, 4, "plac pdf")


def scn():
    api = "https://supreme-cms.supremecourt.gov.ng/api/v1.0/judgment-new/search"
    rows = {}
    d0 = datetime.date(1960, 1, 1)
    today = datetime.date.today()
    months = []
    y, m = 1960, 1
    while datetime.date(y, m, 1) <= today:
        months.append((y, m)); m += 1
        if m == 13:
            y, m = y + 1, 1
    def month(ym):
        y, m = ym
        a = datetime.date(y, m, 1)
        b = (datetime.date(y + (m == 12), m % 12 + 1, 1) - datetime.timedelta(days=1))
        fn = os.path.join(CACHE, "scn", "months", f"{y}-{m:02d}.json")
        if not os.path.exists(fn):
            get(f"{api}?judgmentDate={a}&judgmentDate2={b}", fn)
            time.sleep(1.5)
        return fn
    with ThreadPoolExecutor(1) as ex:
        fns = list(ex.map(month, months))
    for fn in fns:
        try:
            for r in json.load(open(fn, encoding="utf-8")).get("data") or []:
                rows[r["case_id"]] = r
        except Exception:
            pass
    json.dump(sorted(rows.values(), key=lambda r: r["case_id"]), open(os.path.join(CACHE, "scn", "judgments.json"), "w", encoding="utf-8"), indent=0)
    log(f"scn: {len(rows)} judgments listed")
    jobs = [(r["pdfFile"], os.path.join(CACHE, "scn", "pdf", f"{r['case_id']}.pdf")) for r in rows.values() if r.get("pdfFile")]
    pool(jobs, 2, "scn pdf")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    log(f"fetch start {what}")
    if what in ("lfn", "all"):
        lfn()
    if what in ("plac", "all"):
        plac()
    if what in ("scn", "all"):
        scn()
    log(f"fetch end {what}")
