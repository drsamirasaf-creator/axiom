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


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ THE ATTRIBUTION BOUNDARY — INTERNAL CAN NEVER BECOME ATTRIBUTED
# ═══════════════════════════════════════════════════════════════════════════

def test_an_internal_response_can_NEVER_be_attributed():
    """⛔ THE ASSERTION THE RULING DEMANDS. `orientation` is the boundary and it
    must not blur. An employee's consent was given to an ANONYMOUS instrument,
    and a later flag cannot retroactively change what they agreed to."""
    assert XF.may_attribute("internal", consented=True) is False, (
        "an internal response became attributable because someone set a "
        "consent flag — §4u-c governs employees regardless")
    with pytest.raises(XF.InternalAttributionRefused):
        XF.attribute("internal", True, "Acme")


def test_an_external_response_is_attributed_only_WITH_consent():
    """⛔ CONSENT IS THE RESPONDENT'S, NOT THE COMPANY'S. A supplier named to
    their customer's CEO without agreeing is a commercial consequence."""
    assert XF.may_attribute("external", consented=True) is True
    assert XF.may_attribute("external", consented=False) is False
    assert XF.attribute("external", True, "Acme") == "Acme"
    assert XF.attribute("external", False, "Acme") is None


def test_an_unclassified_orientation_REFUSES_rather_than_defaulting():
    """⛔ An instrument nobody classified is not evidence that naming is safe —
    the same stricter-default reasoning as the floor."""
    with pytest.raises(XF.InternalAttributionRefused):
        XF.attribute(None, True, "Acme")
    assert XF.may_attribute(None, consented=True) is False


def test_the_refusal_RAISES_rather_than_returning_None():
    """⭐ §4u-c's own reasoning for `assign()` raising on a comment kwarg rather
    than stripping it: silently dropping would let a caller believe it took
    effect. A None here would read as 'no name available' when the truth is
    'this may never be named'."""
    try:
        XF.attribute("internal", True, "Acme")
    except XF.InternalAttributionRefused as e:
        assert "never be attributed" in str(e) and "ANONYMOUS" in str(e)
    else:
        pytest.fail("an internal attribution returned instead of refusing")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐⭐ THE DECLINING SUBSET — THE ADVERSARY, EXPLICIT
# ═══════════════════════════════════════════════════════════════════════════

def test_the_decliner_IS_derivable_from_the_aggregate_and_the_names():
    """⛔⭐⭐ THE ATTACK, ASSERTED RATHER THAN ASSUMED. Nine parties consent and
    one declines; the group mean over ten and the nine published values recover
    the tenth EXACTLY, by one subtraction. If this test ever stops finding it,
    the mechanism below is guarding nothing."""
    consenting = [6, 7, 5, 8, 6, 7, 6, 5, 7]          # nine consenting parties
    hidden = 2.0                                       # the decliner
    group_mean = (sum(consenting) + hidden) / 10
    out = XF.decliner_derivable(10, group_mean, consenting)
    assert out["derivable"] is True
    assert out["exact"] is True, "one decliner is recovered EXACTLY, not narrowed"
    assert out["recovered"] == pytest.approx(hidden), (
        "the adversary did not recover the decliner — the fixture no longer "
        "exercises the attack this mechanism exists to prevent")


def test_two_decliners_are_narrowed_rather_than_recovered_exactly():
    """⭐ Not exact, and ⛔ not safe either — a mean over two is still close
    enough to name a view."""
    consenting = [6, 7, 5, 8]
    hidden = [2.0, 3.0]
    n = len(consenting) + len(hidden)
    gm = (sum(consenting) + sum(hidden)) / n
    out = XF.decliner_derivable(n, gm, consenting)
    assert out["derivable"] is True and out["exact"] is False
    assert out["recovered"] == pytest.approx(2.5)


def test_publishing_the_aggregate_ALONE_defeats_the_adversary():
    """⛔ IT IS THE COMBINATION THAT LEAKS, NOT EITHER ALONE. With no consenting
    values published there is nothing to subtract."""
    out = XF.decliner_derivable(10, 6.0, [])
    assert out["derivable"] is False
    assert "nothing" in out["reason"]


def test_safe_publication_withholds_the_NAMES_and_keeps_the_aggregate():
    """⭐ The aggregate survives — it is what the instrument was fielded for —
    and the named values are withheld with the reason stated."""
    values = {"a": 6, "b": 7, "c": 5, "d": 2}
    out = XF.safe_publication(4, values, consented_parties=["a", "b", "c"])
    assert out["aggregate"] == pytest.approx(5.0)
    assert out["named"] == {}, "named values published beside the aggregate — " \
        "the decliner is recoverable by subtraction"
    assert set(out["withheld"]) == set(values)
    assert "subtraction" in out["why"]
    # ⛔ and the withheld set must actually defeat the attack
    assert XF.decliner_derivable(4, out["aggregate"], [])["derivable"] is False


def test_with_NOBODY_declining_the_names_publish():
    """⭐ THE KNOWN POSITIVE. A mechanism that withheld always would pass every
    test above and be useless."""
    values = {"a": 6, "b": 7, "c": 5}
    out = XF.safe_publication(3, values, consented_parties=["a", "b", "c"])
    assert out["named"] == values and out["withheld"] == []
    assert out["why"] is None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ CONSENT IS SCOPED
# ═══════════════════════════════════════════════════════════════════════════

def test_consent_does_NOT_carry_forward_to_a_new_cycle():
    """⛔⭐⭐ A re-fielded instrument next quarter is a NEW consent. The
    relationship may have changed and the contract may be up for renewal — the
    answer they are about to give is not the one they agreed to publish."""
    c = {"consented": True, "instrument_key": "suppliers", "cycle_id": 11}
    assert XF.consent_valid_for(c, "suppliers", 11) is True
    assert XF.consent_valid_for(c, "suppliers", 12) is False, (
        "consent carried silently into the next cycle")
    assert XF.consent_valid_for(c, "partners", 11) is False, (
        "consent carried across instruments")


def test_an_UNSCOPED_consent_authorises_nothing():
    """⛔ A record with no scope is not a wildcard."""
    assert XF.consent_valid_for({"consented": True}, "suppliers", 11) is False
    assert XF.consent_valid_for(
        {"consented": True, "instrument_key": "suppliers"}, "suppliers", 11) is False
    assert XF.consent_valid_for(None, "suppliers", 11) is False


def test_revocation_stops_future_publication_and_does_not_rewrite_the_past():
    """⭐ A pack is immutable and a board saw what it saw. Retracting a name
    from a published artefact is impossible, and pretending otherwise would be
    the lie — so revocation is recorded with its time instead."""
    c = {"consented": True, "instrument_key": "suppliers", "cycle_id": 11}
    r = XF.revoke_consent(c, note="contract ended")
    assert r["consented"] is False
    assert XF.consent_valid_for(r, "suppliers", 11) is False
    assert r["revoked_at"] and r["revoked_note"] == "contract ended"
    assert r["already_published_unaffected"] is True
