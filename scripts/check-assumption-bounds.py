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
        print("✗ NO CORPUS — exiting non-zero rather than reporting every "
              "assumption in bounds.")
        return 2
    print(f"ASSUMPTION BOUNDS SWEEP — {len(ds)} datasets, source: {src}\n")

    per_field = collections.Counter()
    state_totals = collections.Counter()
    flagged = collections.defaultdict(list)
    for did in sorted(ds, key=lambda x: int(x) if str(x).isdigit() else 0):
        r = assumption_audit(ds[did])
        for name, f in r["fields"].items():
            state_totals[f["state"]] += 1
        for name in r["breaching"]:
            per_field[name] += 1
            flagged[name].append((did, r["fields"][name]))

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
            print(f"       dataset {did}: value {f['value']} — {f['direction']} "
                  f"{f['bound_crossed']}")
    print()
    print("  Reports only. No stored value is modified by this script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
