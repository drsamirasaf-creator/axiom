#!/usr/bin/env python3
"""Log in as operator and member, prove the privilege boundary, run the crawler.

⭐ NOTHING SECRET IS EVER PRINTED, LOGGED, OR WRITTEN. Credentials are read from
os.environ, held in local variables, typed into the page, and passed to the
crawler through the child process ENVIRONMENT — never a command line (visible in
`ps`), never a file, never stdout. The extracted bearer tokens are treated the
same way: this script knows their length and nothing else is ever emitted.

⭐ AND IT PROVES ELEVATION RATHER THAN TRUSTING THE LOGIN. A successful sign-in
says the password was right; it says nothing about the role. So the operator
session must RENDER an operator-only surface, and — the assertion that actually
matters — the MEMBER session must be REFUSED by that same surface. Without the
negative half, a misconfigured account that silently has staff rights would make
every "operator mode" result meaningless while looking perfect.

/admin is the probe: `canAccess = role === "staff" || role === "super"`, and a
non-operator gets a page whose only content is "Operator access required."

USAGE
    AXIOM_OPERATOR_EMAIL=… AXIOM_OPERATOR_PASSWORD=… \
    AXIOM_MEMBER_EMAIL=…   AXIOM_MEMBER_PASSWORD=… \
    python3 scripts/crawler-login.py

Each mode whose credentials are absent is SKIPPED LOUDLY — never silently
downgraded to anonymous, because a run labelled "operator" that was not one is
evidence of the wrong thing.
"""
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

APP = os.environ.get("APP_URL", "http://localhost:4175")
TOKEN_KEY = "axiom.auth.token"
OPERATOR_SURFACE = "/admin"
DENIED_MARKER = "operator access required"


def _creds(role):
    return (os.environ.get(f"AXIOM_{role}_EMAIL"),
            os.environ.get(f"AXIOM_{role}_PASSWORD"))


def login(browser, email, password, label):
    """Sign in inside an ISOLATED context. Returns (token, page, context).

    A fresh context per role is the point: sharing one would let the operator's
    storage leak into the member session and the privilege assertion below would
    be testing the operator twice.

    ⭐ INSTRUMENTED, BECAUSE THE FIRST VERSION REPORTED "FAILED" AND NOTHING ELSE.
    An operator login that works by hand and fails here produced one line of
    output — no status, no message, no URL — so every hypothesis was equally
    consistent with the evidence and none could be eliminated. The login POST's
    STATUS is the decisive signal and it was being thrown away:

        401 -> wrong credentials (very likely a shell-mangled value)
        403 -> account disabled, or email not yet verified
        200 -> the backend accepted it and the failure is client-side

    Nothing secret is emitted: statuses, key NAMES, value LENGTHS, and the
    on-screen error text the app itself displays."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
    pg = ctx.new_page()

    seen = {}

    def on_response(r):
        if "/auth/login" in r.url and r.request.method == "POST":
            seen["status"] = r.status
            try:
                body = r.json()
                # the backend's own words; never the payload's token
                seen["detail"] = str(body.get("detail"))[:120] if isinstance(body, dict) else None
            except Exception:
                seen["detail"] = None

    pg.on("response", on_response)
    pg.goto(f"{APP}/login", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_selector('input[type="email"]', timeout=30000)

    # ⭐⭐ THE DEFECT, MEASURED: THE FORM EXISTS BEFORE REACT BINDS IT.
    # wait_for_selector returns as soon as the input is in the DOM — which it is
    # immediately, because the page is server-rendered. React has not yet attached
    # its handlers at that moment, so `click` lands on a button with no submit
    # handler and NOTHING IS SENT. Isolated, 5 attempts each:
    #
    #     no settle   0/5 logged in   login POST status: None x5  (never fired)
    #     800ms       5/5 logged in   login POST status: 200 x5
    #
    # That is why the operator failed and the member did not: operator runs FIRST
    # against a cold Vite, member second against a warm one, and the same race
    # resolves differently. The old fixed 7s sleep AFTER the click could not help
    # — there was no request in flight to wait for.
    #
    # So the wait is for the HANDLER, not for a duration: poll until React has
    # attached to the form, then act. A sleep would work today and rot on a slower
    # machine; this is the condition the code actually depends on.
    pg.wait_for_function(
        """() => {
            const f = document.querySelector('input[type=email]');
            if (!f) return false;
            return Object.keys(f).some(k => k.startsWith('__react'));
        }""", timeout=30000)
    pg.fill('input[type="email"]', email)
    pg.fill('input[type="password"]', password)

    # ⭐ WAIT FOR THE RESPONSE, NOT A FIXED SLEEP. A fixed 7s both wastes time and
    # races: it can read localStorage before the write on a slow round trip.
    try:
        with pg.expect_response(
                lambda r: "/auth/login" in r.url and r.request.method == "POST",
                timeout=45000):
            pg.click('button[type="submit"]')
    except Exception:
        seen.setdefault("status", None)
        pg.click('button[type="submit"]')
    pg.wait_for_timeout(3500)

    token = pg.evaluate(f"() => window.localStorage.getItem({TOKEN_KEY!r})")
    if token:
        print(f"    {label:<9} sign-in: ok (token length {len(token)})")
        return token, pg, ctx

    # ── failure: say everything that is not a secret ────────────────────────
    keys = pg.evaluate("""() => Object.keys(window.localStorage)
        .filter(k => k.startsWith('axiom.'))
        .map(k => k + ' (len ' + (window.localStorage.getItem(k)||'').length + ')')""")
    # ⭐ NO REGEX HERE ON PURPOSE. The first version embedded \n inside a JS
    # regex written from Python, and Python turned it into a real newline —
    # breaking the JS at runtime, inside the very handler meant to explain a
    # failure. Line-splitting in JS needs no escapes at all.
    err = pg.evaluate("""() => {
        const lines = (document.body.innerText || '').split(String.fromCharCode(10));
        const hit = lines.find(l => /invalid|sign in failed|activate|disabled|incorrect/i.test(l));
        return hit ? hit.trim().slice(0, 160) : null;
    }""")
    print(f"    {label:<9} sign-in: FAILED — no bearer in localStorage")
    print(f"      login POST status : {seen.get('status')}")
    print(f"      backend detail    : {seen.get('detail')}")
    print(f"      on-screen message : {err}")
    print(f"      final URL         : {pg.url}")
    print(f"      axiom.* keys      : {keys or '(none)'}")
    if seen.get("status") == 401:
        print("      ⭐ 401 means the BACKEND rejected the pair. The value this script\n"
              "         received is not the value that works by hand — check for shell\n"
              "         mangling (smart quotes, history expansion on '!' in double quotes).")
    elif seen.get("status") == 403:
        print("      ⭐ 403 is an account state, not a typo: disabled, or email not verified.")
    elif seen.get("status") == 200:
        print("      ⭐ 200 means the backend ACCEPTED it and the token never reached\n"
              "         localStorage — a client-side write or navigation defect.")
    return None, pg, ctx


def sees_operator_surface(pg, label):
    """True if the operator surface RENDERS rather than refusing."""
    pg.goto(f"{APP}{OPERATOR_SURFACE}", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    body = (pg.inner_text("body") or "").lower()
    denied = DENIED_MARKER in body
    print(f"    {label:<9} {OPERATOR_SURFACE}: "
          f"{'REFUSED (operator access required)' if denied else 'RENDERED'}")
    return not denied


def main():
    op_email, op_pw = _creds("OPERATOR")
    mb_email, mb_pw = _creds("MEMBER")
    missing = [n for n, v in (("AXIOM_OPERATOR_EMAIL", op_email),
                              ("AXIOM_OPERATOR_PASSWORD", op_pw),
                              ("AXIOM_MEMBER_EMAIL", mb_email),
                              ("AXIOM_MEMBER_PASSWORD", mb_pw)) if not v]
    if missing:
        print("  MISSING CREDENTIALS (names only):")
        for n in missing:
            print(f"    {n}")
        print("\n  Refusing to run: a mode without credentials would silently be\n"
              "  anonymous, and a result labelled 'operator' that is not one is\n"
              "  worse than no result.")
        return 2

    tokens = {}
    print(f"  target {APP}\n")
    with sync_playwright() as p:
        b = p.chromium.launch()

        op_token, op_pg, op_ctx = login(b, op_email, op_pw, "operator")
        op_sees = sees_operator_surface(op_pg, "operator") if op_token else False

        # ⭐ A SEPARATE CONTEXT, NOT A SEPARATE PAGE. Same context = same
        # localStorage = the member would inherit the operator's bearer.
        mb_token, mb_pg, mb_ctx = login(b, mb_email, mb_pw, "member")
        mb_sees = sees_operator_surface(mb_pg, "member") if mb_token else False

        op_ctx.close(); mb_ctx.close(); b.close()

    print("\n  ELEVATION ASSERTION")
    print(f"    operator reaches {OPERATOR_SURFACE}: {op_sees}")
    print(f"    member   reaches {OPERATOR_SURFACE}: {mb_sees}")
    if not op_sees:
        print("\n  STOP — the operator session cannot reach the operator surface.\n"
              "  Either the account is not staff/super, or the login did not take.\n"
              "  Operator-mode results would be indistinguishable from member ones.")
        return 1
    if mb_sees:
        print("\n  STOP — THE MEMBER SESSION REACHED THE OPERATOR SURFACE.\n"
              "  The privilege boundary is not enforced, so the three-mode run is\n"
              "  meaningless: 'member' and 'operator' would be the same session with\n"
              "  different labels. Reporting this instead of a crawl.")
        return 1
    print("    ✓ boundary holds: operator elevated, member refused.")

    tokens["OPERATOR_TOKEN"] = op_token
    tokens["MEMBER_TOKEN"] = mb_token

    # ⭐ TOKENS TRAVEL IN THE CHILD ENVIRONMENT, NOT ON THE COMMAND LINE. A
    # command line is visible to `ps` for the life of the process; an env var is
    # not, and neither ends up in a log.
    env = {**os.environ, **tokens, "APP_URL": APP}
    print("\n  running auth-regression in all three modes (--interactions OFF)\n")
    r = subprocess.run([sys.executable, "scripts/auth-regression.py"],
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       env=env)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
