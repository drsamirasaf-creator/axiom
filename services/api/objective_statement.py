"""What each optimiser maximises, said out loud — and in ONE place.

⭐⭐ THE DEFECT THIS ANSWERS (CORE §8m.1). Optimization → Solver said
"Recommended moves: Leverage +100.0%" while Optimization → Frontier said "the
risk-adjusted optimum is D/E = 0.00", one tab apart, with **neither surface
stating what it maximises**. Measured, the two agree on enterprise value to
within 0.07% — they were never in conflict about value. They carry different
objectives, and nothing on either page said so.

## ⛔⭐⭐ BOTH PRIORS ARE LITERALLY `0.5` AND THEY ARE NOT THE SAME THING

    frontier   (1−λ)·mean(EV) + λ·(CVaR95(EV) − recapitalised debt)
               a CONVEX BLEND — at λ=0.5 the value term carries weight 0.5

    RAEV       mean(EV) − λ·(mean − p05) − execution − distress
               a PENALTY off a full-weight mean — at λ=0.5 value carries 1.0

⭐ Same number, unrelated algebra. This is §7j.6's name-collision class applied to
a CONSTANT rather than to a noun, and it is worse than the noun case: two nouns
look different, whereas `0.5` and `0.5` look like agreement.

⭐⭐ SO `weight_on_value` IS THE LOAD-BEARING FIELD. It is what a reader can
actually compare — 0.5 against 1.0 — where the two λs cannot be compared at all.
A surface that printed both priors and not their weights would be reporting the
collision rather than resolving it.

## ⭐ WHY ONE MODULE AND NOT A STRING BESIDE EACH ENGINE

Two descriptions of two objectives, maintained apart, drift the way two
definitions of a quantity drift — the failure the sole-ownership programme
exists to prevent, in prose instead of arithmetic. Here the two statements are
written next to each other, so a change to one is read against the other.

⛔ NOTHING HERE COMPUTES. Every number is passed in from the engine that already
produced it; this module names things.
"""

# ── the priors, by name, so a caller cannot invent a third ──────────────────
CONVEX_BLEND = "convex_blend"
PENALTY_OFF_MEAN = "penalty_off_mean"
NO_RISK_TERM = "no_risk_term"

_ENTERS_AS = {
    CONVEX_BLEND: (
        "a convex blend: the prior is the weight on the SAFETY term, and the "
        "value term takes what is left, so raising it takes weight AWAY from "
        "value."),
    PENALTY_OFF_MEAN: (
        "a penalty subtracted from a full-weight mean: the prior scales a "
        "downside spread that is deducted, so the value term keeps weight 1.0 "
        "however the prior moves."),
    NO_RISK_TERM: (
        "not at all — this objective has no risk term, so there is no prior to "
        "set. It is the value-maximising objective, and nothing in it trades "
        "value against safety."),
}

# ⭐⭐ THE WARNING TRAVELS WITH EVERY STATEMENT, not with one of them. A reader
# arrives on whichever tab they arrived on.
COLLISION_NOTE = (
    "This page and the capital-structure Frontier both carry a risk-aversion "
    "figure, and on their default settings both read 0.5. They are not the same "
    "quantity and cannot be compared: one is the weight on safety in a blend, "
    "the other scales a penalty deducted from a full-weight mean. Compare the "
    "weight each objective puts on VALUE, shown beside it, rather than the two "
    "priors.")


# ⭐⭐ B'S SENTENCES ARE VALUES, NOT LITERALS BURIED IN A SEARCH LOOP. A first
# version wrote them inline in `optimal_levers` and the test asserted on source
# text — which the line-wrapper had split, so the assertion failed on formatting
# rather than on meaning. A constant can be asserted for what it SAYS.
AT_BOUND_LEAD = "the best move INSIDE THE SEARCH RANGE is "
OPTIMUM_LEAD = "the optimal move is "
AT_BOUND_WARNING = (
    "A lever on its boundary is where the search was told to stop, not where "
    "the objective turns — this result is UNBOUNDED in that lever, not optimal.")


def _statement(*, maximises, formula, decision_variable, decision_variable_unit,
               constraint_present, constraint_note, prior_name, prior_value,
               prior_enters_as, weight_on_value, prior_visible, prior_adjustable,
               search):
    return {
        "maximises": maximises,
        "formula": formula,
        "decision_variable": decision_variable,
        "decision_variable_unit": decision_variable_unit,
        "search": search,
        "constraint": {"present": constraint_present, "note": constraint_note},
        "prior": {
            "name": prior_name,
            "value": prior_value,
            "enters_as": prior_enters_as,
            "enters_as_note": _ENTERS_AS[prior_enters_as],
            # ⭐⭐ THE COMPARABLE NUMBER. Two priors of 0.5 say nothing; two
            # weights on value say everything.
            "weight_on_value": weight_on_value,
            # ⛔ STATED, BECAUSE THE ASYMMETRY IS ITSELF THE FINDING: one prior is
            # a slider the reader can move, the other was a module constant that
            # was never displayed and still cannot be moved. A reader who adjusts
            # one and not the other does not know the other exists.
            "visible": prior_visible,
            "adjustable": prior_adjustable,
        },
        "collision_note": COLLISION_NOTE,
    }


def frontier_objective(risk_aversion):
    """The capital-structure sweep's objective."""
    lam = float(risk_aversion)
    return _statement(
        maximises="a blend of expected enterprise value and the tail solvency "
                  "margin",
        formula="(1 − λ)·mean(EV) + λ·(CVaR95(EV) − recapitalised debt)",
        decision_variable="target debt-to-equity",
        decision_variable_unit="ratio (D/E)",
        search="an exhaustive sweep of a D/E grid, Pareto-filtered",
        # ⭐ Measured in §8m: no feasibility filter of any kind. Repeated here
        # because an objective statement that omitted it would imply a floor.
        constraint_present=False,
        constraint_note="None. The tail solvency margin is one of two weighted "
                        "objectives, not a floor — no point is excluded, however "
                        "thin its cushion.",
        prior_name="λ (risk aversion)",
        prior_value=lam,
        prior_enters_as=CONVEX_BLEND,
        # ⭐ DERIVED FROM THE PRIOR, never typed: the blend's value weight IS
        # 1−λ, and a hand-written 0.5 would stop tracking the slider the moment
        # the reader moved it.
        weight_on_value=round(1.0 - lam, 6),
        prior_visible=True,
        prior_adjustable=True)


def levers_objective(objective, raev_lambda):
    """The lever search's objective. `objective` is 'ev' or 'raev'."""
    if objective == "ev":
        return _statement(
            maximises="enterprise value, net of an execution-risk penalty",
            formula="EV(levers) − execution penalty",
            decision_variable="five forecast levers, moved together",
            decision_variable_unit="leverage is a MULTIPLE of plan long-term "
                                   "debt, not a D/E ratio",
            search="coordinate ascent inside a fixed box of lever ranges",
            # ⛔ The box is a SEARCH RANGE, not an economic constraint. Calling it
            # a constraint would imply something economic forbids going further.
            constraint_present=False,
            constraint_note="None. Each lever is bounded by a search range, "
                            "which limits where the optimiser may look — it is "
                            "not a statement that anything beyond it is unsafe.",
            prior_name="none",
            prior_value=None,
            prior_enters_as=NO_RISK_TERM,
            weight_on_value=1.0,
            prior_visible=True,
            prior_adjustable=False)
    return _statement(
        maximises="risk-adjusted enterprise value, net of execution and distress "
                  "penalties",
        formula="mean(EV) − λ_RAEV·(mean − p05) − execution penalty − distress "
                "penalty",
        decision_variable="five forecast levers, moved together",
        decision_variable_unit="leverage is a MULTIPLE of plan long-term debt, "
                               "not a D/E ratio",
        search="coordinate ascent inside a fixed box of lever ranges",
        constraint_present=False,
        constraint_note="None. Each lever is bounded by a search range, which "
                        "limits where the optimiser may look — it is not a "
                        "statement that anything beyond it is unsafe.",
        prior_name="λ_RAEV (downside penalty)",
        prior_value=float(raev_lambda),
        prior_enters_as=PENALTY_OFF_MEAN,
        # ⭐ 1.0 REGARDLESS OF THE PRIOR. That is the whole point: this prior
        # cannot take weight off value, and the Frontier's can.
        weight_on_value=1.0,
        # ⛔ WAS NEVER DISPLAYED (§8m.1). It is displayed from this lane on, and
        # it is still not adjustable — a module constant, recorded as such rather
        # than dressed up as a setting.
        prior_visible=True,
        prior_adjustable=False)
