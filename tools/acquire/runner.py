"""Nigeria runner: build legislation (lfn, cama, plac) and push; then finish the SCN fetch and push the caselaw repo.
Resumable: each build skips versions already in the history (Source-key / Scn-case trailers)."""
import subprocess, os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(os.path.dirname(ROOT), "nigeria-law-build")
CASE = os.path.join(os.path.dirname(ROOT), "nigeria-law-caselaw")
NW = 0x08000000


def log(m):
    with open(os.path.join(ROOT, "progress.log"), "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} runner: {m}\n")


def run(args, cwd=ROOT):
    log("start " + " ".join(args[-2:]))
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NW)
    log(f"{' '.join(args[-2:])} rc={r.returncode} {(r.stdout or '').strip()[-300:]} {(r.stderr or '').strip()[-300:]}")
    return r


def push(repo):
    run(["git", "-C", repo, "push", "origin", "main"])
    r = run(["git", "-C", repo, "ls-remote", "origin", "refs/heads/main"])
    log(f"remote main {r.stdout.split()[0] if r.stdout.strip() else '?'}")


py = [sys.executable, "-I", "-W", "ignore"]
for part in ("lfn,cama", "plac"):
    run(py + ["tools/build.py", REPO, part])
    push(REPO)
run(py + ["tools/fetch.py", "scn"])
run(py + ["tools/caselaw.py", CASE])
push(CASE)
log("done")
