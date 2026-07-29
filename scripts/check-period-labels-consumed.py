#!/usr/bin/env python3
"""Every period shown to a human must render the SUPPLIED label, not raw `year`.

⭐ THIS EXISTS BECAUSE "WIRED" WAS REPORTED AND WAS NOT TRUE. The period-label
lane's commit message said the frontend consumed the backend labels; four sites
had been changed out of roughly eighty-six. Nothing contradicted it, because
there was no way to ask the question — so the claim stood until a customer saw
`20231` in a column header.

A count is the point. "Some sites are wired" is not a state anyone can act on;
"61 of 63 are wired, here are the two" is. This reports the remaining work as a
list, so completion is checkable rather than asserted.

WHAT COUNTS AS A RENDER SITE
  · a JSX interpolation of a period-ish value — {y}, {c.year}, {row.year}
  · a Recharts axis/tooltip/legend keyed on a period without a tickFormatter
    (the tick label IS the raw value otherwise)
  · a period pushed into a CSV row or a column-header array

WHAT COUNTS AS CONSUMING THE LABEL
  · periodLabel(...) / periodLabels(...) — the lookup helper
  · a *_label field off the payload (year_label)
  · a period_labels map read

⭐ IT TOOK THREE CALIBRATIONS AND THAT WAS THE WORK. The raw pattern flagged 53
sites; 14 of those were SVG geometry (`<line y1={cy} y2={y}>`), React keys
(`key={y}` is never shown to anyone), dict lookups (`blk.get(str(y))`) and this
file's own docstring quoting the defect. A checker whose first output is mostly
noise gets muted, and then it is worse than nothing — it looks like coverage.
The exclusions are specific and named so the next reader can judge each one.

⭐ ITS BLIND SPOT, STATED: this is a regex over source text. A site that renders a
period through an indirection it cannot see is invisible to it, and a site that
merely mentions `periodLabel` nearby is counted as wired. It is a floor that
turns an unbounded question into a finite list — not a proof.
"""
import os, re, sys

FRONTEND = os.environ.get(
    "AXIOM_FRONTEND",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "..", "optimization-anchor"))
SRC = os.path.join(FRONTEND, "src")
BACKEND_RENDERERS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "services/api/report_pdf.py"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "services/api/reporting.py"),
]

PERIOD_VARS = r'(?:y|yr|year|c\.year|d\.year|r\.year|p\.year|row\.year|pt\.year|e\.year)'
SITES = [
    (re.compile(r'\{\s*' + PERIOD_VARS + r'\s*\}'), "JSX prints a raw period"),
    (re.compile(r'\{\s*String\(\s*' + PERIOD_VARS + r'\s*\)\s*\}'), "JSX prints String(period)"),
    (re.compile(r'dataKey\s*=\s*"year"'), "chart axis/series keyed on raw year"),
    (re.compile(r'\.map\(\s*\(?\s*' + PERIOD_VARS + r'\s*\)?\s*=>\s*(?:String\()?\s*' + PERIOD_VARS),
     "a period list mapped straight to strings"),
    # ⭐ PROSE RENDERS A PERIOD TOO — BUT ONLY THE NARROW PATTERN IS USABLE.
    # A generic `${y}` inside a template literal was tried and abandoned: `y` is
    # the conventional name for an SVG y-coordinate, so it flagged arc paths
    # (`M 10 100 A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`) and CSS class
    # builders far more often than captions. What remains matches an
    # interpolation drawn from a PERIOD LIST, which is what a caption actually
    # does, plus a bare 5-digit YYYYQ appearing in prose. A caption reading "forecast years
    # (20231–20241)" is a render site the JSX-expression patterns cannot see —
    # the period is inside a template literal, not an interpolation slot of its
    # own. Added after a caption shipped with raw periods AND the wrong unit word.
    (re.compile(r'`[^`]*\$\{[^}]*(?:years|forecast_years|historical_years)\s*\[[^]]*\][^}]*\}'),
     "template literal interpolates a period from a list"),
    (re.compile(r'`[^`]*\b(?:19|20)\d{2}[1-4]\b[^`]*`'),
     "prose contains a literal YYYYQ period"),
    (re.compile(r'(?:forecast|historical)\s+years\b', re.I),
     "caption says 'years' — must follow the dataset frequency"),
]
CONSUMES = re.compile(r'periodLabels?\s*\(|year_label|period_labels|tickFormatter')
SKIP_DIRS = {"node_modules", "dist", ".output", "__pycache__", ".git"}
# ⭐ CALIBRATED BEFORE USE. The first run flagged SVG radar-chart geometry —
# `<line y1={cy} y2={y}>` — because `y` is a coordinate there, not a period. A
# checker that cries wolf is switched off within a week, so the exclusions are
# specific and named rather than a blanket lowering of sensitivity.
EXEMPT = re.compile(
    r'fiscal_year_end|copyright|birth'
    r'|<(?:line|text|circle|rect|path|polygon|g)\b'      # SVG geometry
    r'|\b(?:x|y|cx|cy|x1|y1|x2|y2|dx|dy|r)\s*=\s*\{'      # coordinate props
    r'|\bkey\s*=\s*\{'                                 # React keys are not renders
    r'|translate\(|rotate\(|scale\(|\bd\s*=\s*[`"]'      # SVG transforms and paths
    r'|\bx\(|\by\(|xOf\(|yOf\(|cxOf\(|cyOf\('           # coordinate helpers
    r'|\.toFixed\('                                          # coordinate rounding
    r'|textAnchor|dominantBaseline|transform=',
    re.I)


def scan_text(rel, text):
    hits = []
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        st = line.strip()
        if st.startswith(("//", "*", "/*", "#")) or EXEMPT.search(line):
            continue
        window = "\n".join(lines[max(0, i - 3):i + 2])
        for rx, what in SITES:
            if rx.search(line) and not CONSUMES.search(window):
                hits.append((rel, i, what, st[:78]))
                break
    return hits


def main():
    hits = []
    if os.path.isdir(SRC):
        for dp, dn, fn in os.walk(SRC):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fn:
                if f.endswith((".ts", ".tsx")):
                    p = os.path.join(dp, f)
                    try:
                        hits += scan_text(os.path.relpath(p, FRONTEND), open(p, encoding="utf-8").read())
                    except Exception:
                        pass
    else:
        print(f"  (frontend not found at {SRC} — skipped, NOT passed)")

    for p in BACKEND_RENDERERS:
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8").read()
        rel = os.path.relpath(p, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lines = text.split("\n")
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            window = "\n".join(lines[max(0, i - 3):i + 2])
            # ⭐ A LOOKUP IS NOT A RENDER. `blk.get(str(y))` keys a dict by the
            # period; it displays nothing. And prose inside a docstring that
            # QUOTES the old code is not the old code — the first run flagged
            # this checker's own explanation of the defect it checks for.
            if re.search(r'str\(\s*(?:y|year)\s*\)', line) \
                    and not re.search(r'\.get\(\s*str\(|\[\s*str\(', line) \
                    and not re.search(r'^\s*[#*]|`|⭐', line) \
                    and not CONSUMES.search(window) \
                    and "format_period" not in window and "period_headers" not in window:
                hits.append((rel, i, "board pack renders str(period)", line.strip()[:78]))

    by_file = {}
    for rel, i, what, src in hits:
        by_file.setdefault(rel, []).append((i, what, src))
    for rel in sorted(by_file):
        print(f"\n  {rel}  ({len(by_file[rel])})")
        for i, what, src in by_file[rel][:40]:
            print(f"    :{i:<5} {what}\n           {src}")

    print(f"\n  {'='*66}")
    print(f"  UNWIRED PERIOD RENDER SITES: {len(hits)}")
    if hits:
        print(f"  Each must consume the supplied label — `year_label` on statement rows,\n"
              f"  `period_labels` on list responses, via periodLabel() in TS or\n"
              f"  format_period()/period_headers() in the board pack.")
        return 1
    print("  ✓ every period render site consumes the supplied label")
    return 0


if __name__ == "__main__":
    sys.exit(main())
