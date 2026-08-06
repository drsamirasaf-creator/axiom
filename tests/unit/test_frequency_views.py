"""Frequency views: three views, declared aggregation, partial buckets,
interpolation. Controls in memory, each failing on its own input.
"""
import pytest

import services.api.frequency_views as FV
from services.api.modules.financials import dimensions as D
from services.api.modules.financials import periods as PR


def _ds(freq, periods, *, rev=100.0, cash=1000.0):
    return {"company": {"name": "F"},
            "periods": {"frequency": freq, "historical": list(periods),
                        "forecast": []},
            "income_statement": {"revenue": {str(p): rev for p in periods}},
            "balance_sheet": {"cash": {str(p): cash for p in periods},
                              "equity": {str(p): 5000.0 for p in periods}},
            "cash_flow": {"capex": {str(p): 10.0 for p in periods}}}


Q = [20241, 20242, 20243, 20244]
M12 = [202401 + i for i in range(12)]


# ── ruling 2 · three views, not four ────────────────────────────────────────

def test_there_are_exactly_three_views_and_semi_annual_is_not_one():
    assert FV.VIEWS == ("monthly", "quarterly", "annual")
    assert "semi_annual" not in FV.VIEWS and "semiannual" not in FV.VIEWS
    assert "semi_annual" not in FV._PER_YEAR


# ── ruling 5 · a finer view is disabled AND says why ────────────────────────

def test_quarterly_data_enables_quarterly_and_annual_but_not_monthly():
    e = {v["view"]: v for v in FV.enabled_views("quarterly")}
    assert e["quarterly"]["enabled"] and e["quarterly"]["is_base"]
    assert e["annual"]["enabled"]
    assert not e["monthly"]["enabled"]
    assert e["monthly"]["requires_interpolation"]


def test_annual_data_enables_annual_only():
    e = {v["view"]: v for v in FV.enabled_views("annual")}
    assert e["annual"]["enabled"]
    assert not e["quarterly"]["enabled"] and not e["monthly"]["enabled"]


def test_every_view_carries_a_reason_enabled_or_not():
    """⛔ A disabled control with no explanation is indistinguishable from a
    broken one."""
    for freq in ("annual", "quarterly", "monthly"):
        for v in FV.enabled_views(freq):
            assert v["reason"], (freq, v["view"])


def test_an_unknown_frequency_falls_back_to_annual_rather_than_crashing():
    e = {v["view"]: v for v in FV.enabled_views("fortnightly")}
    assert e["annual"]["enabled"] and not e["quarterly"]["enabled"]


# ── ruling 3 · the classification is declared, never inferred ───────────────

def test_every_registry_token_declares_an_aggregation():
    v, _g, _r = __import__(
        "services.api.modules.financials.ratio_registry",
        fromlist=["_index"])._index()
    missing = [t for t, m in v.items() if not (m or {}).get("aggregation")]
    assert missing == [], f"{len(missing)} token(s) undeclared: {missing[:5]}"
    assert len(v) >= 70


def test_an_unknown_token_returns_none_rather_than_a_default():
    """⛔⭐ THE DEFAULT IS THE DEFECT. An unclassified token taking `sum` would
    silently triple a stock — the exact failure this field exists to prevent."""
    assert FV.aggregation_of("nope.not_a_token") is None


def test_the_classification_is_not_derivable_from_the_prefix():
    """⭐⭐ THE RULING SAYS NOTHING INFERS IT FROM A NAME, and these four are why:
    a prefix rule gets every one of them wrong."""
    assert FV.aggregation_of("mk.dps") == "sum"              # a flow among stocks
    assert FV.aggregation_of("mk.share_price") == "closing"
    assert FV.aggregation_of("sa.arr") == "closing"          # a run rate, not a flow
    assert FV.aggregation_of("po.days_in_period") == "period_defined"


def test_flows_stocks_and_derived_are_all_populated():
    v, _g, _r = __import__(
        "services.api.modules.financials.ratio_registry",
        fromlist=["_index"])._index()
    kinds = {}
    for m in v.values():
        kinds[m["aggregation"]] = kinds.get(m["aggregation"], 0) + 1
    for k in ("sum", "closing", "derived"):
        assert kinds.get(k, 0) > 5, kinds


# ── ruling 6 · aggregation obeys the classification ────────────────────────

def test_flows_sum_across_the_bucket():
    r = FV.aggregate_statements(_ds("quarterly", Q), "annual")
    assert r["blocks"]["income_statement"]["revenue"]["2024"] == 400.0
    assert r["blocks"]["cash_flow"]["capex"]["2024"] == 40.0


def test_coarsening_a_balance_sheet_does_not_multiply_assets():
    """⭐⭐ THE LOAD-BEARING ASSERTION. Summing four quarterly balance sheets
    quadruples assets AND liabilities, so the result still balances — a
    reconciliation check would not catch it."""
    r = FV.aggregate_statements(_ds("quarterly", Q, cash=1000.0), "annual")
    assert r["blocks"]["balance_sheet"]["cash"]["2024"] == 1000.0
    assert r["blocks"]["balance_sheet"]["equity"]["2024"] == 5000.0


def test_a_stock_takes_the_LAST_sub_period_not_the_first_or_the_mean():
    ds = _ds("quarterly", Q)
    ds["balance_sheet"]["cash"] = {"20241": 100.0, "20242": 200.0,
                                   "20243": 300.0, "20244": 400.0}
    r = FV.aggregate_statements(ds, "annual")
    got = r["blocks"]["balance_sheet"]["cash"]["2024"]
    assert got == 400.0, f"closing is 400; got {got} (mean would be 250)"


def test_a_derived_line_is_never_aggregated_directly():
    """⭐ It is recomputed from aggregated inputs; aggregating it would be a
    second definition of it."""
    assert FV.aggregation_of("bs.total_assets") == "derived"
    # ⭐ A NON-EMPTY BUCKET. A first version passed `[]`, so the loop never ran
    # and nothing raised — the test passed for the wrong reason.
    b = FV.bucket(Q, "quarterly", "annual")
    with pytest.raises(ValueError):
        FV.aggregate_series({str(p): 1.0 for p in Q}, b, "derived")


def test_absence_propagates_through_a_bucket():
    ds = _ds("quarterly", Q)
    ds["income_statement"]["revenue"]["20243"] = None
    r = FV.aggregate_statements(ds, "annual")
    assert r["blocks"]["income_statement"]["revenue"]["2024"] is None


def test_a_rate_that_changed_mid_bucket_is_absent_not_averaged():
    b = FV.bucket(Q, "quarterly", "annual")
    same = FV.aggregate_series({str(p): 0.25 for p in Q}, b, "constant")
    assert same["2024"] == 0.25
    moved = dict({str(p): 0.25 for p in Q}, **{"20243": 0.30})
    assert FV.aggregate_series(moved, b, "constant")["2024"] is None


# ── the target encoding ─────────────────────────────────────────────────────

def test_aggregated_periods_are_encoded_at_the_TARGET_frequency():
    """⛔⭐⭐ THE DEFECT THIS LANE SHIPPED AND CAUGHT. A first version built a
    monthly→quarterly key as year*100+q, giving 202401 — six digits, which IS the
    monthly encoding. `derive_frequency` reads frequency from DIGIT COUNT, so the
    aggregated series would have declared itself monthly to every consumer."""
    b = FV.bucket(M12, "monthly", "quarterly")
    keys = [x["period"] for x in b]
    assert keys == [20241, 20242, 20243, 20244]
    assert PR.derive_frequency(keys) == "quarterly"
    assert PR.format_period(keys[0], "quarterly") == "2024Q1"


def test_a_coarser_view_cannot_be_built_from_finer_data_by_aggregation():
    with pytest.raises(ValueError):
        FV.bucket(Q, "quarterly", "monthly")


# ── ruling 7 · partial buckets ──────────────────────────────────────────────

def test_eight_months_leaves_the_third_quarter_partial():
    b = FV.bucket([202401 + i for i in range(8)], "monthly", "quarterly")
    assert [x["have"] for x in b] == [3, 3, 2]
    assert [x["partial"] for x in b] == [False, False, True]


def test_a_partial_bucket_is_reported_by_period_not_merely_counted():
    """⭐ The surface has to name WHICH bucket is partial, or the caveat cannot
    be attached to the figure it qualifies."""
    r = FV.aggregate_statements(
        _ds("monthly", [202401 + i for i in range(8)]), "quarterly")
    assert r["partial"] == [20243]


def test_a_partial_flow_sums_only_what_is_there_and_says_so():
    r = FV.aggregate_statements(
        _ds("monthly", [202401 + i for i in range(8)]), "quarterly")
    assert r["blocks"]["income_statement"]["revenue"]["20243"] == 200.0
    assert 20243 in r["partial"]


def test_a_partial_stock_is_the_latest_reported_position():
    """⭐ A closing balance on an incomplete quarter is still a true statement
    about a date — unlike a partial flow, which is a smaller number than the
    quarter will turn out to hold."""
    ds = _ds("monthly", [202401 + i for i in range(8)])
    ds["balance_sheet"]["cash"]["202408"] = 7777.0
    r = FV.aggregate_statements(ds, "quarterly")
    assert r["blocks"]["balance_sheet"]["cash"]["20243"] == 7777.0


# ── interpolation · ruling 1 as amended ─────────────────────────────────────

def test_interpolated_is_a_status_and_imputed_is_still_forbidden():
    """⭐⭐ THE RECONCILIATION, ASSERTED. §8a's refusal is unchanged; a different
    act got a different name."""
    assert D.INTERPOLATED in D.DATA_STATUSES
    assert "imputed" not in D.DATA_STATUSES
    assert "imputed_status" in D.FORBIDDEN


def test_interpolated_is_weaker_than_estimated_and_degrades_a_result():
    assert D.weakest_status("observed", D.INTERPOLATED) == D.INTERPOLATED
    assert D.weakest_status("estimated", D.INTERPOLATED) == D.INTERPOLATED
    assert D.weakest_status(D.INTERPOLATED, "unavailable") == "unavailable"


def test_a_flow_divides_evenly_and_every_child_is_marked():
    out = FV.interpolate_series({"20241": 300.0}, [20241], "monthly",
                                "quarterly", "sum")
    assert [v["value"] for v in out.values()] == [100.0, 100.0, 100.0]
    assert all(v["status"] == FV.INTERPOLATED for v in out.values())
    assert all(v["method"] == FV.LINEAR for v in out.values())


def test_a_stock_holds_its_level_and_is_not_divided():
    """⛔ Dividing a closing balance by three is the tripling defect in reverse."""
    out = FV.interpolate_series({"20241": 1200.0}, [20241], "monthly",
                                "quarterly", "closing")
    assert [v["value"] for v in out.values()] == [1200.0, 1200.0, 1200.0]


def test_the_last_child_of_a_stock_is_reported_data_and_is_not_marked():
    """⭐ The closing position IS true at the last child — marking it estimated
    would understate what the client actually supplied."""
    out = FV.interpolate_series({"20241": 1200.0}, [20241], "monthly",
                                "quarterly", "closing")
    ks = sorted(out)
    assert out[ks[-1]]["status"] is None
    assert out[ks[0]]["status"] == FV.INTERPOLATED


def test_a_rate_is_carried_through_and_is_NOT_marked_as_estimated():
    out = FV.interpolate_series({"20241": 0.25}, [20241], "monthly",
                                "quarterly", "constant")
    assert all(v["value"] == 0.25 for v in out.values())
    assert all(v["status"] is None for v in out.values())


def test_the_status_travels_on_the_figure_not_beside_the_series():
    """⭐⭐ The CXO chose it; a pack recipient did not. A series-level flag is
    lost the moment one number is copied out of it."""
    out = FV.interpolate_series({"20241": 300.0}, [20241], "monthly",
                                "quarterly", "sum")
    for v in out.values():
        assert set(v) == {"value", "status", "method"}


def test_the_method_is_named_on_every_interpolated_figure():
    out = FV.interpolate_series({"20241": 300.0}, [20241], "monthly",
                                "quarterly", "sum")
    assert all(v["method"] == FV.LINEAR for v in out.values())
    assert "not reported data" in FV.METHOD_LABEL[FV.LINEAR]


def test_a_ratio_is_never_interpolated():
    with pytest.raises(ValueError):
        FV.interpolate_series({"20241": 1.0}, [20241], "monthly", "quarterly",
                              "derived")


def test_interpolation_only_goes_finer():
    with pytest.raises(ValueError):
        FV.interpolate_series({"2024": 1.0}, [2024], "annual", "quarterly",
                              "sum")


def test_a_non_linear_method_is_refused_and_the_refusal_carries_its_ruling():
    """⭐ The refusal ships as a VALUE — a capability simply missing reads as
    unbuilt and the next lane builds it."""
    with pytest.raises(ValueError):
        FV.interpolate_series({"20241": 1.0}, [20241], "monthly", "quarterly",
                              "sum", method="seasonal")
    r = FV.REFUSED_METHODS["seasonal"]
    assert r["refused"] and r["ruling"]
    low = r["reason"].lower()
    assert "two years" in low and "declares" in low


def test_absence_survives_interpolation():
    out = FV.interpolate_series({"20241": None}, [20241], "monthly",
                                "quarterly", "sum")
    assert all(v["value"] is None and v["status"] is None
               for v in out.values())
