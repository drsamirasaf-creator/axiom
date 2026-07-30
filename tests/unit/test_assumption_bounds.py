"""An out-of-range assumption is flagged at every stored dataset, never refused.

⭐ WHY THIS EXISTS. `validate_dataset` tested presence and float-castability and
nothing else, so 0.2, 20 and -5 validated identically to 0.02 on every
client-settable field. One live paying customer holds eight datasets and
twenty-seven stored valuation runs carrying `size_premium = 0.2` — twenty
percentage points added straight to cost of equity by `engines.py:476`, roughly
halving their enterprise value. Nothing in the system looked at it.

⭐ THE SCOPE IS THE SUBSTANCE. Those eight datasets were written on 16 July and
will never re-ingest. A check that only fires at upload leaves every existing
dataset unguarded — the same reasoning that made `balance_audit` run on every
stored period rather than historicals only. `test_the_audit_is_dataset_scoped_not_ingest_scoped`
encodes that so the scope cannot quietly narrow later.
"""
import pytest

from services.api.modules.financials.engines import (
    ASSUMPTION_BOUNDS, assumption_audit, validate_dataset,
)


def _ds(**company):
    """A dataset that balances, so only assumption findings can arise."""
    base = {"tax_rate": 0.25, "risk_free_rate": 0.04, "market_risk_premium": 0.06,
            "cost_of_debt": 0.07, "standard": "ifrs", "ownership": "private",
            "dlom": 0.12, "size_premium": 0.02, "specific_risk_premium": 0.025,
            "unlevered_industry_beta": 1.1, "target_debt_to_equity": 0.4}
    base.update(company)
    bs = {"cash": {"2024": 10.0}, "other_current_assets": {"2024": 20.0},
          "noncurrent_assets": {"2024": 70.0},
          "current_liabilities_ex_debt": {"2024": 15.0},
          "short_term_debt": {"2024": 25.0}, "long_term_debt": {"2024": 20.0},
          "preferred_equity": {"2024": 0.0}, "minority_interest": {"2024": 0.0},
          "total_equity": {"2024": 40.0}}
    return {"periods": {"historical": [2024], "forecast": []},
            "income_statement": {"revenue": {"2024": 100.0}},
            "balance_sheet": bs, "cash_flow": {}, "company": base}


# ── the three states ────────────────────────────────────────────────────────

def test_in_bounds_is_clean():
    r = assumption_audit(_ds())
    assert r["in_bounds"] and r["breaching"] == []


def test_out_of_bounds_names_field_value_bound_and_direction():
    """⭐ Not "assumptions out of range" — a surface must be able to badge the
    exact field, and a reader must know which way it went."""
    f = assumption_audit(_ds(size_premium=0.2))["fields"]["size_premium"]
    assert f["state"] == "out_of_bounds"
    assert f["value"] == 0.2
    assert f["max"] == 0.1 and f["min"] == 0.0
    assert f["direction"] == "above"
    assert f["bound_crossed"] == 0.1


def test_below_the_floor_is_reported_as_below():
    f = assumption_audit(_ds(size_premium=-0.05))["fields"]["size_premium"]
    assert f["state"] == "out_of_bounds" and f["direction"] == "below"
    assert f["bound_crossed"] == 0.0


def test_absent_is_a_THIRD_STATE_named_and_not_in_bounds():
    """⭐ A field that could not be checked must not be indistinguishable from one
    that passed. An absent assumption cannot be out of range, and coercing it
    would manufacture a breach out of an absence."""
    d = _ds()
    d["company"].pop("dlom")
    r = assumption_audit(d)
    assert r["fields"]["dlom"]["state"] == "absent"
    assert r["fields"]["dlom"]["value"] is None
    assert "dlom" in r["absent"]
    assert "dlom" not in r["breaching"]
    assert r["fields"]["dlom"]["state"] != "in_bounds"


def test_absent_is_excluded_from_the_checked_count():
    """`checked` must count what was actually tested, or a corpus of absences
    reports as fully verified."""
    d = _ds()
    for k in ("dlom", "size_premium", "specific_risk_premium"):
        d["company"].pop(k)
    r = assumption_audit(d)
    assert r["checked"] == len(ASSUMPTION_BOUNDS) - len(r["absent"])
    assert len(r["absent"]) >= 3


def test_a_bool_is_not_a_number():
    """`isinstance(True, int)` is True in Python; a boolean assumption is absent,
    not a value of 1."""
    assert assumption_audit(_ds(size_premium=True))["fields"]["size_premium"]["state"] == "absent"


# ── flag, never refuse ──────────────────────────────────────────────────────

def test_it_flags_and_never_refuses():
    """⭐ FLAG-NOT-REFUSE IS A DECISION A LATER EDIT COULD QUIETLY REVERSE, which
    is why the balance audit encodes exactly this and why it is copied rather
    than reinvented. Refusing would lock a customer out of their own data because
    a premium looked unusual — a worse failure than the one being guarded."""
    v = validate_dataset(_ds(size_premium=0.2))
    assert any("size_premium" in w for w in v["warnings"])
    assert v["errors"] == [] or not any("size_premium" in str(e) for e in v["errors"]), \
        "an out-of-range assumption must never produce a blocking error"
    assert v["assumptions"]["breaching"] == ["size_premium"]


def test_the_warning_states_the_consequence_not_just_the_range():
    w = [x for x in validate_dataset(_ds(size_premium=0.2))["warnings"]
         if "size_premium" in x][0]
    assert "0.2" in w and "0.1" in w
    assert "cost of equity" in w
    assert "Left as supplied" in w, "the warning must say the value was not altered"


# ── scope ───────────────────────────────────────────────────────────────────

def test_the_audit_is_dataset_scoped_not_ingest_scoped():
    """⭐ THE CONTROL FOR THE SCOPE. The eight affected datasets will never
    re-ingest; a check reachable only through the upload path would leave them
    and every other stored dataset unguarded forever.

    `assumption_audit` takes a payload and nothing else — no db, no request, no
    upload context — so it can be swept over stored rows. If a future edit makes
    it require ingest state, this fails.
    """
    import inspect
    sig = inspect.signature(assumption_audit)
    assert list(sig.parameters) == ["data"], \
        "assumption_audit must take only a payload, so stored rows can be swept"
    assert assumption_audit(_ds())["checked"] > 0


# ── the known positive is REAL ──────────────────────────────────────────────

def test_known_positive_is_the_live_value_not_a_synthetic_one():
    """⭐ A guard whose only proof is a fabricated case proves it CAN fire, not
    that it fires on the thing it exists for. 0.2 is the value eight live
    datasets actually carry, against a measured corpus range of 0.018–0.03."""
    r = assumption_audit(_ds(size_premium=0.2))
    assert r["breaching"] == ["size_premium"]
    assert r["fields"]["size_premium"]["value"] == 0.2


@pytest.mark.parametrize("v", [0.018, 0.02, 0.03])
def test_the_corpus_typical_values_do_not_trip(v):
    """The bound must not flag the population it was measured against."""
    assert assumption_audit(_ds(size_premium=v))["breaching"] == []


# ── the bounds themselves ───────────────────────────────────────────────────

def test_bounds_are_the_measured_ones():
    """⭐ These were calibrated against the live corpus — 8 of 321 field-values,
    2.5%, every trip the one known incident. Changing one without re-measuring
    the hit rate turns a calibrated bound into a guess."""
    assert ASSUMPTION_BOUNDS["size_premium"] == (0.0, 0.10)
    assert ASSUMPTION_BOUNDS["specific_risk_premium"] == (0.0, 0.10)
    assert ASSUMPTION_BOUNDS["tax_rate"] == (0.0, 0.60)
    assert ASSUMPTION_BOUNDS["shares_outstanding"] == (1.0, None)


def test_every_client_settable_numeric_field_has_a_bound():
    """A field entering a computed figure with no bound is the gap this closes."""
    from services.api.modules.financials.engines import COMPANY_FIELDS
    numeric = {k for k, (_, t) in COMPANY_FIELDS.items() if t is float}
    assert numeric - set(ASSUMPTION_BOUNDS) == set(), \
        "a numeric company field has no bound"
