#!/usr/bin/env python3
"""G3 — the external availability probe. Runs OUTSIDE Railway, on GitHub Actions.

⭐⭐ A MONITOR INSIDE THE THING IT MONITORS DIES WITH IT. Sentry reports errors
FROM the application; a dead application sends none. Until this existed, the time
to detect a total outage was "until a human loads the site" — unbounded.

⭐ IT ASSERTS THE BODY, NOT ONLY THE STATUS. A 200 carrying
{"status": "unhealthy"} is read as UP by every monitor ever written, so this
checks both — and /health returns 503 in that case precisely so the two agree.

Exit 0 healthy · 1 unhealthy · 2 unreachable. The distinction matters: unreachable
means the process is gone, unhealthy means it is alive and cannot serve.

    python3 scripts/probe-availability.py                 # uses AXIOM_HEALTH_URL
    python3 scripts/probe-availability.py --url https://…
"""
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT = "https://web-production-0e3de.up.railway.app/health"
TIMEOUT = 20


def probe(url, timeout=TIMEOUT):
    """-> (verdict, detail, body|None). verdict in ok|unhealthy|unreachable."""
    req = urllib.request.Request(url, headers={"User-Agent": "axiom-availability-probe"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = r.status
            raw = r.read(64_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code = e.code
        raw = e.read(64_000).decode("utf-8", "replace") if e.fp else ""
    except Exception as e:
        # ⭐ NO RESPONSE AT ALL — the process is gone, DNS failed, or the edge is
        # down. Distinct from a reachable-but-broken app.
        return "unreachable", f"{type(e).__name__}: {e}", None

    try:
        body = json.loads(raw)
    except Exception:
        body = None

    if code != 200:
        detail = "http %s" % code
        if isinstance(body, dict) and body.get("checks"):
            detail += " · checks=%s" % json.dumps(body["checks"])[:300]
        return "unhealthy", detail, body

    # ⭐ 200 IS NOT ENOUGH. The body must also say it is well.
    if isinstance(body, dict) and body.get("status") not in (None, "ok"):
        return "unhealthy", "http 200 but status=%r" % body.get("status"), body
    if isinstance(body, dict):
        chk = body.get("checks") or {}
        if chk.get("database") not in (None, "ok"):
            return "unhealthy", "database=%s" % chk["database"], body
    return "ok", "http 200", body


def main(argv):
    url = DEFAULT
    if "--url" in argv:
        url = argv[argv.index("--url") + 1]
    url = os.environ.get("AXIOM_HEALTH_URL") or url

    verdict, detail, body = probe(url)
    rel = (body or {}).get("release") if isinstance(body, dict) else None
    print(f"probe: {url}")
    print(f"  verdict : {verdict}")
    print(f"  detail  : {detail}")
    if rel:
        print(f"  release : {rel}")
    if verdict == "ok":
        return 0
    # ⭐ the message a human will actually read in the alert
    print("")
    print(f"AXIOM IS {verdict.upper()} — {detail}")
    return 1 if verdict == "unhealthy" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
