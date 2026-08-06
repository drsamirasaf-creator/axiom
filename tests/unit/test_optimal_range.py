"""The optimal range: shaped from `frontier`, never recomputed.

⭐⭐ THE CONTROLS ARE IN MEMORY and each fails on its own input. A frontier fixture
is built by hand so every assertion has a known answer — running the real engine
here would make these tests a measurement of the Monte Carlo rather than of the
shaping, and a seeded 4000-path valuation in a unit test is a minute nobody spends.
"""
import services.api.optimal_range as R


def _pt(de, ev, safety, wacc=0.12, pareto=True, debt=0.0):
    return {"de": de, "wacc": wacc, "value_mean_ev": ev,
            "safety_tail_margin": safety, "debt_recap": debt, "std": 1.0,
            "objective": 0.0, "pareto_efficient": pareto}


def _frontier(points, current_de, recommended, lam=0.5):
    return {"risk_aversion_lambda": lam, "mode": "proforma",
            "current_de": current_de, "points": points,
            "recommended": recommended, "narrative": ["n"],
            "checkpoints": [], "all_checkpoints_pass": True}


# ── the range ───────────────────────────────────────────────────────────────

def test_the_current_point_is_carried_when_the_grid_evaluated_it():
    cur = _pt(0.6, 3215.4, 1662.1)
    pts = [_pt(0.0, 2578.8, 2312.7), cur, _pt(1.0, 3496.4, 1364.1)]
    out = R.build_range(_frontier(pts, 0.6, pts[0]))
    assert out["current_evaluated"] is True
    assert out["current"]["de"] == 0.6
    assert out["current"]["value_mean_ev"] == 3215.4


def test_a_current_level_the_grid_never_evaluated_is_declared_not_omitted():
    """⭐ The showcase company stands at 0.60 and the default grid steps by 0.25.
    Silently dropping "you are here" leaves a range with no anchor and reads as a
    product defect rather than as a missing evaluation."""
    pts = [_pt(0.5, 3130.8, 1750.6), _pt(0.75, 3330.5, 1540.7)]
    out = R.build_range(_frontier(pts, 0.6, pts[0]))
    assert out["current_evaluated"] is False
    assert out["current"] is None
    assert out["current_de"] == 0.6      # still reported, so the surface can say so


def test_the_nearest_point_is_never_substituted_for_the_current_one():
    """⛔ A nearest-match fallback would tell the reader what they are worth at a
    leverage level they are not at, with nothing on the surface saying so."""
    pts = [_pt(0.5, 3130.8, 1750.6)]
    out = R.build_range(_frontier(pts, 0.51, pts[0]))
    assert out["current"] is None


# ── the moves: metric and move as one object ────────────────────────────────

def test_every_move_carries_from_to_and_delta_not_just_a_delta():
    cur = _pt(0.6, 3215.4, 1662.1, wacc=0.1605)
    opt = _pt(0.0, 2578.8, 2312.7, wacc=0.1605)
    out = R.build_range(_frontier([cur, opt], 0.6, opt))
    assert out["moves"], "no moves were produced for two differing points"
    for m in out["moves"]:
        assert {"metric", "label", "from", "to", "delta", "direction"} <= set(m)
    ev = next(m for m in out["moves"] if m["metric"] == "enterprise_value")
    assert ev["from"] == 3215.4 and ev["to"] == 2578.8
    assert abs(ev["delta"] - (2578.8 - 3215.4)) < 1e-9


def test_the_direction_is_stated_and_unchanged_is_its_own_direction():
    """⭐ "safety falls" and "the number goes down" are the same arithmetic and
    opposite readings. And a >= test would report an unchanged metric as rising."""
    cur = _pt(0.6, 3000.0, 1000.0, wacc=0.13)
    opt = _pt(1.0, 3500.0, 800.0, wacc=0.13)      # wacc identical on purpose
    out = R.build_range(_frontier([cur, opt], 0.6, opt))
    d = {m["metric"]: m["direction"] for m in out["moves"]}
    assert d["enterprise_value"] == "rises"
    assert d["tail_solvency_margin"] == "falls"
    assert d["wacc"] == "unchanged"


def test_no_moves_when_the_current_point_was_not_evaluated():
    pts = [_pt(0.5, 3130.8, 1750.6)]
    out = R.build_range(_frontier(pts, 0.6, pts[0]))
    assert out["moves"] == []


# ── the range is the Pareto set, and its width is reported ──────────────────

def test_the_range_spans_the_efficient_points_not_the_grid():
    pts = [_pt(0.0, 100.0, 900.0), _pt(1.0, 300.0, 700.0),
           _pt(2.0, 200.0, 100.0, pareto=False)]
    out = R.build_range(_frontier(pts, 0.0, pts[1]))
    assert out["range"]["lo"] == 0.0
    assert out["range"]["hi"] == 1.0          # 2.0 is dominated, so outside
    assert out["range"]["n_efficient"] == 2
    assert out["range"]["n_evaluated"] == 3


def test_the_efficient_share_is_reported_so_a_wide_frontier_cannot_pose_as_a_selection():
    """⭐⭐ MEASURED: 8 of 9 points are efficient on the showcase dataset. A
    "Pareto efficient" badge on almost every point implies a narrowing that did
    not happen, so the share ships as a number."""
    pts = [_pt(float(i), 100.0 + i, 900.0 - i) for i in range(8)]
    pts.append(_pt(9.0, 1.0, 1.0, pareto=False))
    out = R.build_range(_frontier(pts, 0.0, pts[0]))
    assert out["range"]["n_efficient"] == 8
    assert abs(out["range"]["efficient_share"] - 8 / 9) < 1e-9


def test_already_optimal_is_true_only_when_the_two_points_coincide():
    cur = _pt(0.6, 3215.4, 1662.1)
    out = R.build_range(_frontier([cur], 0.6, cur))
    assert out["already_optimal"] is True
    other = _pt(0.0, 2578.8, 2312.7)
    out2 = R.build_range(_frontier([cur, other], 0.6, other))
    assert out2["already_optimal"] is False


# ── the constraint and the assumption are on the surface ────────────────────

def test_the_optimum_is_declared_unconstrained_and_never_implied_safe():
    """⛔⭐⭐ MEASURED, NOT ASSUMED: `frontier` applies no feasibility filter.
    Pushing the grid out returns tail margins of 242, 75 and 29 — every one
    ranked, none refused. The word `safe` must not appear."""
    cur = _pt(0.6, 3215.4, 1662.1)
    out = R.build_range(_frontier([cur], 0.6, cur))
    assert out["constraint"]["present"] is False
    reason = out["constraint"]["reason"].lower()
    assert "unconstrained" in reason
    assert "not " in reason and "safe" in reason      # "not the same as safe"
    # the claim it must never make
    assert "is safe" not in reason


def test_the_declared_prior_travels_with_the_recommendation():
    cur = _pt(0.6, 3215.4, 1662.1)
    out = R.build_range(_frontier([cur], 0.6, cur, lam=0.25))
    assert out["assumption"]["risk_aversion_lambda"] == 0.25
    assert "prior" in out["assumption"]["note"].lower()


def test_an_optimum_never_ships_without_both_its_constraint_and_its_assumption():
    """⭐ The pair is the ruling. Either alone leaves an optimum reading as a
    target: a constraint with no prior hides who chose the point, and a prior with
    no constraint implies a floor that does not exist."""
    cur = _pt(0.6, 3215.4, 1662.1)
    out = R.build_range(_frontier([cur], 0.6, cur))
    assert out["optimal"] is not None
    assert out["constraint"] and out["assumption"]


# ── the two frontiers must not converge on one noun (§7j.6) ─────────────────

def test_the_payload_names_which_frontier_this_is_in_a_field_not_in_prose():
    """⭐⭐ A scope report once matched the substring "frontier" and did not check
    which one. A field can be asserted; a sentence in a narrative cannot."""
    cur = _pt(0.6, 3215.4, 1662.1)
    out = R.build_range(_frontier([cur], 0.6, cur))
    assert out["engine"] == "intelligence.frontier"
    assert out["not_this_other_frontier"]["engine"] == "prescience_decision"
    assert "move" in out["not_this_other_frontier"]["note"].lower()


def test_the_range_never_carries_a_prescience_move_field():
    """⛔ The two engines answer different questions over different decision
    variables. A field from the move search appearing here would be the merge."""
    cur = _pt(0.6, 3215.4, 1662.1)
    out = R.build_range(_frontier([cur], 0.6, cur))
    for forbidden in ("moves_selected", "atoms", "raev", "excludes", "prereqs"):
        assert forbidden not in out


# ── the audit ───────────────────────────────────────────────────────────────

def test_the_audit_reports_its_denominator():
    a = R.audit()
    assert a["n"] == len(a["rows"])
    assert sum(a["counts"].values()) == a["n"]


def test_every_audit_row_states_a_status_and_a_reason_for_it():
    for r in R.audit()["rows"]:
        assert r["status"] in ("computed", "absent", "refused")
        if r["status"] == "computed":
            assert r["owner"] and r["objective"], r["quantity"]
        else:
            # ⭐ absent needs what it WOULD take; refused needs the ruling.
            assert r.get("needs") or r.get("ruling"), r["quantity"]


def test_no_optimum_is_claimed_for_a_quantity_with_no_objective_function():
    """⭐ The row most likely to be misread. A grading band is not an optimum."""
    ratios = next(r for r in R.audit()["rows"] if r["quantity"] == "key_ratios")
    assert ratios["status"] == "absent"
    assert ratios["owner"] is None and ratios["objective"] is None
    assert "band is not an optimum" in ratios["needs"]


def test_product_mix_reports_contribution_and_never_enterprise_value():
    """⛔ CORE §8k's boundary, asserted where it is stated rather than trusted."""
    mix = next(r for r in R.audit()["rows"] if r["quantity"] == "product_mix")
    assert "contribution" in mix["objective"].lower()
    assert "enterprise value" not in mix["objective"].lower()
    assert "NEVER ENTERPRISE VALUE" in mix["note"]


def test_the_three_refusals_each_name_their_ruling():
    refused = [r for r in R.audit()["rows"] if r["status"] == "refused"]
    assert len(refused) == 3
    for r in refused:
        assert r["ruling"]


# ── the range's two ends ────────────────────────────────────────────────────

def test_the_two_ends_are_reported_and_the_recommendation_is_not_called_value_maximising():
    """⭐⭐ MEASURED: at the default weight the recommended point LOWERS expected
    enterprise value by 636 on the showcase dataset. Naming it the
    value-maximising point would be false, and a name that overstates a number
    survives every test that checks the number."""
    lo = _pt(0.0, 2578.8, 2312.7)          # safety end
    mid = _pt(0.6, 3215.4, 1662.1)
    hi = _pt(1.75, 3736.9, 943.4)          # value end
    out = R.build_range(_frontier([lo, mid, hi], 0.6, lo))
    assert out["ends"]["value_max"]["de"] == 1.75
    assert out["ends"]["safety_max"]["de"] == 0.0
    # the recommendation is its own field and is NOT the value-maximising end
    assert out["optimal"]["de"] == 0.0
    assert "value_maximising" not in out
    assert out["optimal"]["de"] != out["ends"]["value_max"]["de"]


def test_the_ends_are_drawn_from_the_efficient_set_only():
    """⛔ A dominated point can hold the highest raw value on one axis. Reading
    the ends off the grid would name a point no reader should stand on."""
    eff_hi = _pt(1.0, 300.0, 700.0)
    dominated = _pt(2.0, 900.0, 10.0, pareto=False)   # highest EV, dominated
    out = R.build_range(_frontier([_pt(0.0, 100.0, 900.0), eff_hi, dominated],
                                  0.0, eff_hi))
    assert out["ends"]["value_max"]["de"] == 1.0


def test_the_range_carries_the_sweeps_objective_statement_and_does_not_restate_it():
    """⭐ A · One description of one objective. The range SHAPES the sweep; if it
    wrote its own statement there would be two to keep in step, which is the
    drift the sole-ownership programme exists to prevent — in prose."""
    cur = _pt(0.6, 3215.4, 1662.1)
    f = _frontier([cur], 0.6, cur)
    f["objective_statement"] = {"formula": "SENTINEL", "prior": {"weight_on_value": 0.5}}
    out = R.build_range(f)
    assert out["objective_statement"]["formula"] == "SENTINEL"
    assert out["objective_statement"]["prior"]["weight_on_value"] == 0.5
