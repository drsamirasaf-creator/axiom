"""The DuPont tree shapes; it never computes.

⭐⭐ §7r-O. Every value comes from `ratio_registry` — `evaluate_period` for the
ratios, `_resolve` for the operands. A lane deleted `tiers.py` last turn for
being a second owner; this module must not become one.
"""
import json
import os

import pytest

from services.api import dupont_tree as DT
from services.api.modules.financials import engines as FE
from services.api.modules.financials import ratio_registry as RR

SCRATCH = os.environ.get(
    "AXIOM_SCRATCH",
    "/private/tmp/claude-501/-Users-samirasaf/5dfccbe2-516b-41df-b70a-8355f80ec452/scratchpad")
DATASET = os.path.join(SCRATCH, "meridian-45.json")


def _data():
    if not os.path.exists(DATASET):
        pytest.skip("the showcase dataset is not cached in this environment")
    return json.load(open(DATASET, encoding="utf-8"))


def _walk(n):
    yield n
    for k in n["children"]:
        yield from _walk(k)


def test_the_tree_has_the_ruled_shape():
    t = DT.build_tree(_data())
    root = t["root"]
    assert root["id"] == "axiom.roe"
    assert [c["id"] for c in root["children"]] == list(DT.FACTORS)
    for f in root["children"]:
        assert len(f["children"]) == 2, f"{f['id']} needs a numerator and a denominator"


def test_every_node_carries_what_a_clickable_node_needs():
    t = DT.build_tree(_data())
    for n in _walk(t["root"]):
        for field in ("label", "value", "status", "period", "basis",
                      "formula", "definition", "implication", "children"):
            assert field in n, f"{n['id']} is missing {field}"
        assert n["status"] in (DT.OBSERVED, DT.ABSENT, DT.DERIVED), n["status"]


def test_definitions_come_from_the_registry_and_are_not_authored_here():
    """⛔ No new definition text. Each factor's definition must be byte-identical
    to its registry row's own `definition:` field."""
    rows = {r["id"]: r for r in RR.load()["ratios"]}
    t = DT.build_tree(_data())
    for n in _walk(t["root"]):
        if n["id"].startswith("axiom."):
            assert n["definition"] == rows[n["id"]].get("definition"), n["id"]
    src = open(DT.__file__, encoding="utf-8").read()
    # the module must not contain a sentence that looks like a definition it wrote
    assert "Profit after tax over average" not in src, \
        "a registry definition has been copied into this module"


def test_no_implication_is_invented():
    """⛔ Measured 7 Aug: nothing owns 'what this means' for a ratio. Inventing
    per-node prose here would create an owner nobody ruled on."""
    t = DT.build_tree(_data())
    assert t["implications_available"] is False
    assert t["implications_note"]
    for n in _walk(t["root"]):
        assert n["implication"] is None, f"{n['id']} invented an implication"


def test_the_mixed_basis_travels_as_DATA_not_as_copy():
    """⛔ `financial_leverage` is average assets over PERIOD-END equity — the
    only mixed-basis figure among the average-basis ratios. A surface must not
    have to infer that from a sentence."""
    t = DT.build_tree(_data())
    lev = next(c for c in t["root"]["children"]
               if c["id"] == "axiom.financial_leverage")
    assert lev["basis"] == "mixed"
    assert lev["basis_note"] and "period-end equity" in lev["basis_note"]
    # ⭐ and it is the ONLY one
    others = [c for c in t["root"]["children"] if c["id"] != "axiom.financial_leverage"]
    assert all(c["basis_note"] is None for c in others)


def test_the_reconciliation_is_STRUCTURAL_not_a_variance():
    """⭐ Under A2 the average-assets terms cancel, so the product IS ROE by
    algebra. The payload must let a surface render a reconciliation that HOLDS,
    not a difference to monitor."""
    t = DT.build_tree(_data())
    r = t["reconciliation"]
    assert r["kind"] == "structural"
    assert r["holds"] is True
    assert abs(r["residual"]) < 1e-9
    assert "cancel" in r["why"]


def test_the_operands_resolve_through_the_REGISTRY_not_a_second_reader():
    """⛔⭐⭐ THE DEFECT THIS CAUGHT. A first version read the stored blocks
    directly and EVERY LEAF came back absent — `is.pat` is derived as
    `net_income`, `bs.equity` is stored as `total_equity`, and `bs.total_assets`
    is not stored at all. The ratios computed while their own operands showed
    as missing."""
    d = _data()
    assert "pat" not in d["income_statement"], \
        "the fixture now stores pat — this control no longer proves anything"
    assert "total_assets" not in d["balance_sheet"]
    t = DT.build_tree(d)
    leaves = [n for n in _walk(t["root"]) if not n["children"]]
    assert leaves, "no leaves"
    assert all(n["status"] == DT.OBSERVED for n in leaves), \
        [n["id"] for n in leaves if n["status"] != DT.OBSERVED]


def test_absence_propagates_upward_and_never_becomes_zero():
    """⛔ A parent whose child is absent is absent too — the product of an
    absent factor is not a number."""
    d = json.loads(json.dumps(_data()))
    d["income_statement"]["revenue"] = {}          # remove a real operand
    t = DT.build_tree(d)
    assert t["root"]["status"] == DT.ABSENT
    assert t["root"]["value"] is None, "an absent root rendered a number"
    for n in _walk(t["root"]):
        assert n["value"] != 0 or n["status"] == DT.OBSERVED, \
            f"{n['id']} turned an absence into a zero"


def test_a_leaf_never_claims_a_period_its_parent_refuses():
    """⛔⭐⭐ THE REGRESSION, FOUND BY MEASURING RATHER THAN BY A FAILURE.

    `_operand` read `if basis == "average" and i > 0`, so at the FIRST period it
    fell through to the point-value branch and returned a period-end number
    still labelled `basis: "average"` — status OBSERVED, while `asset_turnover`
    itself was ABSENT for exactly the missing opening balance. Measured on the
    showcase: 2021 parent=absent, leaf=observed.

    ⭐ §III.15. The basis label was a PROXY for the basis, and a proxy fails
    silently — the number rendered, and only its name was wrong. This asserts
    the HARM: a leaf and its parent agreeing about whether a period exists.
    """
    d = _data()
    years = FE.derive_series(d)["years"]
    n = FE.derive_series(d)["n_historical"]
    for i in range(n):
        t = DT.build_tree(d, period_index=i)
        for factor in t["root"]["children"]:
            for leaf in factor["children"]:
                if leaf["status"] == DT.OBSERVED:
                    continue
                assert factor["status"] == DT.ABSENT, (
                    f"{years[i]}: leaf {leaf['id']} is absent but its parent "
                    f"{factor['id']} is {factor['status']}")
        # ⛔ THE KNOWN POSITIVE for the average basis specifically.
        first = DT._operand(d, years, i, "bs.total_assets", "average")
        if i == 0:
            assert first["status"] == DT.ABSENT and first["absence_reason"], (
                "the first period reported an AVERAGE without an opening "
                "balance — the branch this test exists for")
        else:
            assert first["status"] == DT.OBSERVED


def test_every_absent_node_says_why():
    """⭐ An absence with no reason is a blank cell the user cannot act on."""
    d = _data()
    years = FE.derive_series(d)["years"]
    for i in range(FE.derive_series(d)["n_historical"]):
        for n in _walk(DT.build_tree(d, period_index=i)["root"]):
            if n["status"] == DT.ABSENT and not n["children"]:
                assert n.get("absence_reason"), f"{n['id']} at {years[i]}"
