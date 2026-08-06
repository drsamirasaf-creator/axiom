#!/usr/bin/env python3
"""A committed report must not carry the exposure it describes.

⭐⭐ WHY THIS EXISTS, AND WHY IT IS A FILE RATHER THAN A HABIT. The
production-truth lane (7 Aug) grepped its own report for exposure terms before
committing, found two matches, judged both benign — **and recorded that judgement
only in chat.** A guard that lives in a chat message is not a guard: the next lane
cannot see it, cannot inherit the reasoning, and cannot tell a considered override
from an oversight.

⛔ THE TWO MATCHES ARE RECORDED BELOW AS HIT-AND-OVERRIDE. That is the whole
point — *an override nobody records is an allowlist that grows silently*, and this
pair had no record at all until now.

⭐ SCOPE: reports under `docs/reports/`, which are world-readable. This checks for
TERMS THAT DESCRIBE AN EXPOSURE, not for the exposure itself — a report may
legitimately say the word "public" and must not carry a customer figure. The
customer-figure rule is separate and older.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "docs", "reports")

# ⛔ Terms whose appearance in a committed report may mean the report is
# restating an exposure rather than describing one.
TERMS = re.compile(r"(public repo|publicly readable|world-readable|"
                   r"visibility\s*=|repository is public|repo is public)", re.I)

# ⭐⭐ THE HISTORICAL PAIR, RECORDED — T0 of the three-mode lane.
# The production-truth lane (7 Aug) grepped its own report before committing with
# a BROAD single-word pattern — `public|visibility|private|exposure` — got two
# matches, judged both benign, and recorded that judgement ONLY IN CHAT.
#
# ⛔ THE JUDGEMENTS WERE RIGHT AND THE INSTRUMENT WAS WRONG, and both facts are
# recorded because only one of them was obvious:
#
#   "public demo"  — describes WHY dataset 45 is anonymously readable (the
#                    showcase exemption in `require_report_read`). A statement
#                    about a product decision, not about the repository.
#   "exposure"     — the sentence saying a finding was deliberately WITHHELD and
#                    reported in chat instead. ⭐ Naming the withholding is the
#                    honest act; deleting the pointer would leave a reader unable
#                    to tell the report is incomplete by design.
#
# ⭐ AND THE BROAD PATTERN CANNOT BE THE GUARD. `public` and `private` are core
# DOMAIN vocabulary here — public companies, private companies, "no live dataset
# is public" (value-per-share-2026-08-03.md:174, a false positive this measured).
# A recogniser that floods on domain language gets muted, so the shipped pattern
# is phrase-scoped to REPOSITORY visibility and does not match either of the two.
#
# ⛔ They are therefore recorded as HISTORICAL, not as live overrides: an
# override list must measure the present, and neither is a present hit.
HISTORICAL = {
    ("production-truth-2026-08-07.md", "public demo"):
        "matched only by the broad 7 Aug grep; the shipped pattern does not "
        "flag it, and the sentence describes the showcase exemption",
    ("production-truth-2026-08-07.md", "exposure"):
        "matched only by the broad 7 Aug grep; it is the pointer naming a "
        "deliberately withheld finding, which must stay",
}
OVERRIDES = {}


def main():
    if not os.path.isdir(REPORTS):
        print("  · docs/reports/ is absent — nothing scanned")
        return 0
    files = sorted(f for f in os.listdir(REPORTS) if f.endswith(".md"))
    print(f"  {len(files)} committed report(s) scanned")
    # ⭐ §III.4 — an empty corpus fails.
    if len(files) < 20:
        print(f"  ✗ only {len(files)} reports found — the scan is wrong")
        return 1

    fails, hits = [], []
    for f in files:
        s = open(os.path.join(REPORTS, f), encoding="utf-8").read()
        for m in TERMS.finditer(s):
            line = s[:m.start()].count("\n") + 1
            hits.append((f, m.group(0).lower(), line))

    # the two recorded overrides, matched loosely on the term they carry
    known = {(f, t) for (f, t) in OVERRIDES}
    matched = set()
    for f, term, line in hits:
        key = next(((kf, kt) for (kf, kt) in known
                    if kf == f and (kt in term or term in kt)), None)
        if key:
            matched.add(key)
            continue
        fails.append(f"{f}:{line} — {term!r} is not a recorded override. Read it: "
                     f"either it restates an exposure and must go, or it is "
                     f"deliberate and belongs in OVERRIDES with its reason.")

    print(f"  {len(hits)} term match(es) · {len(OVERRIDES)} live override(s), "
          f"{len(matched)} hit · {len(HISTORICAL)} historical (recorded, not live)")
    for (f_, t_), why in sorted(HISTORICAL.items()):
        print(f"    · HISTORICAL {f_} :: {t_!r} — {why}")
    for (f, t), why in sorted(OVERRIDES.items()):
        state = "HIT" if (f, t) in matched else "NOT HIT"
        print(f"    · {f} :: {t!r} — {state}")
        print(f"        {why}")

    # ⭐⭐ THE OPPOSITE RATCHET. An override that no longer matches anything is an
    # allowlist entry outliving its reason — the same failure the stroke guard
    # was corrected for, applied here from the start rather than after.
    for key in sorted(known - matched):
        fails.append(f"{key[0]} :: {key[1]!r} is a recorded override but no "
                     f"longer matches — remove it, so the list measures the "
                     f"present.")

    # ── controls, in memory ───────────────────────────────────────────────
    assert TERMS.search("the repository is public"), \
        "control: the term recogniser missed a real exposure phrase"
    assert not TERMS.search("a public demo of the product"), \
        "control: 'public demo' is matched by the bare word and would flood"
    assert TERMS.search("visibility=public"), \
        "control: the recogniser missed an API-shaped disclosure"
    assert not TERMS.search("the customer figure was withheld"), \
        "control: an unrelated sentence matched"
    print("  ✓ controls: an exposure phrase is seen, a benign 'public demo' is "
          "not, an API-shaped disclosure is seen, an unrelated sentence is not")

    for f in fails:
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(fails)} unrecorded exposure term(s).")
        return 1
    print("\n  ✓ every exposure term in a committed report is a recorded "
          "override with its reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
