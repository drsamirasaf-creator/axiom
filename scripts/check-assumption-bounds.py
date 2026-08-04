#!/usr/bin/env python3
"""Sweep EVERY STORED DATASET for out-of-range assumptions. Reports, never repairs.

⭐ THE SCOPE IS THE SUBSTANCE. The eight affected datasets were written on 16 July
and will never re-ingest. A check that only fires at upload leaves every existing
dataset unguarded — the same reasoning that made `balance_audit` run on every
stored period rather than historicals only.

⭐ THREE STATES, COUNTED SEPARATELY. `absent` is not `in_bounds`. A field that
could not be checked must not be indistinguishable from one that passed.

Reads the durable corpus cache (scripts/pull-corpus.py) or the live database.
Source the lane env once — `source scripts/lane-env.sh` — rather than invoking
`railway run` per query; the CLI degrades under repetition.

    python3 scripts/check-assumption-bounds.py
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.api.modules.financials.engines import (  # noqa: E402
    ASSUMPTION_BOUNDS, assumption_audit,
)

CACHE = os.environ.get("DS_CACHE") or os.path.join(
    os.path.expanduser("~"), ".axiom-cache", "ds.json")

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE ADJUDICATED BREACHES — §7u.2, 4 Aug.
#
# ⛔ NOT CORRECTED AND NOT DELETED, and both refusals are the ruling.
# Correcting the stored values would leave 27 valuation runs contradicting
# their own inputs; deleting the datasets would destroy the only surviving
# record of the incident, and `original_filename` is null on all eight so the
# source workbook is already gone. An allowlist is the only option that touches
# no stored value.
#
# WHAT THEY ARE: eight datasets written on 16 July on the operator's own tenant,
# carrying one byte-identical assumption block whose `size_premium` is 0.2 —
# exactly `dlom`'s value in the same block, against a corpus whose next-highest
# observation is 0.03. All eight are INACTIVE with `enterprise_id IS NULL`, so
# every customer path (which filters on `enterprise_id`) excludes them: zero
# packs, zero report issues, zero edits, zero stale marks.
#
# ⭐ KEYED BY (dataset id, field) AND MATCHED ON THE VALUE TOO — never
# "ignore this dataset". A blanket dataset entry would silently absorb a
# DIFFERENT field going out of bounds later, which is the shape that turns an
# allowlist into a blind spot. If the stored value changes, the entry stops
# matching and the breach is reported as new.
# ═══════════════════════════════════════════════════════════════════════════
_ADJUDICATION = ("§7u.2 4 Aug — historical artefact of a 16 Jul test run on the "
                 "operator's own tenant; inactive, enterprise_id NULL, no "
                 "customer path. Not corrected (27 runs would contradict their "
                 "inputs) and not deleted (loses the record).")
ADJUDICATED = {(did, "size_premium"): (0.2, _ADJUDICATION)
               for did in range(8, 16)}


def is_adjudicated(did, field, f):
    """True only if this exact dataset, field AND stored value were adjudicated.

    ⭐ THE VALUE IS PART OF THE KEY. An allowlist that forgives a field rather
    than a finding grants standing permission for that field to be wrong.
    """
    try:
        key = (int(did), field)
    except (TypeError, ValueError):
        return False
    entry = ADJUDICATED.get(key)
    return entry is not None and f.get("value") == entry[0]


def load():
    """Live DB if the lane env is sourced, else the durable cache.

    ⭐ RETURNS None RATHER THAN {} WHEN NOTHING IS AVAILABLE, so a caller cannot
    sweep zero datasets and report that every assumption is in bounds.
    """
    url = os.environ.get("DATABASE_PUBLIC_URL")
    if url:
        try:
            import psycopg
            cn = psycopg.connect(url.replace("postgresql+psycopg://", "postgresql://"))
            cur = cn.cursor()
            cur.execute("select id, data from financial_datasets order by id")
            out = {}
            for did, d in cur.fetchall():
                out[str(did)] = d if isinstance(d, dict) else json.loads(d)
            cn.close()
            return out, "live database"
        except Exception as e:
            print(f"  ! live read failed ({type(e).__name__}); falling back to cache")
    if os.path.exists(CACHE):
        try:
            d = json.load(open(CACHE, encoding="utf-8"))
            return (d or None), f"cache {CACHE}"
        except Exception:
            return None, "cache unreadable"
    return None, "no source"


def main():
    ds, src = load()
    if not ds:
        # ⭐⭐ IT REPORTS WHAT IT DID NOT CHECK AND EXITS 0 — ruled 4 Aug, the
        # same shape as `check-period-labels-published.py` at 94a7ce0.
        #
        # It returned 2, which is a FAILURE ON A CONDITION IT DOES NOT GUARD:
        # this gate guards assumption bounds, not whether a corpus is reachable.
        # The corpus lives in the live database or in a cache at
        # ~/.axiom-cache/ds.json — untracked and MACHINE-LOCAL — so CI has
        # neither and the gate was structurally red there while passing here.
        # Every lane that reported "29/29 gates green" was true on one machine.
        #
        # ⭐⭐ AND IT MUST NOT CLAIM A PASS IT DID NOT EARN. The old comment on
        # `load()` is still right — returning None rather than {} is what stops
        # a sweep of zero datasets reporting every assumption in bounds. The
        # answer is not to fail; it is to SAY WHICH HALF RAN, in the output a
        # reader sees, exactly as the period-labels gate now does.
        print("  ⚠ NOT RUN — no corpus reachable "
              f"(no DATABASE_PUBLIC_URL, no cache at {CACHE}).")
        print("  This run swept 0 datasets and asserts NOTHING about assumption "
              "bounds. It is not a pass: source scripts/lane-env.sh, or run "
              "scripts/pull-corpus.py to write the cache, to make it one.")
        return 0
    print(f"ASSUMPTION BOUNDS SWEEP — {len(ds)} datasets, source: {src}\n")

    per_field = collections.Counter()
    state_totals = collections.Counter()
    flagged = collections.defaultdict(list)
    adjudicated_hits, new_hits = [], []
    for did in sorted(ds, key=lambda x: int(x) if str(x).isdigit() else 0):
        r = assumption_audit(ds[did])
        for name, f in r["fields"].items():
            state_totals[f["state"]] += 1
        for name in r["breaching"]:
            per_field[name] += 1
            flagged[name].append((did, r["fields"][name]))
            hit = (did, name, r["fields"][name])
            (adjudicated_hits if is_adjudicated(did, name, r["fields"][name])
             else new_hits).append(hit)

    total = sum(state_totals.values())
    print("  THREE STATES, counted separately")
    print(f"    in_bounds       {state_totals['in_bounds']:>5}")
    print(f"    out_of_bounds   {state_totals['out_of_bounds']:>5}")
    print(f"    absent          {state_totals['absent']:>5}   "
          f"(skipped and named — NOT in_bounds)")
    print(f"    ─────────────────────")
    print(f"    field-values    {total:>5}   over {len(ASSUMPTION_BOUNDS)} fields "
          f"x {len(ds)} datasets")
    checked = state_totals['in_bounds'] + state_totals['out_of_bounds']
    print(f"    checked         {checked:>5}\n")

    if not per_field:
        print("  no field is out of bounds")
    for name, n in per_field.most_common():
        lo, hi = ASSUMPTION_BOUNDS[name]
        print(f"  ⭐ {name}: {n} dataset(s) out of bounds  "
              f"[{lo}, {'unbounded' if hi is None else hi}]")
        for did, f in flagged[name][:10]:
            tag = "  [ADJUDICATED §7u.2]" if is_adjudicated(did, name, f) else ""
            print(f"       dataset {did}: value {f['value']} — {f['direction']} "
                  f"{f['bound_crossed']}{tag}")

    # ⭐⭐ THE ALLOWLIST IS REPORTED, NOT APPLIED SILENTLY. An entry that stops
    # matching — a value edited, a dataset re-activated — drops OUT of
    # `adjudicated` and INTO `new`, where it is visible. A blanket
    # "ignore datasets 8-15" would have swallowed that.
    print(f"\n  ADJUDICATED (§7u.2, 4 Aug): {len(adjudicated_hits)} of "
          f"{len(ADJUDICATED)} allowlisted entries matched")
    stale = [k for k in ADJUDICATED
             if k not in {(int(d), n) for d, n, _f in adjudicated_hits}]
    if stale:
        print(f"     ⭐ {len(stale)} allowlisted entr(ies) NO LONGER BREACH: "
              f"{sorted(stale)}")
        print("       The allowlist is now broader than the corpus. Retire the "
              "stale entries rather than leaving standing permission behind.")
    print(f"  NEW, UNADJUDICATED BREACHES: {len(new_hits)}")
    for did, name, f in new_hits:
        print(f"     ⭐ dataset {did}: {name} = {f['value']} — not covered by "
              f"the §7u.2 allowlist")
    if not new_hits:
        print("     none — every breach in this corpus has been adjudicated")

    print()
    print("  Reports only. No stored value is modified by this script.")
    # ⛔ STILL RETURNS 0 ON A BREACH, AND THAT IS UNCHANGED BY THE ALLOWLIST.
    # §7u.2 ruled the allowlist; it did NOT rule that this becomes a gate. With
    # the 8 adjudicated the corpus is clean, so flipping `new_hits` to a
    # non-zero exit is now a one-line change — but it is a RULING, and it is
    # worth nothing until CI can reach a corpus at all (§8w). A gate that can
    # only fail on one laptop is the defect eb89ee8 removed, pointed the other
    # way.
    return 0


if __name__ == "__main__":
    sys.exit(main())
