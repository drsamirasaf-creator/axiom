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
    # ⭐ THE FACTOR LIST IS READ OFF THE IDENTITY'S FORMULA, not a tuple here
    # or in the module. `axiom.dupont_three_step` IS the declaration.
    assert [c["id"] for c in root["children"]] == list(DT.factors())
    assert set(DT.factors()) == {"axiom.net_margin", "axiom.asset_turnover",
                                 "axiom.financial_leverage"}
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
    have to infer that from a sentence.

    ⭐⭐ AND THE SENTENCE IS GONE. This module used to ship a `basis_note`
    composing that fact in prose. The registry row rules against it in as many
    words — *"the precision lives in `definition`, which a reader actually
    sees"* — so the note was a second statement that would drift the moment
    ruling A2 was reworded. What travels now is the DATUM (`basis`), the
    registry's own definition, and the operand texts, which show which term is
    wrapped in `avg(` and which is not.
    """
    t = DT.build_tree(_data())
    lev = next(c for c in t["root"]["children"]
               if c["id"] == "axiom.financial_leverage")
    assert lev["basis"] == "mixed"
    assert "basis_note" not in lev, (
        "a composed basis sentence is back; the registry row says the "
        "precision belongs in `definition`")
    # ⭐ the precision is READABLE, from the owner that holds it
    assert "PERIOD-END" in (lev["definition"] or "").upper()
    # ⭐ and the mixture is STRUCTURAL in the operands, not prose
    bases = {c["id"]: c["basis"] for c in lev["children"]}
    assert set(bases.values()) == {"average", "period_end"}, bases
    # ⭐ mixed is the ONLY one — the other two factors are single-basis
    others = [c for c in t["root"]["children"] if c["id"] != lev["id"]]
    assert all(c["basis"] != "mixed" for c in others), \
        [c["id"] for c in others if c["basis"] == "mixed"]


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
        # ⛔ THE KNOWN POSITIVE, on the node the defect lived in. In the first
        # period `avg(bs.total_assets)` has no opening balance; the owner says
        # so, and this asserts the tree carries that through rather than
        # rendering a period-end number under an "average" label.
        turn = next(c for c in DT.build_tree(d, period_index=i)["root"]["children"]
                    if c["id"] == "axiom.asset_turnover")
        avg = next(c for c in turn["children"] if c["id"].startswith("avg("))
        if i == 0:
            assert avg["status"] == DT.ABSENT and avg["absence_reason"], (
                "the first period reported an AVERAGE without an opening "
                "balance — the branch this test exists for")
            assert "opening balance" in avg["absence_reason"]
        else:
            assert avg["status"] == DT.OBSERVED


def test_every_absent_node_says_why():
    """⭐ An absence with no reason is a blank cell the user cannot act on."""
    d = _data()
    years = FE.derive_series(d)["years"]
    for i in range(FE.derive_series(d)["n_historical"]):
        for n in _walk(DT.build_tree(d, period_index=i)["root"]):
            if n["status"] == DT.ABSENT and not n["children"]:
                assert n.get("absence_reason"), f"{n['id']} at {years[i]}"


def test_a_four_of_five_series_ships_five_points_one_of_them_absent():
    """⛔⭐⭐ A SERIES MUST NOT DROP THE PERIOD IT COULD NOT COMPUTE.

    Measured on the showcase: `asset_turnover` and `financial_leverage` are
    4-of-5, both from the single missing 2021 opening balance. Two wrong
    renderings are possible and this test forbids both — a 5-point line with an
    invented value, and a 4-point line that silently omits a period that
    exists. The absent point ships with its reason, and `observed`/`n` ship so
    the denominator is never inferred from the array's length.
    """
    d = _data()
    der = FE.derive_series(d)
    n = der["n_historical"]
    t = DT.build_tree(d)
    four = [q for q, s in t["series"].items() if s["observed"] < s["n"]]
    assert four, ("no series on this dataset is short, so this test cannot "
                  "tell a correct implementation from one that drops points")
    for q, s in t["series"].items():
        assert s["n"] == n, f"{q} shipped {s['n']} points for {n} periods"
        assert len(s["points"]) == n
        assert [p["period"] for p in s["points"]] == der["years"][:n]
        for p in s["points"]:
            assert p["status"] in (DT.OBSERVED, DT.ABSENT)
            if p["status"] == DT.ABSENT:
                assert p["value"] is None, "an absence carried a value"
                assert p["absence_reason"], f"{q} at {p['period']} says nothing"
            else:
                assert p["value"] is not None
        assert s["observed"] == sum(1 for p in s["points"]
                                    if p["status"] == DT.OBSERVED)
    for q in four:
        assert t["series"][q]["observed"] == n - 1
        assert "opening balance" in t["series"][q]["points"][0]["absence_reason"]


def test_the_series_is_a_LOOP_not_a_second_fetch():
    """⭐ §7r-O. The history comes from the dataset already in hand — a series
    that needed a second call would be a second read path to keep in step."""
    import inspect
    src = inspect.getsource(DT.series_for)
    for forbidden in ("requests", "httpx", "get_db", "Session", "urlopen"):
        assert forbidden not in src, f"series_for reaches for {forbidden}"
    d = _data()
    one = DT.series_for(d, "axiom.roe")
    assert one["points"] == DT.build_tree(d)["series"]["axiom.roe"]["points"]


def test_the_series_stops_at_the_last_REAL_period():
    """⛔ A projection of a projection must not enter a history line without
    being marked. The default is historical only, and when forecasts are asked
    for every point says which it is."""
    d = _data()
    n = FE.derive_series(d)["n_historical"]
    assert all(p["projection"] is False
               for p in DT.series_for(d, "axiom.roe")["points"])
    full = DT.series_for(d, "axiom.roe", historical_only=False)
    assert full["n"] > n
    assert [p["projection"] for p in full["points"]][:n] == [False] * n
    assert all(p["projection"] for p in full["points"][n:])
