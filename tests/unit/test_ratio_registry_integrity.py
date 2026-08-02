"""The registry must be internally resolvable.

⭐ THREE OF THE FIVE DEFECTS FIXED ON 2 Aug WERE THE SAME DEFECT: a token
referenced and never declared. `is.ebit` named a storage field instead of its
token, and `bs.total_assets` / `bs.total_liabilities` each referenced a bare
name in no namespace. `evaluation.forbidden` already prohibited exactly this —
"any token not present in `vocabulary`" — and nothing enforced it, so the rule
sat in the file being violated by the file for five registry versions.

A rule with no instrument is prose. These are the instrument.
"""
import os
import re

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRY = os.path.join(ROOT, "docs", "reference", "axiom_ratio_registry.yaml")

TOK = re.compile(r"\b(?:is|bs|cf|mk|po|hc|sa)\.[a-z_0-9]+")
RAT = re.compile(r"\baxiom\.[a-z_0-9]+")


@pytest.fixture(scope="module")
def reg():
    return yaml.safe_load(open(REGISTRY, encoding="utf-8"))


@pytest.fixture(scope="module")
def vocab(reg):
    return {t for g in reg["vocabulary"].values() for t in g}


def _exprs(reg):
    """Every expression in the file: ratio formulas AND derived vocab exprs."""
    for r in reg["ratios"]:
        yield r["id"], r["formula"]
    for g in reg["vocabulary"].values():
        for tok, meta in (g or {}).items():
            if isinstance(meta, dict) and isinstance(meta.get("expr"), str):
                yield tok, meta["expr"]


# ⭐ READ FROM THE REGISTRY, NOT RESTATED HERE. Written first as a literal set,
# it went stale the moment R7 added five delegating functions — the test then
# reported `net_debt(...)` as an undeclared identifier, which is the file's own
# defect class committed inside the test that polices it. The evaluator's
# operators plus whatever `engine_functions` declares.
def _funcs(reg):
    return ({"avg", "prior", "abs", "min", "max"}
            | set(reg["evaluation"].get("functions") or {})
            | set(reg["evaluation"].get("engine_functions") or {}))
# Any identifier at all, so a BARE name is visible — see the test below.
ANY_NAME = re.compile(r"\b[A-Za-z_][A-Za-z0-9_.]*\b")

# ⭐ TWO `derived` ENTRIES WHOSE `expr` IS PROSE, NOT AN EXPRESSION:
#   po.cost_of_equity  "CAPM: risk_free_rate + beta * market_risk_premium + premia"
#   po.days_in_period  "365 | 366 | 90 by period basis"
# Neither parses under `safe_ast`. Both have real owners in code
# (ratios.cost_of_equity_at, and the period machinery). Scanning them for
# undeclared tokens would report English words as missing vocabulary, which is
# a finding about the scanner. Their disposition is a ruling, not a fix.
PROSE_EXPRS = {"po.cost_of_equity", "po.days_in_period"}

# ⭐⭐ EMPTY, AND THAT IS THE POINT OF IT HAVING BEEN A LIST.
#
# Stage 1 left two entries, each a token whose MEANING was ruled and whose
# DECLARATION was stage 2's work:
#
#   axiom.wacc / actual_leverage   R2 — declared as po.actual_leverage,
#                                  `source: caller_resolved`, because it is
#                                  mode-dependent (market D/E for public, the
#                                  target-D/E policy input for private) and one
#                                  expr would assert an identity the code lacks.
#   cf.operating_cash_flow / nwc   R1 — declared as bs.nwc on the OPERATING
#                                  basis, ex-cash and ex-debt.
#
# ⭐ THE RATCHET FIRED RATHER THAN THE LIST BEING EDITED BY HAND. Declaring both
# tokens made the two entries STALE, and the both-directions assertion below
# failed the build demanding the list be updated. That is the shrink-only
# mechanism doing its job: an entry cannot quietly outlive its reason, and this
# list could not silently keep two names that no longer needed excusing.
#
# It stays as an empty set, not deleted: a sixth undeclared token appearing
# tomorrow must land in `unexpected` and fail, never be absorbed.
PENDING = set()


def test_every_referenced_token_is_declared(reg, vocab):
    """⭐⭐ EVERY REFERENCE, INCLUDING BARE ONES — AND THE FIRST DRAFT MISSED
    ALL THREE DEFECTS IT WAS WRITTEN FOR.

    Written first against the prefixed-token pattern `(is|bs|cf|...)\\.name`, it
    passed on the pre-fix 7r.7 registry. Every one of defects 1-3 was a BARE
    name — `depreciation_amortization`, `noncurrent_assets`,
    `other_noncurrent_liabilities` — carrying no namespace at all, which is
    precisely WHY they were undeclared and why nothing resolved them. A pattern
    keyed on the namespace can only find tokens that have one.

    Verified by running against `383b9e0`'s registry: this now fails there and
    passes here. A regression test that does not fail on the regression is a
    spelling check.
    """
    ratio_ids = {r["id"] for r in reg["ratios"]}
    funcs = _funcs(reg)
    bad = {}
    for owner, expr in _exprs(reg):
        if "<" in expr or owner in PROSE_EXPRS:
            continue
        missing = set()
        for name in ANY_NAME.findall(expr):
            if name in vocab or name in ratio_ids or name in funcs:
                continue
            if name.replace(".", "").isdigit():
                continue
            missing.add(name)
        if missing:
            bad[owner] = sorted(missing)

    unexpected = {o: t for o, t in bad.items() if o not in PENDING}
    assert unexpected == {}, (
        "identifiers referenced but declared nowhere — neither a vocabulary "
        f"token, a ratio id, nor an evaluator function: {unexpected}")

    # ⭐ AND THE PENDING LIST IS SHRINK-ONLY, IN BOTH DIRECTIONS. An entry that
    # no longer fires is stale and fails too, so declaring `nwc` in stage 2
    # forces this list to be updated rather than quietly outliving its reason.
    stale = sorted(set(PENDING) - set(bad))
    assert stale == [], (
        f"PENDING entries that no longer have an undeclared token: {stale} — "
        f"the ruling has been built; remove them from the list")


def test_every_canonical_chain_resolves(reg):
    """A chain into a ratio that does not exist — defect 5's shape."""
    ids = {r["id"] for r in reg["ratios"]}
    bad = {}
    for r in reg["ratios"]:
        missing = sorted({c for c in RAT.findall(r["formula"])
                          if c not in ids and c != r["id"]})
        if missing:
            bad[r["id"]] = missing
    assert bad == {}, f"formulas chaining into undefined ratios: {bad}"


def test_coverage_floor(reg, vocab):
    """⭐ §III.4 — the two assertions above pass trivially on an empty corpus.

    "0 undeclared tokens in 0 formulas" and "0 in 95" print the same green.
    """
    exprs = list(_exprs(reg))
    assert len(exprs) >= 90, f"only {len(exprs)} expressions — corpus shrank"
    assert len(vocab) >= 60, f"only {len(vocab)} vocabulary tokens"
    assert sum(len(TOK.findall(e)) for _o, e in exprs) >= 200, \
        "the token scan found almost nothing to check"


def test_the_control_would_catch_a_new_undeclared_token(vocab):
    """⭐ A KNOWN POSITIVE. The three assertions above have never fired in this
    tree — they were written the day the defects were fixed, so on this corpus
    they are green from birth. That is exactly the state in which a guard proves
    only that it can print a tick. The recogniser is run here against a token
    that IS absent, so the green above is read against a demonstrated fire."""
    planted = "bs.a_token_that_does_not_exist"
    assert planted not in vocab
    found = TOK.findall(f"bs.cash + {planted} - is.revenue")
    assert planted in found, "the token recogniser cannot see an undeclared token"
    assert [t for t in found if t not in vocab] == [planted]


def test_percent_ratios_scale_to_percent(reg):
    """Defect 4's shape: `unit: percent` while the formula yields a fraction.

    ⭐ SCOPED TO THE DIVISION FORMS, NOT ALL PERCENTS. A ratio declared percent
    whose formula is a chain of other percents (a spread, a difference) needs no
    scale of its own — `axiom.roic_wacc_spread` is `roic - wacc`, and demanding
    a `* 100` there would be demanding a double conversion.

    ⭐⭐ AND THE EXEMPTION IS CHECKED, NOT ASSUMED — the first draft's was not,
    and it let defect 4 through. "Chains into a ratio" was treated as "chains
    into a percent", so `axiom.roic`'s `avg(axiom.invested_capital)` — a
    CURRENCY quantity — bought it an exemption from the very rule it was
    breaking. The test passed on the pre-fix registry. Now the chained ratios
    must THEMSELVES be percent for the exemption to apply.
    """
    unit_of = {r["id"]: r.get("unit") for r in reg["ratios"]}
    bad = []
    for r in reg["ratios"]:
        if r.get("unit") != "percent":
            continue
        f = r["formula"]
        if "<" in f:                      # placeholder, not a formula
            continue
        chained = RAT.findall(f)
        if chained and all(unit_of.get(c) == "percent" for c in chained):
            continue                      # genuinely a percent-over-percent form
        if "/" not in f:                  # not a quotient
            continue
        if "* 100" not in f and "*100" not in f:
            bad.append((r["id"], f))
    assert bad == [], f"declared percent but not scaled to percent: {bad}"


# ── stage 2: the rulings ────────────────────────────────────────────────────
# ⭐ EVERY TEST BELOW WAS RUN AGAINST 383b9e0 BEFORE IT WAS BELIEVED. Stage 1's
# first draft went green on the regression it was written for, so "red on the
# old artefact, green on the new" is the standing bar, not a nicety.

def test_r1_nwc_is_the_operating_basis_and_distinct(reg, vocab):
    """R1 — bs.nwc excludes cash and short-term debt; working capital includes
    both. Two quantities, two names, and the test asserts they DIFFER.

    ⭐ ASSERTING bs.nwc MERELY EXISTS WOULD PASS ON A TOKEN DEFINED THE WRONG
    WAY. The ruling is about WHICH definition, so the operands are what is
    checked: an expr naming cash or short-term debt would be the inclusive
    basis wearing the operating name.
    """
    assert "bs.nwc" in vocab, "R1's token is not declared"
    expr = next(g["bs.nwc"]["expr"] for g in reg["vocabulary"].values()
                if "bs.nwc" in g)
    operands = set(TOK.findall(expr))
    assert operands == {"bs.other_current_assets", "bs.other_current_liabilities"}, \
        f"bs.nwc is not the engine's operating basis: {expr}"
    # and it must NOT reach cash or short-term debt through its operands
    assert "bs.cash" not in operands and "bs.short_term_debt" not in operands

    wc = next(r["formula"] for r in reg["ratios"]
              if r["id"] == "axiom.working_capital")
    assert wc != expr, "the two working-capital measures have collapsed into one"
    assert set(TOK.findall(wc)) == {"bs.current_assets", "bs.current_liabilities"}


def test_r1_fcff_uses_the_operating_basis(reg):
    """R1 — the third live registry-versus-engine disagreement.

    FCFF feeds the DCF and renders in the KPI strip. The registry used the
    inclusive basis; the engine (engines.py:462) has always used the operating
    one. RED at 383b9e0, where the formula still carries bs.current_assets.
    """
    f = next(r["formula"] for r in reg["ratios"] if r["id"] == "axiom.fcff")
    assert "bs.nwc" in f, f"axiom.fcff does not use the operating basis: {f}"
    assert "bs.current_assets" not in f and "bs.current_liabilities" not in f, \
        f"axiom.fcff still carries the inclusive working-capital term: {f}"


def test_r2_engine_functions_are_declared_with_owners(reg):
    """R2 — delegation is the pattern, so a delegating call is DECLARED.

    Both were in use and neither was declared, so the registry called functions
    its own `forbidden` list prohibited.
    """
    ef = reg["evaluation"].get("engine_functions") or {}
    # ⭐ THE SET GREW FROM TWO TO SEVEN UNDER R7 AND THE ASSERTION HAD TO BE
    # REWRITTEN, NOT RELAXED. Pinning the exact membership is what makes a
    # SIXTH delegation appearing without an owner fail here; loosening it to
    # "at least these" would let an undeclared one in silently.
    assert set(ef) == {"wacc_at", "cagr", "net_debt", "total_debt",
                       "invested_capital", "roic", "eva"}, \
        f"declared engine functions: {sorted(ef)}"
    for name, meta in ef.items():
        assert meta.get("owner"), f"{name} names no owner"
        assert "::" in meta["owner"], f"{name}'s owner is not a symbol: {meta['owner']}"


def test_r2_cagr_states_a_horizon(reg):
    """⭐ A CAGR WITHOUT A WINDOW IS NOT A NUMBER. `cagr(is.revenue)` was
    ambiguous as written and the dispatch made this a stop condition: declare
    the engine's horizon, or stop and report that none exists.

    The engine states one at all three call sites — the full historical window,
    endpoint to endpoint, exponent n = hist_n - 1. It is window-RELATIVE, not a
    fixed number of years: measured across the 33 stored datasets hist_n runs
    2, 3, 5, 6 and 12, so a declared "5-year CAGR" would be wrong on 17 of 33.
    """
    cagr = reg["evaluation"]["engine_functions"]["cagr"]
    h = cagr.get("horizon", "")
    assert h, "cagr declares no horizon"
    assert "historical" in h, f"the horizon does not name its window: {h}"
    assert "- 1" in h or "-1" in h, f"the horizon does not state its exponent: {h}"
    # the forecast-window CAGR is a DIFFERENT quantity sharing the name
    assert "plan_cagr" in cagr.get("distinct_from", "")


def test_r3_removals_are_recorded_not_deleted(reg):
    """R3 — out of the arithmetic, still on the record.

    ⭐ A SILENTLY VANISHED RATIO IS INDISTINGUISHABLE FROM ONE NOBODY THOUGHT
    OF. The next reader of a registry with no common-size ratios must be able to
    find out why without re-deriving the ruling.
    """
    ids = {r["id"] for r in reg["ratios"]}
    gone = {"axiom.common_size_is", "axiom.common_size_bs", "axiom.ohlson_o"}
    assert not (ids & gone), f"still in the arithmetic: {sorted(ids & gone)}"
    withdrawn = {w["id"] for w in reg.get("withdrawn") or []}
    assert withdrawn == gone, f"withdrawal record incomplete: {sorted(withdrawn)}"
    for w in reg["withdrawn"]:
        assert w.get("ruling"), f"{w['id']} was removed with no reason recorded"
        assert w.get("was"), f"{w['id']} does not record what it was"


def test_no_placeholder_formulas_remain(reg):
    """The three placeholders were the only unparseable FORMULAS. With R3 done,
    every remaining formula is a formula. RED at 383b9e0 on all three."""
    bad = [r["id"] for r in reg["ratios"] if "<" in r["formula"]]
    assert bad == [], f"placeholder formulas remaining: {bad}"


def test_recorded_counts_match_the_file(reg):
    """⭐ THE COUNT IS READ FROM ONE PLACE AND CHECKED AGAINST THE CORPUS.
    It lived in prose in three paragraphs as '79' and went stale the moment
    stage 1 made it 80. A count repeated in prose disagrees with itself."""
    g = reg["enumeration_guard"]
    assert g["ratio_count"] == len(reg["ratios"])
    assert g["withdrawn_count"] == len(reg["withdrawn"])
    assert g["headline_count"] == sum(1 for r in reg["ratios"] if r.get("headline"))
