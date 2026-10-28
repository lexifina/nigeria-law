"""Read a Federal Government Printer (Nigeria) Act from the text layer of its PDF into provision units.

Layout of an FGP print (Official Gazette supplement, and the Federal Ministry of Justice's 2011 print of the
Constitution): one body column, side notes (the section headings, and a few references such as "Cap. 192 LFN.") in a
narrow column beside it, a running head at the top of each page. Every line is read with its position (PyMuPDF), so:
- side notes are told apart from the body by position, never by wording;
- a section's heading is the side note printed level with the section's first line;
- a new paragraph starts at a new text block or at an enumerator ((1), (a), (iv), (2A)) at the start of a line;
  a wrapped line is joined to the line before it with one space (a line ending in a hyphen is joined without one).

No OCR is used: a page without a text layer has no lines and is reported. Nothing here is specific to one Act except
the configuration passed in (page range, where the enacted text starts and stops, running-head band).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "″": '"', "‘": "'", "’": "'", "‚": "'", "´": "'",
                        "–": "-", "‑": "-", "­": "", "·": " "})
ENUM = re.compile(r"^\((?:[a-z]{1,3}|[ivxl]{1,6}|\d{1,3}[A-Z]{0,2})\s?\)(?=\s|$|[A-Z\"“(])")
SEC = re.compile(r"^(\d{1,3}[A-Z]{0,2})\s?\.\s*(?:[—–-]\s*)?(?=\(1\)|[A-Z\"“(]|$)")
SEC_LOOSE = re.compile(r"^(\d{1,3}[A-Z]{0,2})\s?(?:[—–-]+)\s*(?=\(1\)|[A-Z\"“(]|$)")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).translate(QUOTES).replace(" ", " ").replace("\t", " ")
    s = re.sub(r"[—]", "—", s)
    s = re.sub(r"\(\s*([a-zA-Z0-9]{1,6})\s+\)", r"(\1)", s)  # "(f )" -> "(f)"
    s = re.sub(r"\s+([;,:])", r"\1", s) if False else s
    return re.sub(r" {2,}", " ", s).strip()


@dataclass
class Line:
    page: int
    x0: float
    y0: float
    x1: float
    text: str
    block: int
    first_in_block: bool


@dataclass
class Page:
    body: list[Line] = field(default_factory=list)
    notes: list[tuple[float, float, str]] = field(default_factory=list)  # (y0, y1, text)


def read_pages(doc, first: int, last: int, head_max_y: float, foot_min_y: float = 10_000.0) -> dict[int, Page]:
    """Body lines and side notes of pages first..last (0-based, inclusive)."""
    out: dict[int, Page] = {}
    bid = 0
    for i in range(first, last + 1):
        pg = Page()
        d = doc[i].get_text("dict")
        blocks = [b for b in d["blocks"] if b.get("type") == 0]
        wide = [b for b in blocks if b["bbox"][2] - b["bbox"][0] > 150 and b["bbox"][1] >= head_max_y]
        if not wide:
            out[i] = pg
            continue
        bx0 = min(b["bbox"][0] for b in wide)
        bx1 = max(b["bbox"][2] for b in wide)
        for b in blocks:
            x0, y0, x1, y1 = b["bbox"]
            if y1 <= head_max_y or y0 >= foot_min_y:
                continue
            lines = []
            for ln in b["lines"]:
                t = "".join(s["text"] for s in ln["spans"])
                if t.strip():
                    lines.append((ln["bbox"], t))
            if not lines:
                continue
            if x0 >= bx1 - 3 or x1 <= bx0 + 3:
                pg.notes.append((y0, y1, " ".join(norm(t) for _, t in lines)))
                continue
            bid += 1
            # PyMuPDF can put two visual lines of one block on one "line" record; keep its order
            for k, (bb, t) in enumerate(lines):
                pg.body.append(Line(i, bb[0], bb[1], bb[2], t, bid, k == 0))
        pg.body.sort(key=lambda l: (round(l.y0, 0), l.x0))
        out[i] = pg
    return out


def note_at(pg: Page, y: float, tol: float = 9.0) -> str | None:
    best = None
    for (y0, y1, t) in pg.notes:
        if abs(y0 - y) <= tol and (best is None or abs(y0 - y) < abs(best[0] - y)):
            best = (y0, t)
    return best[1] if best else None


def _num(s: str) -> tuple[int, str]:
    m = re.match(r"(\d+)([A-Z]*)", s)
    return int(m.group(1)), m.group(2)


def is_next(prev: str | None, cur: str) -> bool:
    if prev is None:
        return _num(cur) == (1, "")
    pn, ps = _num(prev)
    cn, cs = _num(cur)
    if cn == pn + 1 and cs == "":
        return True
    if cn == pn and cs > ps:
        return True
    return False


def key_of(num: str, prefix: str = "sec") -> str:
    n, s = _num(num)
    return f"{prefix}-{n:03d}" + (f"-{s.lower()}" if s else "")


def paragraphs(lines: list[Line]) -> list[str]:
    """Join wrapped lines into paragraphs (see the module note)."""
    paras: list[str] = []
    for ln in lines:
        t = norm(ln.text)
        if not t:
            continue
        new = (not paras or ln.first_in_block and not re.match(r"^[a-z]", t) or bool(ENUM.match(t))
               or re.match(r"^Provided\b", t) is not None and paras[-1].rstrip().endswith((":", ";", ".")))
        if ln.first_in_block and paras and re.match(r"^[a-z]", t):
            new = False
        if new:
            paras.append(t)
        elif paras[-1].endswith("-") and not paras[-1].endswith(" -"):
            paras[-1] = paras[-1] + t
        else:
            paras[-1] = paras[-1] + " " + t
    return [re.sub(r" {2,}", " ", p).strip() for p in paras if p.strip()]


@dataclass
class Unit:
    key: str
    label: str
    kind: str
    heading: str | None
    lines: list[Line]


def split_sections(pages: dict[int, Page], start: re.Pattern, stop: re.Pattern | None,
                   schedule_rx: re.Pattern | None, prefix: str = "sec", label_word: str = "Section",
                   preamble_key: str | None = None, preamble_label: str = "Preamble",
                   drop_rx: re.Pattern | None = None, max_section: int | None = None) -> tuple[list[Unit], dict]:
    """Cut the body into sections (numbered in sequence), an optional preamble before section 1, and schedules.

    start: the first body line of the enacted text matches it (that line itself is not text, e.g. "ENACTED by...").
    stop: the first body line after the enacted text (e.g. "EXPLANATORY MEMORANDUM", "I certify").
    """
    units: list[Unit] = []
    report = {"structure_lines": [], "no_heading": []}
    seq = [l for i in sorted(pages) for l in pages[i].body]
    i0 = next((k for k, l in enumerate(seq) if start.search(norm(l.text))), None)
    if i0 is None:
        raise ValueError("start line not found")
    seq = seq[i0 + 1:]
    if stop is not None:
        k = next((k for k, l in enumerate(seq) if stop.search(norm(l.text))), None)
        if k is not None:
            seq = seq[:k]
    cur: Unit | None = None
    prev_num: str | None = None
    in_schedules = False
    sch_n = 0
    pre: list[Line] = []
    for l in seq:
        t = norm(l.text)
        if drop_rx and drop_rx.search(t):
            continue
        if schedule_rx and l.first_in_block and schedule_rx.match(t) and (prev_num is not None):
            in_schedules = True
            sch_n += 1
            cur = Unit(f"sch-{sch_n:02d}", t.title() if t.isupper() else t, "schedule", t, [])
            units.append(cur)
            continue
        if not in_schedules:
            m = SEC.match(t) or (SEC_LOOSE.match(t) if l.first_in_block else None)
            if m and is_next(prev_num, m.group(1)) and (max_section is None or _num(m.group(1))[0] <= max_section) \
                    and (l.first_in_block or prev_num is None or True):
                num = m.group(1)
                prev_num = num
                head = note_at(pages[l.page], l.y0)
                rest = t[m.end():].strip()
                ln = Line(l.page, l.x0, l.y0, l.x1, rest, l.block, True)
                cur = Unit(key_of(num, prefix), f"{label_word} {num}", "sec", head, [ln] if rest else [])
                if head is None:
                    report["no_heading"].append(num)
                units.append(cur)
                continue
            if re.match(r"^(PART|Part|CHAPTER|Chapter)\b", t) and l.first_in_block or (t.isupper() and len(t) > 3
                                                                                      and l.first_in_block):
                # structure heading (Part / Chapter / sub-heading in capitals): not part of any section's text
                if cur is not None or prev_num is None:
                    report["structure_lines"].append(t)
                    # a heading printed in two lines: swallow until a section starts
                    cur_struct = True
                    cur = None
                    continue
            if cur is None:
                if prev_num is None:
                    pre.append(l)
                else:
                    report["structure_lines"].append(t)
                continue
        cur.lines.append(l)
    if pre and preamble_key:
        units.insert(0, Unit(preamble_key, preamble_label, "preamble", None, pre))
    return units, report


def unit_text(u: Unit, schedule_lines: bool = False) -> str:
    if u.kind == "schedule":
        # tables and lists: one printed block per line, wrapped lines inside a block joined
        out: list[str] = []
        blk = None
        for ln in u.lines:
            t = norm(ln.text)
            if not t:
                continue
            if ln.block != blk or ENUM.match(t):
                out.append(t)
            elif out[-1].endswith("-"):
                out[-1] += t
            else:
                out[-1] += " " + t
            blk = ln.block
        body = out
        head = f"# {u.heading}"
    else:
        body = paragraphs(u.lines)
        num = u.label.split()[-1]
        head = f"# {num}. {u.heading.rstrip('.')}" if u.heading else f"# {u.label}"
        if u.kind == "preamble":
            head = f"# {u.label}"
    return "\n".join([head] + body) + "\n"
