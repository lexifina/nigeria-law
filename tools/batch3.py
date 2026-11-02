"""Nigeria batch 3: the 2025 tax reform Acts and the Electoral Act, 2026, from the Federal Government Printer's
gazettes as published by the National Assembly (nass.gov.ng, Acts & Publications). One corpus.d part per Act.

    python -X utf8 scripts/nigeria-law/batch3.py    # reads the pinned PDFs; writes the parts + verification-batch3.json

Same reader and word-for-word fidelity check as batch 2 (gazette.py through parse.read_act); text layer, no OCR.
Deterministic: the same cache gives the same bytes.
"""
from __future__ import annotations

import hashlib
import json
import re
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
        first=8, head=148, fixes={"15. . Notwithstanding": "15. Notwithstanding"}, clean_headings=True,
        # side notes the reader could not place: ss. 66 and 67 print theirs 15 points below the first line; the notes
        # of ss. 103 and 104 are printed as one
        headings={"sec-066": "Remission of penalty", "sec-067": "Recovery of tax",
                  "sec-103": "Failure to grant access for the deployment of technology",
                  "sec-104": "Failure to use fiscalisation system"}),
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
        first=10, head=148, fixes={"148—(1) For the purposes": "148.—(1) For the purposes",
                                     "154—(1) Without prejudice": "154.—(1) Without prejudice"},
        table_pages=(170, 202), notes_pages_from=208, clean_headings=True,
        # the notes of ss. 156 and 157 are printed as one ("Business restructur-ing Fiscalisation of supplies for VAT")
        headings={"sec-156": "Business restructuring", "sec-157": "Fiscalisation of supplies for VAT"},
        table_drop=[r"Nigeria Tax Act, 2025", r"2025\s+No\.\s*7(?:\s+A\s+\d{3})?", r"A\s+\d{3}(?:\s+2025\s+No\.\s*7)?"]),
    "electoral": dict(
        doc=11248, sha="dee5a37b62b920c9cfaf009b7dc1dcf5ccb5cbbeff807f5487eac868ce882fd6", part="60-electoral",
        law="act-2026-1", label="Act No. 1 of 2026", title="Electoral Act, 2026",
        short="Electoral Act 2026", frm="2026-02-18", printed="[ 18th day of February, 2026]",
        gazette="Official Gazette No. 40, Vol. 113, of 2 March 2026 (Government Notice No. 3)", published="2026-03-02",
        first=8, head=148),
}


# a cross-reference side note printed just under a section's heading note joins it ("Declaration of result Cap. C23,
# LFN, 2004", "Charge of duties Ninth Schedule"); the reader leaves such notes out everywhere else
XREF = re.compile(r"\s+(?:Cap\.?\s*[A-Z]\s?\d+[A-Z]?,?\s*LFN,?\s*\d{4}|Act,?\s+No\.\s*\d+,?\s*\d{4}|"
                  r"(?:" + "|".join(ORDINALS + ["Thid"]) + r")\s+[Ss]s?c?hedule)$")


def clean_headings(units: dict, given: dict, unused_notes: list[str]) -> list:
    """Remove cross-references from the end of section headings, and set the headings in `given` (each must be printed
    in a side note the reader did not use, or inside the merged note it is cut from). Returns what changed."""
    done = []
    printed_heads = [u["text"].partition("\n")[0] for k, u in units.items() if k.startswith("sec-")]
    for key, u in units.items():
        if not key.startswith("sec-"):
            continue
        head, nl, rest = u["text"].partition("\n")
        m = re.match(r"^# (\d+[A-Z]?)\. (.+)$", head)
        num = re.sub(r"^0+", "", key[4:7]) + key[8:].upper()
        if key in given:
            new = given[key]
            if not any(new in n for n in unused_notes + printed_heads):
                raise SystemExit(f"{key}: heading {new!r} is not printed in any side note")
            u["text"] = f"# {num}. {new}" + nl + rest
            done.append((key, head, f"# {num}. {new}"))
            continue
        if m:
            h = m.group(2)
            while (x := XREF.search(h)) and x.start() > 0:
                h = h[:x.start()]
            if h != m.group(2):
                u["text"] = f"# {num}. {h}" + nl + rest
                done.append((key, head, f"# {num}. {h}"))
    return done


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
                     "start": r"^EN[AE]CTED by", "stop": STOP, "schedule": SCHEDULE,
                     "structure": None, "renumber": None, "fixes": ITEMS[k].get("fixes"),
                     "schedule_pages_from": ITEMS[k].get("notes_pages_from"), "table_pages": ITEMS[k].get("table_pages"),
                     "table_drop": ITEMS[k].get("table_drop")}
    P.RETRIEVED = RETRIEVED
    ver_path = HERE / "verification-batch3.json"
    verification = json.loads(ver_path.read_text(encoding="utf-8")) if ver_path.exists() else {}
    for k in keys:
        it, p = ITEMS[k], pins[k]
        u, r = P.read_act(k)
        if it.get("clean_headings"):
            r["headings_cleaned"] = clean_headings(u, it.get("headings") or {}, r["side_notes_not_headings"])
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
        if it.get("fixes"):
            part["decisions"].append(
                f"{it['short']}: misprinted section-number lines are read as their section's first line: "
                + "; ".join(f"\"{a}\" as \"{b}\"" for a, b in it["fixes"].items())
                + ". Without the full stop the reader would not see the section start; the words are unchanged.")
        if it.get("clean_headings"):
            part["decisions"].append(
                f"{it['short']}: where a cross-reference side note (\"Act No. 6, 2021\", \"Cap. P10, LFN, 2024\", "
                f"\"Ninth Schedule\") is printed straight under a section's heading note, it is left out of the heading, "
                f"like every other cross-reference note. Headings the reader could not place are set from their side "
                f"notes: " + "; ".join(f"{k}: \"{v}\"" for k, v in (it.get("headings") or {}).items())
                + ". verification-batch3.json lists every heading changed (headings_cleaned).")
        if it.get("table_pages"):
            a, b = it["table_pages"]
            part["decisions"].append(
                f"{it['short']}: gazette pages {a + 1}-{b + 1} (PDF numbering) are printed as tables only, most of them "
                f"landscape: the end of the Eighth Schedule and the Ninth and Tenth Schedules. They are read line by "
                f"line as printed (each printed line, left to right, one line in the file), without the table layout, "
                f"so a cell that runs over several printed lines is split across lines of the file. The running head "
                f"of those pages is left out. A second reading of every such page (pdftotext) gives the same words.")
        if it.get("notes_pages_from"):
            part["decisions"].append(
                f"{it['short']}: on gazette page {it['notes_pages_from'] + 1} (the Thirteenth Schedule) a table column "
                f"is printed in the margin; its cells are read as body lines at their own height.")
        P.write_atomic(HERE / "corpus.d" / f"{it['part']}.json", part)
    P.write_atomic(ver_path, verification)
    print(json.dumps({k: {x: v[x] for x in ("units", "sections", "last_section", "sections_without_heading",
                                             "orphan_lines", "words_printed", "words_kept", "words_missing",
                                             "words_added", "schedules")}
                      for k, v in verification.items() if k in keys}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
