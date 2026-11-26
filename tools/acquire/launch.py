"""Start a tools/ script detached with no console window: python -I tools/launch.py <name> <script> [args...]"""
import subprocess, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, args = sys.argv[1], sys.argv[2:]
out = open(os.path.join(ROOT, f"{name}.out"), "ab")
p = subprocess.Popen([sys.executable, "-I"] + args, cwd=ROOT, stdout=out, stderr=out, stdin=subprocess.DEVNULL,
                     creationflags=0x00000008 | 0x00000200 | 0x08000000)
open(os.path.join(ROOT, f"{name}.pid"), "w").write(str(p.pid))
print(p.pid)
