"""Append Nigeria's law text to the repository's main branch with git fast-import, one commit per version.

python -I tools/build.py <repo> <part>[,<part>...]   parts: constitution, lfn, plac, cama
Each version is dated noon Africa/Lagos on the day it took effect. A version already in the history (its Source-key
trailer) is skipped, so the build is re-runnable. Items with no text layer are held and listed in held.json."""
import json, os, re, subprocess, sys, datetime, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from parse import page_body, html_lines, split_lines, commencement, slug, date_text  # noqa: E402

CACHE = os.path.join(ROOT, "cache")
TODAY = datetime.date(2026, 11, 26)
LFN_DAY = datetime.date(2002, 12, 31)
LFN_BASE = "https://placng.org/lawsofnigeria/"
HELD = []
OCR = {}
ORD = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH", "EIGHTH", "NINTH", "TENTH"]


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, encoding="utf-8").stdout


def held(key, title, why, url=""):
    HELD.append({"key": key, "title": title, "why": why, "url": url})


def pdf_text(path):
    import pymupdf
    try:
        d = pymupdf.open(path)
    except Exception as e:
        return None, 0, f"unreadable PDF ({e})"
    pages, imgpages = [], 0
    for p in d:
        pages.append(p.get_text())
        try:
            area = p.rect.width * p.rect.height
            if any(r.width * r.height > 0.6 * area for img in p.get_images() for r in p.get_image_rects(img[0])):
                imgpages += 1
        except Exception:
            pass
    n = len(pages)
    OCR[path] = n > 0 and imgpages >= 0.5 * n
    chars = sum(len(p.strip()) for p in pages)
    if n == 0 or chars < 150 * n:
        return None, n, f"no usable text layer ({chars} characters on {n} pages): a page scan, not OCRed here"
    return pages, n, None


def pdf_lines(pages):
    out = []
    for p in pages:
        ls = [re.sub(r"[ \t ]+", " ", l).strip() for l in p.replace("\r", "").split("\n")]
        ls = [l for l in ls if l and not re.fullmatch(r"\d{1,4}|Page \d+( of \d+)?|[A-Z]?\s?\d{1,4}", l)]
        out += ls
    # join wrapped lines into paragraphs: a line that does not start a new numbered/lettered item and follows one
    # that does not end a sentence is appended to it
    paras = []
    for l in out:
        new = re.match(r"^(\(?\d{1,3}[A-Z]{0,2}\)?\.?|\([a-z]{1,4}\)|\([ivx]+\)|PART\b|CHAPTER\b|SCHEDULE|[A-Z ,()'-]{12,}$)", l)
        if paras and (re.fullmatch(r"\d{1,3}[A-Z]{0,2}\.", paras[-1]) or (not new and not re.search(r"[.:;]$", paras[-1]))):
            paras[-1] += " " + l
        else:
            paras.append(l)
    return paras


def lfn_items(have):
    cat = json.load(open(os.path.join(CACHE, "lfn", "catalogue.json"), encoding="utf-8"))
    items = []
    for href, title in cat:
        title = re.sub(r"\s+", " ", title.replace("’", "'")).strip()
        title = re.sub(r"STUDlES", "STUDIES", title)
        key = f"lfn:{href}"
        if key in have:
            continue
        url = LFN_BASE + href.replace(" ", "%20")
        name = title.title().replace("'S ", "'s ").replace(" And ", " and ").replace(" Of ", " of ").replace(" The ", " the ") \
            .replace(" For ", " for ").replace(" In ", " in ").replace(" On ", " on ").replace(" To ", " to ").replace(" Etc", " etc")
        sub = None
        cap = None
        if href.startswith("view2.php"):
            sn = int(re.search(r"sn=(\d+)", href).group(1))
            fn = os.path.join(CACHE, "lfn", "html", f"sn-{sn:04d}.html")
            if not os.path.exists(fn):
                held(key, name, "not fetched", url); continue
            s = open(fn, encoding="utf-8", errors="replace").read()
            _, b = page_body(s)
            i = b.find("SUBSIDIARY LEGISLATION")
            lines = html_lines(b[:i] if i > 0 else b)
            if i > 0:
                sl = html_lines(b[i:])
                if len(sl) > 1 and not re.match(r"(?i)no subsidiary", sl[1]) and sum(len(x) for x in sl) > 200:
                    sub = "\n\n".join(sl)
            fmt = "PLAC's HTML page of the Act"
        else:
            cap = re.sub(r"\.pdf$", "", os.path.basename(href), flags=re.I)
            if not re.fullmatch(r"[A-Z]\d{1,3}", cap):
                cap = None
            fn = os.path.join(CACHE, "lfn", "pdf", os.path.basename(href))
            if not os.path.exists(fn):
                held(key, name, "not fetched", url); continue
            pages, n, why = pdf_text(fn)
            if why:
                held(key, name, why, url); continue
            lines = pdf_lines(pages)
            fmt = f"PLAC's PDF of the Act ({n} pages, its own text layer)"
            if OCR.get(fn):
                fmt = f"publisher OCR: the text layer PLAC's PDF carries over its page scans ({n} pages)"
        if sum(len(x) for x in lines) < 80:
            held(key, name, "page holds no Act text", url); continue
        c, craw = commencement(lines)
        if c and LFN_DAY < c <= TODAY:
            d, basis = c, f"commencement printed at the head of the text ([{craw}]); the text is later than the LFN 2004 revision (31 December 2002)"
        else:
            d, basis = LFN_DAY, "Laws of the Federation of Nigeria 2004, a revision of the statutes as at 31 December 2002; the Act's own commencement is in the Commenced trailer"
        files = split_lines(lines)
        whole = files is None
        if whole:
            files = [("text.md", "\n\n".join(lines))]
        folder = "acts/" + slug(title)
        tr = {"Kind": "publisher", "In-force": d.isoformat(), "In-force-basis": basis}
        if c:
            tr["Commenced"] = f"{c.isoformat()} (printed: [{craw}])"
        if cap:
            tr["Lfn-chapter"] = f"Cap. {cap} LFN 2004"
        tr.update({"Text-source": fmt if fmt.startswith("publisher OCR") else f"{fmt}; no OCR by Lexifina", "Source": url, "Source-key": key})
        nsec = sum(1 for f, _ in files if f.startswith("section-"))
        desc = ("One file: the reader found no section numbering to split on." if whole else
                f"{len(files)} files: {nsec} sections, the front matter and {len(files) - nsec - 1} schedules.")
        sfiles = [(f"subsidiary/{slug(title)}/text.md", sub)] if sub else []
        items.append(dict(key=key, date=d, folder=folder, files=files, extra=sfiles, replace=True,
                          subject=f"{name}: Laws of the Federation of Nigeria 2004, {d.isoformat()}",
                          body=f"{name}, as the Laws of the Federation of Nigeria 2004 print it, from the Policy and Legal\n"
                               f"Advocacy Centre's compendium of the 2004 Laws (placng.org/lawsofnigeria). {desc}\n"
                               + ("The subsidiary legislation printed under it is in subsidiary/, one file.\n" if sub else ""),
                          trailers=tr, author=("Laws of the Federation of Nigeria 2004", "lfn-2004@placng.org.invalid")))
    return items


def show_many(repo, paths):
    """Read many blobs in one git cat-file --batch call."""
    inp = "".join(f"origin/preview:{p}\n" for p in paths).encode("utf-8")
    r = subprocess.run(["git", "-C", repo, "cat-file", "--batch"], input=inp, capture_output=True).stdout
    out, i = {}, 0
    for p in paths:
        j = r.index(b"\n", i)
        size = int(r[i:j].split()[2])
        out[p] = r[j + 1:j + 1 + size].decode("utf-8")
        i = j + 1 + size + 1
    return out


def preview_items(repo, have, part):
    out = []
    if part == "constitution" and "preview:constitution-1999" not in have:
        names = git(repo, "ls-tree", "-r", "--name-only", "origin/preview", "constitution/").split()
        blobs = show_many(repo, names)
        files = []
        for p in names:
            b = os.path.basename(p)
            if b == "README.md":
                continue
            t = blobs[p]
            b = re.sub(r"^sec-", "section-", b)
            b = re.sub(r"^sch-", "schedule-", b)
            files.append((b, t.strip()))
        out.append(dict(key="preview:constitution-1999", date=datetime.date(1999, 5, 29), folder="constitution", files=files,
                        extra=[], replace=True,
                        subject="Constitution of the Federal Republic of Nigeria, 1999: as promulgated, 1999-05-29",
                        body="The Constitution of the Federal Republic of Nigeria, 1999, as promulgated by Decree No. 24 of 1999,\n"
                             "in force from 29 May 1999 (section 1(2) of the Promulgation Decree). Text: the body of the Federal\n"
                             "Ministry of Justice's print (text layer, no OCR); the Alteration Acts are recorded as later commits.\n",
                        trailers={"Kind": "enactment", "Law": "Constitution of the Federal Republic of Nigeria (Promulgation) Decree No. 24 of 1999",
                                  "Enacted": "1999-05-05", "In-force": "1999-05-29",
                                  "In-force-basis": "section 1(2) of the Promulgation Decree: in force on 29 May 1999",
                                  "Text-source": "Federal Ministry of Justice print, text layer, no OCR",
                                  "Source": "https://justice.gov.ng/wp-content/uploads/2020/09/Nigerian-Constitution.pdf",
                                  "Source-copy": "https://web.archive.org/web/20211015170245id_/https://justice.gov.ng/wp-content/uploads/2020/09/Nigerian-Constitution.pdf",
                                  "Source-key": "preview:constitution-1999"},
                        author=("Decree No. 24 of 1999", "decree-1999-24@justice.gov.ng.invalid")))
    if part == "cama" and "preview:cama-2020" not in have:
        names = git(repo, "ls-tree", "-r", "--name-only", "origin/preview", "companies/").split()
        blobs = show_many(repo, names)
        files = []
        for p in names:
            b = os.path.basename(p)
            if b == "README.md":
                continue
            t = blobs[p]
            b = re.sub(r"^sec-", "section-", b)
            b = re.sub(r"^sch-", "schedule-", b)
            files.append((b, t.strip()))
        out.append(dict(key="preview:cama-2020", date=datetime.date(2020, 8, 7), folder="acts/companies-and-allied-matters-act",
                        files=files, extra=[], replace=True,
                        subject="Companies and Allied Matters Act, 2020: as enacted, 2020-08-07",
                        body="The Companies and Allied Matters Act, 2020 (Act No. 3 of 2020), as enacted; it repeals and replaces\n"
                             "the Act of Cap. C20 LFN 2004. Text: the Federal Government Printer's gazette (Official Gazette\n"
                             "No. 124, Vol. 107, 10 August 2020), text layer, no OCR. The amendments made by the Business\n"
                             "Facilitation (Miscellaneous Provisions) Act, 2022 are not applied.\n",
                        trailers={"Kind": "enactment", "Law": "Act No. 3 of 2020", "Enacted": "2020-08-07",
                                  "Published": "2020-08-10", "In-force": "2020-08-07",
                                  "In-force-basis": "day of assent printed on the Act",
                                  "Text-source": "Federal Government Printer gazette, text layer, no OCR",
                                  "Source": "https://pre.cac.gov.ng/assets/images/CAMA-NOTE%20FINAL-FULL-VERSION.pdf",
                                  "Source-copy": "https://web.archive.org/web/20210301095237id_/https://pre.cac.gov.ng/assets/images/CAMA-NOTE%20FINAL-FULL-VERSION.pdf",
                                  "Source-key": "preview:cama-2020"},
                        author=("Act No. 3 of 2020", "act-2020-3@nass.gov.ng.invalid")))
    return out


SKIP_TITLES = re.compile(r"(?i)\bbill\b|budget|bills signed|full details|nigeria data protection act|electoral act,? 2026|appropriation")


def act_date(lines, year):
    head = "\n".join(lines[:400])[:12000]
    for m in re.finditer(r"\[([^\[\]]{6,60})\]\s*(?:Commencement)?", head):
        d = date_text(m.group(1))
        if d and (not year or abs(d.year - year) <= 1) and d <= TODAY:
            return d, f"commencement printed in square brackets at the head of the Act ([{m.group(1).strip()}])"
    m = re.search(r"(?i)(?:assent|commencement)[^\n]{0,80}?(\d{1,2}(?:st|nd|rd|th)?\s*(?:day\s+of\s+)?[A-Za-z]+,?\s+\d{4})", head)
    if m:
        d = date_text(m.group(1))
        if d and (not year or abs(d.year - year) <= 1) and d <= TODAY:
            return d, f"date printed by the assent or commencement words at the head of the Act ({m.group(1)})"
    if year:
        return datetime.date(year, 12, 31), f"31 December of the Act's year ({year}), a placeholder: no day was found at the head of the text"
    return None, None


def plac_items(have, used):
    docs = json.load(open(os.path.join(CACHE, "plac", "acts.json"), encoding="utf-8"))
    items, seen = [], set()
    for d in sorted(docs, key=lambda x: x["date"]):
        import html as H
        title = re.sub(r"\s+", " ", H.unescape(d["title"]["rendered"])).strip()
        key = f"plac:{d['id']}"
        if key in have:
            continue
        if SKIP_TITLES.search(title) and "Alteration" not in title:
            held(key, title, "not an Act text (a Bill, budget summary, list, appropriation, or already on main)", d["link"]); continue
        pdfs = d.get("_pdfs") or []
        if not pdfs:
            held(key, title, "no PDF linked on the page", d["link"]); continue
        u = pdfs[0]
        fn = os.path.join(CACHE, "plac", "pdf", hashlib.sha1(u.encode()).hexdigest()[:12] + ".pdf")
        if not os.path.exists(fn):
            held(key, title, "not fetched", u); continue
        pages, n, why = pdf_text(fn)
        if why:
            held(key, title, why, u); continue
        lines = pdf_lines(pages)
        ym = re.findall(r"(?<!\d)((?:19|20)\d\d)(?!\d)", title)
        year = int(ym[-1]) if ym else None
        dd, basis = act_date(lines, year)
        if not dd:
            held(key, title, "no date: no year in the title and no day at the head of the text", u); continue
        base = re.sub(r",?\s*\(?(?:19|20)\d\d\)?\s*(\(Updated\))?$", "", title).strip()
        base = re.sub(r"(?i)^immigtation", "Immigration", base)
        alter = "Alteration" in title
        amend = re.search(r"(?i)amendment|repeal", title) is not None
        if alter:
            folder = "constitution/alterations/" + slug(re.sub(r"(?i)^.*?1999,?\s*\(?", "", title)).replace("act-2023", "2023")
        elif amend:
            folder = "acts/" + slug(title)
        else:
            folder = "acts/" + slug(base)
        sig = (folder, dd.year)
        if sig in seen:
            held(key, title, "a second copy of an Act already taken from PLAC", u); continue
        seen.add(sig)
        files = split_lines(lines)
        whole = files is None
        if whole:
            files = [("text.md", "\n\n".join(lines))]
        nsec = sum(1 for f, _ in files if f.startswith("section-"))
        desc = ("One file: the reader found no section numbering to split on." if whole else
                f"{len(files)} files: {nsec} sections, the front matter and {len(files) - nsec - 1} schedules.")
        what = "the Alteration Act as enacted (not yet applied to the Constitution's sections)" if alter else "as enacted"
        tr = {"Kind": "enactment", "In-force": dd.isoformat(), "In-force-basis": basis,
              "Text-source": (f"publisher OCR: the text layer of the PDF the Policy and Legal Advocacy Centre publishes ({n} pages of page scans)" if OCR.get(fn) else f"PDF published by the Policy and Legal Advocacy Centre ({n} pages), its own text layer, no OCR"),
              "Source": u, "Source-page": d["link"], "Source-key": key}
        items.append(dict(key=key, date=dd, folder=folder, files=files, extra=[], replace=not amend and not alter,
                          subject=f"{title}: {what}, {dd.isoformat()}",
                          body=f"{title}, {what}, from the copy the Policy and Legal Advocacy Centre publishes.\n{desc}\n"
                               + ("It takes the place of the earlier Act under the same short title in this folder.\n" if (folder in used and not amend and not alter) else ""),
                          trailers=tr, author=(re.sub(r"[<>]", "", title)[:120], f"plac-{d['id']}@placng.org.invalid")))
        used.add(folder)
    return items


def folder_years(repo):
    """{folder: {years of the In-force days of versions already committed there}}."""
    out = {}
    cur = None
    for line in git(repo, "log", "--format=@@%(trailers:key=In-force,valueonly,separator=)", "--name-only", "main", "--", "acts", "subsidiary").split("\n"):
        if line.startswith("@@"):
            cur = line[2:].strip()[:4]
        elif line.strip() and cur and cur.isdigit():
            parts = line.strip().split("/")
            if len(parts) >= 3:
                out.setdefault("/".join(parts[:2]), set()).add(int(cur))
    return out


def clean_title(t):
    t = re.sub(r"\s+", " ", t.replace("’", "'")).strip().rstrip(".")
    t = re.sub(r"(?i),?\s*\(?(?:act )?no\.?\s*\d+\s+of\s+(?:19|20)\d\d\)?", "", t)
    t = re.sub(r"(?i),?\s*\(?statutory instrument no\.?\s*[\d.]+\s*(?:of\s+(?:19|20)\d\d)?\)?", "", t)
    t = re.sub(r"(?i),?\s*\(?S\.\s*I\.?,?\s*(?:No\.?)?\s*[\d.]+\s*(?:of\s+(?:19|20)\d\d)?\)?", "", t)
    t = re.sub(r"\s*\((?:S\.?\s*I|L\.?\s*N|Government Notice)[^)]*\)?$", "", t)
    t = re.sub(r"\./(?:19|20)\d\d$", "", t).rstrip(".")
    t = re.sub(r"(?i),?\s*\(?statutory instrument\)?\s*$", "", t)
    t = re.sub(r"\s*-\s*$", "", t)
    return t.strip(" ,")


def secondary_items(repo, have, used):
    """Federal Acts and regulations from FAOLEX and WIPO Lex copies with a text layer: versions not already in the repo."""
    fy = folder_years(repo)
    cands = []
    fp = os.path.join(CACHE, "faolex", "records.json")
    if os.path.exists(fp):
        for r in json.load(open(fp, encoding="utf-8")):
            types = {t.get("name") for t in r.get("type_of_text") or []}
            if not types & {"Legislation", "Regulation"} or r.get("territorial_subdivisions"):
                continue
            files = [f for f in r.get("links_to_full_text") or [] if f.lower().endswith(".pdf")]
            if not files:
                continue
            cands.append(dict(key=f"faolex:{r['faolex_id']}", title=r["title_of_text"], fn=os.path.join(CACHE, "faolex", "pdf", files[0]),
                              url="https://faolex.fao.org/docs/pdf/" + files[0], page=r["_url"], date_of_text=None if r.get("has_partial_date_of_text") else r.get("date_of_text"),
                              eif=r.get("entry_into_force") or "", reg="Regulation" in types and "Legislation" not in types,
                              imprint=r.get("serial_imprint") or "", src="FAOLEX (FAO Legal Database)",
                              terms="FAO: reuse for non-commercial purposes with credit"))
    wp = os.path.join(CACHE, "wipo", "items.json")
    if os.path.exists(wp):
        for it in json.load(open(wp, encoding="utf-8")):
            if not it.get("pdfs"):
                continue
            t = re.sub(r"(?i),\s*Nigeria,\s*WIPO Lex\s*$", "", it["title"]).strip()
            u = it["pdfs"][0].split("?")[0]
            eif = ""
            dp = os.path.join(CACHE, "wipo", "details", f"{it['id']}.html")
            if os.path.exists(dp):
                pt = re.sub(r"<[^>]+>", "\n", re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", open(dp, encoding="utf-8", errors="replace").read()))
                m = re.search(r"(?:Entry into force|Commenced):\s*([A-Z][a-z]+ \d{1,2}, \d{4})", re.sub(r"\s+", " ", pt))
                if m:
                    eif = datetime.datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat()
            cands.append(dict(key=f"wipolex:{it['id']}", title=t, fn=os.path.join(CACHE, "wipo", "pdf", os.path.basename(u)),
                              url=u, page=it["url"], date_of_text=None, eif=eif, reg=bool(re.search(r"(?i)regulations|rules|order|notice", t)),
                              imprint="", src="WIPO Lex", terms="WIPO Lex: national texts reproduced for information"))
    items, seen = [], set()
    for c in cands:
        if c["key"] in have:
            continue
        title = clean_title(c["title"])
        ym = re.findall(r"(?<!\d)((?:19|20)\d\d)(?!\d)", c["title"])
        year = int(ym[-1]) if ym else (int(c["date_of_text"][:4]) if c.get("date_of_text") else None)
        if re.search(r"(?i)\bcap(?:ter|\.)?\s*[A-Z]?\d|chapter\s+[A-Z]?\.?\s*\d|laws of the federation|\bLFN\b", c["title"]):
            continue  # an LFN revision copy: the LFN 2004 text is already taken from PLAC
        if not year or year < 2003:
            continue  # the LFN 2004 revision (as at 2002) is the earliest layer taken; earlier texts are not versions we can place
        if re.search(r"(?i)\b(policy|strategy|plan|guidelines?|code of practice|framework|bill)\b", title) and not re.search(r"(?i)\bact\b|regulations", title):
            held(c["key"], title, "not a legal text (a policy, plan, strategy or guideline)", c["url"]); continue
        if not os.path.exists(c["fn"]):
            held(c["key"], title, "not fetched", c["url"]); continue
        pages, n, why = pdf_text(c["fn"])
        if why:
            held(c["key"], title, why, c["url"]); continue
        lines = pdf_lines(pages)
        base = re.sub(r",?\s*\(?(?:19|20)\d\d\)?$", "", title).strip()
        amend = re.search(r"(?i)amendment|repeal", title) is not None
        if c["reg"]:
            folder = "subsidiary/" + slug(base)
        elif amend:
            folder = "acts/" + slug(title)
        else:
            folder = "acts/" + slug(base)
        if year in fy.get(folder, set()) or (folder, year) in seen:
            held(c["key"], title, "a version of this year is already in the repo (official or another copy)", c["url"]); continue
        dd, basis = act_date(lines, year)
        if basis and basis.startswith("31 December"):
            for k, lab in (("eif", "entry into force"), ("date_of_text", "date of the text")):
                v = c.get(k) or ""
                if re.fullmatch(r"\d{4}-\d\d-\d\d", v) and not v.endswith("-01-01") and abs(int(v[:4]) - year) <= 1:
                    dd = datetime.date.fromisoformat(v)
                    basis = f"{lab} as {c['src']} records it ({v}); no commencement day is printed at the head of the copy"
                    break
        if not dd or dd > TODAY:
            held(c["key"], title, "no reliable in-force day", c["url"]); continue
        if dd.year in fy.get(folder, set()) or (folder, dd.year) in seen:
            held(c["key"], title, "a version of this year is already in the repo (official or another copy)", c["url"]); continue
        seen.add((folder, dd.year))
        seen.add((folder, year))
        files = split_lines(lines)
        if files:
            tot = sum(len(x) for _, x in files) or 1
            if sum(len(x) for f, x in files if not f.startswith(("section-", "schedule-"))) > 0.3 * tot:
                files = None  # the numbering run found is not the Act's own (e.g. regulations printed with it): keep one file
        whole = files is None
        if whole:
            files = [("text.md", "\n\n".join(lines))]
        nsec = sum(1 for f, _ in files if f.startswith("section-"))
        desc = ("One file: the reader found no section numbering to split on." if whole else
                f"{len(files)} files: {nsec} sections, the front matter and {len(files) - nsec - 1} schedules.")
        ocr = OCR.get(c["fn"])
        tr = {"Kind": "enactment", "In-force": dd.isoformat(), "In-force-basis": basis,
              "Text-source": (f"publisher OCR: the text layer of the PDF {c['src']} serves ({n} pages of page scans)" if ocr
                              else f"PDF served by {c['src']} ({n} pages), its own text layer, no OCR"),
              "Source-status": f"secondary copy ({c['src']}, {c['page']})",
              "Source": c["url"], "Source-key": c["key"]}
        if c.get("imprint"):
            tr["Published"] = c["imprint"]
        replace = not amend and not c["reg"]
        items.append(dict(key=c["key"], date=dd, folder=folder, files=files, extra=[], replace=replace or c["reg"],
                          subject=f"{title}: as enacted, {dd.isoformat()}",
                          body=f"{title}, as enacted, from the copy {c['src']} serves (a secondary source; no official copy with a\n"
                               f"text layer was found). {desc}\n"
                               + ("It takes the place of the earlier Act under the same short title in this folder.\n" if (folder in used and replace) else ""),
                          trailers=tr, author=(re.sub(r"[<>]", "", title)[:120], f"{c['key'].replace(':', '-').lower()}@{'fao.org' if c['key'].startswith('faolex') else 'wipo.int'}.invalid")))
        used.add(folder)
    return items


def when(d, seq):
    t = int(datetime.datetime(d.year, d.month, d.day, 11, 0, tzinfo=datetime.timezone.utc).timestamp())
    if t < 0:
        t = 11 * 3600 + seq
    return f"{t} +0100"


def main():
    repo = sys.argv[1]
    parts = sys.argv[2].split(",")
    log = git(repo, "log", "--format=%(trailers:key=Source-key,valueonly,separator=%x0A)", "main")
    have = {x.strip() for x in log.split("\n") if x.strip()}
    used = {p for p in git(repo, "ls-tree", "-d", "-r", "--name-only", "main").split()}
    items = []
    for part in parts:
        if part in ("constitution", "cama"):
            items += preview_items(repo, have, part)
        elif part == "lfn":
            items += lfn_items(have)
        elif part == "plac":
            items += plac_items(have, used)
        elif part == "secondary":
            items += secondary_items(repo, have, used)
    items.sort(key=lambda r: (r["date"], r["folder"]))
    if not items:
        print("nothing to commit"); return
    parent = git(repo, "rev-parse", "main").strip()
    p = subprocess.Popen(["git", "-C", repo, "fast-import", "--quiet", "--done"], stdin=subprocess.PIPE)
    w = p.stdin

    def data(b):
        w.write(f"data {len(b)}\n".encode()); w.write(b); w.write(b"\n")
    for seq, it in enumerate(items):
        msg = it["subject"] + "\n\n" + it["body"] + "\n" + "".join(f"{k}: {v}\n" for k, v in it["trailers"].items())
        tm = when(it["date"], seq)
        w.write(b"commit refs/heads/main\n")
        w.write(f"author {it['author'][0]} <{it['author'][1]}> {tm}\ncommitter Lexifina <nigeria-law@lexifina.com> {tm}\n".encode("utf-8"))
        data(msg.encode("utf-8"))
        if seq == 0:
            w.write(f"from {parent}\n".encode())
        if it["replace"]:
            w.write(f"D {it['folder']}\n".encode("utf-8"))
        for name, txt in it["files"]:
            w.write(f"M 100644 inline {it['folder']}/{name}\n".encode("utf-8")); data((txt.strip() + "\n").encode("utf-8"))
        for path, txt in it["extra"]:
            w.write(f"M 100644 inline {path}\n".encode("utf-8")); data((txt.strip() + "\n").encode("utf-8"))
        w.write(b"\n")
    w.write(b"done\n"); w.close(); p.wait()
    hp = os.path.join(ROOT, "held.json")
    old = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else []
    keys = {h["key"] for h in HELD}
    json.dump([h for h in old if h["key"] not in keys] + HELD, open(hp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"committed {len(items)}; held {len(HELD)}; fast-import rc {p.returncode}")


if __name__ == "__main__":
    main()
