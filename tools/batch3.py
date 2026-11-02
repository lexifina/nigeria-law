"""Nigeria batch 3: the 2025 tax reform Acts and the Electoral Act, 2026, from the Federal Government Printer's
gazettes as published by the National Assembly (nass.gov.ng, Acts & Publications). One corpus.d part per Act.

    python -X utf8 scripts/nigeria-law/ng_get.py <url> ...   # fetch (official host, through the shared scheduler)
    python -X utf8 scripts/nigeria-law/batch3.py             # parse: cache only, writes the parts + verification-batch3.json

Same reader and word-for-word fidelity check as batch 2 (gazette.py through parse.read_act); text layer, no OCR.
Deterministic: the same cache gives the same bytes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

RETRIEVED = "2026-11-02"
NASS = "https://nass.gov.ng/documents/download/"
STOP = r"^I,? certify|^EXPLANATORY MEMORANDUM|^SCHEDULE TO (?:THE )?[A-Z ,()]+BILL"
ORDINALS = ("First Second Third Fourth Fifth Sixth Seventh Eighth Ninth Tenth Eleventh Twelfth Thirteenth "
            "Fourteenth Fifteenth").split()
# a schedule heading is a line of its own: "SCHEDULE", "FIRST SCHEDULE" or "First Schedule" (a bare "Schedule" line is
# a wrapped body line, and "SCHEDULES" heads the list of schedules)
SCHEDULE = (r"^(?:SCHEDULE|(?:" + "|".join(o.upper() + "|" + o for o in ORDINALS) + r") (?:SCHEDULE|Schedule))"
            r"(?:\s*[—–-].*)?$")

# key: (NASS document id, sha256, part file, act number label, title, short, from, gazette, first page, head band)
ITEMS = {
    "revenue-service": dict(
        doc=11251, sha="c100f5f10b089ae9a162c0c05fe8ba425b0b79ae936065aa0788893a8ef2b2a8", part="50-revenue-service",
        law="act-2025-4", label="Act No. 4 of 2025", title="Nigeria Revenue Service (Establishment) Act, 2025",
        short="NRS Act 2025", frm="2025-06-26", printed="[ 26th June, 2025 ]",
        gazette="Official Gazette No. 117, Vol. 112, of 26 June 2025 (Government Notice No. 23)", published="2025-06-26",
        first=4, head=165),
    "tax-administration": dict(
        doc=11250, sha="eb3ea717052f48492cc6441ad23f9e7ac2ad4782395db1c391580cc1adef20e2", part="51-tax-administration",
        law="act-2025-5", label="Act No. 5 of 2025", title="Nigeria Tax Administration Act, 2025",
        short="NTAA 2025", frm="2025-06-26", printed="[26th June, 2025]",
        gazette="Official Gazette No. 117, Vol. 112, of 26 June 2025 (Government Notice No. 24)", published="2025-06-26",
        first=8, head=148),
    "joint-revenue-board": dict(
        doc=11247, sha="97b648230dee2f6fc1e9f5248343dfb8d6c6d17b4c2d38abe661abee6201e458", part="52-joint-revenue-board",
        law="act-2025-6", label="Act No. 6 of 2025", title="Joint Revenue Board of Nigeria (Establishment) Act, 2025",
        short="JRB Act 2025", frm="2025-06-26", printed="[ 26th June, 2025 ]",
        gazette="Official Gazette No. 117, Vol. 112, of 26 June 2025 (Government Notice No. 25)", published="2025-06-26",
        first=4, head=148),
    "tax": dict(
        doc=11249, sha="41abf6887bc58a3c97116fd9a048aa91ad49c1cab156f39065a58401c0fce94f", part="53-tax",
        law="act-2025-7", label="Act No. 7 of 2025", title="Nigeria Tax Act, 2025",
        short="NTA 2025", frm="2026-01-01", printed="[1st January, 2026]",
        gazette="Official Gazette No. 117, Vol. 112, of 26 June 2025 (Government Notice No. 26)", published="2025-06-26",
        first=10, head=148),
    "electoral": dict(
        doc=11248, sha="dee5a37b62b920c9cfaf009b7dc1dcf5ccb5cbbeff807f5487eac868ce882fd6", part="60-electoral",
        law="act-2026-1", label="Act No. 1 of 2026", title="Electoral Act, 2026",
        short="Electoral Act 2026", frm="2026-02-18", printed="[ 18th day of February, 2026]",
        gazette="Official Gazette No. 40, Vol. 113, of 2 March 2026 (Government Notice No. 3)", published="2026-03-02",
        first=8, head=148),
}


def url_of(key: str) -> str:
    return NASS + str(ITEMS[key]["doc"])


def pin(key: str) -> dict:
    import fitz  # noqa: PLC0415
    u = url_of(key)
    b = (HERE / ".cache" / hashlib.sha256(u.encode("utf-8")).hexdigest()).read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    if sha != ITEMS[key]["sha"]:
        raise SystemExit(f"{key}: sha256 {sha} does not match the pin {ITEMS[key]['sha']}")
    if not b.startswith(b"%PDF-") or b"%%EOF" not in b[-2048:]:
        raise SystemExit(f"{key}: not a whole PDF")
    return {"url": u, "original": u, "via": "direct", "capture": None, "sha256": sha, "bytes": len(b),
            "pages": len(fitz.open(stream=b, filetype="pdf"))}


def main() -> None:
    import parse as P  # noqa: PLC0415
    keys = sys.argv[1:] or list(ITEMS)
    pins = {k: pin(k) for k in keys}
    P.PINS.update(pins)
    for k in keys:
        P.ACTS[k] = {"pages": (ITEMS[k]["first"], None), "head_max_y": ITEMS[k]["head"],
                     "start": r"^EN[AE]CTED by", "stop": STOP, "schedule": SCHEDULE, "schedule_pages_from": None,
                     "structure": None, "renumber": None}
    P.RETRIEVED = RETRIEVED
    ver_path = HERE / "verification-batch3.json"
    verification = json.loads(ver_path.read_text(encoding="utf-8")) if ver_path.exists() else {}
    for k in keys:
        it, p = ITEMS[k], pins[k]
        u, r = P.read_act(k)
        verification[k] = r
        act = {"slug": k, "short": it["short"], "title": it["title"], "url": p["original"], "first_law": it["law"],
               "earlier_laws": [],
               "versions": [{"from": it["frm"], "source_url": p["url"], "sha256": p["sha256"], "units": u,
                             "note": f"The Act as enacted ({it['label']}), from the Federal Government Printer's "
                                     f"{it['gazette']}; in force from {it['frm']}, the commencement date printed "
                                     f"under its long title (\"{it['printed']}\")."}]}
        part = {
            "sources": [P.source_entry(
                k, f"Federal Government Printer: {it['title']} ({it['gazette']})",
                f"{it['label']} as gazetted, published by the National Assembly of Nigeria (nass.gov.ng, Acts & "
                f"Publications, document {it['doc']}).")],
            "laws": {it["law"]: P.law(it["label"], it["title"], "law", it["frm"], it["published"], p["original"])},
            "acts": [act],
            "decisions": [
                f"{it['short']}: one version, the Act as enacted, dated {it['frm']} by the commencement date printed "
                f"under its long title (\"{it['printed']}\"); the gazette is dated {it['published']}.",
                f"{it['short']}: no amending Act was found (the National Assembly's Acts & Publications list and the "
                f"National Library of Nigeria's repository, both checked {RETRIEVED}), so the enacted text is taken "
                f"as today's text.",
                f"{it['short']}: the Schedules are one file each; tables in them are read line by line as printed. "
                f"The gazette's back matter (the schedule of the Bill's passage, the clerk's certificate and any "
                f"explanatory memorandum) is not law and is left out.",
            ],
        }
        P.write_atomic(HERE / "corpus.d" / f"{it['part']}.json", part)
    P.write_atomic(ver_path, verification)
    print(json.dumps({k: {x: v[x] for x in ("units", "sections", "last_section", "sections_without_heading",
                                             "orphan_lines", "words_printed", "words_kept", "words_missing",
                                             "words_added", "schedules")}
                      for k, v in verification.items() if k in keys}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
