#!/usr/bin/env python3
"""Gate: period formatting must not be reimplemented in TypeScript.

⭐ WRITTEN WHILE ZERO INSTANCES EXIST, WHICH IS THE ONLY CHEAP MOMENT.

The frontend currently has NO period formatter — every surface prints whatever
the backend hands it. That is the state this gate preserves. The alternative is
already documented in this repo's history: money formatting had no single owner,
and six independent implementations grew, two of which silently disagreed on a
board pack.

The gate is a regex over the shapes someone reaches for when they want "2023Q1"
in TypeScript. It is not a proof — a determined reimplementation can evade it —
but it does not need to be. It needs to fire on the FIRST person who tries,
while the answer "the API already sends year_label / period_labels" is still one
sentence long.

WHAT TO DO IF THIS FIRES: use the label the backend supplies. Statement rows
carry `year_label`; list-shaped responses carry a `period_labels` map keyed by
the raw period. If a surface needs a label the API does not send, add it in
`services/api/modules/financials/periods.py` — the one definition — and send it.
"""
import re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.environ.get(
    "AXIOM_FRONTEND", os.path.join(os.path.dirname(ROOT), "optimization-anchor"))
SRC = os.path.join(FRONTEND, "src")

PATTERNS = [
    (re.compile(r'`\$\{[^}]*\}\s*Q\s*\$\{'), 'a template literal building "<year>Q<quarter>"'),
    (re.compile(r'["\'`]Q["\'`]\s*\+'), 'string concatenation onto a "Q"'),
    (re.compile(r'%\s*10\b.*\bQ\b|\bQ\b.*%\s*10\b'), 'decoding YYYYQ with % 10'),
    (re.compile(r'Math\.floor\s*\(\s*\w+\s*/\s*10\s*\)'), 'decoding YYYYQ with Math.floor(x / 10)'),
    (re.compile(r'\btoString\(\)\.slice\(\s*-?\s*1\s*\)'), 'slicing the last digit off a period'),
]
SKIP_DIRS = {"node_modules", "dist", ".output", "__pycache__", ".git"}


def main():
    if not os.path.isdir(SRC):
        print(f"  (frontend not found at {SRC} — gate skipped, not passed)")
        return 0
    hits = []
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith((".ts", ".tsx")):
                continue
            path = os.path.join(dirpath, fn)
            try:
                text = open(path, encoding="utf-8").read()
            except Exception:
                continue
            for i, line in enumerate(text.split("\n"), 1):
                if line.lstrip().startswith(("//", "*", "/*")):
                    continue
                for rx, what in PATTERNS:
                    if rx.search(line):
                        hits.append((os.path.relpath(path, FRONTEND), i, what, line.strip()[:90]))
    for rel, i, what, line in hits:
        print(f"  {rel}:{i}  {what}\n      {line}")
    if hits:
        print(f"\nFAIL — {len(hits)} site(s) formatting a period in TypeScript.\n"
              f"The backend already sends the label: `year_label` on statement rows, "
              f"`period_labels` on list responses. One definition lives in "
              f"services/api/modules/financials/periods.py.")
        return 1
    print("✓ no-ts-period-format: no period formatting in TypeScript "
          "(regex gate — see the module docstring for its limits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
