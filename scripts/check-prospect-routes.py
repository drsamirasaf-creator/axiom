#!/usr/bin/env python3
"""Every prospect-facing route must resolve for a visitor who has no account.

⭐⭐ THE DEFECT THIS EXISTS FOR. `/what-is-axiom` returned 404 to every anonymous
visitor while rendering perfectly for every signed-in operator, and BOTH the
lane's wiring assertion and the three-mode crawl reported pass. The page was
never gated — it was UNREACHABLE BY ITS OWN NAME. The sidebar labelled it
"What is AXIOM?" and the only URL was `/how-it-works`.

⭐ THE WIRING ASSERTION READ A FILE AND MATCHED SUBSTRINGS. It proved a file
existed and contained the component. ⭐⭐ IT NEVER MADE A REQUEST AND NEVER NAMED
A URL, so the page's NAME and the page's PATH were never compared — and the gap
between them was the whole defect.

⭐ THE CRAWL DISCOVERED ITS ROUTES FROM THE SIDEBAR, which only exists once you
are signed in. ⭐⭐ DISCOVERY THAT DEPENDS ON BEING SIGNED IN CANNOT COVER THE
SIGNED-OUT CASE — the mode with the most to prove had the smallest route list.

⭐ CONTROLS PLANTED IN MEMORY, never in production source — the guard-planting
cleanup failure has happened three times.

Structural by default. `--against-app` fetches the live frontend.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

APP_BASE = os.environ.get("AXIOM_APP_BASE", "https://axiomdynamics.app")


def unreachable(results):
    """`results` = [{path, status}] -> the prospect routes a visitor cannot reach.

    ⭐ 2xx AND 3xx BOTH PASS. A redirect is a route that resolves; `/how-it-works`
    is deliberately a redirect and failing it would punish the fix.

    ⭐ PURE OVER A LIST, so the control and the live check run the SAME code. A
    guard whose control exercises a different function has tested nothing.
    """
    return [r for r in results if not (200 <= int(r["status"]) < 400)]


def _control():
    """⭐⭐ THE KNOWN POSITIVE — a scanner that has never fired has not been
    tested. Case one is the exact 1 Aug shape."""
    fails = []
    cases = [
        ([{"path": "/what-is-axiom", "status": 404}], True,
         "the exact defect: a prospect route 404s anonymously"),
        ([{"path": "/what-is-axiom", "status": 200}], False, "it resolves"),
        ([{"path": "/how-it-works", "status": 307}], False,
         "a redirect is a route that resolves"),
        ([{"path": "/pricing", "status": 401}], True,
         "a prospect route behind a login wall"),
        ([{"path": "/pricing", "status": 500}], True, "a prospect route that errors"),
    ]
    for rows, should_flag, label in cases:
        if bool(unreachable(rows)) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}")
    return fails


def routes():
    """⭐ ONE LIST, READ FROM THE CRAWLER. Two copies of a route list drift, and
    the copy nobody checks is the one that goes stale."""
    import importlib.util
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth-regression.py")
    spec = importlib.util.spec_from_file_location("_ar", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.PROSPECT_ROUTES), set(mod.HOLDING_ROUTES)


def main():
    fails = _control()
    if fails:
        print("✗ check-prospect-routes: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags a 404, a login wall and a 500 on a prospect route; "
          "accepts a 200 and accepts a redirect")

    rs, holding = routes()
    # ⭐ COVERAGE PRINTED. "0 unreachable in 0 routes" and "0 in 10" print the
    # same tick and mean opposite things (III.4).
    print(f"  prospect routes declared: {len(rs)}")
    if not rs:
        print("✗ zero prospect routes declared — a broken selector, not a clean list")
        return 1
    for r in rs:
        # ⭐ DARK IS DECLARED, NOT DISCOVERED. A route suppressed on purpose and
        # a route that 404s both need naming; only one is a defect.
        print(f"    {r}" + ("   [deliberately dark — holding mode]" if r in holding else ""))
    print(f"  of which deliberately dark: {len(holding & set(rs))}")

    if "/what-is-axiom" not in rs:
        print("✗ /what-is-axiom is not among the prospect routes — the page the "
              "guard exists for is not covered by it")
        return 1

    if "--against-app" not in sys.argv:
        print("✓ check-prospect-routes: structural control passed "
              "(pass --against-app to fetch the live frontend)")
        return 0

    import urllib.error
    import urllib.request
    results = []
    for path in rs:
        try:
            req = urllib.request.Request(APP_BASE + path,
                                         headers={"User-Agent": "axiom-prospect-guard"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                st = resp.status
        except urllib.error.HTTPError as e:
            st = e.code
        except Exception as e:
            st = f"ERR {type(e).__name__}"
        results.append({"path": path, "status": st})
        print(f"    {path} -> {st}")

    bad = unreachable([r for r in results if isinstance(r["status"], int)]) + \
        [r for r in results if not isinstance(r["status"], int)]
    if bad:
        print(f"✗ {len(bad)} prospect route(s) a visitor cannot reach:")
        for b in bad:
            print(f"   {b['path']} -> {b['status']}")
        print("\n  A prospect reaches these before they have an account. A 404 "
              "here is lost revenue, not a broken link.")
        return 1
    print(f"✓ all {len(results)} prospect routes resolve for an anonymous visitor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
