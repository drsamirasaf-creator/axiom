#!/usr/bin/env python3
"""A capability marked IN DEVELOPMENT must still be absent from the codebase.

⭐⭐ THE SAME RULE AS THE COMPARISON MATRIX'S GREENS, RUN IN THE OTHER
DIRECTION. `check-comparison-matrix.py` refuses a green whose capability does
not exist. This refuses the REMOVAL of an in-development marking while the
capability still does not exist — because the moment the marking goes, the block
reads as shipped, and a claim of existence must be backed by existence.

⭐ WHY THIS EXISTS AT ALL. "Segment and Product Line Revenue and Profitability
Analysis" is on a prospect-facing page and is NOT BUILT. It is admissible only
because it does not assert present existence — a stated, bounded exception to the
admissibility rule (CORE §4z.1). The exception survives exactly as long as the
marking does, so the marking is guarded rather than trusted.

⭐⭐ AND IT FAILS IN BOTH DIRECTIONS, which is the point:
  · marking removed while the capability is absent  -> the page now lies
  · marking present after the capability SHIPS      -> the page understates,
    and the exception should be retired rather than left standing

CONTROLS ARE IN MEMORY. Nothing is written to disk — the planted-control leak
has happened four times.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FE = os.environ.get("AXIOM_FRONTEND",
                    "/Users/samirasaf/dev/optimization-anchor")

MARKED_FILE = "src/components/FeaturesAndBenefits.tsx"
MARKER_ATTR = 'data-in-development="revenue-profitability"'
# The words a prospect reads. Losing these is losing the disclosure even if the
# attribute survives, so both are required.
MARKER_WORDS = ("In development", "not available today")

# ⭐ WHAT WOULD PROVE THE CAPABILITY EXISTS. Deliberately NOT the words
# "revenue" or "profitability" — both appear all over a finance product and
# would make this guard fire on prose. These are the shapes the capability would
# have to take: an endpoint, a module, or a registry ratio.
EXISTENCE_SIGNALS = (
    (os.path.join(ROOT, "services", "api"), re.compile(
        r"segment_profitability|product_line_profitability|"
        r"/companies/\{company_id\}/(segment|product-line)-")),
)


def frontend_missing():
    return not os.path.exists(os.path.join(FE, MARKED_FILE))


def capability_exists():
    """-> (bool, evidence). Searched by SHAPE, never by the word 'revenue'."""
    for base, pat in EXISTENCE_SIGNALS:
        for d, dirs, names in os.walk(base):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for n in names:
                if not n.endswith(".py"):
                    continue
                p = os.path.join(d, n)
                try:
                    m = pat.search(open(p, encoding="utf-8").read())
                except OSError:
                    continue
                if m:
                    return True, f"{os.path.relpath(p, ROOT)} :: {m.group(0)}"
    return False, ""


def control():
    """⭐ KNOWN POSITIVE, in memory. The recogniser must FIRE on a synthetic
    capability and STAY SILENT on ordinary finance prose — a matcher that hit on
    the word 'revenue' would fail every file in this product."""
    bad = []
    pat = EXISTENCE_SIGNALS[0][1]
    if not pat.search("def segment_profitability(db, cid):"):
        bad.append("the existence recogniser does not fire on a real signature")
    if pat.search('"total revenue and profitability of the segment"'):
        bad.append("the existence recogniser fires on ordinary prose — it would "
                   "report the capability as built on any finance page")
    if MARKER_WORDS[0].lower() not in "in development — not available today":
        bad.append("marker words drifted from the rendered text")
    return bad


def main():
    bad = control()
    if bad:
        print("  ✗ CONTROL FAILED — the verdict below is unreadable:")
        for b in bad:
            print(f"      {b}")
        return 2
    print("  ✓ control: the existence recogniser fires on a real signature and "
          "stays silent on prose")

    if frontend_missing():
        # ⭐ NOT A PASS. A missing checkout is an unmeasured claim, and this
        # guard exists precisely so the claim is never unmeasured.
        print(f"  ✗ {MARKED_FILE} not found under {FE} — the marking cannot be "
              f"verified, so this is a refusal, not a green.")
        return 2

    src = open(os.path.join(FE, MARKED_FILE), encoding="utf-8").read()
    marked = MARKER_ATTR in src and all(w in src for w in MARKER_WORDS)
    exists, evidence = capability_exists()

    print(f"  marking present : {marked}")
    print(f"  capability built: {exists}{'  (' + evidence + ')' if exists else ''}")

    if not marked and not exists:
        print("\n  ✗ THE IN-DEVELOPMENT MARKING IS GONE AND THE CAPABILITY IS "
              "NOT BUILT.\n    The block now reads as shipped capability on a "
              "prospect-facing page.\n    A claim of existence must be backed "
              "by existence — restore the\n    marking, or build the thing.")
        return 1
    if marked and exists:
        print("\n  ✗ THE CAPABILITY SHIPPED AND IS STILL MARKED IN DEVELOPMENT.\n"
              "    The page now understates the product, and CORE §4z.1's "
              "stated\n    exception should be RETIRED rather than left "
              "standing.")
        return 1
    print("\n  ✓ the marking and the codebase agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
