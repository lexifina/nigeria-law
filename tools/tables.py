"""Table pages of a Federal Government Printer gazette: pages printed as a table only (often landscape), which have no
line of body text, so gazette.read_pages files every word on them as a side note.

read_lines() rebuilds such a page line by line as printed: every text span is turned to reading orientation (the
page's rotation undone), spans on one baseline are joined left to right, and lines are ordered top to bottom. This is
the same "read line by line as printed, without the table layout" rule as the other Schedules' tables. No word is
changed, added or dropped, except the running head, which `drop` matches and the caller reports.
"""
from __future__ import annotations

import re


def read_lines(page, drop: list[re.Pattern]) -> tuple[list[tuple[float, str]], list[str]]:
    """([(y, line text)] in reading order, [dropped running-head spans]). `drop` matches a whole span of the running
    head ("Nigeria Tax Act, 2025", "2025  No. 7        A  557"); on landscape pages the head is printed along the
    page's edge, level with table rows, so it is removed span by span before lines are formed."""
    m = page.rotation_matrix
    pieces = []
    dropped: list[str] = []
    for b in page.get_text("dict", sort=False)["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            for s in ln["spans"]:
                if not s["text"].strip():
                    continue
                if any(rx.fullmatch(s["text"].strip()) for rx in drop):
                    dropped.append(re.sub(r"\s+", " ", s["text"].strip()))
                    continue
                import fitz  # noqa: PLC0415
                r = fitz.Rect(s["bbox"]) * m
                pieces.append([r.x0, r.y0, r.x1, r.y1, s["text"]])
    pieces.sort(key=lambda p: ((p[1] + p[3]) / 2, p[0]))
    lines: list[list] = []          # [y centre, height, [pieces]]
    for p in pieces:
        yc, h = (p[1] + p[3]) / 2, p[3] - p[1]
        if lines and abs(lines[-1][0] - yc) < max(2.5, 0.35 * min(h, lines[-1][1])):
            lines[-1][2].append(p)
        else:
            lines.append([yc, h, [p]])
    out = []
    for yc, _, ps in lines:
        ps.sort(key=lambda p: p[0])
        t = ""
        for k, p in enumerate(ps):
            piece = p[4]
            # a space where the print leaves a gap (as gazette.read_pages joins spans)
            if k and p[0] - ps[k - 1][2] > 1.0 and not t.endswith(" ") and not piece.startswith(" "):
                t += " "
            t += piece
        t = re.sub(r"\s+", " ", t).strip()
        out.append((yc, t))
    return out, dropped
