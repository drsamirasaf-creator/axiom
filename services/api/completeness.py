"""What a customer's data can actually answer — derived, never hand-listed.

⭐⭐ WHY THIS EXISTS. Measured 7 Aug across **340 registered paths**: **0 paths and
0 schema fields** mention completeness, coverage, mapping status or missing
fields. The nearest machinery is the `validation` column, present on 33/33
datasets and carrying exactly one key, `warnings`.

⛔ **AND IT IS BUILT BEFORE THE ENGINES IT GATES, NOT AFTER.** A first customer
upload reaches ~54% of the declared quantities. Without this, that surface reads
as a broken product; with it, 54% is a progress bar and a next action.

## ⛔⭐⭐ THE REQUIREMENT SET IS DERIVED. IT IS NEVER A LIST.

A hand list drifts the moment an engine's inputs change, and **a guard over a
list cannot see what the list omits** — the law that has cost this codebase the
most. So:

  · **the VERDICT** — can this quantity be computed — comes from calling
    `ratio_registry.evaluate_period`, **the production path**. Re-implementing
    the resolution here would measure this module's copy of the rules, not the
    rules (a harness must invoke the production path).
  · **the EXPLANATION** — *which named input is missing* — is parsed from the
    row's own `formula` field. Nothing is enumerated by hand; a new row with a
    new namespace is picked up the day it lands.

⭐ **The two are deliberately different sources.** If the parse ever stops
covering a formula the verdict is still right, and `unparsed_formulas` says so
out loud rather than reporting a confident empty reason.

## ⭐⭐ THREE STATES, AND THE THIRD IS NOT DECIDED HERE

`is_unallocated` exists on `ax_dimension_member`; **`not_supplied` does not
exist**, and whether it ships is a founder ruling that is owed.

⛔ **An empty table cannot distinguish "this business has no geography dimension"
from "the upload failed"**, and those need different messages. So a dimension's
state is carried as one of three values and the third is simply *never asserted*
until a declaration exists. **A two-state score that later needs a third is a
rewrite of every consumer**, which is the one outcome this must not cause.
"""
import re

from .modules.financials import engines as FE
from .modules.financials import ratio_registry as RR

# ── the three states a dimension can be in ──────────────────────────────────
SUPPLIED = "supplied"          # members exist and observations attribute to them
UNALLOCATED = "unallocated"    # the dimension exists; this fact is not attributed
NOT_SUPPLIED = "not_supplied"  # ⚠️ DECLARED absence — never inferred from 0 rows
DIMENSION_STATES = (SUPPLIED, UNALLOCATED, NOT_SUPPLIED)

# ── the three states a QUANTITY can be in, which is a different axis ────────
# ⛔⭐⭐ "THE CUSTOMER LACKS THE INPUT" AND "WE NEVER DECLARED WHAT IT NEEDS" ARE
# NOT THE SAME MISS, and collapsing them charges the customer for our gap. The
# first is a next action they can take; the second is a next action WE owe. A
# two-state score reports both as "not reachable" and sends a CFO looking for a
# field nobody ever said was required.
REACHABLE = "reachable"
BLOCKED = "blocked"                          # inputs known, and some are absent
REQUIREMENT_UNDECLARED = "requirement_undeclared"   # we cannot say what it needs
QUANTITY_STATES = (REACHABLE, BLOCKED, REQUIREMENT_UNDECLARED)

# ⛔⭐⭐ T4 — TWO SCORES, NEVER POOLED. The registry score counts AXIOM's computed
# vocabulary; a spec-engine score would count units of a scope document. They are
# different quantities over different denominators, and one number carrying two
# definitions is the two-owners class in a metric — with no ragged edge to notice.
# Every score names its denominator, and `assert_not_poolable` refuses two that
# do not agree.
REGISTRY_DENOMINATOR = "axiom.registry.declared_quantities"


def assert_not_poolable(a, b):
    """Refuse to combine two scores measured against different denominators.

    ⭐ Structural, not advisory. A caller that tries to average a registry score
    with a spec-engine score gets an exception naming both denominators, rather
    than a plausible blended percentage nobody can trace.
    """
    da, db = a.get("denominator_id"), b.get("denominator_id")
    if da != db:
        raise ValueError(
            f"refusing to combine scores over different denominators: "
            f"{da!r} and {db!r}. These count different things — see "
            f"completeness.REGISTRY_DENOMINATOR. If a single figure is wanted, "
            f"that is a ruling about which denominator governs, not an average.")
    return True

# ⭐ Any `namespace.field` reference. Deliberately NOT a fixed prefix list — the
# registry already uses is/bs/cf/company/po/mk/sa and a hand list would silently
# skip the next one. `axiom.` is excluded and resolved transitively instead,
# because a reference to another quantity is not an input the customer supplies.
_TOKEN = re.compile(r"\b(?!axiom\.)([a-z][a-z0-9_]{1,10})\.([a-z_][a-z_0-9]*)")
_REF = re.compile(r"\b(axiom\.[a-z_0-9]+)")


def declared_inputs(row, _seen=None):
    """The input tokens a registry row needs, following `axiom.` references.

    ⭐ Transitive, because `axiom.dupont_three_step` names three other ratios and
    a reader asking "what is missing" needs the LEAF inputs, not a pointer to
    another row they must then expand themselves.
    """
    _seen = _seen or set()
    if row["id"] in _seen:
        return set()          # a cycle is a registry defect, not a crash here
    _seen = _seen | {row["id"]}
    formula = row.get("formula") or ""
    toks = {f"{ns}.{f}" for ns, f in _TOKEN.findall(formula)}
    by_id = {r["id"]: r for r in RR.load()["ratios"]}
    for ref in _REF.findall(formula):
        if ref in by_id:
            toks |= declared_inputs(by_id[ref], _seen)
    return toks


def requirements():
    """Every declared quantity and the inputs it needs. Derived on every call."""
    out = {}
    for row in RR.load()["ratios"]:
        out[row["id"]] = {
            "id": row["id"],
            "name": row.get("name"),
            "category": row.get("category"),
            "inputs": sorted(declared_inputs(row)),
            "formula": row.get("formula"),
        }
    return out


def _present(data, token, derived=None):
    """Can this `namespace.field` token be OBTAINED — stored or derived?

    ⛔⭐⭐ IT ASKS "CAN THE PRODUCT GET IT", NOT "DID THE CUSTOMER TYPE IT", AND THE
    DIFFERENCE IS THE WHOLE POINT OF THE REASON. The first version of this
    checked only the stored blocks and reported `is.ebit` as a missing input for
    six quantities — but EBIT is not a stored line on these datasets, it is
    produced by `derive_series` from lines the customer already supplied.
    **Telling a customer to supply something they already have is worse than
    saying nothing**: they go looking for a field the template does not even
    offer, and the real blockers (`bs.current_assets`, `bs.total_assets`) are
    buried among false ones.

    ⭐ That was a proxy standing in for the harm — the §III.15 shape, caught here
    before it shipped because a blocker that looked wrong was checked instead of
    believed.

    ⛔ RETURNS None WHEN THE NAMESPACE IS UNKNOWN — not False. "I cannot tell" and
    "it is missing" are different answers, and reporting the second for the first
    would invent a missing field the customer cannot supply.
    """
    ns, _, field = token.partition(".")
    block = {"is": "income_statement", "bs": "balance_sheet",
             "cf": "cash_flow", "company": "company"}.get(ns)
    if block is None:
        return None
    section = (data or {}).get(block) or {}
    if block == "company":
        if section.get(field) is not None:
            return True
    else:
        vals = section.get(field)
        if isinstance(vals, dict) and any(v is not None for v in vals.values()):
            return True
    # ⭐ Second source: anything `derive_series` produces is obtainable without
    # the customer supplying another figure.
    series = (derived or {}).get(field)
    if isinstance(series, list) and any(v is not None for v in series):
        return True
    return False


def score(data, period_index=None):
    """The completeness score for one dataset, with a reason per quantity.

    ⛔ "54% complete" is a grade. "54%, and these six need channel data you have
    not supplied" is a next action (§7q — an absence with a plausible reason is
    the most informative signal). This returns the second.
    """
    reqs = requirements()
    derived = FE.derive_series(data)
    years = derived["years"]
    i = derived["n_historical"] - 1 if period_index is None else period_index

    engines, unparsed = [], []
    for qid, req in sorted(reqs.items()):
        # ⭐ THE VERDICT COMES FROM THE PRODUCTION PATH.
        try:
            value = RR.evaluate_period(data, years, i, qid)
            reachable = not isinstance(value, RR.Absent)
            error = None
        except Exception as exc:                      # noqa: BLE001
            reachable, error = False, f"{type(exc).__name__}: {exc}"

        missing, unknown = [], []
        if not reachable:
            for tok in req["inputs"]:
                p = _present(data, tok, derived)
                if p is False:
                    missing.append(tok)
                elif p is None:
                    unknown.append(tok)
            if not req["inputs"]:
                unparsed.append(qid)

        # ⭐ T3 — THE THIRD STATE, kept out of the customer's column. A quantity
        # whose formula we could not parse is OUR undeclared requirement, not
        # their missing data.
        if reachable:
            state = REACHABLE
        elif not req["inputs"]:
            state = REQUIREMENT_UNDECLARED
        else:
            state = BLOCKED

        engines.append({
            "id": qid, "name": req["name"], "category": req["category"],
            "state": state,
            "reachable": reachable,
            # ⭐ The named inputs, so a surface can group "six engines need
            # channel data" rather than listing six unrelated sentences.
            "missing_inputs": sorted(missing),
            # ⛔ Tokens this module cannot resolve. Reported rather than counted
            # as missing — see `_present`.
            "unresolved_inputs": sorted(unknown),
            "error": error,
        })

    ok = sum(1 for e in engines if e["state"] == REACHABLE)
    blocked = sum(1 for e in engines if e["state"] == BLOCKED)
    undeclared = sum(1 for e in engines
                     if e["state"] == REQUIREMENT_UNDECLARED)
    total = len(engines)
    return {
        "computable": ok,
        "declared": total,
        # ⛔ THE THREE STATES SUM TO THE DENOMINATOR AND ARE REPORTED APART.
        # A surface that shows only `computable` invites "the rest is missing
        # data", which is false for the undeclared ones.
        "blocked": blocked,
        "requirement_undeclared": undeclared,
        "states": QUANTITY_STATES,
        # ⛔⭐⭐ THE DENOMINATOR IS NAMED, NOT IMPLIED. "54%" with an unnamed
        # denominator is a number two readers will define differently — and this
        # one is specifically NOT the spec's engine count, which is unruled.
        "denominator_id": REGISTRY_DENOMINATOR,
        "denominator_label": "AXIOM registry-declared quantities",
        # ⭐ The denominator travels with the fraction, always.
        "fraction": round(ok / total, 4) if total else None,
        "percent": round(100.0 * ok / total, 1) if total else None,
        "period": years[i] if 0 <= i < len(years) else None,
        "engines": engines,
        # ⭐⭐ §III.4 — a formula this module could not parse is announced, not
        # silently reported as "no missing inputs".
        "unparsed_formulas": sorted(unparsed),
        "dimension_states": DIMENSION_STATES,
    }


def missing_input_index(scored):
    """Which inputs block the most quantities — the next action, ranked.

    ⭐ This is what turns a grade into a to-do list: one missing line item can
    be the sole blocker for a dozen quantities, and the customer cannot see that
    from a per-engine list.
    """
    idx = {}
    for e in scored["engines"]:
        for tok in e["missing_inputs"]:
            idx.setdefault(tok, []).append(e["id"])
    return sorted(
        ({"input": k, "blocks": len(v), "quantities": sorted(v)}
         for k, v in idx.items()),
        key=lambda r: (-r["blocks"], r["input"]))
