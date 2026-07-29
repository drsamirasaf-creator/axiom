#!/usr/bin/env python3
"""Sweep every anonymous read route THROUGH THE PATH THE BROWSER TAKES.

⭐ WHY THIS EXISTS. A prospect on the demo saw "Failed to fetch" on
/api/v1/intelligence/cash-runway/45 while the standing sweep reported 50/50
green. Both were true. The sweep called the backend DIRECTLY; the browser calls
it through a same-origin Worker proxy (frontend `src/routes/api.public.axiom-proxy.ts`).
The failure lives on the hop the sweep did not traverse.

⭐ A SWEEP THAT BYPASSES THE PATH USERS TAKE PROVES NOTHING ABOUT WHAT USERS
EXPERIENCE. That is the whole point of this file, and it is why the DEFAULT
follows the topology rather than a fixed choice of hop.

The Worker proxy was removed (frontend 086c27d) after it was measured at 67.4%
transport failure against 0.0% direct, so browsers call the backend DIRECTLY
again and direct is now the default here. `--proxy` remains for the day someone
reintroduces a hop: the flag to reach for is the one that matches what the
browser does, and if that ever changes, THIS DEFAULT MUST CHANGE WITH IT. A
sweep whose default silently stops matching the browser is exactly the failure
this file was written after — 50/50 green over a path no browser took.

⭐ AND IT SEPARATES TRANSPORT FAILURE FROM HTTP STATUS. "Failed to fetch" is not
a status code: there is no response at all, so a sweep that records only status
codes cannot see it. Every request here records the curl exit code beside the
status, and a non-zero exit is counted as a FAILURE even when no HTTP status was
ever produced. Observed exit codes and what they mean:

    0   response received (check the status)
    16  HTTP/2 framing error   <- this is the demo failure
    92  HTTP/2 stream error
    28  timeout
    35  TLS handshake failure
    56  receive error

⭐ THE ROUTE LIST IS DERIVED FROM SOURCE, NOT TYPED HERE. A hardcoded list goes
stale silently and then reports green over routes it has never heard of — the
same fail-open shape `check-period-labels-published.py` was built to close. This
parses the router modules for their decorators on every run, so a new route is
swept the day it is added.

Repetition matters: the failure is INTERMITTENT (~17% measured on the proxy hop,
0% direct). One pass per route would miss it, so each route is hit `--repeat`
times and the failure RATE is what gets reported, not a pass/fail tick.
"""
import argparse
import os
import re
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.environ.get("APP_URL", "https://axiomdynamics.app").rstrip("/")
BACKEND = os.environ.get(
    "BACKEND_URL", "https://web-production-0e3de.up.railway.app").rstrip("/")
PROXY = "/api/public/axiom-proxy?path="

# Router modules to sweep, with the prefix each mounts at.
# ⭐ accounts.py WAS MISSING AND THAT IS THE WHOLE LESSON. This sweep reported
# "33/33 clean · every swept route answered on the browser's path" at the exact
# moment SIX anonymous routes were returning 500 — /assessment/swot,
# /departments, /initiatives, /initiatives/cockpit, /assessment/sentiment and
# /assessment/axis/{code}/comments. Every one of them lives in accounts.py, which
# was not in this list.
#
# This file's own docstring warns that a hardcoded list "goes stale silently and
# then reports green over routes it has never heard of". That warning was written
# about the endpoint map, and then the same mistake was made one constant above
# it. A sweep is only as wide as its inventory, and the inventory needs the same
# suspicion as the thing it inventories.
ROUTER_FILES = [
    "services/api/accounts.py",
    "services/api/modules/intelligence/router.py",
    "services/api/modules/financials/router.py",
    "services/api/modules/valuation/router.py",
    "services/api/modules/twin/router.py",
]

EXIT_MEANING = {
    0: "ok", 16: "HTTP/2 framing", 92: "HTTP/2 stream", 28: "timeout",
    35: "TLS", 56: "recv error", 7: "connect failed", 6: "DNS",
}


# Params that are dependencies, not caller input — never sent as query params.
_DEP_PARAMS = {"db", "tenant", "scoped", "authed", "member", "user", "perm",
               "request", "response", "authorization", "x_axiom_tenant"}


def _required_query_params(src, decorator_end):
    """Params the handler REQUIRES as query string, from its signature.

    ⭐ WITHOUT THIS THE SWEEP REPORTS ITS OWN GAP AS A DEFECT. Two routes take
    `dataset_id` as a QUERY param rather than a path param; calling them bare
    returns 422, and the first run duly listed both as failures. A checker whose
    output contains its own mistakes gets muted, and then it is worse than
    nothing — so the signature is read rather than guessed."""
    tail = src[decorator_end:decorator_end + 1200]
    m = re.search(r'def\s+\w+\(([^)]*)\)', tail, re.S)
    if not m:
        return []
    out = []
    for raw in m.group(1).split(","):
        part = raw.strip()
        if not part or "=" in part:          # has a default -> optional
            continue
        name = part.split(":")[0].strip()
        if not name or name in _DEP_PARAMS:
            continue
        out.append(name)
    return out


def routes_from_source():
    """Every GET route in the swept routers, with its prefix and required query
    params.

    Only GETs: a sweep must not issue writes, and the demo surfaces a prospect
    touches are reads."""
    out = []
    for rel in ROUTER_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        # ⭐ POSITIONAL, NOT A NAME->PREFIX DICT. accounts.py rebinds the name
        # `router` SIX times with different prefixes (/auth, /auth/oauth, none,
        # /me, /admin, none). A dict keyed on the variable name keeps only the
        # last, which would have mis-prefixed every route in the file. The prefix
        # that applies is the nearest PRECEDING assignment to that same name.
        assigns = [(m.start(), m.group(1), m.group(2) or "")
                   for m in re.finditer(
                       r'(\w+)\s*=\s*APIRouter\((?:prefix="([^"]*)")?', src)]

        def prefix_at(name, pos):
            best = None
            for start, var, pfx in assigns:
                if var == name and start < pos:
                    best = pfx
            return best

        for m in re.finditer(r'@(\w+)\.get\("([^"]+)"', src):
            router, route = m.group(1), m.group(2)
            prefix = prefix_at(router, m.start())
            if prefix is None:
                continue
            in_path = set(re.findall(r"\{(\w+)\}", route))
            need = [q for q in _required_query_params(src, m.end())
                    if q not in in_path]
            out.append((rel, prefix + route, tuple(need)))
    return sorted(set(out), key=lambda t: t[1])


def fill(route, need, dataset_id, company_id):
    """Substitute path params and append required query params. A route whose
    params we cannot fill is SKIPPED and reported as skipped — never silently
    dropped, which would shrink the denominator and make the sweep look better
    than it is."""
    known = {"dataset_id": dataset_id, "company_id": company_id}
    filled = (route
              .replace("{dataset_id}", str(dataset_id))
              .replace("{company_id}", str(company_id)))
    if "{" in filled:
        return None
    qs = []
    for q in need:
        if q not in known:
            return None                      # unknown required input -> skip, loudly
        qs.append(f"{q}={known[q]}")
    return filled + ("?" + "&".join(qs) if qs else "")


def request(url, timeout=45):
    """(http_status, curl_exit). curl_exit != 0 means NO RESPONSE — the
    'Failed to fetch' case, invisible to a status-only check."""
    p = subprocess.run(
        ["curl", "-s", "-o", os.devnull, "-w", "%{http_code}", "-m", str(timeout), url],
        capture_output=True, text=True)
    status = (p.stdout or "000").strip()
    return status, p.returncode


def sweep(routes, through_proxy, repeat, workers):
    def target(path):
        if through_proxy:
            return f"{APP}{PROXY}{urllib.parse.quote(path, safe='')}"
        return f"{BACKEND}{path}"

    results = {}

    def run_one(path):
        statuses, exits = [], []
        for _ in range(repeat):
            s, e = request(target(path))
            statuses.append(s)
            exits.append(e)
        return path, statuses, exits

    with ThreadPoolExecutor(workers) as ex:
        for path, statuses, exits in ex.map(run_one, routes):
            results[path] = (statuses, exits)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proxy", action="store_true",
                    help="route through the Worker proxy (only if one is reintroduced)")
    ap.add_argument("--direct", action="store_true",
                    help="explicit direct mode; direct is already the default")
    ap.add_argument("--repeat", type=int, default=6,
                    help="requests per route; the failure is intermittent, so >1 is the point")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dataset", type=int, default=45)
    ap.add_argument("--company", type=int, default=20)
    args = ap.parse_args()

    discovered = routes_from_source()
    routes, skipped = [], []
    for rel, route, need in discovered:
        f = fill(route, need, args.dataset, args.company)
        (routes if f else skipped).append(f or route)
    routes = sorted(set(routes))

    through_proxy = args.proxy and not args.direct
    where = "THROUGH the Worker proxy" if through_proxy else "DIRECT to the backend (the browser's path)"
    print(f"  {len(routes)} GET route(s) from {len(ROUTER_FILES)} router module(s), "
          f"{args.repeat}x each, {where}")
    if skipped:
        print(f"  {len(skipped)} skipped (unfillable path params) — NOT counted as passing:")
        for s in skipped:
            print(f"      skip {s}")

    results = sweep(routes, through_proxy, args.repeat, args.workers)

    transport, http_err, clean, n_gated = [], [], 0, 0
    exit_tally = {}
    for path, (statuses, exits) in sorted(results.items()):
        bad_exit = [e for e in exits if e != 0]
        for e in exits:
            exit_tally[e] = exit_tally.get(e, 0) + 1
        # ⭐ 401/403 IS A CORRECTLY GATED ROUTE, NOT A BROKEN ONE. An anonymous
        # sweep can only assert what is anonymously readable; counting auth
        # refusals as failures would bury the real 500s under noise and get the
        # whole sweep muted.
        bad_http = [s for s, e in zip(statuses, exits)
                    if e == 0 and not s.startswith("2") and s not in ("401", "403")]
        gated = [s for s, e in zip(statuses, exits) if e == 0 and s in ("401", "403")]
        if bad_exit:
            transport.append((path, len(bad_exit), len(exits), sorted(set(bad_exit))))
        elif gated and not bad_http:
            n_gated += 1
        elif bad_http:
            http_err.append((path, sorted(set(bad_http)), len(bad_http), len(exits)))
        else:
            clean += 1

    total_reqs = sum(len(e) for _, e in results.values())
    fails = sum(1 for _, (_, exits) in results.items() for e in exits if e != 0)

    if transport:
        print(f"\n  TRANSPORT FAILURES — no HTTP response at all "
              f"(this is what renders as 'Failed to fetch'):")
        for path, n, of, codes in transport:
            names = ", ".join(f"{c} ({EXIT_MEANING.get(c, '?')})" for c in codes)
            print(f"    {n}/{of}  {path}\n         curl exit {names}")
    if http_err:
        print(f"\n  HTTP ERROR STATUS:")
        for path, codes, n, of in http_err:
            print(f"    {n}/{of}  {path}  -> {','.join(codes)}")

    print(f"\n  auth-gated (401/403, correctly refused anonymously): {n_gated}")
    print(f"  clean routes: {clean}/{len(routes)}   "
          f"requests: {total_reqs}   transport failures: {fails} "
          f"({100.0 * fails / total_reqs:.1f}%)" if total_reqs else "")
    print("  curl exit tally: " + "  ".join(
        f"{k}×{v} ({EXIT_MEANING.get(k, '?')})" for k, v in sorted(exit_tally.items())))

    if transport or http_err:
        print("\n  FAIL — a route a prospect can reach did not answer on the path "
              "the browser uses.")
        return 1
    print("\n  ✓ every swept route answered on the browser's path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
