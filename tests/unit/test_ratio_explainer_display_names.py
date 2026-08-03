"""The ratio explainer must render names a CFO reads, never internal tokens.

⭐⭐ THE DEFECT. Expanding Gross Margin on Dashboard → Ratio Analysis rendered

    is.gross_profit / is.revenue * 100
    numerator    IS_.gross_profit
    denominator  IS_.revenue
    read from    is.gross_profit — derived: is.revenue - is.cogs

Three different internal spellings on one panel: the registry identifier, the
namespace prefix, and `IS_` — which exists ONLY because `is` is a Python
keyword and the parser renames it before `ast.parse`. **A rename that exists to
satisfy a parser has no business on a page a client reads.**

⭐ THE NAMES ARE NOT INVENTED. Every one is a label AXIOM already prints on the
client's own template: the statement line labels, the locked subtotal rows, and
the company input rows. A token with no such label renders as its identifier and
is REPORTED — a missing name is a registry gap, not a rendering choice.
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL",
                      "sqlite:///" + tempfile.mktemp(prefix="rx-", suffix=".db"))

import pytest

from services.api.modules.financials import ratio_registry as rr
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def gross_margin():
    data = meridian()
    years = data["periods"]["historical"]
    return rr.explain(data, years, len(years) - 1, "axiom.gross_margin")


# ── 1 · the evaluator's artefact never leaves the evaluator ────────────────

def test_IS_underscore_appears_nowhere_in_the_payload(gross_margin):
    """⭐⭐ THE HEADLINE PROHIBITION. `IS_` is `ast.unparse` reporting the tree the
    parser had to rename; it is not a name of anything."""
    assert "IS_" not in repr(gross_margin), (
        "the parser's keyword workaround is in the payload")


def test_every_ratio_in_the_registry_is_free_of_the_artefact():
    """⭐ NOT JUST THE ONE THAT WAS REPORTED. The rename applies to every `is.`
    formula, so one ratio proving clean proves almost nothing."""
    data = meridian()
    years = data["periods"]["historical"]
    _v, _g, ratios = rr._index()
    assert len(ratios) > 40, "the corpus is too small to be a sweep"
    dirty = []
    for rid in ratios:
        e = rr.explain(data, years, len(years) - 1, rid)
        if "IS_" in repr(e):
            dirty.append(rid)
    assert dirty == [], f"{len(dirty)} ratios leak IS_: {dirty[:5]}"


# ── 2 · display names, from labels AXIOM already prints ────────────────────

def test_a_stored_token_resolves_to_its_template_line_label():
    assert rr.display_name("is.revenue") == "Revenue"
    assert rr.display_name("is.cogs") == "Cost of Goods Sold"
    # ⭐ AND IT FOLLOWS THE CLIENT'S STANDARD. One hard-coded name would be
    # wrong for every IFRS client on the platform.
    assert rr.display_name("is.cogs", "ifrs") == "Cost of Sales"


def test_a_derived_subtotal_resolves_to_its_locked_template_row():
    """⭐ `Gross Profit` is a row the client SEES on their own workbook — the
    locked subtotal the template writes. Using it is a lookup, not an
    invention."""
    assert rr.display_name("is.gross_profit") == "Gross Profit"
    assert rr.display_name("is.ebitda") == "EBITDA"


def test_a_company_input_resolves_through_its_company_row():
    """The vocabulary points these at `company.<field>`; the label is the one on
    the company sheet."""
    assert rr.display_name("po.cost_of_debt")
    assert "cost of debt" in rr.display_name("po.cost_of_debt").lower()


def test_a_token_with_no_owned_label_returns_none_rather_than_a_guess():
    """⭐⭐ THE CONSTRAINT, AS A TEST. `is.pat` has no label on any template, and
    inventing 'Profit After Tax' here would put a name into the product that no
    owner ever ruled. It returns None and is reported."""
    assert rr.display_name("is.pat") is None
    assert rr.display_name("bs.nwc") is None


# ── 3 · the rendered strings ───────────────────────────────────────────────

def test_the_formula_renders_in_names(gross_margin):
    """⭐ THE ARITHMETIC STAYS VISIBLE. This is a labelling fix, not a removal —
    the claim is the formula, and a reader checking it needs to see it."""
    assert gross_margin["formula_display"] == "Gross Profit ÷ Revenue × 100"
    assert gross_margin["formula"] == "is.gross_profit / is.revenue * 100", (
        "the machine-readable formula must survive beside the display form")


def test_the_operands_render_in_names(gross_margin):
    by_role = {o["role"]: o for o in gross_margin["operands"]}
    assert by_role["numerator"]["text_display"] == "Gross Profit"
    assert by_role["denominator"]["text_display"] == "Revenue"


def test_the_read_from_lines_render_in_names(gross_margin):
    by_tok = {i["token"]: i for i in gross_margin["inputs"]}
    assert by_tok["is.revenue"]["name"] == "Revenue"
    gp = by_tok["is.gross_profit"]
    assert gp["name"] == "Gross Profit"
    # ⭐ the derivation is rendered in names too — it was the fourth leak
    assert gp["expr_display"] == "Revenue − Cost of Goods Sold"  # us_gaap: Meridian


def test_an_unnamed_token_falls_back_to_its_identifier_and_is_declared():
    """⭐ Where no owned name exists the identifier is the honest rendering —
    and the payload SAYS which tokens those were, so the gap is visible rather
    than looking like a naming style."""
    data = meridian()
    years = data["periods"]["historical"]
    e = rr.explain(data, years, len(years) - 1, "axiom.net_margin")
    by_tok = {i["token"]: i for i in e["inputs"]}
    pat = by_tok.get("is.pat")
    assert pat is not None and pat["name"] is None
    assert "is.pat" in e["unnamed_tokens"]
    assert "IS_" not in pat["expr_display"]


def test_a_definition_that_names_a_token_in_prose_is_relabelled():
    """⭐⭐ THE THIRD LEAK PATH, FOUND BY THE SWEEP. Three registry definitions
    mention a token in their PROSE — "...compared against po.cost_of_debt used
    in WACC" — and that sentence was rendered verbatim. Relabelling it needs no
    registry edit: the token resolves to the company row the client filled in."""
    data = meridian()
    years = data["periods"]["historical"]
    e = rr.explain(data, years, len(years) - 1, "axiom.average_cost_of_debt")
    assert "po.cost_of_debt" in e["definition"], "the raw prose must survive"
    assert "po.cost_of_debt" not in e["definition_display"]
    assert "Cost of Debt" in e["definition_display"]


def test_the_declared_gap_matches_what_the_payload_actually_renders():
    """⭐⭐ A DECLARATION THAT DOES NOT MATCH WHAT A READER SEES IS NOT ONE.
    `unnamed_tokens` is derived from the payload's own display strings, because
    an identifier reaches the panel three ways the formula's leaves do not
    cover: a nested derivation, a mention in prose, and the `needs` line of a
    ratio that did not compute."""
    import re
    data = meridian()
    years = data["periods"]["historical"]
    ident = re.compile(r"\b(?:is|bs|cf|mk|po|hc|sa)\.[a-z_][a-z_0-9]*")
    _v, _g, ratios = rr._index()
    for rid in sorted(ratios):
        e = rr.explain(data, years, len(years) - 1, rid)
        declared = set(e["unnamed_tokens"])
        shown = set()
        for s in (e.get("formula_display"), e.get("definition_display"),
                  e.get("needs_display")):
            shown |= set(ident.findall(s or ""))
        for o in e.get("operands") or ():
            shown |= set(ident.findall(o.get("text_display") or ""))
        for i in e.get("inputs") or ():
            shown |= set(ident.findall(i.get("expr_display") or ""))
            if not i.get("name"):
                shown.add(i["token"])
        undeclared = {t for t in shown if t in _v} - declared
        assert not undeclared, f"{rid} renders {undeclared} without declaring them"


# ── 4 · the gap is reported, and its size is pinned ────────────────────────

def test_the_registry_gap_is_enumerated_and_pinned():
    """⭐⭐ §III.4 — the denominator ships with the numerator. If a later registry
    edit names some of these, this fails and the number is corrected DELIBERATELY
    rather than drifting."""
    gap = rr.unnamed_vocabulary()
    assert isinstance(gap, dict)
    renderable = gap["renderable"]
    assert len(renderable) == 12, (
        f"the unnamed-but-renderable set moved: {len(renderable)} — {renderable}")
    # every one is derived or caller-resolved: an `absent` token can never be an
    # operand of a computed ratio, so it cannot reach a reader as a bare token
    assert set(renderable) >= {"is.pat", "is.pbt", "bs.nwc", "bs.total_debt"}
    assert gap["named"] >= 23 and gap["used_by_ratios"] >= 50
