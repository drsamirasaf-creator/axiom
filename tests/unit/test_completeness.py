"""The completeness score — derived, baseline-pinned, and reasoned.

⭐⭐ THE BASELINE IS THE TEST. 45/77 for company 20 and 42/77 for 25/38/39 were
measured before this module existed. ⛔ If the derivation stops reproducing them
the derivation is wrong — **the baseline is never adjusted to match the code.**
"""
import json
import os

import pytest

from services.api import completeness as C
from services.api.modules.financials import ratio_registry as RR

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")


def _data():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    return json.load(open(DATASET, encoding="utf-8"))


# ── the requirement set is DERIVED ──────────────────────────────────────────

def test_every_declared_quantity_has_a_requirement_entry():
    """⛔ §III.4 — the denominator, and an empty corpus fails."""
    reqs = C.requirements()
    declared = {r["id"] for r in RR.load()["ratios"]}
    assert len(declared) >= 70, f"only {len(declared)} rows — the registry is wrong"
    assert set(reqs) == declared, "the requirement set drifted from the registry"


def test_no_formula_is_left_unparsed():
    """⭐⭐ THE ANTI-HAND-LIST ASSERTION. A namespace nobody anticipated must be
    picked up by the pattern, not by an enumeration someone remembers to edit.
    The registry already uses is/bs/cf/company/po/mk/sa."""
    missed = [q for q, r in C.requirements().items() if not r["inputs"]]
    assert not missed, (
        f"{len(missed)} formula(s) yielded no inputs: {missed[:6]}. Either the "
        f"token pattern stopped matching a namespace, or a row lost its "
        f"formula — both make the REASON silently empty while the verdict "
        f"stays right.")


def test_a_reference_to_another_quantity_resolves_to_LEAF_inputs():
    """⭐ `dupont_three_step` names three ratios. A reader asking what is missing
    needs the leaves, not a pointer to another row they must expand."""
    inputs = C.requirements()["axiom.dupont_three_step"]["inputs"]
    assert inputs, "the transitive resolution produced nothing"
    assert not any(i.startswith("axiom.") for i in inputs), \
        f"an axiom.* reference survived into the leaf set: {inputs}"
    assert any(i.startswith("is.") or i.startswith("bs.") for i in inputs)


# ── the baseline, pinned ────────────────────────────────────────────────────

def test_the_showcase_reproduces_its_measured_baseline():
    """⛔ 45/77, measured 7 Aug BEFORE this module existed. Not adjustable."""
    s = C.score(_data())
    assert (s["computable"], s["declared"]) == (45, 77), (
        f"got {s['computable']}/{s['declared']}. The baseline is not the thing "
        f"to change — the derivation is.")
    assert s["percent"] == 58.4


def test_the_fraction_carries_its_denominator():
    s = C.score(_data())
    assert s["declared"] == len(RR.load()["ratios"])
    # ⭐ `fraction` is rounded to 4dp on purpose, so the tolerance must match
    # the declared rounding rather than assert an exactness the field never
    # claimed — asserting 1e-9 here failed on the rounding, not on the number.
    assert abs(s["fraction"] - s["computable"] / s["declared"]) < 5e-5


# ── the REASON is the deliverable, not the grade ────────────────────────────

def test_every_unreachable_quantity_says_why_or_admits_it_cannot():
    """⛔ §7q — an absence with a plausible reason is the most informative
    signal. A quantity that is simply 'not reachable' teaches nothing."""
    s = C.score(_data())
    silent = [e["id"] for e in s["engines"]
              if not e["reachable"] and not e["missing_inputs"]
              and not e["unresolved_inputs"] and not e["error"]]
    # A small number is tolerable (a derived-series shortfall rather than a
    # missing input), but it must be VISIBLE, not the norm.
    unreachable = [e for e in s["engines"] if not e["reachable"]]
    assert unreachable, "nothing is unreachable — the fixture cannot test this"
    assert len(silent) <= 2, f"{len(silent)} unreachable with no reason: {silent}"


def test_a_derived_input_is_NOT_reported_as_missing():
    """⛔⭐⭐ THE DEFECT CAUGHT BEFORE SHIPPING. The first version tested whether a
    token was STORED, as a proxy for whether it could be OBTAINED. `is.ebit` is
    not stored on these datasets — `derive_series` produces it — so six
    quantities blamed a field the customer already has and the template does not
    even offer. Telling a customer to supply what they already have is worse
    than saying nothing."""
    d = _data()
    assert "ebit" not in d["income_statement"], \
        "the fixture now stores EBIT — this control no longer proves anything"
    s = C.score(d)
    blamed = {t for e in s["engines"] for t in e["missing_inputs"]}
    assert "is.ebit" not in blamed, \
        "a DERIVED input was reported as one the customer must supply"


def test_the_next_action_ranks_inputs_by_how_much_they_unblock():
    """⭐ One missing line can be the sole blocker for a dozen quantities, and a
    per-engine list cannot show that."""
    s = C.score(_data())
    idx = C.missing_input_index(s)
    if not idx:
        pytest.skip("this dataset blocks on nothing nameable")
    assert idx == sorted(idx, key=lambda r: (-r["blocks"], r["input"]))
    top = idx[0]
    assert top["blocks"] == len(top["quantities"])
    assert all(q.startswith("axiom.") for q in top["quantities"])


def test_an_unknown_namespace_is_unresolved_not_missing():
    """⛔ 'I cannot tell' and 'it is missing' are different answers. Reporting
    the second for the first invents a field the customer cannot supply."""
    assert C._present({}, "zz.mystery", {}) is None
    assert C._present({"income_statement": {}}, "is.revenue", {}) is False


# ── three states, and the third is not decided here ─────────────────────────

def test_the_score_can_carry_THREE_dimension_states():
    """⚠️ FENCED. Whether `not_supplied` ships as a declared state is a founder
    ruling and is owed. ⛔ But a two-state score that later needs a third is a
    rewrite of every consumer, so the vocabulary exists now and the ruling
    decides only whether anything ever ASSERTS the third."""
    assert C.DIMENSION_STATES == (C.SUPPLIED, C.UNALLOCATED, C.NOT_SUPPLIED)
    assert len(C.DIMENSION_STATES) == 3
    assert C.score(_data())["dimension_states"] == C.DIMENSION_STATES


def test_not_supplied_is_never_inferred_from_an_empty_result():
    """⛔ An empty table cannot distinguish 'this business has no geography
    dimension' from 'the upload failed'. Nothing in this module may assert the
    declared state — only a declaration can."""
    s = C.score(_data())
    assert C.NOT_SUPPLIED not in json.dumps(s["engines"]), \
        "the score asserted a DECLARED absence it has no declaration for"


# ── T3: the third state is in the DENOMINATOR, not folded into the customer's
# column ────────────────────────────────────────────────────────────────────

def test_the_three_quantity_states_sum_to_the_denominator():
    """⛔ A surface showing only `computable` invites "the rest is missing data",
    which is false for the undeclared ones."""
    s = C.score(_data())
    assert s["computable"] + s["blocked"] + s["requirement_undeclared"] == \
        s["declared"]
    assert s["states"] == C.QUANTITY_STATES
    assert len(C.QUANTITY_STATES) == 3


def test_our_undeclared_requirement_is_not_charged_to_the_customer():
    """⛔⭐⭐ "You have not supplied this" and "AXIOM never declared what this
    needs" are different misses — the first is the reader's next action, the
    second is ours. A quantity with no declared inputs must NOT appear as
    blocked."""
    s = C.score(_data())
    for e in s["engines"]:
        if e["state"] == C.REQUIREMENT_UNDECLARED:
            assert not e["missing_inputs"], (
                f"{e['id']} has no declared requirement yet names missing "
                f"inputs — the two states have been collapsed")
    # ⛔ A BLOCKED QUANTITY NEED NOT NAME A FIELD, and asserting otherwise was
    # wrong. `axiom.revenue_cagr` has every input present and is still not
    # computable, because CAGR needs MORE THAN ONE PERIOD — a structural
    # shortfall, not a missing field and not an undeclared requirement. The
    # invariant that matters is the one the ruling is about: the undeclared
    # state must never be charged to the customer. Blocked-without-a-field is
    # bounded and visible instead (see the `silent` test above).
    fieldless = [e["id"] for e in s["engines"]
                 if e["state"] == C.BLOCKED and not e["missing_inputs"]
                 and not e["unresolved_inputs"] and not e["error"]]
    assert len(fieldless) <= 2, (
        f"{len(fieldless)} quantities are blocked with no nameable cause: "
        f"{fieldless}. Each one is a reader told 'not available' with nothing "
        f"to do about it.")


def test_every_engine_carries_exactly_one_state():
    s = C.score(_data())
    for e in s["engines"]:
        assert e["state"] in C.QUANTITY_STATES, e
        assert (e["state"] == C.REACHABLE) is e["reachable"]


# ── T1: the denominator is NAMED ────────────────────────────────────────────

def test_the_denominator_is_named_on_the_payload():
    """⛔ "54%" with an unnamed denominator is a number two readers define
    differently — and this one is specifically NOT the spec's engine count."""
    s = C.score(_data())
    assert s["denominator_id"] == C.REGISTRY_DENOMINATOR
    assert "registry" in s["denominator_label"].lower()
    assert s["declared"] == len(RR.load()["ratios"])


# ── T4: two scores, structurally never pooled ───────────────────────────────

def test_two_scores_over_the_same_denominator_may_combine():
    """⭐ The known-negative. A refusal that fired on everything would be
    replaced with a bypass within a week."""
    s = C.score(_data())
    assert C.assert_not_poolable(s, dict(s)) is True


def test_pooling_across_denominators_is_REFUSED_structurally():
    """⛔ One number with two definitions is the two-owners class in a metric,
    and it has no ragged edge — a blended percentage looks exactly like a real
    one. This must raise, not warn."""
    s = C.score(_data())
    spec_like = {"denominator_id": "spec.boxed_formulas",
                 "computable": 9, "declared": 19}
    with pytest.raises(ValueError) as ei:
        C.assert_not_poolable(s, spec_like)
    msg = str(ei.value)
    assert C.REGISTRY_DENOMINATOR in msg and "spec.boxed_formulas" in msg, \
        "the refusal must NAME both denominators, or a reader cannot tell " \
        "which two things were nearly averaged"


def test_the_undeclared_state_ACTUALLY_FIRES_when_a_formula_is_missing(monkeypatch):
    """⭐⭐ THE KNOWN POSITIVE. Every registry formula parses today, so
    `requirement_undeclared` is 0 on real data — and collapsing the state into
    `blocked` changed nothing, which means the three-state assertions above were
    passing without ever exercising the third. §III.11 in the tests written to
    prove it.

    ⛔ So the state is DRIVEN here: a row is stripped of its formula, which is
    exactly the shape that produces an undeclared requirement in production."""
    real = RR.load
    # ⛔ THE TARGET MUST ALREADY BE UNREACHABLE. The first draft stripped
    # ratios[0] — `gross_margin`, which computes fine — so the quantity stayed
    # REACHABLE and never reached the undeclared branch at all. The state
    # applies only to quantities that cannot be computed, so the victim is
    # picked from the ones already blocked on this dataset.
    baseline = C.score(_data())
    target = next(e["id"] for e in baseline["engines"]
                  if e["state"] == C.BLOCKED)

    def stripped():
        out = json.loads(json.dumps(real()))
        for r in out["ratios"]:
            if r["id"] == target:
                r["formula"] = ""     # AXIOM declared no inputs for it
        return out

    monkeypatch.setattr(RR, "load", stripped)
    s = C.score(_data())
    victim = next(e for e in s["engines"] if e["id"] == target)
    assert s["requirement_undeclared"] >= 1, \
        "stripping a formula did not produce an undeclared requirement"
    assert victim["state"] == C.REQUIREMENT_UNDECLARED
    # ⛔ AND IT IS NOT CHARGED TO THE CUSTOMER.
    assert victim["missing_inputs"] == []
    assert target in s["unparsed_formulas"]
    assert s["computable"] + s["blocked"] + s["requirement_undeclared"] == s["declared"]
