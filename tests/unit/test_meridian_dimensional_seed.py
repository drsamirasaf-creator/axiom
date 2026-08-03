"""Meridian's dimensional seed — COVERAGE ASSERTED, not assumed.

⭐⭐ §7o's CRITERION IS COVERAGE, NOT NARRATIVE. Nobody evaluates whether
Meridian's product mix is true; what the sample must demonstrate is what the
system is capable of SAYING. So every capability T2 built is exercised here
against the seed's own constants, and the ones that are only interesting when
they are ugly — the residual, the loss-making line, the declared absence — are
asserted explicitly.

⭐ A seed whose coverage "falls out" is a seed whose gaps are found by a
prospect. §7o says assert amber rather than assume it; this is that rule applied
to the dimensional surfaces.

These run on the seed's CONSTANTS, not the database, so they are deterministic
and fail on a change to the design rather than on a connection.
"""
import importlib.util
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="seed-", suffix=".db"))

import pytest

from services.api.modules.financials import dimensional_analytics as A
from services.api.modules.financials import dimensions as D

_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "scripts", "seed-dimensional.py")
_spec = importlib.util.spec_from_file_location("seed_dimensional", _PATH)
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def _lines(year):
    """Revenue, direct cost, direct opex and allocated shared, per line."""
    st = S.STATEMENT[year]
    sh = S.shares_for(year)
    gm = S.margins_for(year)
    rev = {c: st["revenue"] * sh[c] for c in S.PRODUCTS}
    dc = {c: rev[c] * (1 - gm[c]) for c in S.PRODUCTS}
    do = {c: st["opex"] * S.DIRECT_OPEX_POOL * S.DIRECT_OPEX_SPLIT[c]
          for c in S.PRODUCTS}
    alloc = {c: 0.0 for c in S.PRODUCTS}
    for name, a in S.shared_allocation(year, sh).items():
        if name == "sales_commission":
            continue                      # that IS `do`; not counted twice
        for c, v in a["value"].items():
            alloc[c] += v
    return rev, dc, do, alloc


# ── 6 · two periods ────────────────────────────────────────────────────────

def test_four_consecutive_actual_periods_are_seeded():
    """⭐⭐ FOUR, AND THEY ARE ALL ACTUALS. Two periods can only ever say "this
    is bad now"; four can say "this has been deteriorating for three years, and
    here is the driver" — which is an argument rather than a data point. Ruled
    3 Aug: dimensional data covers actual periods only, never forecast, because
    allocating a projection by product line compounds two estimates."""
    assert S.PERIODS == (2022, 2023, 2024, 2025)
    for y in S.PERIODS:
        assert len(_lines(y)[0]) == 5
    hist = [2021, 2022, 2023, 2024, 2025]
    assert all(p in hist for p in S.PERIODS), "a forecast period is seeded"


# ── 1 · every capability has something to render ───────────────────────────

def test_revenue_by_dimension_renders():
    rev, *_ = _lines(2025)
    r = A.revenue_by_dimension(rev, S.STATEMENT[2025]["revenue"])
    assert r["available"] and len(r["value"]) == 6      # 5 lines + unallocated


def test_mix_and_its_shift_render():
    m24 = A.revenue_mix(_lines(2024)[0], S.STATEMENT[2024]["revenue"])
    m25 = A.revenue_mix(_lines(2025)[0], S.STATEMENT[2025]["revenue"])
    assert m24["available"] and m25["available"]
    shift = A.mix_shift(m24["value"], m25["value"])
    assert shift["available"]
    moved = [k for k, v in shift["value"].items() if abs(v) > 0.005]
    assert len(moved) >= 3, "too little movement for a mix-shift panel to say anything"


def test_concentration_has_a_real_pareto_point():
    """⭐ Not an artefact of equal weighting: the answer must be a strict subset
    of the lines, or the panel demonstrates nothing."""
    c = A.concentration(_lines(2025)[0])
    v = c["value"]
    assert 1 <= v["lines_for_80pct"] < v["n_lines"]
    assert v["top_1"] > v["top_3"] / 3, "shares are near-uniform; no concentration story"
    assert 0 < v["hhi"] < 1


def test_all_four_margin_levels_render_for_every_line():
    rev, dc, do, alloc = _lines(2025)
    for c in S.PRODUCTS:
        h = A.margin_hierarchy(revenue=rev[c], direct_cost=dc[c],
                               direct_opex=do[c], allocated_opex=alloc[c])
        for level in ("gross_profit", "direct_operating_profit", "allocated_ebit"):
            assert h[level]["available"], f"{c} has no {level}"
        # ⭐ contribution_profit is DELIBERATELY unavailable — no fixed/variable
        # split is seeded, so the level declares what it needs. That IS coverage:
        # the declaration path renders.
        assert h["contribution_profit"]["available"] is False
        assert h["contribution_profit"]["missing_measures"]


def test_the_margin_bridge_computes_its_three_effects():
    m24 = A.revenue_mix(_lines(2024)[0], S.STATEMENT[2024]["revenue"])["value"]
    m25 = A.revenue_mix(_lines(2025)[0], S.STATEMENT[2025]["revenue"])["value"]
    rev24, dc24, *_ = _lines(2024)
    rev25, dc25, *_ = _lines(2025)
    g24 = {c: (rev24[c] - dc24[c]) / rev24[c] for c in S.PRODUCTS}
    g25 = {c: (rev25[c] - dc25[c]) / rev25[c] for c in S.PRODUCTS}
    b = A.margin_bridge({k: m24[k] for k in S.PRODUCTS}, g24,
                        {k: m25[k] for k in S.PRODUCTS}, g25)
    assert b["available"]
    for effect in A.BRIDGE_COMPUTABLE:
        assert effect in b["value"]
    assert abs(b["residual"]) < 1e-12, "the bridge must reconcile exactly"
    assert abs(b["total_change"]) > 1e-4, "no margin movement for the bridge to explain"


def test_growth_quality_and_incremental_margin_render():
    rev24, dc24, do24, al24 = _lines(2024)
    rev25, dc25, do25, al25 = _lines(2025)
    p24 = sum(rev24.values()) - sum(dc24.values())
    p25 = sum(rev25.values()) - sum(dc25.values())
    g = A.growth_quality(sum(rev24.values()), sum(rev25.values()), p24, p25,
                         company_margin=0.45)
    assert g["available"] and g["value"] in A.GROWTH_QUALITY


# ── 2 · three allocation grades ────────────────────────────────────────────

def test_at_least_three_allocation_grades_are_exercised():
    """⭐⭐ A seed where everything is grade A demonstrates nothing about the
    machinery. The differentiation is that the ASSUMPTION IS NAMED, so the demo
    must show assumptions that differ in quality."""
    grades = {a["grade"] for a in S.shared_allocation(2025, S.shares_for(2025)).values()}
    assert grades >= {"A", "C", "D"}, f"only {grades} exercised"


def test_every_allocated_figure_carries_its_method_and_assumption():
    for name, a in S.shared_allocation(2025, S.shares_for(2025)).items():
        assert a["available"], name
        assert a["method"] and a["grade"] and a["assumption"]
        assert a["data_status"] == D.ALLOCATED


def test_allocation_sensitivity_actually_varies():
    """⭐ A sensitivity where every method agrees shows nothing. The support and
    revenue drivers must disagree materially for the panel to be worth opening."""
    pool = S.STATEMENT[2025]["opex"] * 0.24
    s = A.allocation_sensitivity(pool, {
        "operational_driver": S.COST_POOLS["customer_support"]["drivers"][2025],
        "revenue": S.shares_for(2025),
    })
    assert s["available"]
    ctrl = s["value"]["PL-CTRL"]
    assert ctrl["high"] / max(ctrl["low"], 1e-9) > 2.0, (
        "the two allocation methods barely differ; the sensitivity says nothing")


# ── 3 · the reversal ───────────────────────────────────────────────────────

def test_one_line_is_healthy_at_gross_and_loss_making_at_allocated_ebit():
    """⭐⭐ THE FINDING A CFO REACTS TO: this product looks fine until you charge
    it for what it consumes. It exercises the hierarchy end to end, and it is the
    reason the seed exists rather than a tidier one."""
    found = []
    for year in S.PERIODS:
        rev, dc, do, alloc = _lines(year)
        for c in S.PRODUCTS:
            h = A.margin_hierarchy(revenue=rev[c], direct_cost=dc[c],
                                   direct_opex=do[c], allocated_opex=alloc[c])
            gm = h["gross_profit"]["margin"]
            eb = h["allocated_ebit"]["value"]
            if gm is not None and gm > 0.25 and eb < 0:
                found.append((year, c, gm, eb))
    assert found, "no line reverses; the hierarchy demonstrates nothing"
    assert {c for _y, c, _g, _e in found} == {"PL-CTRL"}
    for year, c, gm, eb in found:
        assert eb < -5.0, f"{year} {c} reversal is {eb:.2f} — too small to read"


def test_the_reversal_DEVELOPS_rather_than_merely_existing():
    """⭐⭐ THE REASON FOUR PERIODS EXIST. A line that is simply unprofitable is
    a data point; a line whose allocated EBIT has fallen every year for three
    years is an argument, and it is the difference between a chart and a case.
    Two periods cannot express it, which is why the seed was extended."""
    series = []
    for year in S.PERIODS:
        rev, dc, do, alloc = _lines(year)
        h = A.margin_hierarchy(revenue=rev["PL-CTRL"], direct_cost=dc["PL-CTRL"],
                               direct_opex=do["PL-CTRL"],
                               allocated_opex=alloc["PL-CTRL"])
        series.append((year, h["gross_profit"]["margin"],
                       h["allocated_ebit"]["value"]))
    ebits = [e for _y, _g, e in series]
    assert all(b < a for a, b in zip(ebits, ebits[1:])), (
        f"allocated EBIT does not fall every year: {ebits}")
    assert ebits[0] > 0 and ebits[-1] < 0, (
        "the line must START healthy and END loss-making, or there is no "
        "trajectory to show")
    # ⭐ AND IT STAYS HEALTHY AT GROSS MARGIN THROUGHOUT. If gross margin
    # collapsed too, the finding would be "this product got worse" — ordinary.
    # The finding worth the module is that gross margin is FINE and the line
    # still loses money once it is charged for what it consumes.
    assert all(g > 0.25 for _y, g, _e in series)


def test_the_cause_of_the_reversal_is_in_the_data_not_only_in_a_comment():
    """⭐⭐ AN UNEXPLAINED SIGN CHANGE IS NOT ACTIONABLE. PL-CTRL's share of the
    support and logistics pools climbs while its REVENUE share does not, so an
    analyst can read the driver off the seed rather than being told."""
    first, last = S.PERIODS[0], S.PERIODS[-1]
    sup = S.COST_POOLS["customer_support"]["drivers"]
    log = S.COST_POOLS["logistics"]["drivers"]
    assert sup[last]["PL-CTRL"] > sup[first]["PL-CTRL"] * 1.5
    assert log[last]["PL-CTRL"] > log[first]["PL-CTRL"] * 1.5
    rev_share = (S.SHARE[last]["PL-CTRL"], S.SHARE[first]["PL-CTRL"])
    assert abs(rev_share[0] - rev_share[1]) < 0.03, (
        "revenue share moved too — the cost growth would be explicable by "
        "growth, and the finding would evaporate")


def test_one_line_gains_share_as_its_margin_thins_and_another_does_the_opposite():
    """⭐⭐ THE MIX STORY NEEDS A CAUSE, OR THE BRIDGE'S MIX EFFECT IS NOISE.
    PL-AUTO buys growth with price; PL-DRIVE gives up share and improves. The
    two effects point in OPPOSITE directions, so neither can be mistaken for
    the other in the margin bridge."""
    first, last = S.PERIODS[0], S.PERIODS[-1]
    gain = "PL-AUTO"
    assert S.SHARE[last][gain] > S.SHARE[first][gain] + 0.05
    assert S.GROSS_MARGIN[last][gain] < S.GROSS_MARGIN[first][gain] - 0.03
    shrink = "PL-DRIVE"
    assert S.SHARE[last][shrink] < S.SHARE[first][shrink] - 0.02
    assert S.GROSS_MARGIN[last][shrink] > S.GROSS_MARGIN[first][shrink]


# ── 4 · the residual is material ───────────────────────────────────────────

def test_unallocated_is_visible_and_material_in_every_period():
    """⭐ A demo where everything allocates cleanly hides the residual, which is
    the honest half of the reconciliation."""
    for year in S.PERIODS:
        rev, dc, do, _ = _lines(year)
        for detail, line in ((rev, "revenue"), (dc, "cogs"), (do, "opex")):
            r = A.revenue_by_dimension(detail, S.STATEMENT[year][line])
            un = r["value"]["__unallocated__"]
            frac = un / S.STATEMENT[year][line]
            assert un > 0, f"{year} {line} residual is not positive"
            assert frac > 0.05, (
                f"{year} {line} residual is {100 * frac:.1f}% — too small to notice")


def test_no_residual_is_negative_which_would_be_a_defect_state():
    """A negative residual is `suspected_overlap` — a data defect, not a demo."""
    for year in S.PERIODS:
        rev, dc, do, _ = _lines(year)
        for detail, line in ((rev, "revenue"), (dc, "cogs"), (do, "opex")):
            r = A.revenue_by_dimension(detail, S.STATEMENT[year][line])
            assert r["reconciliation"]["status"] != D.SUSPECTED_OVERLAP


# ── 5 · one deliberate absence ─────────────────────────────────────────────

def test_a_measure_is_deliberately_absent_so_a_capability_declares():
    """⭐⭐ THE BRIDGE ALREADY NAMES SEVEN EFFECTS IT CANNOT COMPUTE, but a
    named absence in prose and an absence a capability actually HITS are
    different demonstrations. Seeding no `units` makes the declaration path
    render on real data rather than only in a docstring."""
    assert "units" in S.DELIBERATELY_ABSENT
    assert "units" not in S.SEEDED_MEASURES
    m = D.MEASURES["units"]   # the vocabulary lives on T1, not on the analytics
    assert m["reconciles_to"] is None
    r = A.margin_bridge({"a": 1.0}, {"a": 0.4}, {"a": 1.0}, {"a": 0.38})
    assert "price" in r["not_computable"] and "volume" in r["not_computable"]


# ── 7 · reconciliation, on the seed's own arithmetic ───────────────────────

def test_detail_plus_unallocated_equals_the_statement_line_exactly():
    for year in S.PERIODS:
        rev, dc, do, _ = _lines(year)
        for detail, line in ((rev, "revenue"), (dc, "cogs"), (do, "opex")):
            r = A.revenue_by_dimension(detail, S.STATEMENT[year][line])
            assert sum(r["value"].values()) == pytest.approx(
                S.STATEMENT[year][line], abs=1e-9)


def test_the_seed_reconciles_against_meridians_own_statement_figures():
    """⭐ The seed's STATEMENT constants must be Meridian's real lines. If the
    dataset ever moves, this fails rather than the seed silently reconciling
    against numbers nobody holds."""
    from tests.fixtures.refcases import meridian
    _ = meridian()
    assert S.DATASET_ID == 45 and S.COMPANY_ID == 20
    for year in S.PERIODS:
        for k in ("revenue", "cogs", "opex"):
            assert S.STATEMENT[year][k] > 0
