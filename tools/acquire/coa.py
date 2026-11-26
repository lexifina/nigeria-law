"""Append Court of Appeal of Nigeria judgments (text-layer PDFs only) to the private caselaw repository.

python -I tools/coa.py <repo>
The Court's judgments list (coa-admin.courtofappeal.gov.ng/api/judgements) links each judgment as a Google Drive file the
Court shares publicly. One file per judgment, court-of-appeal/<year>/<file-no>.md; one commit per judgment dated noon
Africa/Lagos on the day it was delivered. Protected cases are left out and listed in held-coa.json."""
import json, os, re, subprocess, sys, datetime, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build import pdf_text, when, git  # noqa: E402
from fetch import get  # noqa: E402
from caselaw import PROTECTED  # noqa: E402

D = os.path.join(ROOT, "cache", "coa")
API = "https://coa-admin.courtofappeal.gov.ng/api/judgements"


def main():
    repo = sys.argv[1]
    rows = json.load(open(os.path.join(D, "judgements.json"), encoding="utf-8"))["data"]
    have = {x.strip() for x in git(repo, "log", "--format=%(trailers:key=Coa-judgment,valueonly,separator=%x0A)", "main").split("\n") if x.strip()}
    held, items = [], []
    for r in rows:
        jid = str(r["id"])
        if jid in have:
            continue
        fno = re.sub(r"\s+", " ", (r.get("file_no") or "")).strip()
        fno = re.sub(r"\s+MR\.?$", "", fno).strip()
        parties = re.sub(r"\s*\n\s*", " ", (r.get("parties") or "").strip())
        m = re.search(r"/d/([A-Za-z0-9_-]+)", r.get("download_link") or "")
        if not m or not r.get("date"):
            held.append([jid, fno, "no file link or no date"]); continue
        d = datetime.date.fromisoformat(r["date"][:10])
        fn = os.path.join(D, "pdf", f"{jid}.pdf")
        get(f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t", fn, 1000)
        time.sleep(1)
        if not os.path.exists(fn) or open(fn, "rb").read(5) != b"%PDF-":
            held.append([jid, fno, "PDF not fetched"]); continue
        pages, n, why = pdf_text(fn)
        if why:
            held.append([jid, fno, why]); continue
        text = "\n".join(pages)
        if PROTECTED.search(parties) or PROTECTED.search(text[:20000]):
            held.append([jid, fno, "protected case (sexual offence, child or family matter): left out"]); continue
        name = re.sub(r"[^A-Za-z0-9]+", "-", fno.split(";")[0]).strip("-").lower() or f"judgment-{jid}"
        path = f"court-of-appeal/{d.year}/{name}-{jid}.md"
        body = (f"# {parties}\n\nCourt of Appeal of Nigeria ({r.get('division') or ''} Division), {fno}, judgment delivered {d.isoformat()}.\n"
                f"Panel: {(r.get('justice') or '').strip()}\n"
                + (f"Subject matter: {r['subject_matter'].strip()}\n" if (r.get("subject_matter") or "").strip() else "")
                + "\n---\n\n" + re.sub(r"\n{3,}", "\n\n", text).strip() + "\n")
        items.append((d, jid, fno, parties, path, body, r, n))
    items.sort()
    if items:
        parent = git(repo, "rev-parse", "--verify", "-q", "main").strip()
        p = subprocess.Popen(["git", "-C", repo, "fast-import", "--quiet", "--done"], stdin=subprocess.PIPE)
        w = p.stdin
        for seq, (d, jid, fno, parties, path, body, r, n) in enumerate(items):
            msg = (f"{fno}: {parties[:150]}, {d.isoformat()}\n\n"
                   f"Court of Appeal of Nigeria judgment delivered {d.isoformat()}, from the copy the Court links in its\n"
                   f"judgments list ({n} pages, the PDF's own text layer, no OCR).\n\n"
                   f"Kind: judgment\nCourt: Court of Appeal of Nigeria\nDivision: {r.get('division') or ''}\nDelivered: {d.isoformat()}\n"
                   f"File-no: {fno}\nText-source: Court of Appeal PDF text layer, no OCR\nSource: {r['download_link']}\n"
                   f"Source-list: {API}\nCoa-judgment: {jid}\n").encode("utf-8")
            tm = when(d, seq)
            w.write(f"commit refs/heads/main\nauthor Court of Appeal of Nigeria <coa@courtofappeal.gov.ng.invalid> {tm}\n"
                    f"committer Lexifina <nigeria-law@lexifina.com> {tm}\n".encode())
            w.write(f"data {len(msg)}\n".encode() + msg + b"\n")
            if seq == 0 and parent:
                w.write(f"from {parent}\n".encode())
            b = body.encode("utf-8")
            w.write(f"M 100644 inline {path}\ndata {len(b)}\n".encode("utf-8") + b + b"\n\n")
        w.write(b"done\n"); w.close(); p.wait()
    json.dump(held, open(os.path.join(ROOT, "held-coa.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"committed {len(items)}; held {len(held)}")


if __name__ == "__main__":
    main()
