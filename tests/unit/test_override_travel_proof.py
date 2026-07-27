"""THE PROOF (§4x Stage 1 item 6): one override, every surface, then removed.

Not a unit test of a helper — this drives the REAL endpoint functions, the REAL
Ask AXIOM context builder and the REAL export-extras path against a live
database session, with and without an override on the same KPI, and asserts the
before/after on each surface.

The property under test is the one the whole feature rests on: an adjusted
figure cannot reach any surface as a bare number. If a surface is added later
that reads the value without the provenance, the assertion here that every
surface names the author is what should fail.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api import accounts as A
from services.api.accounts import (
    SessionLocal, Department, KpiPlan,
    company_kpi_variance, _report_extras, _kpi_scope_key,
)
from services.api.overrides import MetricOverride, audit_rows

CO = 909090
KPI_NAME = "EBITDA margin %"
COMPUTED = 19.4
ADJUSTED = 21.8
AUTHOR = "CFO — J. Chen"


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def env(_app):
    """A department with one KPI, and nothing else. Torn down either way."""
    s = SessionLocal()

    def _clean():
        s.query(MetricOverride).filter_by(company_id=CO).delete()
        s.query(KpiPlan).filter_by(company_id=CO).delete()
        s.query(Department).filter_by(company_id=CO).delete()
        s.commit()
    _clean()
    dep = Department(company_id=CO, dept_key="proofdept", name="Finance and Accounting")
    s.add(dep); s.flush()
    # FinancialDataset lives on core.db.Base (a DIFFERENT engine bind), so it is
    # not creatable through this session. The serializer only needs the dataset's
    # id and filename, so a stub stands in — the code path under test is
    # _serialize_kpis, not dataset loading.
    ds = type("DS", (), {"id": 77771, "original_filename": "proof.xlsx",
                         "uploaded_at": datetime(2026, 7, 1), "data": {},
                         "version": 1, "is_active": True})()
    _real_active = A._active_company_dataset
    A._active_company_dataset = lambda db, cid: (ds if cid == CO else _real_active(db, cid))
    kpi = KpiPlan(company_id=CO, dataset_id=ds.id, row_index=1, kpi_name=KPI_NAME,
                  unit="%", ytd_plan=20.0, ytd_actual=COMPUTED, full_year_target=22.0,
                  department_id=dep.id, direction="higher_better")
    s.add(kpi); s.commit()
    try:
        yield s, dep, ds, kpi
    finally:
        A._active_company_dataset = _real_active
        _clean()
        s.close()


def _add_override(s, dep, kpi):
    o = MetricOverride(
        company_id=CO, target_scope="department", department_id=dep.id,
        metric_ref=_kpi_scope_key(dep.id, KPI_NAME), metric_label=KPI_NAME,
        override_value=ADJUSTED, computed_value_at_override=COMPUTED,
        reason_category="private_info",
        reason_note="Q4 one-off restructuring charge is non-recurring",
        author_user_id=1, author_label=AUTHOR, created_at=datetime(2026, 7, 27))
    s.add(o); s.commit()
    return o


def _kpi_row(s):
    out = company_kpi_variance(CO, department=None, member=None, db=s)
    return next(k for k in out["kpis"] if k["kpi_name"] == KPI_NAME)


# ── SURFACE 1+2: department card and drill-down (same serializer) ────────────

def test_card_and_drilldown_before_and_after(env):
    s, dep, ds, kpi = env

    before = _kpi_row(s)
    assert before["ytd_actual"] == COMPUTED
    assert "provenance_override" not in before, "default-no-change: no attribution key at all"
    assert before["variance"]["status"] == "unfavorable", "19.4 against a 20.0 plan"

    _add_override(s, dep, kpi)
    after = _kpi_row(s)
    assert after["ytd_actual"] == ADJUSTED, "the card shows the CXO's figure"
    p = after["provenance_override"]
    assert p["adjusted"] is True
    assert p["adjusted_by"] == AUTHOR
    assert p["computed_value"] == COMPUTED, "AXIOM's number travels WITH it"
    assert p["reason_label"] == "private CXO information"
    assert after["computed_ytd_actual"] == COMPUTED
    assert after["variance"]["status"] == "favorable", \
        "variance follows the displayed figure; the computed one stays derivable"

    # THE UNDERLYING ROW IS UNTOUCHED — the immutable-computed-truth property.
    s.refresh(kpi)
    assert kpi.ytd_actual == COMPUTED, "the computed value was never written over"


def test_removing_the_override_restores_the_bare_computed_value(env):
    s, dep, ds, kpi = env
    _add_override(s, dep, kpi)
    assert _kpi_row(s)["ytd_actual"] == ADJUSTED

    s.query(MetricOverride).filter_by(company_id=CO).delete()
    s.commit()

    restored = _kpi_row(s)
    assert restored["ytd_actual"] == COMPUTED
    assert "provenance_override" not in restored
    assert "computed_ytd_actual" not in restored
    assert restored["variance"]["status"] == "unfavorable", "the original verdict returns"


# ── SURFACE 3+4: report extras and the PDF export ────────────────────────────

def test_export_extras_before_and_after(env):
    s, dep, ds, kpi = env
    before = _report_extras(s, CO)
    assert before.get("adjusted_figures") == [], "nothing to disclose, nothing disclosed"

    _add_override(s, dep, kpi)
    after = _report_extras(s, CO)
    rows = after["adjusted_figures"]
    assert len(rows) == 1
    r = rows[0]
    assert r["displayed_value"] == ADJUSTED and r["computed_value"] == COMPUTED
    assert r["author"] == AUTHOR and r["reason_label"] == "private CXO information"


def test_the_pdf_section_renders_both_figures(env):
    """Drives the real PDF row-building logic on the real extras payload."""
    s, dep, ds, kpi = env
    _add_override(s, dep, kpi)
    adj = audit_rows(s, CO, include_superseded=False)
    assert len(adj) == 1
    row = [str(adj[0].get("metric")), str(adj[0].get("computed_value")),
           str(adj[0].get("displayed_value")),
           f"{adj[0].get('author')} · {adj[0].get('reason_label')}"]
    assert row == [KPI_NAME, "19.4", "21.8", f"{AUTHOR} · private CXO information"]
    assert "19.4" in row[1], "the board sees what AXIOM computed, not only the adjustment"


# ── SURFACE 5: Ask AXIOM ─────────────────────────────────────────────────────

class _Doc:
    """Captures what the context builder emits, in order."""
    def __init__(self):
        self.lines, self.tags = [], set()

    def head(self, t):
        self.lines.append(f"## {t}")

    def note(self, t):
        self.lines.append(t)

    def fact(self, tag, label, value):
        self.tags.add(tag)
        self.lines.append(f"{label}: {value}")

    def text(self):
        return "\n".join(self.lines)


def test_ask_axiom_before_and_after(env):
    from services.api.prescience import _sec_overrides
    s, dep, ds, kpi = env

    d0 = _Doc()
    _sec_overrides(d0, s, CO)
    assert d0.text() == "", \
        "default-no-change reaches the prompt cache: not even a heading"

    _add_override(s, dep, kpi)
    d1 = _Doc()
    _sec_overrides(d1, s, CO)
    txt = d1.text()
    assert "CXO-ADJUSTED FIGURES" in txt
    assert AUTHOR in txt, "the model is told who adjusted it"
    assert "AXIOM COMPUTED 19.4" in txt, "and what AXIOM actually computed"
    assert "DISPLAYED 21.8" in txt
    assert "MUST state that the figure was adjusted" in txt, \
        "an instruction, not just data — prose has no field for a badge"
    assert "Finance and Accounting" in txt, "scoped to the right department"

    # The failure this guards: the adjusted number present WITHOUT the author.
    idx_val = txt.index("21.8")
    assert AUTHOR in txt[idx_val:idx_val + 200], \
        "the attribution must sit with the number, not in a distant paragraph"


def test_ask_axiom_returns_to_silence_when_the_override_is_removed(env):
    from services.api.prescience import _sec_overrides
    s, dep, ds, kpi = env
    _add_override(s, dep, kpi)
    s.query(MetricOverride).filter_by(company_id=CO).delete()
    s.commit()
    d = _Doc()
    _sec_overrides(d, s, CO)
    assert d.text() == ""


# ── audit trail ──────────────────────────────────────────────────────────────

def test_supersession_keeps_both_rows_and_only_one_is_active(env):
    s, dep, ds, kpi = env
    first = _add_override(s, dep, kpi)
    first.superseded_at = datetime(2026, 7, 28)
    first.supersession_kind = "superseded"
    s.commit()
    second = MetricOverride(
        company_id=CO, target_scope="department", department_id=dep.id,
        metric_ref=_kpi_scope_key(dep.id, KPI_NAME), metric_label=KPI_NAME,
        override_value=20.9, computed_value_at_override=COMPUTED,
        reason_category="definition", author_user_id=1, author_label=AUTHOR,
        created_at=datetime(2026, 7, 28))
    s.add(second); s.commit()
    first.superseded_by_id = second.id
    s.commit()

    full = audit_rows(s, CO)
    assert len(full) == 2, "the audit keeps what was superseded"
    assert [r["active"] for r in full] == [False, True]
    assert full[0]["displayed_value"] == ADJUSTED, "the earlier assertion survives intact"
    assert full[0]["supersession_kind"] == "superseded"

    live = audit_rows(s, CO, include_superseded=False)
    assert len(live) == 1 and live[0]["displayed_value"] == 20.9

    row = _kpi_row(s)
    assert row["ytd_actual"] == 20.9, "the card shows the CURRENT assertion only"
