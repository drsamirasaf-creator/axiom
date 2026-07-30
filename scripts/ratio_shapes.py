"""Canonical arithmetic SHAPES for the registry's ratios.

A shape is the arithmetic structure of a formula with its operand IDENTITIES
removed but its operand REUSE preserved. `(a - b) / b` and `(x - y) / y` are the
same shape; `(a - b) / c` is a different one, because the repeat is structural.

⭐ KEYED ON SHAPE, NOT ON IDENTIFIER, per the registry's enumeration_guard. An
identifier-keyed check either false-positives on every dict key that happens to
be called `net_debt` or gets "resolved" by pointing it at the library — the
defect wearing the fix's clothes.

⭐ CHAINS ARE LEAVES, NOT EXPANSIONS. `avg(axiom.invested_capital)` inside
`axiom.roic` is a CALL. Expanding it would make a second ROIC that computes its
own denominator inline INVISIBLE, because the inlined canonical form and the
duplicate would then share a shape. That is the whole reason the registry
permits canonical chaining.
"""
import re

TOKEN = re.compile(r'\b(?:is|bs|cf|mk|po|hc|sa)\.[a-z_0-9]+')
RATIO = re.compile(r'\baxiom\.[a-z_0-9]+')
NUM = re.compile(r'\b\d+(?:\.\d+)?\b')
FUNC = re.compile(r'\b(avg|prior|abs|min|max)\s*\(')


def canonical(formula: str) -> str:
    """Shape string: operands become @0,@1,... by first occurrence; chained
    ratio references become #0,#1,... so a call is never confused with a token."""
    s = " ".join(formula.split())
    slots, chains = {}, {}

    def sub_ratio(m):
        k = m.group(0)
        return chains.setdefault(k, f"#{len(chains)}")
    s = RATIO.sub(sub_ratio, s)

    def sub_tok(m):
        k = m.group(0)
        return slots.setdefault(k, f"@{len(slots)}")
    s = TOKEN.sub(sub_tok, s)
    return re.sub(r'\s+', '', s)


def leaves(formula: str):
    return sorted(set(TOKEN.findall(formula))), sorted(set(RATIO.findall(formula)))


def complexity(formula: str) -> dict:
    """What makes a shape findable in code, measured rather than asserted."""
    toks, chs = leaves(formula)
    shape = canonical(formula)
    n_slots = len(set(re.findall(r'@\d+', shape)))
    n_chain = len(set(re.findall(r'#\d+', shape)))
    reuse = len(re.findall(r'@\d+', shape)) > n_slots
    funcs = set(FUNC.findall(formula))
    lits = {n for n in NUM.findall(formula)} - {"1"}
    ops = len(re.findall(r'[+\-*/]', shape))
    return {"shape": shape, "slots": n_slots, "chains": n_chain,
            "reuse": reuse, "funcs": funcs, "literals": lits, "ops": ops}


def detectable(c: dict) -> bool:
    """Can this shape be looked for at all?

    ⭐ A BARE BINARY OPERATION CANNOT. `@0/@1` matches every division in the
    codebase; a scan keyed on it reports thousands of "duplicates" and means
    nothing. Structure above a single operator is what makes a search possible:
    three or more operands, a reused operand, an avg()/prior() call, or a
    distinctive literal.
    """
    if c["chains"]:
        return True                      # a call to a canonical ratio is findable
    if c["slots"] + c["chains"] < 2:
        return False
    if c["ops"] <= 1:
        return False                     # @0/@1, @0+@1 — indistinguishable

    # ⭐ A BARE ADDITIVE CHAIN IS NOT DISTINCTIVE EITHER, AND ASSUMING IT WAS
    # PUT FIVE FALSE POSITIVES IN THE FIRST RUN. `@0+@1-@2` is net debt AND an
    # invite TTL (`created + ttl - now`, accounts.py:1258) AND a non-current
    # asset rollforward (`prev + capex - da`, forecast_studio.py:187). Three
    # operands is arity, not structure. A shape earns detectability by carrying
    # a division, a function, a reused operand or a distinctive literal — some
    # feature beyond "several things added and subtracted".
    additive_only = not re.search(r'[/*]', c["shape"])
    if additive_only and not (c["reuse"] or c["funcs"] or c["literals"]):
        return False

    return bool(c["reuse"] or c["funcs"] or c["slots"] >= 3 or c["literals"])
