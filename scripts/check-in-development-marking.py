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

# ⭐⭐ WHAT WOULD PROVE THE CAPABILITY EXISTS — REWRITTEN 5 Aug, AND THE OLD
# FORM IS THE FINDING OF THIS LANE.
#
# It read:
#     r"segment_profitability|product_line_profitability|"
#     r"/companies/\{company_id\}/(segment|product-line)-"
# and its comment explained the choice: "Deliberately NOT the words 'revenue' or
# 'profitability' — both appear all over a finance product and would make this
# guard fire on prose."
#
# ⛔⭐ THE PRECAUTION AGAINST A FALSE POSITIVE PRODUCED A PERMANENT FALSE
# NEGATIVE. Avoiding "profitability" meant avoiding every name the capability
# would actually be given. Measured 5 Aug: all four alternatives match ZERO files
# in services/api. The capability shipped as `profitability_surface`,
# `optimise_mix`, `contribution`, `avoidability` and `dimensional_analytics`, and
# the guard stayed green through T1, T2, the seed, T3, T4.1–T4.5, T5.1 and the
# consolidation — the exact condition it was written to catch.
#
# ⭐ THE SHAPES BELOW ARE DEFINITION SITES, NOT WORDS. `def profitability_surface`
# cannot occur in prose; the bare word can. That keeps the original precaution
# while naming things that exist.
EXISTENCE_SIGNALS = (
    (os.path.join(ROOT, "services", "api"), re.compile(
        r"def profitability_surface\b|def optimise_mix\b|"
        r"def contribution_per_constrained_unit\b|def avoidability\b|"
        r"def _mix_shift_series\b")),
)

# ⭐⭐ THE CONTROL IS DRAWN FROM THE REPOSITORY, NEVER INVENTED. The old control
# asserted the recogniser matched the string
#     "def segment_profitability(db, cid):"
# which the guard had written itself. The regex matched its own example, and that
# is ALL it ever proved — a known positive drawn from the same source as the
# pattern tests nothing about the world. This one reads a real line out of
# router.py, so the control fails if the codebase's naming moves away from it.
CONTROL_SOURCE = os.path.join(ROOT, "services", "api", "modules", "financials",
                              "router.py")


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
    # ⭐⭐ A REAL SIGNATURE, READ FROM DISK. If nothing in router.py matches, the
    # recogniser has drifted from the codebase and every verdict below is void —
    # which is precisely the state this guard sat in for eight lanes.
    try:
        real = open(CONTROL_SOURCE, encoding="utf-8").read()
    except OSError:
        bad.append(f"control source unreadable: {CONTROL_SOURCE}")
        real = ""
    hit = pat.search(real)
    if not hit:
        bad.append("the existence recogniser matches NOTHING in router.py — it "
                   "has drifted from the codebase's own naming, which is how it "
                   "stayed green through the whole Profitability build")
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
    print("  ✓ control: the existence recogniser fires on a signature READ FROM "
          "router.py and stays silent on prose")

    # ⭐ THE BACKEND HALF IS THIS REPOSITORY'S AND RUNS UNCONDITIONALLY. Whether
    # the capability exists is answerable here, with or without a frontend
    # checkout, so it is measured BEFORE the checkout is consulted.
    exists, evidence = capability_exists()

    if frontend_missing():
        # ⭐⭐ EXIT CODE FIXED 4 Aug (§8x) — the third application of the shape
        # ruled at 94a7ce0 and eb89ee8. This returned 2, which is a FAILURE ON A
        # CONDITION IT DOES NOT GUARD: the gate guards whether the marking and
        # the capability agree, not whether a SIBLING REPOSITORY happens to be
        # checked out beside this one. CI has no `optimization-anchor` checkout,
        # so wiring it while it returned 2 would have made CI permanently red.
        #
        # ⛔ AND IT IS NOT WEAKENED TO A SKIP. The half that CAN run still runs
        # and is reported below; the half that cannot is NAMED, and the output
        # states plainly that it asserts nothing about the marking. A silent
        # exit 0 here would be green over zero files — the other defect.
        print(f"  ⚠ MARKING HALF NOT RUN — {MARKED_FILE} not found under {FE}.")
        print(f"  capability built: {exists}"
              f"{'  (' + evidence + ')' if exists else ''}")
        print("  This run asserts NOTHING about whether the in-development "
              "marking is present. It is not a green: set AXIOM_FRONTEND to a "
              "checkout to make it one.")
        if exists:
            # ⭐ ONE THING IS STILL DECIDABLE WITHOUT THE FRONTEND. If the
            # capability has SHIPPED, CORE §4z.1's stated exception should be
            # retired whatever the marking says — and that is this repository's
            # fact, so it is still enforced.
            print("\n  ✗ THE CAPABILITY IS BUILT, so §4z.1's in-development "
                  "exception should be RETIRED.\n    That is decidable here "
                  "and does not need the frontend.")
            return 1
        return 0

    src = open(os.path.join(FE, MARKED_FILE), encoding="utf-8").read()
    marked = MARKER_ATTR in src and all(w in src for w in MARKER_WORDS)

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
