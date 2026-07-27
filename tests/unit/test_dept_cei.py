"""Department CEI on /departments — server-side, alias-resolved, three states.

WHY SERVER-SIDE. The cycle aggregate is keyed by the department name AS TYPED ON
THE RESPONSE, which for a renamed department is its FORMER name. On Meridian
only 2 of 7 keys match a current department:

    aggregate keys : Finance · HR · Operations · Sales & Marketing ·
                     Supply Chain · Technology
    department names: Finance and Accounting · Human Resources · Operations ·
                     Sales & Marketing · Information Technology ·
                     Supply Chain and Logistics · Executive Management

A client-side join by name would publish a CEI for two departments and silently
blank five — including Finance 6.02 and IT 6.51, the first two anyone checks.
"""
import pytest
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.assessment_engine import (
    cei_band, CEI_GOOD_MIN, CEI_NEUTRAL_MIN, CEI_DEFINITION, _apply_dept_kfloor,
)


@pytest.fixture(scope="module")
def _app():
    with TestClient(app) as c:
        yield c


def test_band_thresholds_are_the_cei_pages_existing_ones(_app):
    """Reconciling three copies into one scheme must not silently re-band the
    surface that already had it."""
    assert (CEI_GOOD_MIN, CEI_NEUTRAL_MIN) == (7.5, 5.0)


def test_bands(_app):
    for cei, want in ((10, "good"), (7.5, "good"), (7.49, "neutral"),
                      (5.0, "neutral"), (4.99, "poor"), (0, "poor")):
        assert cei_band(cei) == want, cei


def test_a_missing_cei_is_not_poor(_app):
    """Suppressed and absent are STATES, not low scores. Banding None as 'poor'
    would paint a withheld department as failing."""
    assert cei_band(None) is None


def test_meridian_values_band_as_expected(_app):
    """The live numbers, so a threshold edit that moves them fails here."""
    for cei in (6.0233, 6.3816, 6.5085, 6.6658):
        assert cei_band(cei) == "neutral", cei


def test_definition_names_the_measure_and_the_scale(_app):
    assert "Composite Effectiveness Index" in CEI_DEFINITION and "0–10" in CEI_DEFINITION


def test_suppressed_slice_carries_n_but_never_a_cei(_app):
    """THE FIELD TRAP the cards must respect: a withheld slice carries `n`, a
    shown one carries `n_participants`. Reading the wrong key yields None and
    turns 'withheld, 3 responded' into 'withheld, unknown'."""
    depts = {
        "Finance": {"n_participants": 9, "cei": 6.0233},
        "Operations": {"n_participants": 6, "cei": 6.3816},
        "Sales & Marketing": {"n_participants": 6, "cei": 6.6658},
        "Technology": {"n_participants": 4, "cei": 6.5085},
        "HR": {"n_participants": 3, "cei": 6.72},
        "Supply Chain": {"n_participants": 2, "cei": 5.9},
    }
    out = _apply_dept_kfloor(depts)
    for k in ("HR", "Supply Chain"):
        assert out[k].get("cei") is None, "a withheld CEI must not survive serialization"
        assert out[k]["n"] > 0, "the count is what makes 'withheld' credible"
        assert "n_participants" not in out[k], "shown-slice key on a hidden slice"
    for k in ("Finance", "Technology"):
        assert out[k]["cei"] == depts[k]["cei"]
        assert out[k]["n_participants"] == depts[k]["n_participants"]


def test_dept_cei_map_resolves_aliases_rather_than_joining_by_name(_app):
    """Guards the reason this lives server-side at all."""
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts._dept_cei_map)
    assert "_pick_dept_slice(db, company_id, d, depts_raw)" in src
    assert "apply_kfloor" in src, "the floor must be applied before the map is read"


def test_dept_cei_map_emits_all_three_states(_app):
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts._dept_cei_map)
    for state in ('"scored"', '"suppressed"', '"absent"'):
        assert state in src, state


def test_every_name_used_in_dept_cei_map_is_bound(_app):
    """The 92e7340 class of bug: a bare name that resolves nowhere is a 500 that
    only fires on the branch using it. SUPPRESSION_NOTE and cei_band are
    imported inside the function; _cycle_label is NOT (it is nested inside
    assessment_summary and unreachable from here)."""
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts._dept_cei_map)
    assert "SUPPRESSION_NOTE" in src and "import" in src.split("SUPPRESSION_NOTE")[0]
    assert "_cycle_label(" not in src, "_cycle_label is nested; calling it here is a NameError"


def test_list_departments_ships_cei(_app):
    import inspect
    from services.api import accounts
    src = inspect.getsource(accounts.list_departments)
    assert '"cei": cei.get(d.id)' in src
    assert "_dept_cei_map(db, company_id)" in src
