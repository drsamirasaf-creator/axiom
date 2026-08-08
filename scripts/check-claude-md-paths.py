#!/usr/bin/env python3
"""Every path CLAUDE.md points at must exist.

⛔⭐⭐ WHY THIS AND NOT MORE. CLAUDE.md is the first thing a lane reads, so it
will be CITED INSTEAD OF RE-MEASURED — and a recorded measurement is not a
control (§III.24). The defence is to keep it POINTERS, not copies, and then
assert the pointers.

⭐ WHAT IS CHECKABLE HERE, AND WHAT IS NOT:

    checkable   the paths — the ledger, ONBOARDING, the specs, the scripts and
                hooks it names. If one is renamed or deleted, this fails.
    NOT         the prose. "The frontend ships only when the founder publishes"
                is a fact about a system outside both repos, and no guard in
                either can see it. It is written as a rule rather than a
                measurement for exactly that reason.

⛔ SO THIS DOES NOT MAKE CLAUDE.md TRUE. It makes it impossible for the file to
point at something that is no longer there — which is the failure mode a file of
pointers actually has.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SIBLING = os.path.join(os.path.dirname(REPO), "optimization-anchor")

# Anything that looks like a repo path: a/b or a/b.ext, optionally ../-prefixed
# and optionally dot-leading (.github/, .githooks/).
# ⛔ AN EARLIER VERSION EXCLUDED BACKTICK-PRECEDED MATCHES, which are exactly the
# paths worth checking — it found 2 of 9 and reported OK. It also dropped the
# leading dot and then failed on `githooks/pre-push`, a path that does not exist
# because the regex invented it. Both were the guard measuring itself.
PATH_RE = re.compile(r"((?:\.\./)?\.?[\w][\w./-]*/[\w][\w.-]*)")
SKIP = ("http", "axiomdynamics", "origin/main", "refs/heads")


def paths_in(md, base):
    out = []
    for line in open(md, encoding="utf-8"):
        for m in PATH_RE.finditer(line):
            p = m.group(1).rstrip(".,;:")
            if any(s in p for s in SKIP) or p.endswith("/"):
                continue
            out.append((p, os.path.normpath(os.path.join(base, p))))
    return out


def main() -> int:
    fails, checked = [], 0
    for md, base, label in ((os.path.join(REPO, "CLAUDE.md"), REPO, "axiom"),
                            (os.path.join(SIBLING, "CLAUDE.md"), SIBLING,
                             "optimization-anchor")):
        if not os.path.exists(md):
            if label == "axiom":
                fails.append(f"⛔ {label}: CLAUDE.md is missing")
            else:
                print(f"  · {label}: no checkout here — its CLAUDE.md not checked")
            continue
        seen = set()
        for rel, full in paths_in(md, base):
            if rel in seen:
                continue
            seen.add(rel)
            checked += 1
            if not os.path.exists(full):
                fails.append(f"⛔ {label}/CLAUDE.md points at {rel} — it does not exist")
        print(f"  {label}: {len(seen)} distinct path(s) referenced")

    # ⭐ §III.4 — a zero-path scan is a broken regex, not a clean file.
    if checked == 0:
        print("\n⛔ ZERO paths extracted. The scan is broken, not the file.")
        return 2
    print(f"\npaths checked: {checked}")
    if fails:
        print()
        for f in fails:
            print(f"  {f}")
        print(f"\nFAILED — {len(fails)}")
        return 1
    print("OK — every path CLAUDE.md points at exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
