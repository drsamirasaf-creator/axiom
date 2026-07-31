#!/usr/bin/env python3
"""No company's stored ownership may contradict its active dataset.

⭐⭐ WHY THIS GUARD EXISTS. Ownership selects the cost-of-equity branch AND
decides whether a DLOM applies. Three live datasets carried `dlom = 0.2` while
their enterprise row said `public` — a discount for NON-MARKETABILITY on a company
the record called publicly traded, and one of them was the ACTIVE dataset of the
DEMO company. ⭐ The engine was internally consistent, which is exactly why
nothing broke and nothing noticed.

⭐⭐ IT CARRIES A KNOWN POSITIVE. A guard that has never fired has not been tested,
and this class went unseen for as long as it existed. The control plants a
disagreement in memory and requires the checker to flag it.

Structural check by default (no database). With DATABASE_URL / DATABASE_PUBLIC_URL
and `--against-db`, it also checks every live company.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── ⭐⭐ THE KNOWN POSITIVE ────────────────────────────────────────────────────
class _Ent:
    def __init__(self, i, own):
        self.id, self.ownership = i, own


class _DS:
    def __init__(self, i, own):
        self.id = i
        self.data = {"company": {"ownership": own}} if own else {"company": {}}


class _FakeDB:
    """Minimal stand-in: enough for resolve()/disagreements() and nothing more."""
    def __init__(self, pairs):
        self._ents = [_Ent(i, stored) for i, (stored, _p) in enumerate(pairs, 1)]
        self._ds = {i: (_DS(100 + i, p) if p is not _MISSING else None)
                    for i, (_s, p) in enumerate(pairs, 1)}

    def query(self, _model):
        return self

    def all(self):
        return self._ents

    def get(self, _model, i):
        return next((e for e in self._ents if e.id == i), None)


_MISSING = object()


def _control():
    import services.api.ownership as O

    fails = []
    cases = [
        # (stored, payload)            expectation
        (("public", "private"), True,  "row says public, payload says private"),
        (("private", "private"), False, "agreement"),
        (("private", _MISSING), True,  "row with no dataset is REPORTED (as pending)"),
        ((None, "private"), True,      "row absent while the payload states one"),
        ((None, _MISSING), False,      "nothing stored, nothing derivable"),
    ]
    for (stored, payload), should_flag, label in cases:
        db = _FakeDB([(stored, payload)])
        orig = O._active_company_dataset if hasattr(O, "_active_company_dataset") else None
        import services.api.accounts as A
        saved = A._active_company_dataset
        A._active_company_dataset = lambda _db, cid: db._ds.get(cid)
        try:
            found = O.disagreements(db)
        finally:
            A._active_company_dataset = saved
        if bool(found) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}, got {bool(found)}")
    return fails


def main():
    fails = _control()
    if fails:
        print("✗ check-ownership-agreement: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags a contradicting row, an unsupported row and an "
          "absent row; accepts agreement and accepts nothing-stored-nothing-known")

    if "--against-db" not in sys.argv:
        print("✓ check-ownership-agreement: structural control passed "
              "(pass --against-db with a DATABASE_URL to check live rows)")
        return 0

    url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
    if not url:
        print("✗ --against-db requested with no DATABASE_URL")
        return 1
    os.environ["DATABASE_URL"] = url
    from services.api.core.db import SessionLocal
    from services.api.ownership import contradictions, pending
    db = SessionLocal()
    rows = contradictions(db)
    waiting = pending(db)
    # ⭐ COVERAGE IS PRINTED. "0 disagreements in 0 companies" and "0 in 30"
    # print the same tick.
    from services.api.modules.enterprise_state.models import Enterprise
    n = db.query(Enterprise).count()
    print(f"  checked {n} companies against their active dataset")
    if n == 0:
        print("✗ zero companies examined — that is a broken selector, not a clean corpus")
        return 1
    # ⭐ PENDING IS REPORTED, NEVER FAILED ON — a company created but not yet
    # uploaded holds the creation checkbox's answer and nothing refutes it.
    if waiting:
        print(f"  {len(waiting)} company row(s) awaiting a first dataset "
              f"(reported, not failed): "
              f"{[w['company_id'] for w in waiting]}")
    if rows:
        print(f"✗ {len(rows)} company row(s) contradict the payload:")
        for r in rows:
            print(f"   company {r['company_id']}: stored={r['stored']!r} "
                  f"derived={r['derived']!r} — {r['reason']}")
        return 1
    print("✓ every company's stored ownership agrees with its active dataset")
    return 0


if __name__ == "__main__":
    sys.exit(main())
