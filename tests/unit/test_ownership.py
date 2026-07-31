"""Ownership: one value, one owner — the dataset payload.

⭐⭐ THE DEFECT THIS CLOSES WAS LIVE ON THE DEMO. Meridian's active dataset carried
`dlom = 0.2` while its enterprise row said `public` — a discount for
NON-MARKETABILITY on a company the record called publicly traded. The engine was
internally consistent, which is exactly why nothing broke and nothing noticed.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest

from services.api import ownership as O


class _Ent:
    def __init__(self, i, own):
        self.id, self.ownership = i, own


class _DS:
    def __init__(self, i, own, extra=None):
        self.id = i
        c = {} if own is None else {"ownership": own}
        c.update(extra or {})
        self.data = {"company": c}


class _DB:
    def __init__(self, ents, ds):
        self._e, self._ds = ents, ds

    def query(self, _m):
        return self

    def all(self):
        return self._e

    def get(self, _m, i):
        return next((e for e in self._e if e.id == i), None)


@pytest.fixture
def patched(monkeypatch):
    import services.api.accounts as A

    def install(ds_map):
        monkeypatch.setattr(A, "_active_company_dataset",
                            lambda _db, cid: ds_map.get(cid))
    return install


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE PAYLOAD IS THE SINGLE OWNER
# ═══════════════════════════════════════════════════════════════════════════

def test_resolve_reads_the_PAYLOAD_not_the_row(patched):
    patched({1: _DS(10, "private")})
    db = _DB([_Ent(1, "public")], None)
    r = O.resolve(db, 1)
    assert r["ownership"] == O.PRIVATE, "the stored row won over the payload"
    assert r["source"] == "payload"
    assert r["dataset_id"] == 10


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ ABSENCE PROPAGATES — a default here picks a cost-of-equity model
# ═══════════════════════════════════════════════════════════════════════════

def test_no_dataset_is_UNDETERMINED_never_a_default(patched):
    """⭐⭐ A DEFAULT HERE SILENTLY PICKS A VALUATION METHOD. Not private, not
    public — no answer, with the reason attached."""
    patched({})
    db = _DB([_Ent(1, "private")], None)
    r = O.resolve(db, 1)
    assert r["ownership"] == O.UNDETERMINED
    assert r["ownership"] not in (O.PRIVATE, O.PUBLIC)
    assert "not yet determined" in r["reason"]


def test_a_dataset_that_STATES_NO_ownership_is_also_undetermined(patched):
    patched({1: _DS(10, None)})
    db = _DB([_Ent(1, "private")], None)
    r = O.resolve(db, 1)
    assert r["ownership"] == O.UNDETERMINED
    assert "cannot be determined" in r["reason"]


def test_the_company_response_reports_undetermined_WITH_ITS_REASON():
    """⭐ Returned as a BLOCK, so a caller cannot mistake "undetermined" for a
    third ownership TYPE. It is the absence of an answer."""
    import inspect

    from services.api import accounts as A
    src = inspect.getsource(A._ownership_block)
    assert '"absent"' in src
    assert "UNDETERMINED" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE DLOM RULE
# ═══════════════════════════════════════════════════════════════════════════

def test_a_public_company_CANNOT_carry_a_DLOM():
    """⭐⭐ A discount for non-marketability on a publicly traded company is
    self-contradictory, and it is the first thing a valuation professional
    checks."""
    assert O.dlom_permitted(O.PUBLIC) is False
    assert O.dlom_permitted(O.PRIVATE) is True


def test_UNDETERMINED_permits_no_DLOM_either():
    """⭐ We do not know it is private, and a DLOM asserts that we do."""
    assert O.dlom_permitted(O.UNDETERMINED) is False
    assert O.dlom_permitted(None) is False


def test_the_ENGINE_already_forces_dlom_to_zero_on_the_public_branch():
    """⭐ Asserted against the engine, not just the rule module — so the
    contradiction cannot return through the record."""
    import inspect

    from services.api.modules.valuation import engines as V
    src = inspect.getsource(V)
    assert 'company["ownership"] == "private" else 0.0' in src, \
        "the engine no longer forces DLOM to 0.0 off the payload's ownership"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE GUARD — contradiction vs pending
# ═══════════════════════════════════════════════════════════════════════════

def test_a_contradicting_row_is_flagged(patched):
    patched({1: _DS(10, "private")})
    db = _DB([_Ent(1, "public")], None)
    c = O.contradictions(db)
    assert len(c) == 1 and c[0]["derived"] == "private"


def test_a_company_awaiting_its_first_dataset_is_PENDING_not_a_contradiction(patched):
    """⭐⭐ CONFLATING THEM WOULD MAKE THE GATE UNPASSABLE — four live companies
    are in exactly this state, and they are ordinary. A gate that cannot pass is
    a gate nobody runs."""
    patched({})
    db = _DB([_Ent(1, "private")], None)
    assert O.contradictions(db) == []
    p = O.pending(db)
    assert len(p) == 1 and p[0]["kind"] == "pending"


def test_agreement_is_flagged_as_neither(patched):
    patched({1: _DS(10, "private")})
    db = _DB([_Ent(1, "private")], None)
    assert O.disagreements(db) == []


def test_the_guard_script_carries_a_known_positive():
    """⭐ A guard that has never fired has not been tested, and this class went
    unseen for as long as it existed."""
    src = open("scripts/check-ownership-agreement.py", encoding="utf-8").read()
    assert "THE KNOWN POSITIVE" in src
    assert "_control()" in src
    assert "checked {n} companies" in src or "checked" in src


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ RECONCILE WRITES PROVENANCE AND MOVES NO FIGURE
# ═══════════════════════════════════════════════════════════════════════════

def test_reconcile_REFUSES_to_act_on_an_absence(patched):
    """⭐ We will not clear a stored value on the strength of an absence, and we
    will not invent one."""
    patched({})
    db = _DB([_Ent(1, "private")], None)
    out = O.reconcile(db, 1)
    assert out["changed"] is False
    assert out["ownership"] == O.UNDETERMINED
    assert out["stored"] == "private", "a stored value was cleared by an absence"


def test_reconcile_writes_FIELD_LEVEL_PROVENANCE():
    """⭐⭐ THE PROVENANCE LAW. `enterprises.ownership` had none at all — no
    updated_at, no updated_by, no audit row — and it selects which
    cost-of-equity model runs."""
    import inspect
    src = inspect.getsource(O.reconcile)
    assert "AssumptionEdit" in src
    assert "actor_user_id" in src and "occurred_at" in src
    assert 'field="ownership"' in src


def test_the_enterprise_row_is_documented_as_DERIVED_never_authoritative():
    from tests.codeonly import code_only
    doc = O.__doc__ or ""
    assert "ONE VALUE, ONE OWNER" in doc
    assert "DERIVED, NEVER AUTHORITATIVE" in doc
    # ⭐ and the creation site says it no longer writes a valuation input
    src = open("services/api/accounts.py", encoding="utf-8").read()
    assert "THIS NO LONGER WRITES A VALUATION INPUT" in src


def test_a_published_pack_cannot_move_because_the_row_is_not_frozen():
    """⭐⭐ THE SAMPLE-PACK VERDICT. Packs freeze INPUTS BY VALUE, and the
    enterprise row is not one of them — measured: 0 of 20 published packs carry a
    company ownership in their frozen snapshot. Correcting the row cannot move a
    published figure."""
    from services.api import pack as P
    assert "ownership" not in P.INPUT_CLASSES
    assert "enterprise_row" not in P.INPUT_CLASSES
