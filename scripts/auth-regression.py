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
# Sidebar shape after the 2026-07 restructure (nav consolidated into hub pages):
#  - "Collaborative Assessment" folded into Stakeholder Engagement (Survey Feedback /
#    Survey Design tabs); standalone "SWOT Analysis" + "Risk Analysis" merged into
#    "SWOT & Risk Analysis"; "Valuation" -> "Enterprise Valuation"; "Executive Brief"
#    folded into "Dashboard & Reports"; "Initiative Management" -> "Initiatives & Projects".
EXPECTED_SIDEBAR_LINKS = [
    "Dashboard & Reports", "Stakeholder Engagement", "SWOT & Risk Analysis",
    "Enterprise Valuation", "Business Planning & Forecasting",
    "Enterprise Optimization", "Prescience AI",
    "Initiatives & Projects", "Performance Monitoring",
    "Course Workspace", "What is AXIOM?",
    # custody-10: the data-upload door must have a PERMANENT, app-controlled
    # sidebar link. If this vanishes (a nav restructure drops it), the crawler
    # FAILS — the upload path can never disappear silently again.
    "Data Input",
]
# Routes that must REDIRECT (not appear as their own sidebar link). Folded hub
# routes (/cei, /data-input, /financial-forecasts, /risk-analysis, /brief) still
# render at their own URL — they're just no longer top-level sidebar links — so
# they are asserted via EXPECTED_SIDEBAR_LINKS' absence, not here.
FORBIDDEN_SIDEBAR_HREFS = {"/reports", "/benchmarking"}
EXPECTED_GROUPS = ["ANALYZE", "STRATEGIZE", "EXECUTE & MONITOR", "UTILITY"]

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
    # /data-input is NOT an alias — it renders its own page (the upload door). Its
    # reachability is asserted by the dedicated DATA-UPLOAD probe + sidebar link below.
    "/financial-forecasts": {"dest": "/financial-forecasts",             "needle": "FCFF"},
    # Lovable route alias (reported as a bare tuple); normalized to the committed
    # dict shape + verified live (2026-07): /discussion -> the discussion tab of
    # Stakeholder Engagement. needle is the tab's own heading, not the page H1.
    "/discussion":          {"dest": "/stakeholder-engagement?tab=discussion", "needle": "Discussion"},
}
# sub-tab presence: route -> at least one tab-like control must render
SUBTABS = {
    "/dashboard":              "tab",
    "/risk-analysis":          "tab",
    # Restructure hub pages now carry cross-route tab bars (RouteTabs).
    "/stakeholder-engagement": "tab",   # Survey Feedback / Survey Design / Participants / Discussion
    "/swot":                   "tab",   # SWOT / Risk Analysis / Benchmarking
    "/initiatives":            "tab",   # Initiatives & Projects Underway / Recommendations & Proposals
    # Team moved OFF the top-level sidebar to a tab under My AXIOM (MY_AXIOM_TABS).
    # Both are real routes joined by one RouteTabs bar (no ?tab= param).
    "/my-axiom":               "tab",   # My AXIOM / Team
    "/team":                   "tab",   # My AXIOM / Team
}
# The app's tabs are underline-style <button>s (Tailwind `border-b-2 -mb-px`,
# active=border-brass / inactive=border-transparent) driving ?tab=/?section= —
# NOT role='tab', anchors, or data-state. Verified live 2026-07 (dashboard 3,
# risk-analysis 9, valuation 3, cei 7). The selector also keeps the standard
# ARIA/anchor/tablist forms so a future restyle to those still matches.
TAB_SELECTOR = ("[role='tab'], a[href*='tab='], a[href*='section='], "
                "button[class*='border-b-2'][class*='-mb-px'], "
                # RouteTabs whose tabs are plain route links (no ?tab=), e.g. My AXIOM / Team
                "a[class*='border-b-2'][class*='-mb-px'], [role='tablist'] button")
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


class ConsoleSink:
    """Collects uncaught page errors + console.error output so a click that throws
    an exception or logs an error is attributed to the control that caused it."""
    def __init__(self):
        self.errors = []

    def clear(self):
        self.errors = []

    def on_console(self, msg):
        try:
            if msg.type == "error":
                t = msg.text
                # ignore benign noise (favicon/network 4xx logged by the browser)
                if not any(n in t.lower() for n in ("favicon", "failed to load resource")):
                    self.errors.append(t[:140])
        except Exception:
            pass

    def on_pageerror(self, exc):
        try:
            self.errors.append("pageerror: " + str(exc)[:140])
        except Exception:
            pass


# markers that mean the app's error boundary / a hard render failure is on screen
_ERR_MARKERS = ("something went wrong", "unexpected error", "cannot read propert",
                "is not a function", "is not defined", "application error",
                "this page isn't working", "render error", "reference error",
                "undefined is not")


def _err_surface(page):
    try:
        low = (page.inner_text("body") or "").lower()
    except Exception:
        return False
    return any(m in low for m in _ERR_MARKERS)


# controls to exercise: buttons, tabs, sub-tabs, dropdowns, expanders
INTERACTIVE_SEL = ("button:not([disabled]), [role='tab'], select, [aria-expanded], "
                   "button[class*='border-b-2'][class*='-mb-px'], "
                   "a[class*='border-b-2'][class*='-mb-px']")


def _control_label(el):
    try:
        tag = el.evaluate("e => e.tagName.toLowerCase()")
    except Exception:
        tag = "?"
    txt = ""
    for getter in (lambda: el.inner_text(),
                   lambda: el.get_attribute("aria-label"),
                   lambda: el.get_attribute("title")):
        try:
            v = getter()
            if v and v.strip():
                txt = v.strip(); break
        except Exception:
            pass
    txt = " ".join(txt.split())[:40] or f"<{tag}>"
    return tag, txt


def _find_control(page, tag, txt):
    """Re-locate a fresh handle for (tag,txt) — DOM may have re-rendered since the
    snapshot, so stored handles go stale."""
    try:
        base = page.locator(tag)
        if txt and not txt.startswith("<"):
            cand = base.filter(has_text=txt)
            if cand.count() > 0:
                return cand.first
        return base.first if base.count() > 0 else None
    except Exception:
        return None


def interaction_sweep(page, rec, sink, path, tick, cap=16):
    """Click every interactive control on `path` (bounded to `cap`) in the current
    (authed) session. Returns a list of (route, control, outcome) findings — only
    non-OK outcomes are recorded; a clean control is silent. State is recovered by
    re-navigating whenever an error surface or an off-route navigation is seen."""
    findings, acted = [], 0
    try:
        page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
        page.wait_for_timeout(SETTLE_MS)
    except Exception as e:
        return [(path, "(load)", f"nav error {str(e)[:50]}")], 0
    tick()
    if _err_surface(page):
        return [(path, "(initial render)", "ERROR SURFACE on load")], 1

    # snapshot visible, de-duped control labels first (clicking mutates the DOM)
    labels, seen = [], set()
    try:
        loc = page.locator(INTERACTIVE_SEL)
        scan = min(loc.count(), cap * 5)
        for i in range(scan):
            if len(labels) >= cap:
                break
            el = loc.nth(i)
            try:
                if not el.is_visible():
                    continue
            except Exception:
                continue
            tag, txt = _control_label(el)
            key = (tag, txt.lower())
            if key in seen:
                continue
            seen.add(key)
            labels.append((tag, txt))
    except Exception:
        pass

    prev = None                 # label of the control clicked last iteration
    for tag, txt in labels:
        # a late-rendering (debounced-async) crash from the PREVIOUS click surfaces
        # here — attribute it to that control before recovering.
        if _err_surface(page):
            if prev is not None:
                findings.append((path, prev, "ERROR BOUNDARY (async, after click)"))
            try:
                page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
                page.wait_for_timeout(1200)
            except Exception:
                pass
        prev = f"{tag} · {txt}"
        sink.clear()
        before = len(rec.calls)
        cur = page.url
        el = _find_control(page, tag, txt)
        if el is None:
            continue
        acted += 1
        # dropdowns: cycle each option and watch for a break
        if tag == "select":
            bad = None
            try:
                opts = el.locator("option")
                for oi in range(min(opts.count(), 8)):
                    el.select_option(index=oi, timeout=1500)
                    page.wait_for_timeout(450)
                    if _err_surface(page):
                        try:
                            bad = (opts.nth(oi).inner_text() or "")[:24]
                        except Exception:
                            bad = f"option {oi}"
                        break
            except Exception as e:
                findings.append((path, f"select · {txt}", f"select failed: {str(e)[:40]}"))
                continue
            if bad:
                findings.append((path, f"select · {txt}", f"ERROR on option '{bad}'"))
                try:
                    page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
                    page.wait_for_timeout(1000)
                except Exception:
                    pass
            continue
        # buttons / tabs / expanders / links. The app re-renders continuously
        # (persistent connection), so Playwright's actionability wait never settles
        # → use force + a DOM dispatch fallback to actually fire the handler.
        clicked = False
        try:
            el.click(timeout=1200, force=True)
            clicked = True
        except Exception:
            try:
                el.dispatch_event("click")
                clicked = True
            except Exception as e:
                findings.append((path, f"{tag} · {txt}", f"click failed: {str(e).split(chr(10),1)[0][:40]}"))
        if not clicked:
            continue
        page.wait_for_timeout(1200)     # allow debounced-async flows (compare, fetch, re-render) to fire
        tick()
        if _err_surface(page):
            findings.append((path, f"{tag} · {txt}", "ERROR BOUNDARY"))
            try:
                page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
                page.wait_for_timeout(1000)
            except Exception:
                pass
            continue
        five = [c for c in rec.calls[before:] if c[2] >= 500]
        if five:
            findings.append((path, f"{tag} · {txt}", f"backend {five[0][2]} {five[0][1]}"))
        if sink.errors:
            findings.append((path, f"{tag} · {txt}", f"console: {sink.errors[0][:60]}"))
        # off-route navigation → return to keep sweeping this route's controls
        if _norm_href(page.url) != path:
            try:
                page.goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
                page.wait_for_timeout(900)
            except Exception:
                pass
    return findings, acted


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


LAUNCH_ARGS = ["--disable-dev-shm-usage", "--disable-gpu", "--no-sandbox"]


def run_mode(p, mode, token, headed=False, recycle_every=0, sweep=False):
    """Crawl one mode. `recycle_every` > 0 relaunches the WHOLE browser every N
    navigations (operator mode). The app's heavy authed pages (index-DA3rwP6P
    onward) leak renderer memory across route changes; a single reused tab OOM-
    crashes at ~13 heavy routes, and a fresh page per route deadlocks the browser.
    Batch recycling — one reused page for a batch of N (< crash threshold), then
    destroy+relaunch the browser fresh — caps accumulation without the per-page
    session churn. Anonymous/member pass recycle_every=0 (they complete clean)."""
    fails = []
    rec = Recorder()
    sink = ConsoleSink()
    interactions = []       # (route, control, outcome) findings from the sweep
    authed = mode in ("operator", "member")
    st = {"b": None, "ctx": None, "pg": None, "n": 0}

    def launch():
        b = p.chromium.launch(headless=not headed, args=LAUNCH_ARGS)
        ctx = make_context(b, token)
        pg = ctx.new_page()
        pg.on("response", rec.on_response)
        pg.on("console", sink.on_console)
        pg.on("pageerror", sink.on_pageerror)
        st.update(b=b, ctx=ctx, pg=pg, n=0)

    def shutdown():
        for k in ("pg", "ctx", "b"):
            try:
                if st.get(k):
                    st[k].close()
            except Exception:
                pass

    def tick():
        st["n"] += 1
        if recycle_every and st["n"] >= recycle_every:
            shutdown(); launch()

    launch()

    if authed:
        ok, msg = sanity_gate(st["pg"], rec); tick()
        print(f"  [sanity gate] {'PASS' if ok else 'ABORT'} — {msg}", flush=True)
        if not ok:
            shutdown()
            return {"mode": mode, "aborted": True, "fails": [f"SANITY GATE: {msg}"], "green": 0, "total": 0}

    # ---- route enumeration: discover from the live sidebar (authed) + extras ----
    routes = set()
    sidebar_links, nav_text = ([], "")
    if authed:
        # read the sidebar off the page the sanity gate already left on /dashboard
        # (no recycle has happened yet at n=1, so it's live) — re-navigating a heavy
        # authed page here and then walking the DOM wedged the renderer.
        try:
            sidebar_links, nav_text = read_sidebar(st["pg"])
        except Exception:
            pass
        routes.update(h for _, h in sidebar_links if h.startswith("/"))
    else:
        routes.update(EXTRA_ROUTES_ANON)
    routes.update(ALIASES.keys())
    routes.update(SUBTABS.keys())
    routes.discard("")

    # ---- per-route render + silent-empty ----
    green = 0
    for path in sorted(routes):
        ok, why, _nonok, _n = visit(st["pg"], rec, path); tick()
        if ok:
            green += 1
        else:
            fails.append(f"{mode} route {APP_BASE}{path} :: {why}")
        print(f"    {mode} {path} -> {'ok' if ok else why[:60]}", flush=True)

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
            st["pg"].goto(APP_BASE + alias, wait_until=WAIT_UNTIL, timeout=30000)
            st["pg"].wait_for_timeout(SETTLE_MS)
            final = _norm_href(st["pg"].url)
            body = (st["pg"].inner_text("body") or "")
        except Exception as e:
            fails.append(f"{mode} alias {alias} :: navigation error {e}"); tick(); continue
        tick()
        if final == alias and alias in FORBIDDEN_SIDEBAR_HREFS:
            fails.append(f"{mode} alias {alias} did NOT redirect (still {final})")
        if authed and spec["needle"] and spec["needle"].lower() not in body.lower():
            fails.append(f"{mode} alias {alias} -> {final} missing needle '{spec['needle']}' "
                         f"(VERIFY reconstructed dest/needle)")

    # ---- sub-tabs ----
    if authed:
        for path, _kind in SUBTABS.items():
            try:
                st["pg"].goto(APP_BASE + path, wait_until=WAIT_UNTIL, timeout=30000)
                st["pg"].wait_for_timeout(SETTLE_MS)
                n_tabs = st["pg"].locator(TAB_SELECTOR).count()
            except Exception:
                n_tabs = 0
            tick()
            if n_tabs < 1:
                fails.append(f"{mode} sub-tabs MISSING on {path}")

    # ---- DATA-UPLOAD door reachability (custody-10) ----
    # The upload path has vanished twice (a Lovable redirect, then a missing nav
    # entry). This asserts, from an authed session, that /data-input RENDERS its
    # own upload surface (never redirects away) AND exposes an upload control /
    # template-download / company-select prompt. FAIL = the door is broken again.
    if authed:
        up_ok, up_why = True, ""
        try:
            st["pg"].goto(APP_BASE + "/data-input", wait_until=WAIT_UNTIL, timeout=30000)
            st["pg"].wait_for_timeout(SETTLE_MS)
            final = _norm_href(st["pg"].url)
            body = (st["pg"].inner_text("body") or "").lower()
            has_file = st["pg"].locator("input[type='file']").count() > 0
            markers = any(m in body for m in (
                "download template", "financial data", "additional documents",
                "select a company", "upload"))
            if final != "/data-input":
                up_ok, up_why = False, f"redirected away to {final}"
            elif not (has_file or markers):
                up_ok, up_why = False, "no upload control / data-input surface rendered"
        except Exception as e:
            up_ok, up_why = False, f"navigation error {e}"
        tick()
        if not up_ok:
            fails.append(f"{mode} DATA-UPLOAD door UNREACHABLE on /data-input :: {up_why}")

    # ---- interaction-level sweep (report-only; operator/authed) ----
    # Click every interactive control per route and record any error boundary,
    # console error, backend 5xx, or failed click. Findings are REPORTED, not
    # graded (they don't fail the run) — this is the standing pre-launch gate.
    swept_controls = 0
    if sweep and authed:
        print("  [interaction sweep] clicking controls per route…", flush=True)
        for path in sorted(routes):
            try:
                found, acted = interaction_sweep(st["pg"], rec, sink, path, tick)
            except Exception as e:
                found, acted = [(path, "(sweep)", f"sweep error {str(e)[:50]}")], 0
            swept_controls += acted
            interactions.extend(found)
            mark = f"{len(found)} finding(s)" if found else "clean"
            print(f"    swept {path} ({acted} controls) -> {mark}", flush=True)

    # ---- demo-safety: anonymous fires zero authenticated calls ----
    if mode == "anonymous":
        leaked = rec.any_authed()
        if leaked:
            fails.append(f"anonymous fired {len(leaked)} AUTHENTICATED call(s): {leaked[:5]}")

    total = len(routes) + ((len(EXPECTED_SIDEBAR_LINKS) + len(EXPECTED_GROUPS)
                            + len(ALIASES) + len(SUBTABS) + 1) if authed else 1)
    shutdown()
    return {"mode": mode, "aborted": False, "fails": fails, "green": total - len(fails),
            "total": total, "interactions": interactions, "swept_controls": swept_controls}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["anonymous", "operator", "member", "all"])
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--interactions", action="store_true",
                    help="also click every interactive control per route (authed) and "
                         "report a route·control·outcome table — report-only, does not grade")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. `pip install playwright && playwright install chromium`")
        sys.exit(2)

    modes = ["anonymous", "operator", "member"] if args.mode == "all" else [args.mode]
    # operator's heavy authed pages need browser recycling; the others complete on
    # a single browser. RECYCLE_EVERY is 0 (off) except operator.
    RECYCLE = {"operator": int(os.environ.get("OPERATOR_RECYCLE_EVERY", "8"))}
    results, skipped = [], []
    print(f"AXIOM auth-regression crawler — {APP_BASE}\n")
    with sync_playwright() as p:
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
            results.append(run_mode(p, mode, token, headed=args.headed,
                                    recycle_every=RECYCLE.get(mode, 0),
                                    sweep=args.interactions))
            print()

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

    if args.interactions:
        print("\n============ INTERACTION SWEEP (report-only) ============")
        for r in results:
            inter = r.get("interactions")
            if inter is None:
                continue
            swept = r.get("swept_controls", 0)
            print(f"  mode {r['mode']}: {swept} controls exercised · {len(inter)} finding(s)")
            if inter:
                w1 = min(28, max((len(x[0]) for x in inter), default=6))
                w2 = min(40, max((len(x[1]) for x in inter), default=8))
                print(f"    {'ROUTE'.ljust(w1)}  {'CONTROL'.ljust(w2)}  OUTCOME")
                print(f"    {'-'*w1}  {'-'*w2}  {'-'*30}")
                for route, control, outcome in inter:
                    print(f"    {route[:w1].ljust(w1)}  {control[:w2].ljust(w2)}  {outcome}")
            else:
                print("    (no error boundaries / console errors / dead clicks found)")
        print("========================================================")
    # interaction findings are REPORT-ONLY — they never change the exit code
    sys.exit(1 if any_fail or any(r["aborted"] for r in results) else 0)


if __name__ == "__main__":
    main()
