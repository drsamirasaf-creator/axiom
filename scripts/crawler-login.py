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
    be testing the operator twice."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000})
    pg = ctx.new_page()
    pg.goto(f"{APP}/login", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(2500)
    pg.fill('input[type="email"]', email)
    pg.fill('input[type="password"]', password)
    pg.click('button[type="submit"]')
    pg.wait_for_timeout(7000)
    token = pg.evaluate(f"() => window.localStorage.getItem({TOKEN_KEY!r})")
    ok = bool(token)
    print(f"    {label:<9} sign-in: {'ok' if ok else 'FAILED'}"
          f"{'' if ok else ' — no bearer in localStorage'}"
          f"{f' (token length {len(token)})' if ok else ''}")
    return token, pg, ctx


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
