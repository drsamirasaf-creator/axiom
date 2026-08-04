#!/usr/bin/env python3
"""The SUPPLY side: every payload that carries `period_labels` must reach the store.

⭐ THIS IS THE OTHER HALF OF `check-period-labels-consumed.py`, AND THE GAP BETWEEN
THEM SHIPPED. That checker counts render sites that CONSUME a label and reported
zero unwired. It was right. The Forecast Explorer's axis reads
`tickFormatter={periodTick}` — a correct consumer, at the correct seam. What
nothing checked was whether anything ever PUBLISHED the labels its payload
carried: `POST /forecast` returns `derived.period_labels`, and the fetch handler
did `setData(r.derived)` and dropped them. The axis then fell through to
`String(value)` and printed `20251` beside a correctly-labelled `2024Q4`.

⭐ DECLARED-BUT-UNBOUND AT ONE REMOVE. Both halves were bound — the producer
emitted, the consumer requested — and nothing forced them to meet. A checker that
can only see one end of a wire reports a connected circuit either way.

WHAT IT ASSERTS
  For every frontend fetch whose URL matches an endpoint known to emit
  `period_labels`, `setPeriodLabels` must appear inside THAT FETCH'S OWN PROMISE
  CHAIN — not merely somewhere in the enclosing component.

⭐ THE FIRST VERSION ASSERTED "somewhere in the enclosing component" AND PASSED
THE ONE SITE THIS WAS WRITTEN FOR. `ForecastChartPanel` fetches at :1600 and
calls `setPeriodLabels` at :1629 — same function, different branch: the publish
sits in the pro-forma FALLBACK, which runs only when the primary endpoint
refuses. Same-function proximity is not the same as same-payload. Two other
sites passed for the neighbouring reason — the fetch is in the page component and
the publish is in a CHILD that renders the result, so the labels are published
only if that child happens to mount. On another tab, the payload arrives and the
labels are dropped. Both are the mount-order defect, and a proximity rule calls
both of them wired.

So the rule is the chain: labels are published where the payload ARRIVES, once,
unconditionally.

⭐ THE DURABLE HANDLE IS THE BACKEND CROSS-CHECK, NOT THE URL LIST. A hardcoded
endpoint map goes stale the moment someone adds a sixth emitter, and a stale map
fails OPEN — it reports success over an endpoint it has never heard of. So this
first re-derives the emitting functions from the backend source and FAILS if that
set has changed. Adding an emitter breaks the build until the map is updated.
That converts "the list is out of date" from a silent state into a loud one.

ITS BLIND SPOTS, STATED:
  · URL matching is textual. A fetch built from a variable path is invisible.
  · "Enclosing component calls setPeriodLabels" does not prove it publishes THIS
    payload — only that it publishes something. It is a floor, not a proof.
  · Nothing here checks label COVERAGE: a payload may publish a map that omits
    periods the chart renders. That is a runtime property, not a static one.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.environ.get(
    "AXIOM_FRONTEND",
    os.path.join(os.path.dirname(ROOT), "optimization-anchor"))

# ── the backend cross-check ───────────────────────────────────────────────────
# Functions that emit `period_labels` into a response. Re-derived on every run;
# a mismatch fails the gate rather than silently leaving an endpoint unpoliced.
KNOWN_EMITTERS = {
    "derive_series",                        # engines.py  -> root / derived
    "dashboard_metrics",                    # engines.py  -> chart_data
    "data_coverage",                        # engines.py  -> coverage
    "stochastic_statements",                # proforma.py -> root
    "statement_of_comprehensive_income",    # oci.py      -> root
    # ⭐ §7s.1's pack freeze. ITS CONSUMER IS NOT AN ENDPOINT — it writes period
    # labels into a FROZEN SNAPSHOT that the pack renderer reads, so there is no
    # URL for the frontend check to match. Registered with an explicit empty
    # endpoint list rather than left unmapped, because "unmapped" and
    # "deliberately has no endpoint" are different facts and the gate could not
    # tell them apart.
    #
    # ⭐ THIS GATE WAS RED FROM 4648213 UNTIL 31 Jul AND NOBODY RAN IT — the
    # built-but-not-wired class applied to a GUARD. A guard nothing invokes is
    # indistinguishable from one that passes.
    "_cap_period_labels",                   # pack.py     -> frozen snapshot
}

# Endpoint URL fragments whose payload carries `period_labels`, by emitter.
ENDPOINTS = {
    "derive_series":                     ["/financials/datasets/${datasetId}/derived",
                                          "/financials/datasets/${datasetId}/forecast"],
    "dashboard_metrics":                 ["/metrics/dashboard/"],
    "data_coverage":                     ["/financials/datasets/${id}/profile"],
    "stochastic_statements":             ["/pro-forma"],
    "statement_of_comprehensive_income": ["/comprehensive-income"],
    # ⭐ EMPTY BY DESIGN, NOT BY OMISSION. The pack freeze has no endpoint; its
    # labels reach a reader through the rendered pack, which is checked by
    # check-pack-coverage rather than by a URL match here.
    "_cap_period_labels": [],
}
# Matched loosely: the distinctive tail of each path.
URL_MARKERS = ["/pro-forma", "/comprehensive-income", "/metrics/dashboard/",
               "/profile", "}/derived", "}/forecast`", "}/forecast\","]

# `publishPeriods` is the canonical publisher — it owns the map of WHERE labels
# sit in each payload shape. `setPeriodLabels` is the primitive underneath it and
# is accepted so a call site with an unusual shape is not forced to lie.
PUBLISHERS = ("publishPeriods", "setPeriodLabels")



# ⭐ A COVERAGE FLOOR. A guard that finds NOTHING TO CHECK must be red, never
# green: "0 problems in 0 files" and "0 problems in 400 files" print the same
# tick and mean opposite things. Two of these gates already exited 0 with the
# frontend absent, having opened no file at all.
#
# The floor is the observed count at the time of writing. It is not a target —
# it is the assertion that the SELECTOR still selects. Raise it when the real
# number grows; lowering it is only correct alongside a deliberate deletion, and
# should be argued for in the commit that does so.
MIN_FETCH_SITES = 6


def backend_emitters():
    """Enclosing function name of every `"period_labels":` emission in the API."""
    found = set()
    api = os.path.join(ROOT, "services", "api")
    for dirpath, _, files in os.walk(api):
        for f in files:
            if not f.endswith(".py") or f == "periods.py":
                continue
            p = os.path.join(dirpath, f)
            lines = open(p, encoding="utf-8").read().split("\n")
            for n, line in enumerate(lines):
                if '"period_labels"' not in line or ":" not in line:
                    continue
                if line.strip().startswith(("#", "from ", "import ")):
                    continue
                for i in range(n, -1, -1):
                    m = re.match(r"^(?:async )?def (\w+)", lines[i])
                    if m:
                        found.add(m.group(1))
                        break
    return found


def enclosing(lines, idx):
    """Name of the component/function containing line `idx` (0-based)."""
    for i in range(idx, -1, -1):
        m = re.match(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)", lines[i])
        if m:
            return m.group(1), i
        m = re.match(r"^(?:export\s+)?const\s+(\w+)\s*[:=].*=>", lines[i])
        if m:
            return m.group(1), i
    return "<module>", 0


def chain_extent(lines, fetch_line):
    """Last line of the promise chain the fetch at `fetch_line` belongs to.

    Walks from the `api(` call by paren depth, then keeps consuming while the
    next non-blank line continues the chain (`.then` / `.catch` / `.finally`).
    This is the scope in which the labels must be published: the handler that
    receives the payload, not the component that happens to contain it."""
    start = fetch_line
    for j in range(fetch_line, max(-1, fetch_line - 4), -1):
        if re.search(r"\bapi\s*[<(]", lines[j]):
            start = j
            break
    # ⭐ CALIBRATION: A FETCH PASSED AS A CALLBACK BELONGS TO ITS WRAPPER'S CHAIN.
    # `healOn404({ fetcher: (id) => api(...) })` puts the fetch inside an object
    # literal; the payload arrives on `healOn404(...).then(...)`, which is where
    # the publish correctly sits. Anchoring on the inner `api(` reported that as
    # unpublished — a real shape flagged wrong, which is how a checker gets muted.
    if re.search(r"\bfetcher\s*:", lines[start]):
        for j in range(start, max(-1, start - 12), -1):
            if re.search(r"\b\w+\s*<[^>]*>\s*\(\{|\b\w+\s*\(\{\s*$", lines[j]):
                start = j
                break
    depth = 0
    i = start
    while i < len(lines):
        depth += lines[i].count("(") - lines[i].count(")")
        if depth <= 0 and i >= start:
            nxt = i + 1
            while nxt < len(lines) and not lines[nxt].strip():
                nxt += 1
            if nxt < len(lines) and re.match(r"\s*\.(then|catch|finally)\b", lines[nxt]):
                i = nxt
                depth = 0
                continue
            return i
        i += 1
    return len(lines) - 1


def scan_frontend():
    findings, checked = [], 0
    for dirpath, dirs, files in os.walk(os.path.join(FRONTEND, "src")):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist")]
        for f in files:
            if not f.endswith((".ts", ".tsx")):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, FRONTEND)
            lines = open(p, encoding="utf-8").read().split("\n")
            for n, line in enumerate(lines):
                if not re.search(r"\bapi[<(]", line) and "api<" not in line:
                    # the fetch may put the URL on its own line inside api<T>(
                    if not any(m in line for m in URL_MARKERS):
                        continue
                    # URL-only line: require an api( within 3 lines above
                    if not any("api<" in lines[j] or "api(" in lines[j]
                               for j in range(max(0, n - 3), n)):
                        continue
                if not any(m in line for m in URL_MARKERS):
                    continue
                name, _ = enclosing(lines, n)
                end = chain_extent(lines, n)
                body = "\n".join(lines[n:end + 1])
                checked += 1
                if not any(x in body for x in PUBLISHERS):
                    url = re.search(r"`([^`]+)`", line)
                    findings.append((rel, n + 1, name,
                                     url.group(1) if url else line.strip()[:60]))
    return findings, checked


def main():
    emitters = backend_emitters()
    if emitters != KNOWN_EMITTERS:
        print("FAIL — the set of backend `period_labels` emitters has CHANGED.")
        for e in sorted(emitters - KNOWN_EMITTERS):
            print(f"  NEW emitter, unmapped to any endpoint: {e}()")
        for e in sorted(KNOWN_EMITTERS - emitters):
            print(f"  GONE: {e}()")
        print("\nUpdate KNOWN_EMITTERS and ENDPOINTS together. A stale map fails "
              "OPEN, which is why this is a hard stop.")
        return 1

    if not os.path.isdir(os.path.join(FRONTEND, "src")):
        # ⭐⭐ THE BACKEND HALF RAN AND PASSED, SO THIS EXITS 0 — ruled 4 Aug.
        # It used to return 1, which made CI red on main for three lanes and
        # made a REQUIRED STATUS CHECK impossible: requiring a check that is
        # always red blocks every push. The exit code was the defect, not the
        # code it guards.
        #
        # ⭐⭐ AND THE GREEN IS NOT ALLOWED TO READ AS FULL COVERAGE. The
        # original comment here was right about the hazard — "zero sites is not
        # all sites", and a tick over an unrun half is how a gate that never ran
        # reads as a gate that passed. The answer is not to fail; it is to SAY
        # WHICH HALF RAN, every time, in the output a reader sees.
        #
        # ⛔ `AXIOM_FRONTEND_OPTIONAL` IS GONE. It existed to let a caller
        # downgrade the whole check to a skip, and setting it on the enforced
        # step would have weakened a guard rather than fixed it. The halves are
        # now separate facts and neither is downgradable.
        print(f"  ✓ emitter cross-check: {len(KNOWN_EMITTERS)} emitters, all "
              f"mapped. BACKEND HALF ENFORCED.")
        print(f"  ⚠ FRONTEND HALF NOT RUN — no checkout at {FRONTEND}/src, so "
              f"0 fetch sites were scanned. This run asserts nothing about the "
              f"frontend. That half is enforced by the frontend repo's "
              f"pre-push hook, which has both checkouts.")
        return 0

    findings, checked = scan_frontend()
    print(f"  ✓ emitter cross-check: {len(KNOWN_EMITTERS)} emitters, all mapped.")
    for rel, line, fn, url in findings:
        print(f"  {rel}:{line}  {fn}() fetches a period_labels payload and never "
              f"publishes it\n      {url}")
    if findings:
        print(f"\nFAIL — {len(findings)} of {checked} fetch site(s) drop the labels "
              f"their payload carries. The axis falls back to the raw period.")
        return 1
    if checked < MIN_FETCH_SITES:
        print(f"FAIL — inspected only {checked} fetch site(s), floor is "
              f"{MIN_FETCH_SITES}. A pass over nothing is the failure this gate was "
              f"written after.")
        return 1
    print(f"✓ period-labels-published: {checked} fetch site(s) across "
          f"{len(KNOWN_EMITTERS)} emitters, all publish. "
          f"(Blind to coverage — see the module docstring.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
