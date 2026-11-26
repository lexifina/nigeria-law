"""Append Supreme Court of Nigeria judgments (text-layer PDFs only) to the private caselaw repository.

python -I tools/caselaw.py <repo>
One file per judgment, supreme-court/<year>/<suit-no>.md; one commit per judgment dated noon Africa/Lagos on the day it
was delivered. Protected cases (sexual offences, children, family and matrimonial matters) are left out and listed."""
import json, os, re, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build import pdf_text, when, git  # noqa: E402

CACHE = os.path.join(ROOT, "cache", "scn")
PROTECTED = re.compile(r"(?i)\b(rape|raped|defilement|defile[ds]?|sexual|indecent|carnal|incest|minor|child|children|juvenile|"
                       r"custody of|adoption|divorce|matrimonial|dissolution of (?:the )?marriage|guardian)\b")


def main():
    repo = sys.argv[1]
    rows = json.load(open(os.path.join(CACHE, "judgments.json"), encoding="utf-8"))
    have = {x.strip() for x in git(repo, "log", "--format=%(trailers:key=Scn-case,valueonly,separator=%x0A)", "--all").split("\n") if x.strip()}
    held, items = [], []
    for r in rows:
        cid = str(r["case_id"])
        if cid in have:
            continue
        suit = (r.get("suitNo") or f"case-{cid}").strip()
        parties = f"{(r.get('petitioner') or '').strip()} v. {(r.get('respondent') or '').strip()}"
        d = r.get("dateJudgement")
        fn = os.path.join(CACHE, "pdf", f"{cid}.pdf")
        if not d:
            held.append([cid, suit, "no judgment date"]); continue
        d = datetime.date.fromisoformat(d[:10])
        if not os.path.exists(fn):
            held.append([cid, suit, "PDF not fetched"]); continue
        pages, n, why = pdf_text(fn)
        if why:
            held.append([cid, suit, why]); continue
        text = "\n".join(pages)
        if PROTECTED.search(parties) or PROTECTED.search(text[:20000]):
            held.append([cid, suit, "protected case (sexual offence, child or family matter): left out"]); continue
        name = re.sub(r"[^A-Za-z0-9]+", "-", suit).strip("-").lower() or f"case-{cid}"
        path = f"supreme-court/{d.year}/{name}-{cid}.md"
        body = (f"# {parties}\n\nSupreme Court of Nigeria, {suit}, {r.get('type') or 'Judgment'} delivered {d.isoformat()}.\n"
                f"Lead judgment: {(r.get('leadJudgeName') or r.get('mainjudge') or '').strip()}\n"
                f"Panel: {(r.get('judgeName') or '').strip()}\n\n---\n\n" + re.sub(r"\n{3,}", "\n\n", text).strip() + "\n")
        items.append((d, cid, suit, parties, path, body, r, n))
    items.sort()
    if items:
        parent = git(repo, "rev-parse", "--verify", "-q", "main").strip()
        p = subprocess.Popen(["git", "-C", repo, "fast-import", "--quiet", "--done"], stdin=subprocess.PIPE)
        w = p.stdin
        for seq, (d, cid, suit, parties, path, body, r, n) in enumerate(items):
            msg = (f"{suit}: {parties[:150]}, {d.isoformat()}\n\n"
                   f"Supreme Court of Nigeria {(r.get('type') or 'judgment').lower()} delivered {d.isoformat()}, as the Court's\n"
                   f"website serves it ({n} pages, the PDF's own text layer, no OCR).\n\n"
                   f"Kind: judgment\nCourt: Supreme Court of Nigeria\nDelivered: {d.isoformat()}\nSuit-no: {suit}\n"
                   f"Text-source: Supreme Court PDF text layer, no OCR\nSource: {r['pdfFile']}\nScn-case: {cid}\n").encode("utf-8")
            tm = when(d, seq)
            w.write(f"commit refs/heads/main\nauthor Supreme Court of Nigeria <scn@supremecourt.gov.ng.invalid> {tm}\n"
                    f"committer Lexifina <nigeria-law@lexifina.com> {tm}\n".encode())
            w.write(f"data {len(msg)}\n".encode() + msg + b"\n")
            if seq == 0 and parent:
                w.write(f"from {parent}\n".encode())
            b = body.encode("utf-8")
            w.write(f"M 100644 inline {path}\ndata {len(b)}\n".encode("utf-8") + b + b"\n\n")
        w.write(b"done\n"); w.close(); p.wait()
    json.dump(held, open(os.path.join(ROOT, "held-caselaw.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"committed {len(items)}; held {len(held)}")


if __name__ == "__main__":
    main()
