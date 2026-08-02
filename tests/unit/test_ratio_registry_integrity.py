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


# The evaluator's own function list, plus the two the registry uses and has not
# declared (R2 — `wacc_at` delegates to the owner, `cagr` awaits its horizon).
FUNCS = {"avg", "prior", "abs", "min", "max", "wacc_at", "cagr"}
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

# ⭐⭐ RULED ON 2 Aug, NOT YET BUILT — named individually, never waved through.
# Each is a token whose MEANING is settled and whose DECLARATION is stage 2:
#   axiom.wacc / actual_leverage  R2 — delegation is the pattern; wacc_at's
#                                 argument needs a policy token
#   cf.operating_cash_flow / nwc  R1 — operating working capital, ex-cash and
#                                 ex-debt. Blocks 5 ratios including the
#                                 headline cash_conversion_quality.
# A blanket skip would also hide a SIXTH undeclared token appearing tomorrow,
# which is the defect this whole file exists for. So the list is per-owner and
# asserted in both directions below.
PENDING = {"axiom.wacc", "cf.operating_cash_flow"}


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
    bad = {}
    for owner, expr in _exprs(reg):
        if "<" in expr or owner in PROSE_EXPRS:
            continue
        missing = set()
        for name in ANY_NAME.findall(expr):
            if name in vocab or name in ratio_ids or name in FUNCS:
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
