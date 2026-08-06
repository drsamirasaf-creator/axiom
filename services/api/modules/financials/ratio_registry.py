"""R7 — the registry, executed.

⭐⭐ THIS MODULE IS THE FIRST RUNTIME READER OF `axiom_ratio_registry.yaml`, AND
`check-sole-owner.py` IS BUILT TO FAIL THE BUILD THE MOMENT IT EXISTS while any
registry formula still restates a guarded quantity. That is not an obstacle to
route around: it is the guard firing at exactly the moment it was designed for.
The five restatements — axiom.net_debt, bs.total_debt, axiom.invested_capital,
axiom.roic, axiom.eva — were converted to DELEGATION (R2) in the same lane, so
the guard passes because the defect is gone, not because it was allowlisted.

⭐⭐ ABSENCE PROPAGATES, AND IT IS THE FIRST CONCERN RATHER THAN THE LAST. Every
operator here refuses to fabricate: one absent operand yields an absent result.
A registry evaluator that defaulted a missing line to 0 would produce a
plausible ratio for a company that never supplied the data, on a surface whose
whole claim is that the number came from the statements.

⭐ THE EVALUATOR OWNS NO ARITHMETIC IT DID NOT HAVE TO. Where a quantity has an
owner in `ratios.py`, the formula calls it and this module dispatches the call.
It performs +, -, *, / and nothing else.

WHAT THIS DOES NOT DO
  It does not render. Nothing in the serving path reads it yet — wiring it to a
  surface is a separate decision, because two paths to one number is the defect
  this whole programme exists to end. See `compare_with_engine`, which is how
  the two paths are held against each other while only one of them serves.
"""
import ast
import functools
import os

import yaml

from . import ratios as ratio_lib
from .engines import _n

_HERE = os.path.abspath(__file__)          # services/api/modules/financials/…
_ROOT = _HERE
for _ in range(5):                          # file -> financials -> modules -> api -> services -> root
    _ROOT = os.path.dirname(_ROOT)
REGISTRY_PATH = os.path.join(_ROOT, "docs", "reference",
                             "axiom_ratio_registry.yaml")
if not os.path.exists(REGISTRY_PATH):
    # ⭐ FAIL LOUDLY AT IMPORT, NOT SILENTLY AT FIRST EVALUATION. A registry
    # this module cannot find would make every ratio "absent" — a state
    # indistinguishable from a company that supplied no data.
    raise RuntimeError(f"ratio registry not found at {REGISTRY_PATH}")

# Group -> the dataset block its tokens read. `policy_and_assumptions` and
# `market_and_shares` are company-level rather than per-period.
_BLOCK = {"income_statement": "income_statement",
          "balance_sheet": "balance_sheet",
          "cash_flow": "cash_flow"}
_COMPANY_GROUPS = {"market_and_shares", "policy_and_assumptions",
                   "human_capital", "saas"}


class Absent:
    """A named absence, so a caller can tell WHY a value is missing.

    ⭐ NOT None. `None` says "no value"; this says "no value, and here is the
    token that stopped it". A ratio panel that prints an em dash without the
    reason makes the reader guess whether the input was missing, the formula
    unsupported, or the period out of range.
    """
    __slots__ = ("reason", "token")

    def __init__(self, reason, token=None):
        self.reason, self.token = reason, token

    def __repr__(self):
        return f"Absent({self.reason}{': ' + self.token if self.token else ''})"

    def __bool__(self):
        return False


@functools.lru_cache(maxsize=1)
def load(path=None):
    return yaml.safe_load(open(path or REGISTRY_PATH, encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def _index():
    d = load()
    vocab, group_of = {}, {}
    for gname, items in (d.get("vocabulary") or {}).items():
        for tok, meta in (items or {}).items():
            vocab[tok] = meta or {}
            group_of[tok] = gname
    ratios = {r["id"]: r for r in d.get("ratios") or []}
    return vocab, group_of, ratios


# ── the delegating functions (R2) ───────────────────────────────────────────
# ⭐ EACH ENTRY IS A CALL INTO THE OWNER, NEVER A REIMPLEMENTATION HERE. If this
# table ever grows a lambda that does arithmetic, the registry has acquired a
# second implementation inside the very module written to prevent one.
ENGINE_FUNCTIONS = {
    "net_debt": ratio_lib.net_debt,
    "total_debt": ratio_lib.total_debt,
    "invested_capital": ratio_lib.invested_capital,
    "roic": ratio_lib.roic,
    "eva": ratio_lib.eva,
    # ⭐ §7r-D's three, EXTRACTED to ratios.py 7 Aug and delegated here. The
    # registry stays the caller; ratios.py is the owner.
    "margin": ratio_lib.margin,
    "asset_turnover": ratio_lib.asset_turnover,
    "assets_to_equity": ratio_lib.assets_to_equity,
    "wacc_at": None,      # supplied per-call by the caller; see `context`
    "cagr": None,         # window-relative — see the horizon note in the yaml
}


class _Ctx:
    """One dataset, one period index, plus the caller-resolved values."""

    def __init__(self, data, years, i, company=None, supplied=None):
        self.data, self.years, self.i = data, years, i
        self.company = company or (data.get("company") or {})
        self.supplied = supplied or {}
        self._memo = {}


def _raw(ctx, tok, offset=0):
    """A stored token's value for this period, or an Absent saying why."""
    vocab, group_of, _ = _index()
    meta, grp = vocab.get(tok), group_of.get(tok)
    if meta is None:
        return Absent("token not declared", tok)
    if meta.get("source") == "absent":
        return Absent("not collected", tok)
    if grp in _COMPANY_GROUPS:
        field = (meta.get("field") or "").replace("company.", "")
        v = self_get(ctx.company, field)
        return v if v is not None else Absent("not supplied", tok)
    block = ctx.data.get(_BLOCK.get(grp, ""), {}) or {}
    field = meta.get("field") or tok.split(".", 1)[-1]
    j = ctx.i + offset
    if j < 0 or j >= len(ctx.years):
        return Absent("period out of range", tok)
    v = (block.get(field, {}) or {}).get(str(ctx.years[j]))
    return v if v is not None else Absent("not supplied", tok)


def self_get(d, k):
    return (d or {}).get(k)


def _resolve(ctx, name, offset=0):
    """A token or ratio id -> number | Absent. Memoised per (name, offset)."""
    key = (name, offset)
    if key in ctx._memo:
        return ctx._memo[key]
    ctx._memo[key] = Absent("cycle", name)     # cycle guard before recursion
    vocab, _g, ratios = _index()

    if name in ctx.supplied:
        out = ctx.supplied[name]
        out = out if out is not None else Absent("not supplied", name)
    elif name in ratios:
        out = _eval(ctx, _parse(ratios[name]["formula"]), offset)
    elif name in vocab:
        meta = vocab[name]
        if meta.get("source") == "derived" and meta.get("expr"):
            try:
                out = _eval(ctx, _parse(meta["expr"]), offset)
            except SyntaxError:
                out = Absent("expression is prose, not a formula", name)
        elif meta.get("source") == "caller_resolved":
            out = Absent("caller must supply", name)
        else:
            out = _raw(ctx, name, offset)
    else:
        out = Absent("unknown identifier", name)
    ctx._memo[key] = out
    return out


# ── the parser ──────────────────────────────────────────────────────────────
# `is` is a Python keyword and the income statement is the `is.` namespace —
# the same trap that silently swallowed every IS formula in the sole-owner
# scan until a known positive caught it. Prefix-renamed before parsing, which
# preserves the Attribute structure the walker reads.
import re  # noqa: E402

_IS = re.compile(r"\bis\.")
_NS = {"IS_": "is", "bs": "bs", "cf": "cf", "mk": "mk",
       "po": "po", "hc": "hc", "sa": "sa", "axiom": "axiom"}


@functools.lru_cache(maxsize=512)
def _parse(formula):
    return ast.parse(_IS.sub("IS_.", " ".join(formula.split())), mode="eval").body


def _dotted(node):
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{_NS.get(node.value.id, node.value.id)}.{node.attr}"
    return None


_ALLOWED_CONSTANTS = {0, 1, 2, 4, 12, 100, 365, 366}


def _eval(ctx, node, offset=0):
    """The whole evaluator. +, -, *, / and dispatch. Nothing else."""
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)) or isinstance(node.value, bool):
            return Absent("non-numeric literal")
        # `evaluation.forbidden` limits literals; enforced rather than described.
        if node.value not in _ALLOWED_CONSTANTS:
            return Absent(f"literal {node.value} is not permitted")
        return node.value

    if isinstance(node, ast.Attribute):
        d = _dotted(node)
        return _resolve(ctx, d, offset) if d else Absent("unreadable operand")

    if isinstance(node, ast.Name):
        return _resolve(ctx, node.id, offset)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        v = _eval(ctx, node.operand, offset)
        return v if isinstance(v, Absent) else -v

    if isinstance(node, ast.BinOp):
        a, b = _eval(ctx, node.left, offset), _eval(ctx, node.right, offset)
        if isinstance(a, Absent):
            return a
        if isinstance(b, Absent):
            return b
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            # ⭐ A ZERO DENOMINATOR IS ABSENCE, NOT AN ERROR AND NOT INFINITY.
            # The same reading ratios.roic takes for a zero invested capital.
            return Absent("zero denominator") if b == 0 else a / b
        return Absent(f"operator {type(node.op).__name__} not permitted")

    if isinstance(node, ast.Call):
        return _call(ctx, node, offset)

    return Absent(f"node {type(node).__name__} not permitted")


def _call(ctx, node, offset):
    fn = node.func
    name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)

    if name == "prior":
        return _eval(ctx, node.args[0], offset - 1)
    if name == "avg":
        # mean of opening and closing. R4 removed avg() from ROA/ROE/ROIC; it
        # survives elsewhere, so the operator stays and states its own rule.
        cur = _eval(ctx, node.args[0], offset)
        prev = _eval(ctx, node.args[0], offset - 1)
        if isinstance(cur, Absent):
            return cur
        # ⭐ A SINGLE-BALANCE AVERAGE IS NOT AN AVERAGE (R4). The first period
        # has no opening balance and yields absence rather than the closing one.
        if isinstance(prev, Absent):
            return Absent("no opening balance for an average", "avg")
        return (cur + prev) / 2.0
    if name == "abs":
        v = _eval(ctx, node.args[0], offset)
        return v if isinstance(v, Absent) else abs(v)
    if name in ("min", "max"):
        vs = [_eval(ctx, a, offset) for a in node.args]
        bad = next((v for v in vs if isinstance(v, Absent)), None)
        # ⭐⭐ `bad or …` WAS WRONG, AND WRONG BECAUSE OF A DELIBERATE CHOICE
        # ELSEWHERE. `Absent.__bool__` returns False so that `if not sketch`
        # reads naturally — which makes an Absent fall THROUGH the `or` into
        # `max(vs)`, comparing an int with an Absent and raising TypeError.
        #
        # ⭐ Reachable since R7: `is.tax_expense` is
        # `po.tax_rate_policy * max(is.pbt, 0)`, and `is.pbt` is absent at the
        # first period of any growth chain using `prior()`. It raised instead of
        # propagating absence — the one outcome this evaluator exists to avoid.
        # Found by the ratio surface asking every ratio for every period, which
        # is the first caller to exercise the whole matrix.
        if bad is not None:
            return bad
        return min(vs) if name == "min" else max(vs)

    if name in ENGINE_FUNCTIONS:
        args = [_eval(ctx, a, offset) for a in node.args]
        if name in ("wacc_at", "cagr"):
            # Caller-supplied: these read outside the dataset (market inputs,
            # the whole historical window) and this module does not reach for
            # them. See `context` in evaluate_period.
            v = ctx.supplied.get(name)
            return v if v is not None else Absent("caller must supply", name)
        owner = ENGINE_FUNCTIONS[name]
        # absence propagates THROUGH the delegation, not around it
        if any(isinstance(a, Absent) for a in args):
            return next(a for a in args if isinstance(a, Absent))
        out = owner(*args)
        return out if out is not None else Absent("owner returned absence", name)

    return Absent(f"function {name} is not declared", name)


# ── public surface ──────────────────────────────────────────────────────────
def evaluate_period(data, years, i, ratio_id, supplied=None):
    """One ratio, one period. -> number | Absent."""
    _v, _g, ratios = _index()
    if ratio_id not in ratios:
        return Absent("no such ratio", ratio_id)
    ctx = _Ctx(data, years, i, supplied=supplied)
    return _eval(ctx, _parse(ratios[ratio_id]["formula"]))


def evaluate_all(data, years, supplied_per_period=None):
    """Every ratio, every period. -> {ratio_id: [value|Absent, ...]}."""
    _v, _g, ratios = _index()
    out = {}
    for rid in ratios:
        row = []
        for i in range(len(years)):
            sup = (supplied_per_period or {}).get(i) or {}
            row.append(evaluate_period(data, years, i, rid, supplied=sup))
        out[rid] = row
    return out


def unit_of(ratio_id):
    return _index()[2].get(ratio_id, {}).get("unit")


def as_fraction(ratio_id, value):
    """A percent-unit ratio expressed the way the ENGINE carries it.

    ⭐ THE REGISTRY AND THE ENGINE DISAGREE ON SCALE, NOT ON QUANTITY, AND THAT
    HAS TO BE STATED RATHER THAN QUIETLY DIVIDED AWAY. Registry percents carry
    an explicit `* 100`; the engine returns a fraction and ships
    `format: "percent"` beside it. Comparing the two without naming the
    convention would either report a 100x divergence or hide a real one.
    """
    if isinstance(value, Absent) or value is None:
        return value
    return value / 100.0 if unit_of(ratio_id) == "percent" else value


# ── the explainer ───────────────────────────────────────────────────────────
# ⭐⭐ THE EXPLAINER IS THE CLAIM. "Each ratio opens to its definition, its
# formula, this period's numerator and denominator as ACTUAL NUMBERS, and the
# statement lines those numbers came from." A table of ratios is a dashboard;
# the operands and their provenance are what make it defensible under
# questioning.
#
# ⭐ NO NEW COMPUTATION — asserted by test. Every number below comes from
# `_eval` on a SUB-NODE of the same parsed formula. Nothing here adds, divides
# or scales; it evaluates expressions the registry already owns and reports what
# they returned.

# ── display names ───────────────────────────────────────────────────────────
# ⭐⭐ THE EXPLAINER RENDERED INTERNAL TOKENS TO CLIENTS. Expanding Gross Margin
# showed `is.gross_profit / is.revenue * 100`, operands `IS_.gross_profit` and
# `IS_.revenue`, and a read-from line of `is.gross_profit — derived:
# is.revenue - is.cogs`. Three internal spellings on one panel, one of them a
# PARSER WORKAROUND: `IS_` exists only because `is` is a Python keyword.
#
# ⭐⭐ NO NAME IS INVENTED HERE, AND THAT IS THE WHOLE DESIGN. Every name below
# is a label AXIOM ALREADY PRINTS ON THE CLIENT'S OWN TEMPLATE — the statement
# line labels, the locked subtotal rows the workbook computes, and the company
# input rows. A client reading "Gross Profit" in the explainer is reading the
# row they filled in. A token with no such label resolves to None, renders as
# its identifier, and is REPORTED: a missing name is a registry gap, and
# inventing one here would put a name into the product that no owner ruled.
#
# ⭐ THE LABEL FOLLOWS THE CLIENT'S STANDARD. `is.cogs` is "Cost of Goods Sold"
# for a US GAAP client and "Cost of Sales" for an IFRS one, because those are
# the two template labels. One hard-coded name would be wrong for half of them.

_NAME_SOURCES = ("template line", "company row", "template subtotal")


@functools.lru_cache(maxsize=8)
def _label_maps(standard):
    """The three owned label maps, keyed as the vocabulary's `field` spells them.

    ⭐ IMPORTED LAZILY. `ingest` carries openpyxl, and the explainer runs on
    every ratio of every period — a module-level import would pay for a
    spreadsheet writer on a read path that never writes one.
    """
    from .templates import LABELS, COMPANY_ROWS
    from .ingest import SUBTOTALS
    spec = LABELS.get(standard) or LABELS["us_gaap"]
    lines = dict(spec.get("lines") or {})
    company = {f: lab for f, lab, _applies in COMPANY_ROWS}
    subtotals = {}
    for _sheet, rows in SUBTOTALS.items():
        for label, _formula in rows:
            # ⭐ KEYED BY THE LABEL ITSELF, NORMALISED — not by a hand-written
            # map from label to token. A hand-written pairing is a third place
            # to state what `is.gross_profit` is called, and the one that drifts.
            subtotals[re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")] = label
    return lines, company, subtotals


def display_name(token, standard="us_gaap"):
    """The name a client reads for a vocabulary token, or None if none is owned."""
    vocab, _g, _r = _index()
    meta = vocab.get(token)
    if meta is None:
        return None
    lines, company, subtotals = _label_maps(standard)
    field = meta.get("field") or ""
    if field in lines:
        return lines[field]
    if field.startswith("company."):
        label = company.get(field.split(".", 1)[1])
        if label:
            # ⭐ THE PARENTHETICAL IS AN ENTRY INSTRUCTION, NOT PART OF THE NAME.
            # "Effective Tax Rate (decimal, e.g. 0.25)" is addressed to someone
            # typing into a workbook cell; inside a formula it is noise. The
            # stem is the label, unedited — this drops an instruction, it does
            # not compose a new name.
            return label.split(" (")[0].strip()
    stem = token.split(".", 1)[-1]
    return subtotals.get(stem)


# `a / b * 100` reads as arithmetic to a machine and as noise to a reader. The
# operators are rendered as the symbols a finance reader writes.
_OPERATOR_DISPLAY = ((" / ", " ÷ "), (" * ", " × "), (" - ", " − "))
_TOKEN_RE = re.compile(r"\b(?:is|bs|cf|mk|po|hc|sa|axiom)\.[A-Za-z_][A-Za-z_0-9]*")


def render_expr(expr, standard="us_gaap"):
    """An expression string with its tokens replaced by the names they own.

    ⭐ THE ARITHMETIC SURVIVES. This is a labelling change: every operator and
    every constant stays exactly where it was, because the formula IS the claim
    and a reader checking it needs to see it.
    """
    if not expr:
        return expr
    out = _TOKEN_RE.sub(
        lambda m: display_name(m.group(0), standard) or m.group(0), expr)
    for raw, shown in _OPERATOR_DISPLAY:
        out = out.replace(raw, shown)
    return out


def unnamed_vocabulary(standard="us_gaap"):
    """⭐⭐ THE REGISTRY GAP, ENUMERATED. §III.4: the denominator ships with the
    numerator, so this reports how many tokens ratios actually use as well as
    how many lack a name.

    `renderable` is the set that can reach a reader as a bare identifier — an
    `absent` token is never an operand of a computed ratio, so it cannot.
    """
    vocab, _g, ratios = _index()
    used = set()
    for r in ratios.values():
        used |= {t for t in _leaf_tokens(_parse(r["formula"])) if t in vocab}
    unnamed = sorted(t for t in used if display_name(t, standard) is None)
    renderable = sorted(t for t in unnamed
                        if (vocab[t] or {}).get("source") != "absent")
    return {"used_by_ratios": len(used), "named": len(used) - len(unnamed),
            "unnamed": unnamed, "renderable": renderable,
            # ⭐ A SECOND GAP CLASS, reported separately because it is not
            # vocabulary at all: caller-supplied engine tokens that reach a
            # reader through the `needs` line of a ratio that could not compute.
            "engine_tokens": sorted(k for k in ENGINE_FUNCTIONS
                                    if display_name(k, standard) is None),
            "sources": sorted(_NAME_SOURCES)}


def _unparse(node):
    """⭐⭐ THE PARSER'S RENAME IS REVERSED HERE AND NOWHERE ELSE. `_parse`
    rewrites `is.` to `IS_.` because `is` is a Python keyword; `ast.unparse`
    faithfully reports that rename, and it reached a customer-facing panel. Any
    caller that unparses a node from this module must come through here."""
    return _IS_RENAMED.sub("is.", ast.unparse(node))


_IS_RENAMED = re.compile(r"\bIS_\.")


def _leaf_tokens(node, out=None):
    """Every vocabulary token a node reaches, for provenance."""
    out = set() if out is None else out
    d = _dotted(node)
    if d:
        out.add(d)
    elif isinstance(node, ast.Name):
        out.add(node.id)
    for ch in ast.iter_child_nodes(node):
        _leaf_tokens(ch, out)
    return out


def _statement_lines(tokens, standard="us_gaap"):
    """token -> the statement line it was read from. ⭐ THE PROVENANCE IS READ
    FROM THE VOCABULARY, never restated here: `field` is the stored column, and
    a derived token reports the expression it resolves through."""
    vocab, group_of, _ = _index()
    out = []
    for t in sorted(tokens):
        meta = vocab.get(t)
        if not meta:
            continue
        out.append({
            "token": t,
            "group": group_of.get(t),
            "source": meta.get("source"),
            "field": meta.get("field"),
            "expr": meta.get("expr"),
            "collected": meta.get("collected"),
            # ⭐ `name` IS NULLABLE ON PURPOSE. None means no owner has named
            # this token, and the surface renders the identifier — it does not
            # mean the surface may compose one.
            "name": display_name(t, standard),
            "field_label": _label_maps(standard)[0].get(meta.get("field") or ""),
            "expr_display": render_expr(meta.get("expr"), standard),
        })
    return out


def _operands(ctx, node, offset=0, standard="us_gaap"):
    """The top-level operands of a formula, evaluated. -> [{role, text, value}]

    ⭐ A DIVISION HAS A NUMERATOR AND A DENOMINATOR AND THAT IS THE INTERESTING
    CASE — it is what a reader is checking. Other shapes report their top-level
    terms under a neutral role rather than being forced into a fraction they do
    not have.
    """
    def one(role, n):
        v = _eval(ctx, n, offset)
        # ⭐ `_unparse`, NEVER `ast.unparse`. The raw call reported the parser's
        # `IS_` rename, and that string was rendered verbatim as the numerator
        # on a client-facing panel.
        text = _unparse(n)
        return {"role": role, "text": text,
                "text_display": render_expr(text, standard),
                "value": None if isinstance(v, Absent) else v,
                "absent": v.reason if isinstance(v, Absent) else None}

    # unwrap a trailing unit scale so the operands are the RATIO's, not the
    # percentage's — `a / b * 100` reads as numerator a, denominator b.
    n = node
    while (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult)
           and isinstance(n.right, ast.Constant) and n.right.value == 100):
        n = n.left
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
        return [one("numerator", n.left), one("denominator", n.right)]
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
        return [one("term", n.left), one("term", n.right)]
    if isinstance(n, ast.Call):
        return [one("argument", a) for a in n.args]
    return [one("value", n)]


def explain(data, years, i, ratio_id, supplied=None):
    """One ratio, fully explained for one period. Reads; computes nothing new."""
    _v, _g, ratios = _index()
    r = ratios.get(ratio_id)
    if not r:
        return {"absent": "no such ratio", "id": ratio_id}
    ctx = _Ctx(data, years, i, supplied=supplied)
    node = _parse(r["formula"])
    value = _eval(ctx, node)
    toks = _leaf_tokens(node)
    # ⭐ THE CLIENT'S OWN STANDARD DECIDES THE LABELS. `is.cogs` is "Cost of
    # Goods Sold" on a US GAAP template and "Cost of Sales" on an IFRS one.
    standard = ((data or {}).get("company") or {}).get("standard") or "us_gaap"
    out = {
        "id": r["id"], "name": r["name"], "category": r["category"],
        "unit": r.get("unit"), "polarity": r.get("polarity"),
        "basis": r.get("basis"), "tier": r.get("tier"),
        "headline": bool(r.get("headline")),
        "definition": r.get("definition"),
        # ⭐⭐ THE SWEEP FOUND A THIRD PATH: three definitions carry a raw token
        # in their PROSE ("...compared against po.cost_of_debt used in WACC"),
        # written into the registry yaml and rendered verbatim. Relabelling it
        # here needs no registry edit and invents nothing — `po.cost_of_debt`
        # resolves to the company row the client filled in.
        "definition_display": render_expr(r.get("definition"), standard),
        # ⭐ BOTH FORMS SHIP. The machine-readable formula is what the registry
        # owns and what a reviewer diffs; the display form is what a client
        # reads. Replacing one with the other would lose a reader either way.
        "formula": r["formula"],
        "formula_display": render_expr(r["formula"], standard),
        "display_rule": r.get("display_rule"),
        "operands": _operands(ctx, node, standard=standard),
        "inputs": _statement_lines(toks, standard),
        # ⭐⭐ THE GAP IS IN THE PAYLOAD, PER RATIO. A surface that renders an
        # identifier can say WHY it is rendering one, and a token that quietly
        # never gets a name is visible rather than looking like a naming style.
        # placeholder — filled below from what the payload ACTUALLY renders
        "unnamed_tokens": [],
    }
    if isinstance(value, Absent):
        # ⭐ ABSENCE NAMES WHAT IT NEEDS. "listed once, with the data it would
        # need, rather than shown as a page of blanks."
        out["absent"] = value.reason
        out["needs"] = value.token
        # ⭐⭐ THE SAME LEAK, ON THE ABSENCE PATH — AND IT IS THE WIDER ONE.
        # 32 ratios cannot compute on a typical dataset and each is listed with
        # what it needs; `needs` is a raw vocabulary token, so the "what you
        # would have to supply" line — the one sentence in this panel meant to
        # be ACTED on — was the least readable thing on it.
        out["needs_display"] = (display_name(value.token, standard)
                                or value.token) if value.token else None
    else:
        out["value"] = value
    # ⭐⭐ DERIVED FROM WHAT RENDERS, NOT FROM THE FORMULA'S LEAVES. The first
    # version listed the leaf tokens, and the sweep caught three ways an
    # identifier reaches the panel without being one: a NESTED derivation
    # (`is.pat — derived: is.pbt − is.tax_expense`), a token named only in
    # PROSE (`...until is.purchases is collected`), and the `needs` line of a
    # ratio that did not compute at all. A declaration that does not match what
    # a reader can see is not a declaration.
    out["unnamed_tokens"] = sorted(_unnamed_in_rendered(out, standard))
    return out


_DISPLAY_KEYS = ("formula_display", "definition_display", "needs_display")


def _unnamed_in_rendered(payload, standard):
    """Every unnamed vocabulary token visible in this payload's display text."""
    vocab, _g, _r = _index()
    text = [payload.get(k) or "" for k in _DISPLAY_KEYS]
    text += [o.get("text_display") or "" for o in payload.get("operands") or ()]
    for inp in payload.get("inputs") or ():
        text.append(inp.get("expr_display") or "")
        if not inp.get("name"):
            text.append(inp["token"])
    found = set()
    for s in text:
        found |= set(_TOKEN_RE.findall(s))
    out = {t for t in found
           if t in vocab and display_name(t, standard) is None}
    # ⭐⭐ THE BARE ENGINE TOKENS COUNT TOO, AND THE SWEEP'S FIRST REGEX COULD
    # NOT SEE THEM. `wacc_at` and `cagr` have no namespace prefix, so a pattern
    # built around `is.`/`bs.` missed them entirely — and "needs wacc_at
    # (caller must supply)" is exactly the defect on exactly the panel. Neither
    # owns a name on any template, so the identifier is the ruled rendering;
    # what was missing was DECLARING it.
    needs = payload.get("needs_display") or ""
    if needs in ENGINE_FUNCTIONS:
        out.add(needs)
    return out
