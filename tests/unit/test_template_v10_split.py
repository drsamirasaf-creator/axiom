"""R6 — template v10: the working-capital split.

⭐ THE SPLIT IS DETAIL, NOT A RE-PARTITION. `receivables` and `inventory` are
components of `other_current_assets`; `payables` of `current_liabilities_ex_debt`.
The aggregates are untouched and remain the source of truth for every total, so
no stored figure moves. Deriving the aggregate from the parts — v8's shape for
the non-current split — would have silently dropped prepayments, accrued income
and everything else living in it.

⭐ AND THE ROWS ARE OPTIONAL. Every dataset uploaded before v10 lacks them.
Absence is a fact about those files rather than a failure of them, and a ratio
that needs them renders ABSENCE rather than a number built on a guess.
"""
import copy

import pytest

from services.api.modules.financials import engines
from services.api.modules.financials import ratio_registry as rr
from services.api.modules.financials import template_policy as policy
from services.api.modules.financials import templates

YEARS = [2022, 2023, 2024]
NEW_RATIOS = ["axiom.receivable_days", "axiom.payable_days",
              "axiom.inventory_days", "axiom.inventory_turnover",
              "axiom.cash_conversion_cycle", "axiom.quick_ratio"]


def _y(*v):
    return {str(y): x for y, x in zip(YEARS, v)}


@pytest.fixture
def v9_data():
    """A pre-v10 dataset: complete, and carrying none of the three new rows."""
    return {
        "company": {"tax_rate": 0.25, "cost_of_debt": 0.06, "ownership": "private",
                    "standard": "us_gaap", "risk_free_rate": 0.04,
                    "market_risk_premium": 0.055, "unlevered_industry_beta": 1.1,
                    "target_debt_to_equity": 0.5, "size_premium": 0.0,
                    "specific_risk_premium": 0.0, "name": "fixture",
                    "currency": "USD", "dlom": 0.2},
        "periods": {"historical": YEARS, "forecast": []},
        "income_statement": {
            "revenue": _y(1000.0, 1200.0, 1400.0), "cogs": _y(600.0, 700.0, 800.0),
            "opex": _y(200.0, 240.0, 280.0),
            "depreciation_amortization": _y(50.0, 60.0, 70.0),
            "interest_expense": _y(20.0, 22.0, 24.0)},
        "balance_sheet": {
            "cash": _y(100.0, 120.0, 150.0),
            "other_current_assets": _y(300.0, 340.0, 380.0),
            "noncurrent_assets": _y(800.0, 850.0, 900.0),
            "current_liabilities_ex_debt": _y(180.0, 200.0, 220.0),
            "other_noncurrent_liabilities": _y(50.0, 55.0, 60.0),
            "short_term_debt": _y(90.0, 100.0, 110.0),
            "long_term_debt": _y(400.0, 420.0, 440.0),
            "preferred_equity": _y(30.0, 30.0, 30.0),
            "minority_interest": _y(10.0, 12.0, 14.0),
            "total_equity": _y(600.0, 700.0, 820.0)},
        "cash_flow": {"capex": _y(70.0, 80.0, 90.0),
                      "net_borrowing": _y(15.0, 20.0, 25.0),
                      "dividends": _y(0.0, 0.0, 0.0)},
    }


@pytest.fixture
def v10_data(v9_data):
    d = copy.deepcopy(v9_data)
    d["balance_sheet"]["receivables"] = _y(150.0, 170.0, 190.0)
    d["balance_sheet"]["inventory"] = _y(100.0, 110.0, 120.0)
    d["balance_sheet"]["payables"] = _y(90.0, 100.0, 110.0)
    return d


# ── the version discipline ──────────────────────────────────────────────────
def test_the_version_bumped_and_all_three_strings_agree():
    # ⭐ v14 (4 Aug): cost avoidability (T5.1). The four strings
    # are pinned TOGETHER so a bump cannot move one and leave the others —
    # which is what this test is for, not the number itself.
    assert policy.VERSION_MAJOR == 14
    assert policy.GENERIC_VERSION == "v14"
    assert policy.COMPANY_VERSION == "7M-v14.0"
    assert policy.USER_FACING_VERSION == "v14"


def test_the_new_rows_are_optional_on_every_path():
    """⭐ THE v8 LESSON, WHICH COST A SHIPPED 422. Required-ness was restated in
    three files and the one customers actually use did not learn it."""
    for k in ("receivables", "inventory", "payables"):
        assert k in engines.BS_KEYS
        assert k in engines.BS_OPTIONAL_KEYS
        assert policy.required("balance_sheet", k) is False


def test_the_new_rows_appear_in_both_label_sets():
    for std in ("us_gaap", "ifrs"):
        lines = templates.LABELS[std]["lines"] if hasattr(templates, "LABELS") \
            else None
        if lines is None:                     # label table is private
            continue
        for k in ("receivables", "inventory", "payables"):
            assert k in lines, f"{k} missing from {std} labels"


# ── prior versions parse, and parse as ABSENT ───────────────────────────────
def test_a_v9_dataset_still_validates(v9_data):
    """The parser accepts prior versions unchanged — v1..v9 have no such rows."""
    v = engines.validate_dataset(copy.deepcopy(v9_data))
    assert v["errors"] == [], v["errors"]


def test_a_v9_dataset_renders_the_new_ratios_absent_never_zero(v9_data):
    """⭐⭐ RULE 5, THE ONE THAT MATTERS MOST. A cash conversion cycle computed
    from a receivables figure inferred from the unsplit total is fabrication.
    Every one of the six must be ABSENT, and the absence must NAME the row it
    is waiting for."""
    d = engines.derive_series(copy.deepcopy(v9_data))
    for rid in NEW_RATIOS:
        for i in range(len(d["years"])):
            v = rr.evaluate_period(v9_data, d["years"], i, rid)
            assert isinstance(v, rr.Absent), f"{rid} p{i} produced {v!r}"
            assert v.token in ("bs.receivables", "bs.inventory", "bs.payables"), \
                f"{rid} absence does not name a v10 row: {v!r}"


# ── and the other half: a v10 dataset actually computes them ────────────────
# ⭐⭐ R6 SUPPLIES THE DATA FOR SIX, AND ONLY TWO EXECUTE — A DEPENDENCY THE
# TOKEN COUNT COULD NOT SEE.
#
# The scope report said "+6", and a static recount after the split agreed: all
# six resolve to declared, collected tokens. EXECUTION disagreed, and execution
# is the stronger instrument. Four of them also need `po.days_in_period`, whose
# `expr` is the prose "365 | 366 | 90 by period basis" — a DECLARED token, so a
# resolver that only asks "is every token declared and collected" counts it as
# available, and an evaluator that has to produce a number cannot.
#
# Its disposition is one of the two open rulings carried since stage 2. The
# convention is not a default to pick: 365 vs 366, and 90 vs 91 for a quarter,
# changes every DSO/DPO/DIO figure a customer would be shown.
EXECUTE_NOW = ["axiom.quick_ratio", "axiom.inventory_turnover"]
BLOCKED_ON_DAYS = ["axiom.receivable_days", "axiom.inventory_days",
                   "axiom.payable_days", "axiom.cash_conversion_cycle"]


def test_a_v10_dataset_computes_the_two_that_do_not_need_a_day_count(v10_data):
    """⭐ WITHOUT THIS, 'ALL ABSENT' PROVES NOTHING. A ratio absent on every
    dataset AND absent on a complete one is simply broken, and the v9 test
    above would pass either way."""
    d = engines.derive_series(copy.deepcopy(v10_data))
    for rid in EXECUTE_NOW:
        v = rr.evaluate_period(v10_data, d["years"], 1, rid)
        assert not isinstance(v, rr.Absent), f"{rid} still absent: {v!r}"
        assert isinstance(v, (int, float))


def test_the_day_count_ratios_are_blocked_on_a_named_ruling(v10_data):
    """The remaining four have their DATA and still cannot execute. The absence
    must name `po.days_in_period` and not a v10 row — a reader must be able to
    tell "you have not supplied this" from "we have not ruled on this"."""
    d = engines.derive_series(copy.deepcopy(v10_data))
    for rid in BLOCKED_ON_DAYS:
        v = rr.evaluate_period(v10_data, d["years"], 1, rid)
        assert isinstance(v, rr.Absent), f"{rid} unexpectedly executed: {v!r}"
        assert v.token == "po.days_in_period", \
            f"{rid} absence blames the wrong thing: {v!r}"
        assert "prose" in v.reason


def test_the_split_moves_no_figure(v9_data, v10_data):
    """⭐ THE AGGREGATES ARE UNTOUCHED, SO EVERY EXISTING RATIO IS IDENTICAL.
    Supplying the detail must not change a single previously-computed number —
    if it did, the split would be a re-partition and the aggregate would have
    stopped meaning what it meant."""
    a = engines.derive_series(copy.deepcopy(v9_data))
    b = engines.derive_series(copy.deepcopy(v10_data))
    assert a["ratios"] == b["ratios"]
    assert a["fcff"] == b["fcff"] and a["fcfe"] == b["fcfe"]
    assert a["nwc"] == b["nwc"]


# ── corruption prevention ───────────────────────────────────────────────────
def test_parts_exceeding_the_whole_warn_and_still_store(v10_data):
    """⭐ FLAG AND STORE, NEVER REFUSE. A mis-mapped column costs the customer
    their whole upload if we reject it, and a mapping fault is undiagnosable
    from a rejection."""
    bad = copy.deepcopy(v10_data)
    bad["balance_sheet"]["receivables"] = _y(500.0, 500.0, 500.0)   # > the aggregate
    v = engines.validate_dataset(bad)
    assert v["errors"] == [], "a mis-mapped column must not block persistence"
    assert any("exceeds other_current_assets" in w for w in v["warnings"]), v["warnings"]


def test_the_warning_does_not_fire_on_a_correct_file(v10_data):
    """A warning that cries wolf teaches customers to dismiss warnings, which
    costs exactly on the day one matters."""
    v = engines.validate_dataset(copy.deepcopy(v10_data))
    assert not any("exceeds" in w for w in v["warnings"]), v["warnings"]


def test_the_warning_does_not_fire_when_the_rows_are_absent(v9_data):
    """Absence is a legitimate state, not a fault."""
    v = engines.validate_dataset(copy.deepcopy(v9_data))
    assert not any("exceeds" in w for w in v["warnings"]), v["warnings"]


def test_the_registry_declares_them_as_components_not_replacements():
    reg = rr.load()
    vocab = {t: m for g in reg["vocabulary"].values() for t, m in g.items()}
    for tok, agg in (("bs.receivables", "bs.other_current_assets"),
                     ("bs.inventory", "bs.other_current_assets"),
                     ("bs.payables", "bs.other_current_liabilities")):
        m = vocab[tok]
        assert m["source"] == "stored" and m["collected"] is True
        assert m.get("optional") is True, f"{tok} must be optional"
        assert m.get("component_of") == agg, f"{tok} is not declared a component"
    # the aggregates keep their own definitions
    assert vocab["bs.current_assets"]["expr"] == "bs.cash + bs.other_current_assets"
