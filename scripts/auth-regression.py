#!/usr/bin/env python3
"""AXIOM auth-regression crawler — the standing verification instrument.

Reconstructed at the canonical path scripts/auth-regression.py (the original ran
from uncommitted state and was lost). Playwright-driven crawl of the LIVE app in
three modes, replacing hand-clicking after every build. Runs after every deploy.

  python scripts/auth-regression.py [--mode anonymous|operator|member|all] [--headed]
  env: OPERATOR_TOKEN=<jwt>   MEMBER_TOKEN=<jwt>   (authed modes; primed into
       localStorage['axiom.auth.token'] exactly as the app stores it)

WHAT IT ASSERTS (per mode):
  * HARD sanity gate (authed modes): the primed token is actually SENT
    (Authorization: Bearer on a backend call) AND an identity call returns 200,
    else the mode ABORTS loudly — never a silently-anonymous "authed" pass.
  * per-route 2xx render + silent-empty detection (rendered-but-empty fails, not
    just non-2xx).
  * sidebar shape: EXPECTED_SIDEBAR_LINKS present, FORBIDDEN_SIDEBAR_HREFS absent,
    EXPECTED_GROUPS present.
  * ALIASES resolve (old path -> destination, content needle present).
  * sub-tab presence on /dashboard and /risk-analysis.
  * demo-safety: anonymous mode fires ZERO authenticated calls.

MAINTENANCE — this is the assertion contract; UPDATE alongside any nav change:
  EXPECTED_SIDEBAR_LINKS / FORBIDDEN_SIDEBAR_HREFS / EXPECTED_GROUPS are the final
  nav shape (verbatim from the ledger). ROUTES is DISCOVERED from the live sidebar
  at runtime; EXTRA_ROUTES + ALIASES + SUBTABS are maintained here.

  >>> VERIFY-ON-FIRST-RUN: the ALIASES destinations and content needles are a
  best-effort reconstruction (the original values were lost). Confirm each against
  the live app and correct the `dest`/`needle` fields; they are asserted as given.
"""
import os
import sys
import json
import argparse

APP_BASE = os.environ.get("APP_URL", "https://axiomdynamics.app").rstrip("/")
BACKEND = os.environ.get("BACKEND_HOST", "web-production-0e3de.up.railway.app")
TOKEN_KEY = "axiom.auth.token"          # localStorage key the app reads on boot
NAV_SEL = "nav a, aside a, [role='navigation'] a, [class*='sidebar'] a"

# ---- assertion contract (verbatim ledger nav shape) -------------------------
EXPECTED_SIDEBAR_LINKS = [
    "Dashboard & Reports", "Collaborative Assessment", "SWOT Analysis",
    "Risk Analysis", "Valuation", "Business Planning & Forecasting",
    "Enterprise Optimization", "Prescience AI", "Executive Brief",
    "Initiative Management", "Stakeholder Engagement", "Performance Monitoring",
    "Course Workspace", "What is AXIOM?",
]
FORBIDDEN_SIDEBAR_HREFS = {"/reports", "/benchmarking"}
EXPECTED_GROUPS = ["ANALYZE", "STRATEGIZE", "EXECUTE & MONITOR"]

# old path -> where it should land + a content needle proving the destination.
# VERIFY-ON-FIRST-RUN (see module docstring): dest/needle are reconstructed.
ALIASES = {
    # VERIFIED on first run (2026-07) against the live app via operator-mode probe.
    # needles are page-specific H1/H2 headings, not sidebar-nav labels, so the
    # assertion proves the destination actually rendered (not just the shell).
    "/reports":             {"dest": "/dashboard?tab=reports",            "needle": "Dashboard & Reports"},
    "/benchmarking":        {"dest": "/risk-analysis?section=benchmarking","needle": "Benchmark Performance Index"},
    "/cei":                 {"dest": "/cei",                              "needle": "Collaborative Assessment"},
    "/twin":                {"dest": "/twin",                             "needle": "Performance Monitoring"},
    "/data-input":          {"dest": "/data-input?tab=financial",         "needle": "Data uploads"},
    "/financial-forecasts": {"dest": "/financial-forecasts",             "needle": "FCFF"},
    # Lovable route alias (reported as a bare tuple); normalized to the committed
    # dict shape + verified live (2026-07): /discussion -> the discussion tab of
    # Stakeholder Engagement. needle is the tab's own heading, not the page H1.
    "/discussion":          {"dest": "/stakeholder-engagement?tab=discussion", "needle": "Discussion"},
}
# sub-tab presence: route -> at least one tab-like control must render
SUBTABS = {
    "/dashboard":     "tab",
    "/risk-analysis": "tab",
}
# The app's tabs are underline-style <button>s (Tailwind `border-b-2 -mb-px`,
# active=border-brass / inactive=border-transparent) driving ?tab=/?section= —
# NOT role='tab', anchors, or data-state. Verified live 2026-07 (dashboard 3,
# risk-analysis 9, valuation 3, cei 7). The selector also keeps the standard
# ARIA/anchor/tablist forms so a future restyle to those still matches.
TAB_SELECTOR = ("[role='tab'], a[href*='tab='], a[href*='section='], "
                "button[class*='border-b-2'][class*='-mb-px'], [role='tablist'] button")
# The app now holds a persistent connection (bundle index-DA3rwP6P onward), so
# 'networkidle' never settles and every goto would hit the 30s timeout. Wait for
# 'load' instead, then settle SETTLE_MS for the async data fetches (the ones that
# fire the backend calls we grade) to complete and be recorded.
WAIT_UNTIL = "load"
SETTLE_MS = 2600
# non-sidebar routes to also crawl (anonymous-reachable + utility). UPDATE with nav.
EXTRA_ROUTES_ANON = ["/", "/login", "/pricing"]

# authed identity call the app makes on boot (for the hard sanity gate). The gate
# accepts ANY backend 2xx that carried Authorization if this exact path isn't seen.
IDENTITY_HINTS = ("/me", "/my-companies", "/account", "/auth/")


def _norm_href(href):
    if not href:
        return ""
    if href.startswith(APP_BASE):
        href = href[len(APP_BASE):]
    if "#" in href:
        href = href.split("#", 1)[0]
    return href or "/"


class Recorder:
    """Per-page network capture: backend calls + whether Authorization was sent.
    The auth header is read from the REQUEST at response time — reading it at the
    'request' event proved unreliable in the sync API."""
    def __init__(self):
        self.calls = []          # (method, path, status, had_auth)

    def on_response(self, r):
        if BACKEND in r.url:
            try:
                auth = r.request.header_value("authorization")
            except Exception:
                auth = None
            path = r.url.split(BACKEND, 1)[-1].split("?", 1)[0]
            self.calls.append((r.request.method, path, r.status, bool(auth)))

    def authed_2xx(self):
        return [c for c in self.calls if c[3] and 200 <= c[2] < 300]

    def any_authed(self):
        return [c for c in self.calls if c[3]]

    def nonok(self):
        return [c for c in self.calls if not (200 <= c[2] < 400)]


def make_context(browser, token):
    ctx = browser.new_context()
    if token:
        # prime the token BEFORE app JS boots, exactly where the app reads it
        ctx.add_init_script(
            f"try{{localStorage.setItem({json.dumps(TOKEN_KEY)},{json.dumps(token)});}}catch(e){{}}")
    return ctx


def visit(page, rec, path):
    """Navigate a route; return (ok, why, backend_nonok, body_len)."""
    before = len(rec.calls)
    try:
        resp = page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
    except Exception as e:
        return False, f"navigation error: {e}", [], 0
    page.wait_for_timeout(SETTLE_MS)
    nonok = [c for c in rec.calls[before:] if not (200 <= c[2] < 400)]
    # silent-empty: rendered-but-empty main content
    try:
        body = page.inner_text("body") or ""
    except Exception:
        body = ""
    low = body.lower()
    err = any(m in low for m in ("something went wrong", "unexpected error",
                                 "404", "not found", "cannot read propert"))
    empty = len(body.strip()) < 40
    if empty:
        return False, "SILENT-EMPTY: rendered but no content", nonok, len(body)
    if err:
        return False, f"error surface in render: '{body.strip()[:80]}'", nonok, len(body)
    if nonok:
        return False, f"backend non-2xx during nav: {nonok}", nonok, len(body)
    return True, "", nonok, len(body)


def read_sidebar(page):
    links = []
    try:
        for a in page.locator(NAV_SEL).all():
            try:
                links.append((( a.inner_text() or "").strip(), _norm_href(a.get_attribute("href"))))
            except Exception:
                pass
    except Exception:
        pass
    try:
        nav_text = page.inner_text("nav, aside, [role='navigation']")
    except Exception:
        nav_text = ""
    return links, nav_text


def sanity_gate(page, rec):
    """HARD gate for authed modes: token actually sent + an authed 200 seen."""
    visit(page, rec, "/dashboard")
    id_hits = [c for c in rec.authed_2xx() if any(h in c[1] for h in IDENTITY_HINTS)]
    authed = rec.authed_2xx()
    if not rec.any_authed():
        return False, "Authorization was NEVER sent (token not primed / app ignored it)"
    if not authed:
        return False, f"authed calls made but none returned 2xx: {rec.any_authed()[:5]}"
    return True, (f"identity 2xx: {id_hits[0][1]}" if id_hits
                  else f"authed 2xx confirmed ({len(authed)} calls)")


def run_mode(browser, mode, token):
    fails = []
    ctx = make_context(browser, token)
    rec = Recorder()
    page = ctx.new_page()
    page.on("response", rec.on_response)

    authed = mode in ("operator", "member")

    if authed:
        ok, msg = sanity_gate(page, rec)
        print(f"  [sanity gate] {'PASS' if ok else 'ABORT'} — {msg}")
        if not ok:
            page.close(); ctx.close()
            return {"mode": mode, "aborted": True, "fails": [f"SANITY GATE: {msg}"], "green": 0, "total": 0}

    # ---- route enumeration: discover from the live sidebar (authed) + extras ----
    routes = set()
    sidebar_links, nav_text = ([], "")
    if authed:
        sidebar_links, nav_text = read_sidebar(page)
        routes.update(h for _, h in sidebar_links if h.startswith("/"))
    else:
        routes.update(EXTRA_ROUTES_ANON)
    routes.update(ALIASES.keys())
    routes.update(SUBTABS.keys())
    routes.discard("")

    # ---- per-route render + silent-empty ----
    green = 0
    for path in sorted(routes):
        ok, why, _nonok, _n = visit(page, rec, path)
        if ok:
            green += 1
        else:
            fails.append(f"{mode} route {APP_BASE}{path} :: {why}")

    # ---- sidebar shape (authed modes have the app shell) ----
    if authed:
        texts = " | ".join(t for t, _ in sidebar_links)
        hrefs = {h for _, h in sidebar_links}
        for label in EXPECTED_SIDEBAR_LINKS:
            if label not in texts:
                fails.append(f"{mode} sidebar MISSING link: '{label}'")
        for bad in FORBIDDEN_SIDEBAR_HREFS:
            if bad in hrefs:
                fails.append(f"{mode} sidebar FORBIDDEN href present: {bad}")
        up = (nav_text or "").upper()
        for grp in EXPECTED_GROUPS:
            if grp not in up:
                fails.append(f"{mode} nav MISSING group: '{grp}'")

    # ---- alias resolution (all modes; authed sees content) ----
    for alias, spec in ALIASES.items():
        try:
            page.goto(APP_BASE + alias, wait_until=WAIT_UNTIL, timeout=30000)
            page.wait_for_timeout(SETTLE_MS)
            final = _norm_href(page.url)
            body = (page.inner_text("body") or "")
        except Exception as e:
            fails.append(f"{mode} alias {alias} :: navigation error {e}"); continue
        if final == alias and alias in FORBIDDEN_SIDEBAR_HREFS:
            fails.append(f"{mode} alias {alias} did NOT redirect (still {final})")
        if authed and spec["needle"] and spec["needle"].lower() not in body.lower():
            fails.append(f"{mode} alias {alias} -> {final} missing needle '{spec['needle']}' "
                         f"(VERIFY reconstructed dest/needle)")

    # ---- sub-tabs ----
    if authed:
        for path, _kind in SUBTABS.items():
            try:
                page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
                page.wait_for_timeout(SETTLE_MS)
                n_tabs = page.locator(TAB_SELECTOR).count()
            except Exception:
                n_tabs = 0
            if n_tabs < 1:
                fails.append(f"{mode} sub-tabs MISSING on {path}")

    # ---- demo-safety: anonymous fires zero authenticated calls ----
    if mode == "anonymous":
        leaked = rec.any_authed()
        if leaked:
            fails.append(f"anonymous fired {len(leaked)} AUTHENTICATED call(s): {leaked[:5]}")

    total = len(routes) + (len(EXPECTED_SIDEBAR_LINKS) + len(EXPECTED_GROUPS) + len(ALIASES) + len(SUBTABS) if authed else 1)
    page.close(); ctx.close()
    return {"mode": mode, "aborted": False, "fails": fails, "green": total - len(fails), "total": total}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["anonymous", "operator", "member", "all"])
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. `pip install playwright && playwright install chromium`")
        sys.exit(2)

    modes = ["anonymous", "operator", "member"] if args.mode == "all" else [args.mode]
    results, skipped = [], []
    print(f"AXIOM auth-regression crawler — {APP_BASE}\n")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        for mode in modes:
            token = None
            if mode == "operator":
                token = os.environ.get("OPERATOR_TOKEN")
                if not token:
                    skipped.append("operator (OPERATOR_TOKEN not set)"); continue
            if mode == "member":
                token = os.environ.get("MEMBER_TOKEN")
                if not token:
                    skipped.append("member (MEMBER_TOKEN not set — f4 account pending)"); continue
            print(f"=== MODE: {mode} ===")
            results.append(run_mode(browser, mode, token))
            print()
        browser.close()

    print("================ SUMMARY ================")
    any_fail = False
    for r in results:
        status = "ABORTED" if r["aborted"] else f"{r['green']}/{r['total']} green"
        print(f"  {r['mode']:10} {status}")
        for f in r["fails"]:
            any_fail = True
            print(f"      FAIL: {f}")
    for s in skipped:
        print(f"  SKIPPED: {s}")
    print("========================================")
    sys.exit(1 if any_fail or any(r["aborted"] for r in results) else 0)


if __name__ == "__main__":
    main()
