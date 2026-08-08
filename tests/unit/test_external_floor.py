"""The external floor counts organisations, and a person-count floor would not.

⛔⭐⭐ THE PROOF THE AMENDMENT ASKS FOR, AND IT IS THE WHOLE FILE:

  · five respondents from ONE supplier            -> WITHHELD
  · three respondents from THREE suppliers        -> PUBLISHED

Against a person-count floor the first would wrongly PASS at n=5 ≥ 3 — so the
first test asserts both that the mechanism withholds AND that the person count
was high enough to have fooled the old rule. A test that only asserted
"withheld" would pass against a mechanism that withheld everything.
"""
import pytest

from services.api import external_floor as XF
from services.api import assessment_engine as AE


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE RED PROOF, BOTH DIRECTIONS
# ═══════════════════════════════════════════════════════════════════════════

def test_five_respondents_from_ONE_supplier_is_withheld():
    """⛔⭐⭐ THE CASE §16.7 EXISTS FOR. Five people at Acme is n=5 by person and
    n=1 by firm, and the result describes one nameable company."""
    out = XF.publishable({"acme": [7, 8, 6, 7, 9]}, "supplier")
    assert out["publishable"] is False
    assert out["state"] == "below_floor"
    assert out["value"] is None, "a withheld reading still published a value"
    # ⭐ THE HALF THAT MAKES THIS A PROOF: the person count WOULD have cleared
    # the old floor, so this is not a mechanism that withholds everything.
    assert out["n_respondents"] == 5
    assert out["n_respondents"] >= AE.KFLOOR, (
        "the fixture no longer exercises the defect — with fewer people than "
        "KFLOOR, a person-count floor would also have withheld and this test "
        "could not tell the two rules apart")
    assert out["n_parties"] == 1
    assert out["counts"] == "organisations"


def test_three_respondents_from_THREE_suppliers_publishes():
    """⭐ THE KNOWN POSITIVE. Three firms, one voice each, is three
    organisations — the floor is met and the reading is published."""
    out = XF.publishable({"acme": [7], "borex": [5], "crane": [6]}, "supplier")
    assert out["publishable"] is True
    assert out["state"] == "rated"
    assert out["n_parties"] == 3 and out["n_respondents"] == 3
    assert out["value"] == pytest.approx(6.0)


def test_a_person_count_floor_would_have_got_BOTH_backwards():
    """⛔⭐⭐ THE TWO RULES DISAGREE ON BOTH CASES, WHICH IS WHY THE UNIT MATTERS.

    This asserts the disagreement directly rather than trusting the reasoning:
    counting people passes the one-supplier case; counting firms fails it.
    """
    one_firm = {"acme": [7, 8, 6, 7, 9]}
    three_firms = {"acme": [7], "borex": [5], "crane": [6]}

    def person_count_verdict(by_party):
        n = sum(len(v) for v in by_party.values())
        return n >= AE.KFLOOR

    assert person_count_verdict(one_firm) is True, \
        "the old rule did not publish the one-supplier case — no defect to fix"
    assert XF.publishable(one_firm, "supplier")["publishable"] is False, \
        "the new rule agrees with the old one on the case that motivated it"
    # ⭐ and they agree where they should — three firms passes under both
    assert person_count_verdict(three_firms) is True
    assert XF.publishable(three_firms, "supplier")["publishable"] is True


# ═══════════════════════════════════════════════════════════════════════════
# THE ASYMMETRY (§16.7)
# ═══════════════════════════════════════════════════════════════════════════

def test_customers_have_no_floor_and_suppliers_do():
    """⛔ THE ASYMMETRY IS THE POINT. The same shape of data publishes for
    customers and withholds for suppliers, because whether a mean identifies a
    respondent is a fact about the POPULATION."""
    shape = {"one_party": [7, 8, 6, 7, 9]}
    assert XF.publishable(shape, "customer")["publishable"] is True
    assert XF.publishable(shape, "supplier")["publishable"] is False
    assert XF.floor_for("customer") == 0
    assert XF.floor_for("supplier") == XF.floor_for("partner") == 3


def test_an_unclassified_population_gets_the_STRICTER_rule():
    """⛔ A population nobody classified is not evidence that it is safe to
    publish."""
    assert XF.floor_for("something_new") == 3
    assert XF.publishable({"x": [7]}, "something_new")["publishable"] is False


def test_groups_with_no_firm_behind_them_are_UNAFFILIATED():
    """⭐ General Public, Local Communities and Media have no organisation to
    aggregate to — each respondent is their own party, and the population is
    large and unnamed, so the customer rule applies for the same reason."""
    assert "public" in XF.UNAFFILIATED
    assert XF.floor_for("public") == 0
    out = XF.publishable({f"r{i}": [6] for i in range(4)}, "public")
    assert out["publishable"] is True and out["n_parties"] == 4


# ═══════════════════════════════════════════════════════════════════════════
# AGGREGATION — THE SPREAD IS CARRIED
# ═══════════════════════════════════════════════════════════════════════════

def test_several_respondents_at_one_party_make_ONE_reading():
    out = XF.aggregate_party([6, 8])
    assert out["value"] == pytest.approx(7.0)
    assert out["n_respondents"] == 2


def test_disagreement_is_CARRIED_not_discarded():
    """⛔⭐⭐ Two contacts at one partner with opposite views is NOT noise.
    Averaging it away would delete the most interesting thing on the page."""
    agree = XF.aggregate_party([7, 7, 8])
    split = XF.aggregate_party([2, 9])
    assert agree["dissent"] is False
    assert split["dissent"] is True, "opposite views were averaged into silence"
    assert split["spread"] == pytest.approx(7.0)
    assert split["sd"] > 0
    # ⭐ and dissent LABELS rather than suppresses — the reading still publishes
    out = XF.publishable({"a": [2, 9], "b": [6], "c": [7]}, "supplier")
    assert out["publishable"] is True
    assert out["dissent_parties"] == 1


def test_the_floor_is_applied_AFTER_aggregation():
    """⛔ Anything that floors first is counting people again by another route."""
    out = XF.publishable({"a": [5, 5, 5, 5, 5, 5]}, "partner")
    assert out["n_respondents"] == 6 and out["n_parties"] == 1
    assert out["publishable"] is False


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ COMPLEMENT INFERENCE
# ═══════════════════════════════════════════════════════════════════════════

def test_one_withheld_sibling_takes_a_second_with_it():
    """⛔⭐⭐ Three groups, two published and one withheld, reconstructs the third
    by subtraction whenever the total is known. Suppression is a property of the
    SET, not a row — the reasoning the internal engine already applies."""
    groups = {
        "suppliers": ({"a": [7]}, "supplier"),                     # 1 party -> withheld
        "partners":  ({"p": [6], "q": [5], "r": [7]}, "partner"),  # 3 parties
        "customers": ({f"c{i}": [8] for i in range(9)}, "customer"),
    }
    out = XF.publish_set(groups)
    assert out["suppliers"]["publishable"] is False
    withheld = [n for n, r in out.items() if not r["publishable"]]
    assert len(withheld) == 2, (
        f"only {withheld} withheld — publishing every other member lets a "
        f"reader reconstruct the withheld one by subtraction")
    assert "partners" in withheld, "the cheapest sibling was not the one withheld"
    assert out["partners"]["state"] == "withheld_to_protect_sibling"
    assert out["partners"]["note"]


def test_a_set_with_nothing_withheld_publishes_everything():
    """⭐ THE KNOWN POSITIVE for the set rule — it must not withhold by default."""
    groups = {
        "suppliers": ({"a": [7], "b": [6], "c": [5]}, "supplier"),
        "partners":  ({"p": [6], "q": [5], "r": [7]}, "partner"),
    }
    out = XF.publish_set(groups)
    assert all(r["publishable"] for r in out.values())


def test_the_internal_KFLOOR_is_untouched():
    """⛔ The internal path still counts PEOPLE, correctly — for employees the
    risk is identifying a colleague. The two coexist because the populations
    differ, which is the whole content of the standing ruling."""
    assert AE.KFLOOR == 3
    # ⛔⭐⭐ ASKED OF THE IMPORT GRAPH, NOT THE TEXT. A first version asserted
    # `"KFLOOR" not in inspect.getsource(XF)` and failed on the module's own
    # DOCSTRING, which explains why the internal counter is wrong for external
    # groups. §III.9: a guard matching TEXT punishes the file that states its
    # own rule. What matters is whether the module USES the constant.
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(XF))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            imported |= {a.name for a in n.names}
        elif isinstance(n, ast.Import):
            imported |= {a.name for a in n.names}
    assert "assessment_engine" not in " ".join(imported), \
        "the external mechanism imports the internal engine"
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "KFLOOR" not in used, \
        "the external mechanism reads the internal constant"
