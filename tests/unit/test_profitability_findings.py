"""Findings, margin trend and mix-shift series — derived, gated, and honest.

⭐⭐ THE LANE'S PURPOSE, AND THE PROPERTY THAT MAKES IT SAFE. Every other panel
restates what the client uploaded plus arithmetic they can do themselves. A
findings panel states what the data SAYS — which is only defensible if no
sentence is ever hand-authored for a company. Each one here is a template over
values the payload already carries, gated on a condition read from that payload.

⭐ THE TEST THAT MATTERS MOST IS THE EMPTY ONE. On a company where the pattern
is absent the module must produce NOTHING. A findings engine that always finds
something is a horoscope.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="find-", suffix=".db"))

import pytest

from services.api.modules.financials import router as R


def _lines(gm_series, ebit_series, periods, code="L1"):
    """A `block` shaped exactly as the endpoint builds one."""
    by_period = {}
    for i, p in enumerate(periods):
        by_period[p] = {
            "lines": {code: {
                "gross_profit": {"available": gm_series[i] is not None,
                                 "value": 1.0, "margin": gm_series[i]},
                "allocated_ebit": {"available": ebit_series[i] is not None,
                                   "value": ebit_series[i]},
            }},
            "mix": {"available": False, "value": {}},
            "concentration": {"available": False},
        }
    return {"periods": list(periods), "by_period": by_period}


PERIODS = (2022, 2023, 2024, 2025)


# ── direction ──────────────────────────────────────────────────────────────

def test_a_flat_series_reads_as_flat_despite_floating_point():
    """⭐⭐ THE DEFECT THIS FUNCTION SHIPPED WITH. A gross margin held at exactly
    31% arrives as 0.31, 0.3100000000000001, 0.31 — it is computed as
    (revenue − cost) / revenue — and `==` reported the series as MIXED. The
    trend panel's entire claim is that the margin is HOLDING, so a flat series
    that reads as noise destroys the finding."""
    assert R._direction([0.31, 0.3100000000000001, 0.31, 0.30999999999999994]) \
        == R._FLAT


def test_direction_is_never_going_the_other_way_not_moving_every_step():
    """⭐ 50%, 50%, 51%, 52% is rising. `all(b > a)` rejected it for the one
    equal pair and called it mixed."""
    assert R._direction([0.50, 0.50, 0.51, 0.52]) == R._RISING
    assert R._direction([0.52, 0.52, 0.51, 0.50]) == R._FALLING
    assert R._direction([0.50, 0.60, 0.40, 0.55]) == R._MIXED


def test_a_single_point_has_no_direction():
    assert R._direction([0.5]) is None
    assert R._direction([]) is None


# ── the trend ──────────────────────────────────────────────────────────────

def test_the_divergence_is_named_when_margin_holds_and_ebit_falls():
    """⭐⭐ THE PATTERN THE MODULE EXISTS TO SURFACE. Neither series says it
    alone: the margin says the product is fine, the EBIT says it is not, and
    the finding is that BOTH are true."""
    block = _lines([0.31] * 4, [4.6, -0.8, -8.2, -17.6], PERIODS)
    trend = R._margin_trend(block, PERIODS)["L1"]
    assert trend["gross_margin_direction"] == R._FLAT
    assert trend["allocated_ebit_direction"] == R._FALLING
    assert trend["diverging"] is True


def test_a_line_whose_margin_also_collapses_is_not_diverging():
    """⭐ That is an ordinary deteriorating product. Calling it a divergence
    would make the label meaningless."""
    block = _lines([0.40, 0.34, 0.28, 0.20], [10.0, 5.0, 1.0, -3.0], PERIODS)
    assert R._margin_trend(block, PERIODS)["L1"]["diverging"] is False


# ── findings ───────────────────────────────────────────────────────────────

def test_the_trajectory_finding_needs_more_than_two_periods():
    """⭐⭐ THE REASON THE SEED WAS EXTENDED. With two periods the module may
    say "this is loss-making"; it may NOT say "this has been deteriorating for
    three years", because nobody can see a trend in one step."""
    two = _lines([0.31, 0.31], [4.6, -17.6], (2024, 2025))
    two["trend"] = R._margin_trend(two, (2024, 2025))
    ids = {f["id"].split(":")[0] for f in R._findings(two, {})}
    assert "reversal_trajectory" not in ids
    assert "reversal" in ids, "the plain reversal must still be stated"

    four = _lines([0.31] * 4, [4.6, -0.8, -8.2, -17.6], PERIODS)
    four["trend"] = R._margin_trend(four, PERIODS)
    ids4 = {f["id"].split(":")[0] for f in R._findings(four, {})}
    assert "reversal_trajectory" in ids4


def test_every_finding_carries_the_derivation_that_produced_it():
    """⭐ A sentence a reader cannot audit is a sentence they must take on
    trust, which is the opposite of this product."""
    block = _lines([0.31] * 4, [4.6, -0.8, -8.2, -17.6], PERIODS)
    block["trend"] = R._margin_trend(block, PERIODS)
    found = R._findings(block, {})
    assert found
    for f in found:
        assert f["derivation"] and len(f["derivation"]) > 20
        assert f["sentence"] and f["severity"] in (1, 2, 3)


def test_no_sentence_is_keyed_to_a_company():
    """⭐⭐ THE PROHIBITION, ASSERTED ON THE SOURCE. A finding hand-written for
    Meridian is a demo, not a capability — and it would be indistinguishable
    from a derived one on the screen."""
    import ast
    import inspect
    src = inspect.getsource(R._findings)
    tree = ast.parse(src.lstrip())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            for banned in ("meridian", "pl-ctrl", "control electronics",
                           "drive systems", "halcyon"):
                assert banned not in low, f"hand-authored text: {node.value!r}"


def test_a_company_without_the_pattern_produces_nothing():
    """⭐⭐ THE MOST IMPORTANT TEST IN THIS FILE. Every line healthy, margins
    steady, no concentration: the honest output is SILENCE. A findings engine
    that always finds something is a horoscope."""
    block = _lines([0.40] * 4, [10.0, 10.0, 10.0, 10.0], PERIODS)
    block["trend"] = R._margin_trend(block, PERIODS)
    assert R._findings(block, {}) == []


def test_a_line_that_is_simply_weak_is_not_called_a_reversal():
    """⭐ Negative EBIT with a 9% gross margin is a bad product, not a line
    being crushed by shared cost. Naming it a reversal would send management
    after the wrong cause."""
    block = _lines([0.09] * 4, [1.0, -1.0, -3.0, -6.0], PERIODS)
    block["trend"] = R._margin_trend(block, PERIODS)
    assert R._findings(block, {}) == []


def test_findings_are_ordered_by_severity():
    block = _lines([0.31] * 4, [4.6, -0.8, -8.2, -17.6], PERIODS)
    block["trend"] = R._margin_trend(block, PERIODS)
    sev = [f["severity"] for f in R._findings(block, {})]
    assert sev == sorted(sev)


# ── the mix-shift series ───────────────────────────────────────────────────

def test_a_two_point_share_move_is_material_despite_floating_point():
    """⭐⭐ 20% to 22% arrives as 0.019999999999999997, and `< 0.02` dropped the
    finding on the exact case it was written for."""
    block = {
        "periods": [2024, 2025],
        "by_period": {
            2024: {"mix": {"available": True, "value": {"L1": 0.20, "L2": 0.30}},
                   "lines": {}, "concentration": {"available": False}},
            2025: {"mix": {"available": True, "value": {"L1": 0.22, "L2": 0.28}},
                   "lines": {}, "concentration": {"available": False}},
        },
        # a realistic trend entry: the findings code reads more than the
        # direction, and a partial one must not raise
        "trend": {"L1": {"gross_margin_direction": R._FALLING,
                         "gross_margin": [0.40, 0.36],
                         "allocated_ebit": [5.0, 4.0]},
                  "L2": {"gross_margin_direction": R._RISING,
                         "gross_margin": [0.30, 0.34],
                         "allocated_ebit": [6.0, 7.0]}},
    }
    from services.api.modules.financials import dimensional_analytics as A
    block["mix_shift_series"] = R._mix_shift_series(A, block, [2024, 2025])
    ids = {f["id"] for f in R._findings(block, {})}
    assert "mix_dilutive:L1" in ids, "the gaining, thinning line was not named"
    assert "mix_accretive:L2" in ids, "the opposite trade was not named"


def test_the_series_spans_every_consecutive_pair():
    from services.api.modules.financials import dimensional_analytics as A
    block = {"periods": list(PERIODS), "by_period": {
        p: {"mix": {"available": True, "value": {"L1": 0.2}}} for p in PERIODS}}
    series = R._mix_shift_series(A, block, PERIODS)
    assert [(s["from_period"], s["to_period"]) for s in series] == [
        (2022, 2023), (2023, 2024), (2024, 2025)]
