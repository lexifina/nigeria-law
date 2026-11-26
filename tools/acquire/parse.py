"""Read PLAC's HTML pages of the Laws of the Federation of Nigeria 2004, and text-layer PDFs, into section files."""
import re, html, datetime, unicodedata
from html.parser import HTMLParser

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "div", "table", "blockquote", "ol", "ul", "br"}


class Lines(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self.cur, self.ol, self.cell = [], [], [], False

    def flush(self):
        t = re.sub(r"[ \t ]+", " ", "".join(self.cur)).strip()
        if t:
            self.lines.append(t)
        self.cur = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip = True
        if tag == "ol":
            self.flush()
            try:
                self.ol.append(int(a.get("start") or 1) - 1)
            except ValueError:
                self.ol.append(0)
        elif tag == "li":
            self.flush()
            if self.ol:
                try:
                    self.ol[-1] = int(a["value"]) if a.get("value") else self.ol[-1] + 1
                except ValueError:
                    self.ol[-1] += 1
                self.cur.append(f"{self.ol[-1]}. ")
            else:
                self.cur.append("- ")
        elif tag in ("td", "th"):
            if self.cur and not "".join(self.cur).endswith(" | "):
                self.cur.append(" | ")
        elif tag in BLOCK:
            self.flush()

    def handle_endtag(self, tag):
        if tag == "ol" and self.ol:
            self.flush(); self.ol.pop()
        elif tag in BLOCK:
            self.flush()

    def handle_data(self, d):
        self.cur.append(d.replace("\r", " ").replace("\n", " "))


def html_lines(s):
    p = Lines()
    p.feed(s)
    p.flush()
    return [re.sub(r"^\|\s*|\s*\|$", "", x).strip() for x in p.lines if x.strip(" |")]


def page_body(s):
    """The act's own part of a view2.php page: from its <h3> title to the site footer."""
    m = re.search(r"<h3>(.*?)</h3>", s, re.S)
    title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip() if m else ""
    start = m.end() if m else 0
    e = s.find('<h3 style="color:#333">', start)
    e2 = s.find("What are the Laws of the Federation", start)
    ends = [x for x in (e, e2) if x > 0]
    body = s[start:min(ends)] if ends else s[start:]
    return title, body


SECLINE = re.compile(r"^(\d{1,3}[A-Z]{0,2})\s*\.\s*(?:[-—–]+\s*)?(?=\S)")
SCHEDLINE = re.compile(r"^(?:(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH)\s+)?SCHEDULES?\b(?:\s*[-—–].*|\s*\[.*|\s*\(.*)?$")


def numkey(n):
    m = re.match(r"(\d+)([A-Z]*)", n)
    return (int(m.group(1)), m.group(2))


def best_run(lines, lo=0):
    """The longest run of section numbers counting up from 1, starting at or after line lo."""
    hits = [(i, SECLINE.match(l).group(1)) for i, l in enumerate(lines) if i >= lo and SECLINE.match(l)]
    best = []
    for k, (i, n) in enumerate(hits):
        if n != "1":
            continue
        if len(hits) - k <= len(best):
            break
        if k + 1 < len(hits) and hits[k + 1][1] not in ("2", "1A", "1B") and len(best) > 1:
            continue
        seq, last = [(i, n)], numkey("1")
        for j, m in hits[k + 1:]:
            key = numkey(m)
            if key > last and key[0] <= last[0] + 3:
                seq.append((j, m)); last = key
        if len(seq) >= len(best):
            best = seq
    return best


def fname(n):
    return f"section-{int(re.match(r'\d+', n).group()):03d}{re.sub(r'^\d+', '', n).lower()}.md"


def split_lines(lines):
    """-> list of (filename, text) or None if no section run of 2 or more is found."""
    lo = 0
    for i, l in enumerate(lines):
        if re.match(r"^\[?\s*Commencement", l, re.I):
            lo = i
            break
    run = best_run(lines, lo)
    if len(run) < 2 and lo:
        run = best_run(lines, 0)
    if len(run) < 2:
        return None
    files = []
    head = lines[:run[0][0]]
    if head:
        files.append(("title.md", "\n\n".join(head)))
    last_start = run[-1][0]
    sched = [i for i in range(last_start + 1, len(lines)) if SCHEDLINE.match(lines[i]) and len(lines[i]) < 120]
    end_body = sched[0] if sched else len(lines)
    seen = set()
    for k, (i, n) in enumerate(run):
        e = run[k + 1][0] if k + 1 < len(run) else end_body
        name = fname(n)
        if name in seen:
            return None
        seen.add(name)
        files.append((name, "\n\n".join(lines[i:e])))
    # schedules: start a new file at each SCHEDULE heading (a bare 'SCHEDULES' contents line is merged forward)
    starts = []
    for i in sched:
        if starts and i - starts[-1] <= 1:
            continue
        starts.append(i)
    for j, s in enumerate(starts):
        e = starts[j + 1] if j + 1 < len(starts) else len(lines)
        files.append((f"schedule-{j + 1:02d}.md", "\n\n".join(lines[s:e])))
    return files


def date_text(t):
    t = t.replace(" ", " ")
    m = re.search(r"(\d{1,2})\s*(?:st|nd|rd|th)?\.?\s*(?:day\s+of\s+)?([A-Za-z]+),?\s+(\d{4})", t, re.I)
    if m and m.group(2).lower() in MONTHS:
        try:
            return datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            return None
    return None


def commencement(lines):
    for i, l in enumerate(lines[:400]):
        if re.match(r"^\[?\s*Commencement", l, re.I):
            for c in (l, *(lines[i + 1:i + 3])):
                m = re.search(r"\[([^\]]*\d{4}[^\]]*)\]", c)
                if m:
                    return date_text(m.group(1)), m.group(1).strip()
    return None, None


def slug(s):
    s = unicodedata.normalize("NFKD", html.unescape(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"^the\s+", "", s.strip())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:90].strip("-") or "untitled"


def pdf_lines(path):
    import pymupdf
    d = pymupdf.open(path)
    pages = [p.get_text() for p in d]
    return pages
