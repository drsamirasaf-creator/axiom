#!/usr/bin/env python3
"""Sole ownership of net debt, ROIC, WACC and EVA — enforced by SHAPE.

⭐ WRITTEN BEFORE THE CONSOLIDATION, AND ITS CORRECT INITIAL STATE IS RED.
A guard authored after the fix has never been observed to catch anything: it is
calibrated against a codebase that already passes, so it proves only that it can
print a tick. This one is expected to find FOUR net-debt sites on the day it is
written. If it finds three, the detector is wrong, not the codebase.

⭐⭐ IT KEYS ON ARITHMETIC SHAPE, NOT ON IDENTIFIERS — AND FOR ROIC THAT WAS
FALSE UNTIL 2 Aug. `_roic_shape` required operands literally NAMED `nopat` and
`ic`, so a second ROIC at `benchmarks/engines.py:100` — whose locals come from
`ta, te, td = g("total_assets"), g("total_equity"), g("total_debt")` — read as
zero sites and this file printed "✓ sole ownership holds" over it.

The claim in this docstring was stronger than the mechanism beneath it, which is
the §III.9 shape one level up: a rule that states more than it enforces. Fixed
by resolving local names to what they were BOUND from. The sentence is kept in
its corrected form rather than deleted, because the next reader needs to know
the guard was once wrong in exactly the direction it warns about.

Every one of the four net-debt sites computes the same quantity and only two of
them spell it the same way:

    financials:328    _n(lambda a, b: a - b, debt, cash)          <- inside a lambda,
                                                                     operands are the
                                                                     CALL ARGUMENTS
    intelligence:1569 BS["short_term_debt"][ys] + BS["long_term_debt"][ys]
                        - BS["cash"][ys]                          <- three-operand
    valuation:135     company["_debt_book"] - bs["cash"][ys]      <- TWO-operand
    valuation:542     bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
                        - bs["cash"][ys]                          <- three-operand

A detector that only knows the three-operand form misses valuation:135 — the
site that matters most, because it is the one reading a caller-injected private
key. Grepping for "net_debt" misses it too: the variable is named net_debt at
every site, but so is a DIFFERENT quantity (see the collision exclusion below).

⭐ THE ALLOWLIST ASSERTS ITS OWN COVERAGE, IN BOTH DIRECTIONS.
  · a file that matches a shape and is NOT allowlisted -> fail (a new copy)
  · an allowlist entry that no longer matches          -> fail (stale drift)
One-directional coverage checks report clean on a surface they can no longer
see, which is the failure this whole family of guards exists to prevent.
"""
import ast
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ⭐ EXCLUDED BY PATH, AND THE REASON IS NOT OPTIONAL.
# valuation/engines.py's `deterministic["net_debt"]` is NOT the ratios net debt.
# It is a key on the DCF result dict that happens to share a name; on 30 Jul it
# produced five false positives in check-none-arithmetic until holder-awareness
# told the two apart. It must never be repointed at the ratio library: doing so
# would make the valuation bridge read a ratio computed for a different period
# basis. That would be the defect wearing the fix's clothes, and it is exactly
# the "cleanup" a future reader will reach for on seeing two things named alike.
# ⭐ AND IT IS A POSITIVE ASSERTION, NOT AN EXCLUSION, BECAUSE THE EXCLUSION WAS
# INERT. Written first as a path-based skip, it changed nothing: verified by
# deleting it and re-running — 4 sites either way. `deterministic["net_debt"]`
# is a dict KEY, not an arithmetic shape, so a shape detector never matched it
# and never needed to skip it. A guard clause that guards nothing is the
# declared-but-unbound class this codebase keeps finding, and shipping one
# inside a guard would have been the joke writing itself.
#
# So it asserts the opposite direction: the collision site MUST still be
# present, and MUST NOT be wired to the ratio library. That is a live check —
# it fires the day someone "tidies up" the two same-named things.
COLLISION_SITE = ("services/api/modules/valuation/engines.py",
                  '"net_debt": _r(net_debt)')
COLLISION_MUST_NOT_CONTAIN = ("ratios.net_debt", "ratios.NET_DEBT",
                              "library.net_debt")
COLLISION_EXCLUSIONS = set()   # kept empty: shape matching needs no path skips

# ⭐ THE ALLOWLIST ENCODES THE TARGET, NOT TODAY. One file, one site, per
# quantity. That is why this guard is RED the day it is written: net debt has
# four sites in three files and must have one. A guard whose expected values
# describe the current state is a description, not a guard — it goes green
# immediately and can never fail on the thing it was built for.
#
# LIBRARY is where the sole owner will live. It does not exist yet, so the
# stale-entry check fires too — correctly. Both directions stay honest.
LIBRARY = "services/api/modules/financials/ratios.py"
# ⭐ THE BRIEF EXPECTED 3. THE FIRST MEASUREMENT SAID 14. THE CALIBRATED COUNT
# IS 15 — and the difference is the INSTRUMENT, not the codebase.
#
# `_key_of` could not see through `.get(ys)`, so
# `_n(lambda a, b: a + b, BS["short_term_debt"].get(ys), BS["long_term_debt"].get(ys))`
# at financials:309 was invisible. The defect was found while calibrating the
# INVESTED-CAPITAL counter against a known population, and fixing it there
# raised this count too. A ratchet set from an uncalibrated counter is a number
# about the counter.
#
# ⭐⭐ 15 -> 17 ON 31 Jul: EXTRACTION VISIBILITY, THE THIRD CATEGORY.
# The codebase changed, but the change did not ADD a site — it bound an existing
# sub-expression to a name the counter can see.
#
#   TEST: was the arithmetic present, at that same site, computing the same
#         value, before the edit?  YES -> visibility, raise permitted.
#                                  NO  -> regression, fix the code.
#
# EVIDENCE, both sites, from the Segment C consolidation diff:
#
#   intelligence:1569
#     - net_debt = (BS["short_term_debt"][ys] + BS["long_term_debt"][ys]
#     -             - BS["cash"][ys])
#     + _debt = fin._n(lambda a, b: a + b,
#     +                BS["short_term_debt"][ys], BS["long_term_debt"][ys])
#     + net_debt = ratios.net_debt(_debt, BS["cash"][ys])
#
#   valuation:542
#     - net_debt = (bs["short_term_debt"][ys] + bs["long_term_debt"][ys]
#     -             - bs["cash"][ys])
#     + _debt = fin._n(lambda a, b: a + b,
#     +                bs["short_term_debt"][ys], bs["long_term_debt"][ys])
#     + net_debt = ratios.net_debt(_debt, bs["cash"][ys])
#
# At both, `std + ltd` was already there as a sub-expression of the net-debt
# statement. The guard does not descend into a matched node, so it was never
# counted. Naming it made it visible. Places total debt is formed: unchanged.
#
# ⭐ ONE HONEST QUALIFICATION: the extracted form is `fin._n(a + b)`, not raw
# `a + b`, so on the ABSENCE path it now yields None where the raw form raised.
# Same value wherever a value existed; a different outcome where none did. The
# test above says "computing the same value", and that holds — but the
# qualification belongs on the record, because "identical" would be too strong.
#
# ⭐ RAISING A RATCHET IS NORMALLY FORBIDDEN. It is permitted here, once, and
# only because nothing in the codebase changed — the detector started seeing a
# site that was always there. Lowering it to 14 to keep the guard quiet would
# have hidden a real site; leaving it at 14 would have failed forever on a
# number that was never right. Both are worse than saying so.
#
# THERE ARE 15, ACROSS 5 FILES — 10 IN ONE.
#     intelligence/engines.py   10
#     financials/engines.py      3   (:309 and :609 are both _n forms)
#     sentinel.py                1   (:145, inside the _debt_book function)
#     prescience_decision.py     1   (:240, the base term under the debt_scale shock)
#     valuation/engines.py       1   (:126)
# Recorded as a RATCHET at the measured truth, not at the expected 3: a guard
# pinned to a number the codebase never had is permanently red for a reason
# nobody can action, and gets muted. The number may only go DOWN.
#
# The finding this produces is not "16 is wrong" — total debt is a legitimate
# term to form. It is that intelligence/engines.py re-derives it TEN times by
# hand, and every one of those is a place net debt can be re-derived tomorrow
# without touching the library. That is a consolidation lane of its own.
# ⭐ MEASURED AT 2, NOT PREDICTED. Invested capital is ROIC's DENOMINATOR, so
# ROIC's "single owner" status was only ever true of its numerator: the ratio is
# one expression over another and only one of the two was guarded.
#
#     financials/engines.py:314    _n(lambda d,e,pe,mi,c: d+e+pe+mi-c, ...)
#     intelligence/engines.py:594  debt0 + total_equity + preferred + minority - cash
#
# ⭐ SO ROIC SOLE-OWNERSHIP IS A TARGET, NOT A STATE. Recorded as such. The
# ratchet may only go down; consolidating IC is its own segment.
#
# Calibration (standing law: an expected count is meaningless until the counter
# is calibrated against a known population) found TWO detector defects before
# this number was trusted — `_key_of` could not see through `.get(ys)`, and the
# equity operand is a local named `equity` at one site and BS["total_equity"] at
# the other. Uncalibrated, it would have reported 1.
IC_SITES = [LIBRARY]      # consolidated in Segment E
TOTAL_DEBT_SITES = [
    "services/api/sentinel.py",
    "services/api/modules/valuation/engines.py",
    "services/api/prescience_decision.py",
    "services/api/modules/financials/engines.py",
    "services/api/modules/intelligence/engines.py",
]
# net_debt is CONSOLIDATED — its allowlist is the library and nothing else.
# roic / eva / wacc are single-site but still live in engines.py; moving them is
# Segment D (wacc) and Segment E (roic, after invested capital). Their allowlist
# names the CURRENT home with the owning segment, so the guard is red only on
# real violations — a guard red on work that has not been scheduled yet is
# noise, and noise is how a red stops being read.
ENGINES = "services/api/modules/financials/engines.py"

# ⭐⭐ THE PEER SITE IS ALLOWLISTED BY RULING, AND THE RULING HAS A CONDITION.
# R5 (2 Aug): "Keep both ROICs; label the peer figure as computed on a reduced
# basis. Aligning downward would make a company's headline ROIC differ from its
# benchmark ROIC. The silence is the defect, not the difference."
#
# So this entry is not an excuse — it is the second half of a ruling whose first
# half is a disclosure. `label_control()` fails the build if the disclosure goes
# missing, which makes the allowlist entry conditional on the thing that
# justifies it. An allowlist that outlives its reason is how a guard becomes
# decoration.
PEERS = "services/api/modules/benchmarks/engines.py"
ALLOWLIST = {"net_debt": [LIBRARY],
             "roic": [ENGINES, PEERS],  # -> LIBRARY in Segment E (after IC)
             "eva": [ENGINES],         # -> LIBRARY in Segment E
             "wacc": [LIBRARY],        # consolidated in D-1
             # total_debt is COUNTED, not consolidated — see
             # _total_debt_shape. Its allowlist is the set of
             # callers legitimately forming the base term.
             "total_debt": TOTAL_DEBT_SITES,
             "invested_capital": IC_SITES + [PEERS]}
EXPECTED = {"net_debt": 1, "roic": 2, "eva": 1, "wacc": 1,
            "total_debt": 17, "invested_capital": 2}

# The disclosure R5 requires, and where it lives. Checked as SUBSTANCE, not as a
# string: the note must name what the peer basis omits.
LABEL_SITE = PEERS
LABEL_MUST_MENTION = ("preferred", "minority", "reduced basis")

SCAN_DIRS = ["services/api"]
SKIP = {"__pycache__"}


# ⭐⭐ LOCAL NAMES ARE RESOLVED TO WHAT THEY WERE BOUND FROM. Set per module by
# the Finder; consulted by `_key_of` as a last resort, never before the
# structural reading. See `alias_map` for why this exists.
ALIASES = {}

# Registry formulas wrap operands in the evaluator's own functions. `avg(x)` and
# `prior(x)` are period selectors — they do not change WHICH quantity is meant,
# so an operand recogniser must see through them exactly as it sees through
# `.get(...)`. Without this, `avg(axiom.invested_capital)` reads as None and the
# registry's ROIC goes uncounted.
_TRANSPARENT_CALLS = {"avg", "prior", "abs"}


# ── operand recognisers: what does this expression MEAN, not what is it called ─
def _key_of(node):
    """The last constant string subscript, or the bare name: bs["cash"][ys] -> cash.

    ⭐ IT MUST SEE THROUGH `.get(...)` TOO. Calibration against a known
    population caught this: the inline invested-capital site was detected and
    the `_n` one was not, because financials writes
    `BS["preferred_equity"].get(ys)` — a Call, not a Subscript — and the
    recogniser returned None for every such operand. The counter would have
    reported 1 where there are 2, and an expected count taken from an
    uncalibrated counter is a number about the counter, not the codebase.

    ⭐⭐ AND IT MUST SEE THROUGH A LOCAL NAME TO WHAT THE LOCAL WAS BOUND FROM.
    This is the fix for the breach the guard was missing. `benchmarks:100`
    writes `ebit * (1 - tax_rate) / (td + te - cash)`, where `td` and `te` come
    from `ta, te, td = g("total_assets"), g("total_equity"), g("total_debt")`.
    Every operand recogniser here compared `_key_of` against a fixed vocabulary
    of spellings — `total_equity`, `equity` — so a two-letter local matched
    nothing and a second ROIC read as zero sites.

    A guard whose docstring says "enforced by SHAPE" and which is in fact
    enforced by VARIABLE NAME is the §III.9 shape one level up: the rule states
    a stronger claim than the mechanism delivers. `check-ratio-shapes.py`
    predicted this exact failure in writing — "a second ROIC that computes its
    own denominator inline INVISIBLE" — and it was already in the tree.

    ⭐ THE ALIAS LOOKUP IS LAST, AND ONLY ADDS. A name that already reads as a
    key keeps that reading, so no existing detection can be lost by resolving
    aliases — the direction that matters under the standing law below."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "get":
        node = node.func.value
    # registry period selectors: avg(x) / prior(x) mean the same quantity as x
    while (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
           and node.func.id in _TRANSPARENT_CALLS and len(node.args) == 1):
        node = node.args[0]
    while isinstance(node, ast.Subscript):
        k = node.slice
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            return k.value
        node = node.value
    # registry tokens are dotted: bs.short_term_debt -> short_term_debt
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return ALIASES.get(node.id, node.id)
    return None


def alias_map(tree):
    """name -> the string key it was bound from, within one module.

    Recognises the two binding forms this codebase actually uses:

        td = g("total_debt")                      a keyed accessor call
        ta, te, td = g("total_assets"), g("total_equity"), g("total_debt")

    ⭐ IT DOES NOT FOLLOW ARITHMETIC. `debt = std + ltd` binds a name to an
    EXPRESSION, and calling that alias "short_term_debt" would make the guard
    assert an operand identity the code does not have. Only a direct keyed read
    is followed; anything else leaves the name reading as itself.

    ⭐ AND IT NEVER OVERWRITES A REBOUND NAME WITH AN OLDER READING. A name
    assigned twice from different keys is dropped rather than guessed — an alias
    that is wrong is worse than an alias that is absent, because it produces a
    confident match on the wrong quantity."""
    def keyed(v):
        # g("total_equity") / _series(IS, "revenue", years) — a constant string arg
        if isinstance(v, ast.Call):
            consts = [a.value for a in v.args
                      if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if len(consts) == 1:
                return consts[0]
        # BS["total_equity"].get(ys) / bs["cash"][ys]
        if isinstance(v, (ast.Subscript, ast.Call)):
            k = _key_of(v)
            if k and not isinstance(v, ast.Name):
                return k
        return None

    out, conflicted = {}, set()

    def bind(target, value):
        if not isinstance(target, ast.Name):
            return
        k = keyed(value)
        if not k:
            return
        if target.id in out and out[target.id] != k:
            conflicted.add(target.id)
        out[target.id] = k

    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign) or len(n.targets) != 1:
            continue
        t, v = n.targets[0], n.value
        if isinstance(t, ast.Tuple) and isinstance(v, ast.Tuple) \
                and len(t.elts) == len(v.elts):
            for tt, vv in zip(t.elts, v.elts):
                bind(tt, vv)
        else:
            bind(t, v)
    for c in conflicted:
        out.pop(c, None)
    return out


def _is_cash(n):
    k = _key_of(n)
    return bool(k) and k == "cash"


def _is_debt_component(n):
    k = _key_of(n)
    return k in ("short_term_debt", "long_term_debt")


def _is_debt_aggregate(n):
    """A single operand that already stands for total debt."""
    k = _key_of(n)
    return bool(k) and ("debt" in k) and k not in ("net_debt",) \
        and not _is_debt_component(n)


def _net_debt_shape(node):
    """<debt> - <cash>, in either the three-operand or two-operand form."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)):
        return False
    if not _is_cash(node.right):
        return False
    left = node.left
    # three-operand: (short_term_debt + long_term_debt) - cash
    if isinstance(left, ast.BinOp) and isinstance(left.op, ast.Add):
        if _is_debt_component(left.left) and _is_debt_component(left.right):
            return True
    # two-operand: <debt aggregate> - cash   (valuation:135)
    return _is_debt_aggregate(left)


def _n_call_shape(node):
    """⭐ _n(lambda a, b: a - b, debt, cash) — the operands are the CALL ARGS.

    financials:328 writes it this way, so the BinOp inside the lambda carries
    only placeholder names. The meaning lives one level out, in what is passed."""
    if not (_is_n_call(node) and len(node.args) == 3):
        return False
    fn = node.args[0]
    if not isinstance(fn, ast.Lambda):
        return False
    body = fn.body
    if not (isinstance(body, ast.BinOp) and isinstance(body.op, ast.Sub)):
        return False
    a, b = node.args[1], node.args[2]
    return (_is_debt_aggregate(a) or _is_debt_component(a)) and _is_cash(b)


_NOPAT_KEYS = {"nopat", "n_"}
_IC_KEYS = {"ic", "invested_capital"}
_EBIT_KEYS = {"ebit", "e", "operating_profit"}
_TAX_KEYS = {"tax_rate", "tax_rate_policy", "t", "T", "tax"}


def _is_nopat(n):
    """A name meaning NOPAT, or NOPAT written out: <ebit> * (1 - <tax rate>).

    ⭐ THE INLINE FORM IS THE ONE THAT WAS INVISIBLE. Requiring the literal name
    `nopat` meant the guard could only find a NOPAT somebody had already named,
    which is precisely the site least likely to be a stray copy."""
    if _key_of(n) in _NOPAT_KEYS:
        return True
    if not (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult)):
        return False

    def _one_minus_tax(x):
        return (isinstance(x, ast.BinOp) and isinstance(x.op, ast.Sub)
                and isinstance(x.left, ast.Constant) and x.left.value in (1, 1.0)
                and _key_of(x.right) in _TAX_KEYS)

    return ((_key_of(n.left) in _EBIT_KEYS and _one_minus_tax(n.right))
            or (_key_of(n.right) in _EBIT_KEYS and _one_minus_tax(n.left)))


def _is_ic(n):
    """A name meaning invested capital, or invested capital written out —
    on either the full basis or the reduced one. See `_ic_shape`."""
    return _key_of(n) in _IC_KEYS or _ic_shape(n)


def _roic_shape(node):
    """<nopat> / <invested capital>, with both operands read by MEANING."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
        return False
    return _is_nopat(node.left) and _is_ic(node.right)


def _roic_n_shape(node):
    if not (_is_n_call(node) and len(node.args) == 3):
        return False
    fn = node.args[0]
    if not (isinstance(fn, ast.Lambda) and isinstance(fn.body, ast.BinOp)
            and isinstance(fn.body.op, ast.Div)):
        return False
    return _is_nopat(node.args[1]) and _is_ic(node.args[2])


def _eva_shape(node):
    """<nopat> - <wacc> * <invested capital>, direct or through _n."""
    def _sub_mult(b):
        if not (isinstance(b, ast.BinOp) and isinstance(b.op, ast.Sub)):
            return False
        r = b.right
        return (isinstance(r, ast.BinOp) and isinstance(r.op, ast.Mult)
                and _key_of(b.left) in ("nopat", "n_")
                and _key_of(r.left) in ("wacc", "w") or False)
    if _sub_mult(node):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id == "_n" and node.args:
        fn = node.args[0]
        if isinstance(fn, ast.Lambda) and _sub_mult(fn.body):
            return True
    # ⭐⭐ THE SPREAD FORM: (roic - wacc) * ic, optionally scaled by 100.
    # EVA has two standard spellings — `nopat - wacc*ic` and `(roic - wacc)*ic`
    # — which are algebraically identical and structurally unrelated. The guard
    # knew only the first, and `axiom.eva` in the registry is written the
    # second way, so the registry scan found four of the five duplicates and
    # reported the fifth as absent. This file's own closing note names that
    # blind spot in general terms ("a duplicate that reorders into an
    # algebraically equal but structurally different form is not matched"); a
    # named instance of it is a shape to add, not a limitation to restate.
    if _spread_eva(node):
        return True
    return False


def _spread_eva(node):
    """(<roic> - <wacc>) * <invested capital>, with or without a /100 scale."""
    def _unscale(n):
        # strip a trailing / 100 or * 0.01 — a unit conversion, not a definition
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) \
                and isinstance(n.right, ast.Constant) and n.right.value == 100:
            return n.left
        return n

    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult)):
        return False
    for a, b in ((node.left, node.right), (node.right, node.left)):
        spread = _unscale(a)
        if not (isinstance(spread, ast.BinOp) and isinstance(spread.op, ast.Sub)):
            continue
        if _key_of(spread.left) in ("roic",) and _key_of(spread.right) in ("wacc",) \
                and _is_ic(b):
            return True
    return False


def _wacc_shape(node):
    """The cost-of-capital blend: ke * we + kd * (1 - T) * wd, in any spelling."""
    if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)):
        return False
    txt = ast.unparse(node)
    return ("ke" in txt and "kd" in txt and "*" in txt and
            ("1 - " in txt or "1.0 - " in txt))




def _is_n_call(node):
    """`_n(...)` OR `fin._n(...)`.

    ⭐ CAUGHT BY THE CONSOLIDATION ITSELF. valuation:126 became
    `fin._n(lambda a, b: a + b, ...)` and the total-debt count silently fell
    15 -> 14, because the recogniser matched only a bare Name `_n`. The site had
    not gone anywhere; the detector stopped seeing it the moment the call was
    written through the module alias — a counter that drops when code is
    IMPROVED reports a fix as a removal."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    return ((isinstance(f, ast.Name) and f.id == "_n")
            or (isinstance(f, ast.Attribute) and f.attr == "_n"))


def _total_debt_shape(node):
    """<short_term_debt> + <long_term_debt> — the base term, direct or via _n.

    ⭐ A COUNT, NOT A CONSOLIDATION. Total debt is a legitimate quantity for
    several callers to form; what must not happen is a FOURTH appearing without
    anyone noticing, because each one is a place net debt can be re-derived by
    hand tomorrow."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_debt_component(node.left) and _is_debt_component(node.right)
    if _is_n_call(node) and len(node.args) == 3:
        fn = node.args[0]
        if (isinstance(fn, ast.Lambda) and isinstance(fn.body, ast.BinOp)
                and isinstance(fn.body.op, ast.Add)):
            return (_is_debt_component(node.args[1])
                    and _is_debt_component(node.args[2]))
    return False



# The equity operand is spelled `BS["total_equity"]` at one site and a local
# named `equity` at the other. Calibration surfaced the second; matching only
# the first would have counted 1 where there are 2.
_EQUITY_KEYS = {"total_equity", "equity"}
# ⭐ THE LIBRARY'S OWN PARAMETERS ARE preferred / minority, NOT
# preferred_equity / minority_interest. Folding both sites onto it dropped the
# count to ZERO — the counter could not see the sole owner it had just been
# given. Third instance of the standing law this era: a counter that falls when
# code improves reports a fix as a removal, and a ratchet welcomes it.
_PREF_KEYS = {"preferred_equity", "preferred"}
_MINO_KEYS = {"minority_interest", "minority"}
# An aggregate debt term standing in the invested-capital chain. Components
# (short/long term) are NOT here: two of those with no equity is net debt.
_DEBT_KEYS = {"total_debt", "debt", "debt0", "td"}


def _is_equity(n):
    return _key_of(n) == "total_equity"


def _ic_shape(node):
    """<debt> + <equity> + <preferred> + <minority> - <cash> — invested capital.

    ⭐ ROIC's DENOMINATOR. Sole ownership of ROIC is hollow while invested
    capital has copies: the ratio is one expression over another, and only one
    of the two was being guarded.

    Matched by composition, not by the variable name `ic`: the add-chain must
    carry total_equity and at least one of preferred_equity / minority_interest,
    and the whole thing must subtract cash. That distinguishes it from net debt
    (whose add-chain is two DEBT components) without relying on either site
    spelling the local the same way.
    """
    def _chain_keys(n, out):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            _chain_keys(n.left, out); _chain_keys(n.right, out)
        else:
            k = _key_of(n)
            if k:
                out.add(k)
        return out

    def _match(sub):
        if not (isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Sub)):
            return False
        if not _is_cash(sub.right):
            return False
        keys = _chain_keys(sub.left, set())
        if not (keys & _EQUITY_KEYS):
            return False
        # full basis: equity plus at least one of preferred / minority
        if keys & (_PREF_KEYS | _MINO_KEYS):
            return True
        # ⭐⭐ THE REDUCED BASIS — RULED KEPT (R5, 2 Aug), THEREFORE RULED VISIBLE.
        # `td + te - cash` at benchmarks:100 is invested capital computed without
        # preferred equity or minority interest, because peer disclosures do not
        # carry them. The ruling keeps both definitions and labels the peer one;
        # what it does not permit is the guard reporting ONE site while two
        # definitions ship. An equity-and-debt chain less cash is invested
        # capital on any basis, so it counts here and earns its allowlist entry
        # with a stated reason, rather than passing by being unseen.
        #
        # It cannot be confused with net debt: net debt's add-chain is two DEBT
        # components and carries no equity term at all.
        return bool(keys & _DEBT_KEYS)

    if _match(node):
        return True
    # the _n form: _n(lambda d, e, pe, mi, c: d + e + pe + mi - c, ...args)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "_n" and len(node.args) >= 4):
        fn = node.args[0]
        if isinstance(fn, ast.Lambda) and isinstance(fn.body, ast.BinOp) \
                and isinstance(fn.body.op, ast.Sub):
            argkeys = {_key_of(a) for a in node.args[1:]}
            return (bool(argkeys & _EQUITY_KEYS)
                    and bool(argkeys & (_PREF_KEYS | _MINO_KEYS))
                    and "cash" in argkeys)
    return False


SHAPES = {"net_debt": (_net_debt_shape, _n_call_shape),
          "invested_capital": (_ic_shape,),
          "total_debt": (_total_debt_shape,),
          "roic": (_roic_shape, _roic_n_shape),
          "eva": (_eva_shape,),
          "wacc": (_wacc_shape,)}


class Finder(ast.NodeVisitor):
    def __init__(self, rel, src, aliases=None):
        global ALIASES
        self.rel, self.src = rel, src
        self.hits = {k: [] for k in SHAPES}
        # module-scoped: a local named `te` means total_equity HERE and may mean
        # nothing anywhere else.
        ALIASES = aliases or {}

    def generic_visit(self, node):
        for kind, fns in SHAPES.items():
            if any(f(node) for f in fns):
                txt = ast.unparse(node)[:70]
                if not any(self.rel == p and frag in self.src
                           and frag in txt for p, frag in COLLISION_EXCLUSIONS):
                    self.hits[kind].append((node.lineno, txt))
                # ⭐ DO NOT DESCEND INTO A MATCHED NODE. `_n(lambda n_, i_:
                # n_ - w["wacc"] * i_, ...)` matches, and so does the BinOp in
                # its own lambda body — one expression counted twice. A guard
                # whose count is inflated by its own recursion cannot be
                # compared against an expected count, which is the whole
                # mechanism here.
                return
        super().generic_visit(node)



# ⭐⭐ STANDING LAW — A COUNTER THAT FALLS WHEN CODE IMPROVES IS A LOOSENED GUARD,
# SILENTLY. Observed 31 Jul: rewriting valuation:126 from `a + b` to
# `fin._n(lambda a, b: a + b, ...)` — a strict improvement, absence now
# propagates — dropped total-debt 15 -> 14, because the recogniser matched a
# bare Name `_n` and not the module-qualified `fin._n`. A DOWNWARD-ONLY RATCHET
# ACCEPTS THAT WITHOUT COMPLAINT: the count went down, which is the direction it
# is built to welcome. The guard would have been permanently loosened by a
# correct refactor, and nothing would have said so.
#
# So every shape carries a negative control: the SAME arithmetic written in
# every form the codebase actually uses must yield the SAME count. If a form is
# added to the codebase that this list does not know, the control is what fails.
EQUIVALENT_FORMS = {
    "total_debt": [
        'x = bs["short_term_debt"][ys] + bs["long_term_debt"][ys]',
        'x = _n(lambda a, b: a + b, bs["short_term_debt"][ys], bs["long_term_debt"][ys])',
        'x = fin._n(lambda a, b: a + b, bs["short_term_debt"][ys], bs["long_term_debt"][ys])',
        'x = _n(lambda a, b: a + b, BS["short_term_debt"].get(ys), BS["long_term_debt"].get(ys))',
    ],
    "invested_capital": [
        'ic = debt0 + bs["total_equity"][ys] + bs["preferred_equity"][ys] + bs["minority_interest"][ys] - bs["cash"][ys]',
        'ic = _n(lambda d,e,pe,mi,c: d+e+pe+mi-c, debt, equity, BS["preferred_equity"].get(ys), BS["minority_interest"].get(ys), cash)',
        'ic = _n(lambda d,e,pe,mi,c: d+e+pe+mi-c, debt, equity, preferred, minority, cash)',
    ],
    "eva": [
        'x = _n(lambda n_, i_: n_ - w["wacc"] * i_, nopat_, ic_)',
        'x = (roic - wacc) / 100 * ic',
        'x = (roic - wacc) * invested_capital',
    ],
    "net_debt": [
        'x = bs["short_term_debt"][ys] + bs["long_term_debt"][ys] - bs["cash"][ys]',
        'x = company["_debt_book"] - bs["cash"][ys]',
        'x = _n(lambda a, b: a - b, debt, cash)',
        'x = fin._n(lambda a, b: a - b, debt, cash)',
    ],
}


# ── ⭐⭐ THE REGISTRY IS SCANNED TOO, BECAUSE IT IS ABOUT TO BECOME CODE ───────
#
# This guard walked `.py` files under services/api and nothing else. The ratio
# registry holds 79 formulas in YAML, four of which restate a quantity this file
# exists to keep single. While the registry is inert that is a documentation
# problem; the moment it is EVALUATED (R7, 2 Aug — read at compute time) it is a
# second implementation, and the guard would have printed "✓ sole ownership
# holds" throughout, because a `.yaml` file was never opened.
#
# ⭐ THE EXEMPTION IS TIED TO NON-EXECUTION, NOT ASSERTED. A registry formula is
# allowed to restate a guarded quantity ONLY while nothing reads the registry at
# runtime. `registry_readers()` measures that rather than trusting it: the day a
# module under services/ loads the file, these four must delegate — which is
# R2's ruling, enforced at exactly the moment it starts to matter, and not one
# lane before.
REGISTRY = os.path.join("docs", "reference", "axiom_ratio_registry.yaml")
REGISTRY_SPEC_SITES = {
    "net_debt": "axiom.net_debt",
    "invested_capital": "axiom.invested_capital",
    "roic": "axiom.roic",
    "eva": "axiom.eva",
    "total_debt": "bs.total_debt",
}


# ⭐⭐ `is` IS A PYTHON KEYWORD, AND THE INCOME STATEMENT IS THE `is.` NAMESPACE.
# Caught by the capability control on its first run: `is.gross_profit /
# is.revenue * 100` raises SyntaxError, so EVERY income-statement formula — the
# largest token group in the registry, and the one carrying EBIT, PAT and every
# margin — was landing in the `except SyntaxError` branch and being skipped. The
# scan would have reported its remaining matches and printed no error at all.
#
# This is the reason a control has to be a KNOWN POSITIVE rather than a smoke
# test. Nothing about the output looked wrong: it found the net-debt and
# total-debt duplicates, which live in the `bs.` namespace and parse fine.
#
# The rename is prefix-only and preserves the Attribute structure `_key_of`
# reads, so `IS_.gross_profit` yields exactly the key `is.gross_profit` would.
_IS_PREFIX = re.compile(r'\bis\.')


def _parseable(formula):
    return _IS_PREFIX.sub("IS_.", formula)


def registry_readers():
    """Modules under services/ that open the registry. Empty == inert.

    ⭐⭐ AN AST READ, AND THE FIRST RUN IS WHY. Written as a substring search,
    this reported `services/api/pack_render.py` as a runtime reader and failed
    the build. That module does not load the registry — its DOCSTRING says the
    registry is loaded by nothing but a CI guard, and the search matched the
    sentence describing the absence.

    §III.9, ninth instance, and the first one inside a control written in the
    same lane as the rule it enforces: a check keyed on text punishes the file
    that states the check's own subject. A docstring is not an import."""
    out = []
    for base, dirs, files in os.walk(os.path.join(ROOT, "services")):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            p = os.path.join(base, f)
            try:
                tree = ast.parse(open(p, encoding="utf-8").read())
            except (OSError, SyntaxError):
                continue
            docs = set()
            for n in ast.walk(tree):
                if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                  ast.AsyncFunctionDef)):
                    d = ast.get_docstring(n, clean=False)
                    if d:
                        docs.add(d)
            for n in ast.walk(tree):
                if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                        and "axiom_ratio_registry" in n.value
                        and n.value not in docs):
                    out.append(os.path.relpath(p, ROOT))
                    break
    return out


def scan_registry():
    """-> {kind: [(ratio_id, formula)]}. Every formula parsed as an expression.

    ⭐ THE SHAPE FUNCTIONS ARE REUSED UNCHANGED. A registry token is an
    Attribute (`bs.cash`) where Python writes a Subscript (`bs["cash"]`); once
    `_key_of` reads both, `bs.short_term_debt + bs.long_term_debt - bs.cash` and
    its Python twin are the SAME SHAPE to this guard. That is the point — a
    duplicate that changes file format is still a duplicate."""
    global ALIASES
    hits = {k: [] for k in SHAPES}
    path = os.path.join(ROOT, REGISTRY)
    try:
        import yaml
        doc = yaml.safe_load(open(path, encoding="utf-8"))
    except Exception as e:
        return hits, f"{type(e).__name__}: {e}"

    exprs = [(r["id"], r["formula"]) for r in (doc.get("ratios") or [])
             if isinstance(r.get("formula"), str)]
    for grp in (doc.get("vocabulary") or {}).values():
        for tok, meta in (grp or {}).items():
            if isinstance(meta, dict) and isinstance(meta.get("expr"), str):
                exprs.append((tok, meta["expr"]))

    ALIASES = {}
    parsed, skipped = 0, []
    for rid, formula in exprs:
        try:
            tree = ast.parse(_parseable(formula), mode="eval")
        except SyntaxError:
            # placeholders and prose exprs. NAMED, never silently swallowed —
            # a skip that prints nothing is indistinguishable from a clean pass.
            skipped.append(rid)
            continue
        parsed += 1
        # ⭐ DO NOT DESCEND INTO A MATCHED NODE — the same law the Python
        # Finder carries, and I did not carry it here on the first pass.
        # `axiom.net_debt` is `bs.short_term_debt + bs.long_term_debt - bs.cash`;
        # walking every node counted it once as NET_DEBT and again as TOTAL_DEBT
        # for its own inner add-chain, then reported the second as an
        # "UNEXPECTED registry site". One expression, two accusations.
        stack = [tree.body]
        while stack:
            node = stack.pop()
            matched = False
            for kind, fns in SHAPES.items():
                if any(f(node) for f in fns):
                    hits[kind].append((rid, formula[:64]))
                    matched = True
                    break
            if not matched:
                stack.extend(ast.iter_child_nodes(node))
    note = f"{parsed}/{len(exprs)} expressions parsed"
    if skipped:
        note += f"; {len(skipped)} unparseable: {', '.join(sorted(skipped))}"
    return hits, note


def form_control():
    """Every equivalent spelling of a shape must be detected. Returns failures."""
    bad = []
    for kind, forms in EQUIVALENT_FORMS.items():
        fns = SHAPES[kind]
        for src in forms:
            tree = ast.parse(src)
            if not any(any(f(n) for f in fns) for n in ast.walk(tree)):
                bad.append((kind, src))
    return bad


# ── ⭐ CONTROLS FOR THE TWO NEW CAPABILITIES — IN MEMORY, NOTHING WRITTEN ─────
# The planted-control leak has happened four times. Nothing below touches disk.
#
# A control that only proves detection is half a control: a recogniser that
# matched everything would pass it. Each block therefore carries a POSITIVE that
# must fire and a NEGATIVE that must not.
_ALIAS_POSITIVE = (
    'def f(peer, tax_rate):\n'
    '    ta, te, td = g("total_assets"), g("total_equity"), g("total_debt")\n'
    '    cash = g("cash")\n'
    '    out["roic"] = ebit * (1 - tax_rate) / (td + te - cash)\n')
_ALIAS_NEGATIVE = (
    # same arithmetic SHAPE, operands that mean something else entirely — an
    # alias resolver that fired here would be matching punctuation, not meaning
    'def f():\n'
    '    a, b = g("headcount"), g("payroll_cost")\n'
    '    c = g("revenue")\n'
    '    out["x"] = a * (1 - rate) / (b + c - other)\n')
_REGISTRY_POSITIVE = "bs.short_term_debt + bs.long_term_debt - bs.cash"
_REGISTRY_NEGATIVE = "is.gross_profit / is.revenue * 100"   # also the `is` keyword control


def _fires(src, kind, aliases=None, mode="exec"):
    global ALIASES
    tree = ast.parse(_parseable(src) if mode == "eval" else src, mode=mode)
    ALIASES = aliases if aliases is not None else alias_map(tree)
    return any(any(f(n) for f in SHAPES[kind]) for n in ast.walk(tree))


def capability_control():
    """-> list of failures. Proves the two new capabilities work BOTH ways."""
    global ALIASES
    bad = []
    if not _fires(_ALIAS_POSITIVE, "roic"):
        bad.append("alias resolution does NOT detect an inline peer-style ROIC "
                   "— the breach this lane exists to fix would still be missed")
    if _fires(_ALIAS_NEGATIVE, "roic"):
        bad.append("alias resolution fires on unrelated operands of the same "
                   "shape — it is matching arithmetic, not meaning")
    if not _fires(_REGISTRY_POSITIVE, "net_debt", aliases={}, mode="eval"):
        bad.append("registry formulas are NOT matched — a YAML net debt would "
                   "be invisible, which is the precondition this lane requires")
    if _fires(_REGISTRY_NEGATIVE, "net_debt", aliases={}, mode="eval"):
        bad.append("registry scan fires on a plain margin — it would report "
                   "every percentage in the file as a guarded quantity")
    ALIASES = {}
    return bad


def label_control():
    """R5's disclosure must exist, or the peer allowlist entry loses its reason."""
    try:
        src = open(os.path.join(ROOT, LABEL_SITE), encoding="utf-8").read()
        tree = ast.parse(src)
    except (OSError, SyntaxError) as e:
        return [f"{LABEL_SITE}: {type(e).__name__}"]
    # ⭐ AN AST READ, NOT A TEXT SEARCH — AND THE FIRST RUN PROVED WHY. The note
    # is written as adjacent string literals across seven source lines, so
    # "reduced basis" falls across a line break and a substring search over the
    # file reported it missing while the shipped string contained it. Python
    # joins adjacent literals at parse time, so the Constant carries the whole
    # note. Searching source text would also have matched the explanatory
    # COMMENT above it, passing on prose that never reaches a reader — the
    # §III.9 shape, in the guard written to enforce a disclosure.
    served = [n.value for n in ast.walk(tree)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    missing = [m for m in LABEL_MUST_MENTION
               if not any(m in s for s in served)]
    return ([f"the peer ROIC disclosure no longer states: {missing}"]
            if missing else [])


def main():
    found = {k: [] for k in SHAPES}
    for d in SCAN_DIRS:
        for base, dirs, files in os.walk(os.path.join(ROOT, d)):
            dirs[:] = [x for x in dirs if x not in SKIP]
            for f in sorted(files):
                if not f.endswith(".py"):
                    continue
                path = os.path.join(base, f)
                rel = os.path.relpath(path, ROOT)
                try:
                    src = open(path, encoding="utf-8").read()
                    tree = ast.parse(src)
                except Exception:
                    continue
                fi = Finder(rel, src, alias_map(tree))
                fi.visit(tree)
                for k, hits in fi.hits.items():
                    for ln, txt in hits:
                        found[k].append((rel, ln, txt))

    rc = 0

    # ── equivalent-form control, before any count is believed ───────────────
    bad_forms = form_control()
    if bad_forms:
        print("  ✗ FORM CONTROL FAILED — a spelling this codebase uses is not\n"
              "    detected, so the count below is an undercount and the ratchet\n"
              "    would silently loosen:")
        for kind, src in bad_forms:
            print(f"      {kind}: {src}")
        print()
        rc = 1
    else:
        print(f"  ✓ form control: {sum(len(v) for v in EQUIVALENT_FORMS.values())} "
              f"equivalent spellings all detected\n")

    # ── the two new capabilities, positive AND negative, before any count ────
    bad_cap = capability_control()
    if bad_cap:
        print("  ✗ CAPABILITY CONTROL FAILED — the counts below are unreadable:")
        for b in bad_cap:
            print(f"      {b}")
        print()
        rc = 1
    else:
        print("  ✓ capability control: alias resolution and the registry scan "
              "each fire on a\n    known positive and stay silent on a "
              "same-shaped negative\n")

    bad_label = label_control()
    if bad_label:
        print("  ✗ R5 DISCLOSURE MISSING — the peer allowlist entry exists only\n"
              "    because the reduced basis is disclosed. Without the note the\n"
              "    entry is an exemption with no reason, so the build fails\n"
              "    rather than the silence returning:")
        for b in bad_label:
            print(f"      {b}")
        print()
        rc = 1
    else:
        print("  ✓ R5 disclosure present: the peer ROIC states its reduced "
              "basis\n")

    # ── the name collision, asserted rather than skipped ────────────────────
    cpath, cfrag = COLLISION_SITE
    csrc = ""
    try:
        csrc = open(os.path.join(ROOT, cpath), encoding="utf-8").read()
    except OSError:
        pass
    if cfrag not in csrc:
        print(f"  ✗ COLLISION SITE GONE: {cpath} no longer contains {cfrag!r}.\n"
              f"    deterministic[\"net_debt\"] is the DCF bridge's own figure, not\n"
              f"    the ratios net debt. If it was repointed at the library, the\n"
              f"    bridge now reads a ratio computed on a different period basis —\n"
              f"    the defect wearing the fix's clothes. If it was renamed on\n"
              f"    purpose, update COLLISION_SITE deliberately.\n")
        rc = 1
    else:
        # ⭐ SCOPED TO THE ASSIGNMENT, NOT THE FILE. After consolidation
        # valuation/engines.py legitimately contains "ratios.net_debt" — the
        # line above the bridge calls it. Searching the whole file fired on the
        # fix. The question is only ever whether the COLLIDING KEY was
        # repointed, so look at that statement.
        keyline = next((l for l in csrc.split("\n") if cfrag in l), "")
        bad = [m for m in COLLISION_MUST_NOT_CONTAIN if m in keyline]
        if bad:
            print(f"  ✗ COLLISION SITE REPOINTED AT THE LIBRARY: {bad}\n")
            rc = 1
        else:
            print(f"  ✓ name collision intact and unwired: "
                  f"{cpath} keeps its own net_debt\n")

    for kind in ("net_debt", "total_debt", "invested_capital",
                 "roic", "eva", "wacc"):
        hits = found[kind]
        files = sorted({r for r, _l, _t in hits})
        allowed = ALLOWLIST[kind]
        print(f"  {kind.upper():<9} {len(hits)} site(s) in {len(files)} file(s) "
              f"· expected {EXPECTED[kind]}")
        for r, ln, t in hits:
            print(f"      {r}:{ln}  {t}")

        # direction 1: a shape in a file nobody allowlisted
        strays = [f for f in files if f not in allowed]
        if strays:
            print(f"      ✗ NOT ALLOWLISTED: {strays}")
            rc = 1
        # direction 2: an allowlist entry that no longer matches
        stale = [f for f in allowed if f not in files]
        if stale:
            print(f"      ✗ STALE ALLOWLIST ENTRY (no longer matches): {stale}")
            rc = 1
        if EXPECTED[kind] is not None and len(hits) != EXPECTED[kind]:
            print(f"      ✗ COUNT {len(hits)} != expected {EXPECTED[kind]}")
            rc = 1
        print()

    # ── ⭐⭐ THE REGISTRY, WHICH THIS GUARD COULD NOT SEE UNTIL NOW ───────────
    reg, note = scan_registry()
    readers = registry_readers()
    print(f"  REGISTRY  {REGISTRY}  ({note})")
    print(f"    runtime readers under services/: "
          f"{readers if readers else 'NONE — the registry is inert'}")
    total = sum(len(v) for v in reg.values())
    if total == 0:
        # ⭐ A ZERO HERE IS THE FAILURE MODE, NOT THE GOAL. The whole point is
        # that four formulas DO restate guarded quantities; reporting none means
        # the parser stopped working, not that the registry became clean.
        print("    ✗ ZERO formulas matched any shape. The capability control "
              "passed,\n      so this is a corpus or parse failure, not a "
              "clean registry.")
        rc = 1
    for kind in ("net_debt", "total_debt", "invested_capital", "roic", "eva", "wacc"):
        for rid, formula in reg[kind]:
            expected_id = REGISTRY_SPEC_SITES.get(kind)
            state = "specification" if readers == [] else "EXECUTING"
            flag = "  ✗" if readers else ""
            print(f"    {kind.upper():<17} {rid:<26} [{state}]{flag}")
            if rid != expected_id and expected_id is not None:
                print(f"      ✗ UNEXPECTED registry site — {expected_id!r} was "
                      f"the known duplicate, this is a NEW one")
                rc = 1
            if readers:
                print(f"      ✗ THE REGISTRY IS READ AT RUNTIME AND STILL "
                      f"RESTATES A GUARDED QUANTITY.\n"
                      f"        R2 rules delegation the pattern: this formula "
                      f"must call the owner,\n        as axiom.wacc already "
                      f"does. Until it does, two definitions ship.")
                rc = 1
    print()

    print("  ✓ sole ownership holds." if rc == 0 else
          "  ✗ sole ownership VIOLATED — see above.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
