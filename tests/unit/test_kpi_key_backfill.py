"""KPI stable-key backfill — the dirty-data battery.

The department re-key passed every test and then crashed production, because
those tests all seeded CLEAN data. The naive implementation only fails on data
that is duplicated, blank, or cross-scoped, so this file seeds exactly that and
asserts BOTH directions:

  * test_naive_*  reproduces the failure on the naive approach
  * everything else passes on the safe one

A battery that only proves the fix works cannot tell you the fix was needed.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.accounts import (
    SessionLocal, KpiPlan, KpiAlias, Department,
    _backfill_kpi_keys, _kpi_scope_key, _resolve_kpi_key, _norm_kpi_key,
)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(_app):
    s = SessionLocal()
    try:
        s.query(KpiPlan).delete()
        s.query(KpiAlias).delete()
        s.commit()
        yield s
    finally:
        s.close()


class _Co:
    """A company is just an id to this backfill — it reads KpiPlan/KpiAlias and
    nothing else. Creating a real Enterprise row would drag in the OTHER
    Base/engine (enterprises is not on the accounts bind at all) for no gain."""
    _n = 9000
    def __init__(self):
        _Co._n += 1
        self.id = _Co._n


def _co(db, name):
    return _Co()


def _kpi(db, cid, ds, ri, name, dept=None, archived=False):
    k = KpiPlan(company_id=cid, dataset_id=ds, row_index=ri, kpi_name=name,
                department_id=dept, archived=archived)
    db.add(k); return k


# ── the crash shape, both directions ─────────────────────────────────────────
def test_naive_per_row_query_collides_on_duplicates(db):
    """REPRODUCES THE CRASH. SessionLocal is autoflush=False, so a query inside
    the loop cannot see rows added earlier in the same loop. Two rows with the
    same (dept, name) therefore BOTH look unclaimed and both mint a key — which
    is how the department re-key produced two aliases for one norm and died on
    the unique constraint at commit."""
    ent = _co(db, "Naive Co")
    for ri, nm in enumerate(["On-time delivery %", "On-time delivery %"]):
        _kpi(db, ent.id, 1, ri, nm, dept=5)
    db.commit()

    # the naive loop: ask the DB per row instead of holding a claimed dict
    import uuid as _u
    minted = []
    for r in db.query(KpiPlan).order_by(KpiPlan.row_index).all():
        found = _resolve_kpi_key(db, r.company_id, r.department_id, r.kpi_name)
        if found is None:
            key = _u.uuid4().hex
            minted.append(key)
            db.add(KpiAlias(company_id=r.company_id,
                            scope_key=_kpi_scope_key(r.department_id, r.kpi_name),
                            department_id=r.department_id,
                            name_norm=_norm_kpi_key(r.kpi_name), kpi_key=key))
        r.kpi_key = found or minted[-1]

    assert len(minted) == 2, "the naive pass mints TWO keys for one KPI"
    with pytest.raises(Exception):
        db.commit()                      # uq_kpi_alias fires — the crash
    db.rollback()


def test_safe_backfill_survives_the_same_shape(db):
    """The identical data through the real backfill: one key, one alias, no
    exception."""
    ent = _co(db, "Safe Co")
    for ri, nm in enumerate(["On-time delivery %", "On-time delivery %"]):
        _kpi(db, ent.id, 1, ri, nm, dept=5)
    db.commit()

    res = _backfill_kpi_keys(db, ent.id)
    db.commit()

    rows = db.query(KpiPlan).filter_by(company_id=ent.id).all()
    keys = {r.kpi_key for r in rows}
    assert len(keys) == 1 and None not in keys, "duplicates share ONE key"
    assert db.query(KpiAlias).filter_by(company_id=ent.id).count() == 1
    assert res["assigned"] == 1 and res["reused"] == 1 and res["errors"] == 0


# ── the rest of the dirty battery ────────────────────────────────────────────
def test_same_name_in_two_departments_stays_two_kpis(db):
    """The scoping decision, pinned. IT's "On-time delivery %" is NOT
    Operations'. Merging them would relocate the org-structure duplication bug
    into KPIs."""
    ent = _co(db, "Two Depts Co")
    _kpi(db, ent.id, 1, 0, "On-time delivery %", dept=10)
    _kpi(db, ent.id, 1, 1, "On-time delivery %", dept=20)
    db.commit()
    _backfill_kpi_keys(db, ent.id); db.commit()

    a, b = db.query(KpiPlan).order_by(KpiPlan.row_index).all()
    assert a.kpi_key and b.kpi_key and a.kpi_key != b.kpi_key
    assert db.query(KpiAlias).filter_by(company_id=ent.id).count() == 2


def test_unassigned_departments_do_not_collapse_into_one(db):
    """NULL department is stored as the 0 sentinel. Without it the unique
    constraint would be inert for unassigned KPIs (NULL != NULL in SQL) — but
    two DIFFERENT unassigned names must still stay different KPIs."""
    ent = _co(db, "Unassigned Co")
    _kpi(db, ent.id, 1, 0, "Cash conversion days", dept=None)
    _kpi(db, ent.id, 1, 1, "Cash conversion days", dept=None)   # same → one KPI
    _kpi(db, ent.id, 1, 2, "Headcount", dept=None)              # different → another
    db.commit()
    _backfill_kpi_keys(db, ent.id); db.commit()

    rows = db.query(KpiPlan).order_by(KpiPlan.row_index).all()
    assert rows[0].kpi_key == rows[1].kpi_key
    assert rows[2].kpi_key != rows[0].kpi_key


def test_oldest_dataset_owns_the_key_and_later_versions_inherit(db):
    """Quarterly re-uploads must be ONE KPI with a history, not four KPIs."""
    ent = _co(db, "Versions Co")
    for ds in (7, 3, 9, 1):                       # deliberately out of order
        _kpi(db, ent.id, ds, 0, "DSO days", dept=4)
    db.commit()
    _backfill_kpi_keys(db, ent.id); db.commit()

    rows = db.query(KpiPlan).order_by(KpiPlan.dataset_id).all()
    assert len({r.kpi_key for r in rows}) == 1, "one KPI across four versions"
    assert db.query(KpiAlias).filter_by(company_id=ent.id).count() == 1


def test_blank_names_get_their_own_keys_not_one_shared_key(db):
    """A blank name carries no identity. Sharing one key across every blank row
    would fuse unrelated rows into a single phantom KPI."""
    ent = _co(db, "Blank Co")
    # NOT None: kpi_name is NOT NULL, so a null name cannot reach the table.
    # Empty and whitespace-only CAN — a spreadsheet row with a value but no
    # label produces exactly this.
    _kpi(db, ent.id, 1, 0, "", dept=1)
    _kpi(db, ent.id, 1, 1, "   ", dept=1)
    db.commit()
    res = _backfill_kpi_keys(db, ent.id); db.commit()

    keys = [r.kpi_key for r in db.query(KpiPlan).order_by(KpiPlan.row_index).all()]
    assert all(keys) and len(set(keys)) == 2
    assert res["blank_names"] == 2
    assert db.query(KpiAlias).filter_by(company_id=ent.id).count() == 0


def test_archived_rows_are_keyed_too(db):
    """Archived is not deleted — an archived KPI keeps its identity, or restoring
    it would create a stranger."""
    ent = _co(db, "Archived Co")
    _kpi(db, ent.id, 1, 0, "Churn %", dept=2, archived=True)
    _kpi(db, ent.id, 2, 0, "Churn %", dept=2, archived=False)
    db.commit()
    _backfill_kpi_keys(db, ent.id); db.commit()
    a, b = db.query(KpiPlan).order_by(KpiPlan.dataset_id).all()
    assert a.kpi_key and a.kpi_key == b.kpi_key


def test_case_and_whitespace_variants_are_one_kpi(db):
    ent = _co(db, "Messy Co")
    for ri, nm in enumerate(["DSO days", "  dso   DAYS ", "Dso Days"]):
        _kpi(db, ent.id, ri + 1, 0, nm, dept=3)
    db.commit()
    _backfill_kpi_keys(db, ent.id); db.commit()
    assert len({r.kpi_key for r in db.query(KpiPlan).all()}) == 1


def test_backfill_is_idempotent_and_resumable(db):
    """A partial pass must be safe to re-run — the whole point of the rollback
    story is that an aborted backfill can simply be run again."""
    ent = _co(db, "Resume Co")
    for ri in range(4):
        _kpi(db, ent.id, 1, ri, f"KPI {ri}", dept=6)
    db.commit()
    first = _backfill_kpi_keys(db, ent.id); db.commit()
    before = {r.id: r.kpi_key for r in db.query(KpiPlan).all()}

    second = _backfill_kpi_keys(db, ent.id); db.commit()
    after = {r.id: r.kpi_key for r in db.query(KpiPlan).all()}
    assert before == after, "a second pass must change nothing"
    assert second["scanned"] == 0 and first["assigned"] == 4


def test_companies_never_share_a_key(db):
    """Tenant isolation: the same KPI name in two companies is two KPIs."""
    a = _co(db, "Tenant A"); b = _co(db, "Tenant B")
    _kpi(db, a.id, 1, 0, "Gross margin %", dept=1)
    _kpi(db, b.id, 1, 0, "Gross margin %", dept=1)
    db.commit()
    _backfill_kpi_keys(db); db.commit()
    ka = db.query(KpiPlan).filter_by(company_id=a.id).first().kpi_key
    kb = db.query(KpiPlan).filter_by(company_id=b.id).first().kpi_key
    assert ka and kb and ka != kb
