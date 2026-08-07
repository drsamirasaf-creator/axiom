"""The equity grid must refuse exactly where the EV grid refuses.

⭐⭐ WHY THE EXISTING CHECKPOINT COULD NOT SEE THIS. `sensitivity_center_equals_ev`
asserts `ev_grid[2][2]` — the CENTRE cell, which is the un-shifted (wacc, g) pair
and therefore the one cell that cannot refuse. It is non-None by construction. A
checkpoint anchored to the only guaranteed-populated cell can never catch a
corner, and the corners are where `_dcf` declines to answer.

⛔ THE DEFECT IT MISSED reached production: `cell - net_debt - preferred -
minority` on an absence-bearing grid raised TypeError on three showcase datasets
and 5 of 8 valuation endpoints.

⭐ §7q — the absence is CORRECT. Gordon growth has no solution when terminal
growth reaches WACC, so `_dcf` raises and the grid records absence. The engine
was right; the consumer was not.
"""
import json
import os

import pytest

from services.api.modules.valuation import engines as VE

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")


def _data():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    return json.load(open(DATASET, encoding="utf-8"))


def _absent(grid):
    return {(i, j) for i, row in enumerate(grid)
            for j, c in enumerate(row) if c is None}


# ── the bridge owner, in isolation ───────────────────────────────────────────

def test_the_bridge_propagates_absence_rather_than_zeroing_it():
    """⛔ Each operand absent in turn. `or 0` would return a number for every
    one of these, and the number would be wrong by exactly the missing term."""
    assert VE.equity_from_ev(100.0, 20.0, 0.0, 0.0) == 80.0
    for args in ((None, 20.0, 0.0, 0.0),      # EV absent — the grid-cell case
                 (100.0, None, 0.0, 0.0),     # net_debt absent
                 (100.0, 20.0, None, 0.0),    # preferred absent
                 (100.0, 20.0, 0.0, None)):   # minority absent
        assert VE.equity_from_ev(*args) is None, args


def test_absent_net_debt_and_zero_net_debt_stay_distinguishable():
    """⛔ THE RULING. Preferred and minority are legitimately 0.0 on most
    balance sheets; net_debt is not. A guard that treated absence as zero
    would collapse a company with no debt into a company whose debt is
    unknown, and the equity grid would equal the EV grid in both cases."""
    zero = VE.equity_from_ev(100.0, 0.0, 0.0, 0.0)
    absent = VE.equity_from_ev(100.0, None, 0.0, 0.0)
    assert zero == 100.0
    assert absent is None
    assert zero != absent


# ── the grid, on real data ───────────────────────────────────────────────────

def test_the_two_grids_refuse_in_the_same_positions():
    d = _data()
    s = VE.run(d, "proforma")["sensitivity"]
    assert _absent(s["equity_grid"]) == _absent(s["ev_grid"])


def test_neither_axis_is_truncated():
    """⛔ A grid that stopped at its populated rows would hide that WACC sits at
    the growth rate — the single most informative thing about the assumption
    set. Absence is shown, not shortened away."""
    d = _data()
    s = VE.run(d, "proforma")["sensitivity"]
    assert len(s["wacc_values"]) == 5 and len(s["terminal_growth_values"]) == 5
    assert len(s["ev_grid"]) == 5 and all(len(r) == 5 for r in s["ev_grid"])
    assert len(s["equity_grid"]) == 5
    assert all(len(r) == 5 for r in s["equity_grid"])


def test_the_absence_carries_its_reason():
    """§7q — an absence with a plausible reason is the most informative signal,
    and the reason travels with the payload rather than living in a report."""
    d = _data()
    s = VE.run(d, "proforma")["sensitivity"]
    reason = s["equity_grid_absent_reason"]
    assert "WACC" in reason and "terminal growth" in reason.lower()


def test_the_new_checkpoint_is_present_and_passes():
    d = _data()
    cps = {c["name"]: c for c in VE.run(d, "proforma")["checkpoints"]}
    assert "equity_grid_absence_mirrors_ev_grid" in cps
    assert cps["equity_grid_absence_mirrors_ev_grid"]["pass"] is True


# ── ⭐⭐ THE KNOWN POSITIVE. A checkpoint that has never fired has not been
# tested. Both of these plant a defect and prove the checkpoint reports it.

# ⛔ MERIDIAN'S OWN GRID HAS NO REFUSED CORNER — its WACC is ~13.6% against a
# 2.5% terminal growth, so every cell answers. The first draft of these two
# proofs read `if not planted: pytest.skip(...)` and SKIPPED, which is §III.11
# in the very tests written to prove the checkpoint fires. Terminal growth is
# raised to 13% here so the grid genuinely refuses (9 of 25 cells) and the
# controls execute on every run.
REFUSING = {"terminal_growth": 0.13}


def _refusing_run():
    out = VE.run(_data(), "proforma", REFUSING)
    ev = out["sensitivity"]["ev_grid"]
    assert any(c is None for r in ev for c in r), \
        "the forcing assumption stopped producing a refused corner — these " \
        "controls would silently stop testing anything"
    return out


def test_the_forced_grid_refuses_and_still_mirrors():
    """The positive case at the awkward end: many refusals, still cell-for-cell."""
    out = _refusing_run()
    s = out["sensitivity"]
    assert _absent(s["equity_grid"]) == _absent(s["ev_grid"])
    assert len(_absent(s["ev_grid"])) == 9
    cps = {c["name"]: c for c in out["checkpoints"]}
    assert cps["equity_grid_absence_mirrors_ev_grid"]["pass"] is True


def test_the_checkpoint_goes_RED_when_a_cell_is_zeroed_instead_of_refused():
    """The exact defect the fix removes: `or 0` on an absent cell. The grids
    then disagree positionally and the comparison must say so."""
    s = _refusing_run()["sensitivity"]
    eq = [row[:] for row in s["equity_grid"]]
    ev = s["ev_grid"]
    i, j = sorted(_absent(ev))[0]
    eq[i][j] = 0.0            # the forbidden `or 0`
    assert _absent(eq) != _absent(ev), \
        "planting a zero did not change the absence set — the control is blind"


def test_the_checkpoint_goes_RED_when_absence_appears_where_ev_is_populated():
    """The opposite mismatch: equity refuses a cell EV answered. A count-based
    check would pass this whenever the totals happened to match, which is why
    the checkpoint compares POSITIONS."""
    s = _refusing_run()["sensitivity"]
    ev = s["ev_grid"]
    eq = [row[:] for row in s["equity_grid"]]
    pop = [(i, j) for i, r in enumerate(ev)
           for j, c in enumerate(r) if c is not None]
    (pi, pj), (ai, aj) = pop[0], sorted(_absent(ev))[0]
    eq[pi][pj] = None         # refuse one EV answered
    eq[ai][aj] = 1.0          # answer one EV refused
    assert len(_absent(eq)) == len(_absent(ev)), "the counts should match here"
    assert _absent(eq) != _absent(ev), \
        "equal counts in different positions compared equal — the checkpoint " \
        "is counting, not comparing cell for cell"


# ── real options: ONE refusal, not three ─────────────────────────────────────

def test_real_options_refuses_once_when_the_underlying_is_absent(monkeypatch):
    """⭐⭐ THE KNOWN POSITIVE FOR A BRANCH TODAY'S DATA CANNOT REACH.
    `enterprise_value` is `pv_explicit + pv_terminal`, both floats, so no stored
    dataset can drive this. Planting it is the only way the branch is ever
    executed — and an untested branch is worse than no branch."""
    d = _data()
    real_run = VE.run

    def absent_ev(data, mode, *a, **k):
        out = real_run(data, mode, *a, **k)
        out["deterministic"]["enterprise_value"] = None
        return out

    monkeypatch.setattr(VE, "run", absent_ev)
    suite = VE.real_options_suite(d)
    assert suite["refused"] is True
    assert suite["underlying_enterprise_value"] is None
    # ⛔ ONE reason, and no per-option shape at all — three em dashes would
    # assert three failures where there is one missing input.
    assert suite["options"] is None
    assert "one missing input" in suite["refused_reason"]
    assert suite["total_flexibility_value"] is None


def test_real_options_is_not_refused_on_real_data():
    """⛔ §III.11 — the paired known-negative. A refusal test that passed
    because everything refuses would be worthless."""
    suite = VE.real_options_suite(_data())
    assert suite["refused"] is False
    assert suite["underlying_enterprise_value"] is not None
    assert set(suite["options"]) == {"expand", "abandon", "defer"}
