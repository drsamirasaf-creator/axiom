"""CXO metric overrides — immutable model + read path (§4x Stage 1).

Stage 1 has NO write endpoint on purpose: the provenance-travel property has to
be proven before anyone can author an override through the product. These tests
are that proof, plus the two properties that are cheap now and impossible to
retrofit later — schema-enforced attribution, and the authority rule.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from services.api.main import app
from services.api import overrides as ov
from services.api.overrides import (
    MetricOverride, Resolved, resolve_many, resolve_one, audit_rows,
    can_author, AuthorityError, validate_new, REASON_CATEGORIES,
)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


# ── default-no-change ────────────────────────────────────────────────────────

def test_with_no_override_the_resolver_is_a_passthrough(_app):
    """THE RESTING STATE. Stage 1 must be invisible until an override exists:
    same value, and no attribution anywhere, because there is nothing to
    attribute."""
    r = Resolved(6.02)
    assert r.display == 6.02
    assert r.overridden is False
    assert r.attribution is None
    assert r.to_dict() == {"value": 6.02}, "no provenance key at all in the default case"


def test_to_dict_adds_no_keys_when_unoverridden(_app):
    """A surface that spreads to_dict() into its payload must produce a
    byte-identical payload to the one it produced before this feature."""
    assert set(Resolved(1).to_dict("ytd_actual")) == {"ytd_actual"}


def test_sentence_states_the_bare_value_when_unoverridden(_app):
    assert Resolved(7.1).sentence("Revenue growth") == "Revenue growth: 7.1"


# ── the override case: both figures, always ──────────────────────────────────

def _fake(**kw):
    d = dict(id=1, override_value=6.8, computed_value_at_override=7.1,
             reason_category="private_info", reason_note="known upcoming churn",
             author_label="CFO — J. Chen", created_at=datetime(2026, 7, 27))
    d.update(kw)
    return type("O", (), d)


def test_an_override_never_yields_a_value_without_its_authorship(_app):
    """THE ANTI-LAUNDERING PROPERTY. There is no attribute on Resolved that
    returns an overridden figure stripped of provenance: .display gives the
    number, and every serializer that emits it also emits .attribution."""
    r = Resolved(7.1, _fake())
    assert r.display == 6.8 and r.overridden is True
    a = r.attribution
    assert a["adjusted"] is True
    assert a["adjusted_by"] == "CFO — J. Chen"
    assert a["computed_value"] == 7.1, "AXIOM's number survives beside the CXO's"
    assert a["reason_label"] == "private CXO information"
    d = r.to_dict("ytd_actual")
    assert d["ytd_actual"] == 6.8 and d["provenance"]["adjusted_by"] == "CFO — J. Chen"


def test_the_prose_form_cannot_state_an_adjusted_number_as_fact(_app):
    """For surfaces that emit text rather than JSON — Ask AXIOM's context, the
    export disclosure. Prose has no field for a badge, so the sentence itself
    has to carry both figures."""
    s = Resolved(7.1, _fake()).sentence("Revenue growth")
    assert "ADJUSTED by CFO — J. Chen" in s
    assert "AXIOM computed 7.1" in s
    assert "private CXO information" in s


def test_the_computed_value_is_a_frozen_snapshot_not_a_live_lookup(_app):
    """The dataset can be re-uploaded. What AXIOM said AT THE MOMENT of the
    override is a permanent fact about that decision; re-deriving it later
    gives a different answer and silently rewrites the audit trail."""
    r = Resolved(9.9, _fake())          # live computed has since moved to 9.9
    assert r.attribution["computed_value"] == 7.1, "the snapshot, not the live value"


# ── schema-enforced attribution ──────────────────────────────────────────────

def test_attribution_columns_are_not_nullable(_app):
    """An unattributed or unreasoned override must be UNREPRESENTABLE — enforced
    by the database, not by a validator that a direct insert can bypass."""
    cols = MetricOverride.__table__.columns
    for name in ("override_value", "computed_value_at_override", "reason_category",
                 "author_user_id", "author_label", "created_at"):
        assert cols[name].nullable is False, f"{name} must be NOT NULL"


def test_reason_note_is_optional_but_the_category_is_not(_app):
    """§4l B.5: the CXO can change-and-sign without writing prose. The routing
    CATEGORY is what makes an override reviewable, so that stays required."""
    assert MetricOverride.__table__.columns["reason_note"].nullable is True
    assert MetricOverride.__table__.columns["reason_category"].nullable is False


def test_validate_new_rejects_every_missing_piece(_app):
    ok = dict(override_value=1, computed_value=2, reason_category="private_info",
              author_label="CFO — X")
    assert validate_new(**ok)
    for bad in ({"override_value": None}, {"computed_value": None},
                {"reason_category": "nonsense"}, {"author_label": "  "}):
        with pytest.raises(ValueError):
            validate_new(**{**ok, **bad})


def test_only_one_active_override_per_metric(_app):
    """Two live assertions about one number is a contradiction the UI would have
    to resolve arbitrarily. Supersession releases the slot; history accumulates."""
    uq = [c for c in MetricOverride.__table__.constraints
          if getattr(c, "name", "") == "uq_active_metric_override"]
    assert uq, "the active-override uniqueness constraint is missing"
    assert {c.name for c in uq[0].columns} == {"company_id", "metric_ref", "superseded_at"}


def test_the_model_has_no_update_path_only_supersession(_app):
    """A change is a NEW ROW. Editing an override in place would destroy the
    audit trail of the override itself."""
    cols = set(MetricOverride.__table__.columns.keys())
    assert {"superseded_at", "superseded_by_id", "supersession_kind"} <= cols
    import inspect
    src = inspect.getsource(ov)
    assert "def update_override" not in src and "def edit_override" not in src


# ── authority ────────────────────────────────────────────────────────────────

def test_platform_staff_can_never_author_a_customers_figure(_app):
    """Explicit carve-out: require_company_admin grants operator bypass
    everywhere else, and if that carried into overrides we could author a
    customer's signed board figure."""
    staff = type("U", (), {"id": 1, "is_staff": True})
    with pytest.raises(AuthorityError, match="Platform staff"):
        can_author(None, 20, staff, "department", 13)


def test_authority_fails_closed_before_stage_2_grants_exist(_app):
    """No grant table yet → nobody can author anything. Fail closed is the only
    safe default for a feature that alters numbers a board sees."""
    user = type("U", (), {"id": 7, "is_staff": False})

    class _DB:
        def get(self, model, pk):
            return type("D", (), {"id": pk, "company_id": 20, "name": "Finance"})
    with pytest.raises(AuthorityError, match="Not authorised"):
        can_author(_DB(), 20, user, "department", 13)


def test_a_department_override_requires_a_department(_app):
    user = type("U", (), {"id": 7, "is_staff": False})
    with pytest.raises(AuthorityError, match="needs a department"):
        can_author(None, 20, user, "department", None)


def test_enterprise_scope_is_not_yet_delegable(_app):
    """Rather than defaulting to 'any admin', which is the hole the
    admin-cannot-author rule exists to close."""
    user = type("U", (), {"id": 7, "is_staff": False})
    with pytest.raises(AuthorityError, match="not yet delegable"):
        can_author(None, 20, user, "enterprise", None)


def test_authority_is_not_inferred_from_head_email(_app):
    """_on_behalf_suffix matches Department.head_email by string. Fine for a
    LABEL, unacceptable for a PERMISSION: an admin editing that field would
    silently transfer the right to author board figures."""
    import inspect
    src = inspect.getsource(ov.department_authority)
    code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
    code = code.split('"""')[0] + "".join(code.split('"""')[2:])   # drop the docstring
    assert "head_email" not in code, "authority is resolving a permission from an email field"


# ── provenance travel: the serializer choke point ────────────────────────────

def test_kpi_payloads_are_built_in_exactly_one_place(_app):
    """/kpi-variance and the department okr-map both used to build this dict
    inline. Two copies meant two places an adjusted figure could be emitted
    without its authorship. This asserts the choke point holds."""
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts)
    # The literal payload key paired with the model attribute — the shape a
    # second, unresolved serializer would have.
    assert src.count('"ytd_actual": r.ytd_actual') == 0, \
        "a serializer is reading the raw column instead of the resolver"
    assert "_serialize_kpis" in src
    ser = inspect.getsource(accounts._serialize_kpis)
    assert "resolve_many" in ser


def test_okr_map_goes_through_the_same_serializer(_app):
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts.department_okr_map)
    assert "company_kpi_variance" in src, \
        "okr-map must not build its own KPI payload"


def test_ask_axiom_context_carries_adjusted_figures(_app):
    """The surface most likely to launder a number: it answers in prose, and
    prose has no field for a badge."""
    import inspect
    from services.api import prescience
    src = inspect.getsource(prescience._sec_overrides)
    assert "active_overrides" in src
    assert "MUST state that the figure was adjusted" in src, \
        "the model needs an explicit instruction, not just the data"
    assert "AXIOM COMPUTED" in src
    assembly = inspect.getsource(prescience.build_company_context)
    assert "_sec_overrides(doc, db, company_id)" in assembly


def test_ask_axiom_emits_nothing_when_there_are_no_overrides(_app):
    """Default-no-change reaches the prompt cache: an unchanged context document
    means an unchanged cache prefix, so a company that never overrides pays
    nothing for the feature."""
    import inspect
    from services.api import prescience
    src = inspect.getsource(prescience._sec_overrides)
    assert "if not rows:" in src and "return" in src


def test_every_export_format_carries_the_disclosure(_app):
    """pptx-comprehensive, pptx and pdf are all built from `extras`, so the
    disclosure is attached there rather than three times."""
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts._report_extras)
    assert '"adjusted_figures"' in src and "audit_rows" in src


def test_the_pdf_prints_both_figures_and_does_not_bury_the_section(_app):
    import inspect
    from services.api import report_pdf
    src = inspect.getsource(report_pdf.build_board_pdf)
    assert "adjusted_figures" in src
    assert "AXIOM computed" in src and "Displayed (adjusted)" in src
    # Governance disclosure must precede the legal boilerplate.
    assert src.index("Adjusted Figures") < src.index("Important Notice"), \
        "a disclosure printed behind the disclaimers is designed not to be read"


def test_the_pdf_never_truncates_the_disclosure_silently(_app):
    import inspect
    from services.api import report_pdf
    src = inspect.getsource(report_pdf.build_board_pdf)
    assert "further adjusted figures are listed in the" in src


# ── audit ────────────────────────────────────────────────────────────────────

def test_audit_includes_superseded_rows_by_default(_app):
    """An audit trail that shows only current state is not an audit trail."""
    import inspect
    src = inspect.getsource(audit_rows)
    assert "include_superseded: bool = True" in src


def test_audit_row_carries_both_values_and_the_author(_app):
    import inspect
    src = inspect.getsource(audit_rows)
    for k in ('"computed_value"', '"displayed_value"', '"author"',
              '"reason_category"', '"created_at"', '"active"'):
        assert k in src, k


def test_reason_categories_match_the_spec(_app):
    assert set(REASON_CATEGORIES) == {"calc_error", "data_error", "definition",
                                      "private_info", "other"}


def test_stage_1_exposes_no_write_endpoint(_app):
    """The write path is Stage 2, after review. A router shipped early is a
    write path nobody agreed to."""
    import inspect
    src = inspect.getsource(ov)
    assert "APIRouter" not in src and "@router" not in src
