#!/usr/bin/env python3
"""No two CORE sections may share an anchor.

⭐⭐ FOUND BY THE 7 Aug SYNC, BY DERIVATION. Six anchors name two different
rulings each:

    §4v · §4v.1 · §4v.2   the comparison matrix (1 Aug) AND the strategy map (5–7 Aug)
    §4z.1                 the viewer's tier mark AND "What is AXIOM?"
    §8m · §8n · §8o       T4.2/T4.3/T4.4 (4 Aug) AND optimal range / frequency views (6 Aug)
    §8p                   an existing entry AND the frequency-view 500 (7 Aug)

⛔ **A DISPATCH SAYING "read §8n" IS AMBIGUOUS**, and this is §7j.6's
name-collision class applied to the ledger's own addressing — the document that
records the law about two objects sharing one noun.

⭐ THE MECHANISM WAS INCREMENTING WITHOUT CHECKING. `§8a`–`§8z` were exhausted by
the T-series, and later lanes appended `§8m` again rather than measuring which
letters were free. `§8A`/`§8B` already showed the uppercase escape; nobody looked.

⛔ EXISTING COLLISIONS ARE RECORDED, NOT RENUMBERED — renumbering would require
editing committed reports, and a report is a record of what was said at the time.
`BASELINE` freezes them so the count can only go DOWN.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "docs", "ledger", "AXIOM_LEDGER_CORE.md")

# ⭐ A HEADING is a top-level `# ... §anchor ·`. The anchor is everything from
# the section sign to the separator, so `§8m.1` and `§8m` are distinct.
HEADING = re.compile(r"^#\s+[⭐⛔\s]*§([0-9A-Za-z.]+)\s*[·•]", re.M)

# ⛔ THE COLLISIONS THAT ALREADY EXIST, FROZEN. A downward-only ratchet: a new
# duplicate fails, and removing one from this list is the only way the number
# falls. Each is a real pair, measured.
BASELINE = {
    "4v": "the comparison matrix (1 Aug) and the departmental strategy map (5 Aug)",
    "4v.1": "matrix corrections (1 Aug) and the strategy map's four rulings (5 Aug)",
    "4v.2": "the matrix on a phone (1 Aug) and the strategy map built (6 Aug)",
    "4z.1": "the viewer's tier mark and 'What is AXIOM?' (2 Aug)",
    "8m": "T4.2 managerial analytics (4 Aug) and the optimal range (6 Aug)",
    "8n": "T4.3 Meridian seeded (4 Aug) and frequency views scoped (6 Aug)",
    "8o": "T4.4 direct-or-shared (4 Aug) and frequency views built (6 Aug)",
    "8p": "an existing entry and the frequency-view 500 (7 Aug)",
}


def main():
    src = open(CORE, encoding="utf-8").read()
    seen = {}
    for m in HEADING.finditer(src):
        a = m.group(1)
        seen.setdefault(a, []).append(src[:m.start()].count("\n") + 1)

    n = sum(len(v) for v in seen.values())
    dupes = {a: ls for a, ls in seen.items() if len(ls) > 1}
    print(f"  {n} section heading(s) · {len(seen)} distinct anchor(s) · "
          f"{len(dupes)} duplicated")
    # ⭐ §III.4 — an empty corpus fails. MEASURED at 99 top-level headings on
    # 7 Aug; the floor is set below that with room to grow rather than guessed —
    # a first version used 100 and failed on the true count, which is the shape
    # this rule exists to prevent in the other direction.
    if n < 80:
        print(f"  ✗ only {n} headings parsed — the recogniser has drifted")
        return 1

    fails = []
    for a, lines in sorted(dupes.items()):
        if a in BASELINE:
            print(f"    · §{a} at {lines} — known: {BASELINE[a]}")
            continue
        fails.append(f"§{a} names {len(lines)} different sections (lines {lines}). "
                     f"A dispatch citing it is ambiguous — take a free anchor.")
    # ⭐⭐ THE RATCHET RUNS BOTH WAYS. A baseline entry that stops colliding must
    # leave the list, or the list becomes a claim about a fixed past rather than
    # a measurement of the present — the shape §III.4 keeps catching.
    for a in sorted(BASELINE):
        if a not in dupes:
            fails.append(f"§{a} is in BASELINE but no longer duplicated — remove "
                         f"it, so the count measures the present")

    # ── controls, in memory ───────────────────────────────────────────────
    assert HEADING.search("# ⭐⭐ §8m · THE OPTIMAL RANGE"), \
        "control: the heading recogniser missed a real heading"
    assert HEADING.search("# §4v.2 · THE DEPARTMENTAL STRATEGY MAP").group(1) \
        == "4v.2", "control: the anchor was truncated"
    assert not HEADING.search("see §8m for the range"), \
        "control: a CITATION was read as a heading"
    assert not HEADING.search("## ⭐ §8m · A SUBSECTION"), \
        "control: a second-level heading was counted as a section"
    probe = {"8m": [1, 2]}
    assert [a for a in probe if len(probe[a]) > 1] == ["8m"], \
        "control: the duplicate detector missed a duplicate"
    print("  ✓ controls: a heading is seen, a citation is not, a subsection is "
          "not, and a duplicate is detected")

    for f in fails:
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(fails)} anchor problem(s).")
        return 1
    print(f"\n  ✓ no NEW duplicate anchors; {len(BASELINE)} known collisions "
          f"held at their recorded count")
    return 0


if __name__ == "__main__":
    sys.exit(main())
