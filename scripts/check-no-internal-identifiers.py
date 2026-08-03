#!/usr/bin/env python3
"""⭐⭐ NO INTERNAL IDENTIFIER REACHES A CUSTOMER-FACING PAYLOAD.

THE DEFECT THIS EXISTS FOR. Dashboard → Ratio Analysis, expanding Gross Margin:

    is.gross_profit / is.revenue * 100
    numerator    IS_.gross_profit
    denominator  IS_.revenue
    read from    is.gross_profit — derived: is.revenue - is.cogs

`IS_` is the evaluator's rename of `is`, which is a Python keyword — a
workaround for a parser, on a page a CFO reads. It had been there since the
surface shipped.

⭐ THE SWEEP IS OVER PAYLOADS, NOT OVER SOURCE. Grepping the frontend for
`IS_` finds nothing: the string is never written down anywhere, it is PRODUCED
by `ast.unparse` at request time. Only executing the endpoint's own code path
and reading what comes back can see it — which is why this walks every ratio of
the registry against a real reference dataset.

⭐ §III.4 — the denominator is printed and an empty corpus FAILS.

Read-only. No network, no database, no token.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ⭐ IN-MEMORY, NOT `tempfile.mktemp`. A guard must not mutate the filesystem —
# `test_NO_GUARD_WRITES_TO_THE_FILESYSTEM` caught the first version doing it.
# Nothing here touches a database; the URL exists only to satisfy import.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from services.api.modules.financials import ratio_registry as rr   # noqa: E402
from tests.fixtures.refcases import meridian, halcyon              # noqa: E402

# ⭐ THE EVALUATOR ARTEFACT IS BANNED OUTRIGHT — it names nothing in the
# product. A namespace-prefixed identifier is permitted ONLY on a key whose
# contract is to carry one, because §7r-S4 requires the machine-readable
# formula to survive beside the display form.
ARTEFACT = re.compile(r"\bIS_\.")
IDENTIFIER = re.compile(r"\b(?:is|bs|cf|mk|po|hc|sa)\.[a-z_][a-z_0-9]*")
# ⭐ THE BARE ENGINE TOKENS. The first version of this pattern was built around
# the `is.`/`bs.` prefixes and could not see `wacc_at` or `cagr` — which reach
# a client as "needs wacc_at (caller must supply)" on six ratios. A recogniser
# shaped by the example that was reported misses the cases that were not.
ENGINE_IDENT = re.compile(r"^(?:" + "|".join(sorted(rr.ENGINE_FUNCTIONS)) + r")$")

# Keys that OWN a raw identifier by contract. Every one is paired with a
# `_display` sibling the surface renders instead; the raw form is kept for the
# registry's own readers and for anyone diffing a formula.
RAW_BY_CONTRACT = {"formula", "token", "expr", "needs", "field",
                   "text", "unnamed_tokens", "definition"}

# ⭐⭐ A DISPLAY KEY MAY CARRY AN IDENTIFIER ONLY FOR A TOKEN NOBODY HAS NAMED.
# That is the ruling — render the identifier where no name exists, and report
# the list — so the guard enforces exactly it: an identifier for a token that
# DOES own a name is a leak, and an identifier for one that does not is the
# declared gap. Without this distinction the check is either useless (allow all
# display keys) or forbids the honest fallback.
DISPLAY_KEYS = {"formula_display", "text_display", "expr_display",
                "needs_display", "name", "field_label", "definition_display"}


def walk(node, path=""):
    """Yield (path, string) for every string in the payload."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def leaf(path):
    return re.sub(r"\[\d+\]", "", path).rsplit(".", 1)[-1]


def main():
    failures, checked, cases = [], 0, 0
    fallbacks = set()
    for name, case in (("meridian", meridian), ("halcyon", halcyon)):
        data = case()
        years = data["periods"]["historical"]
        _v, _g, ratios = rr._index()
        if not ratios:
            print("✗ the registry has no ratios — an empty corpus is a failure")
            return 2
        cases += 1
        for rid in sorted(ratios):
            for i in range(len(years)):
                payload = rr.explain(data, years, i, rid)
                checked += 1
                unnamed = set(payload.get("unnamed_tokens") or ())
                for path, s in walk(payload):
                    key = leaf(path)
                    if ARTEFACT.search(s):
                        failures.append(
                            f"{name}/{rid}/{years[i]} {path}: evaluator artefact "
                            f"`IS_` in {s!r}")
                        continue
                    if key in RAW_BY_CONTRACT:
                        continue
                    found = set(IDENTIFIER.findall(s))
                    if ENGINE_IDENT.match(s.strip()):
                        found.add(s.strip())
                    if not found:
                        continue
                    if key in DISPLAY_KEYS:
                        stray = found - unnamed
                        if stray:
                            failures.append(
                                f"{name}/{rid}/{years[i]} {path}: {sorted(stray)} "
                                f"own a display name and rendered raw — {s!r}")
                        fallbacks |= found & unnamed
                    else:
                        failures.append(
                            f"{name}/{rid}/{years[i]} {path}: registry identifier "
                            f"on a rendered key — {s!r}")

    if not checked or not cases:
        print("✗ nothing checked — an empty corpus is a failure, not a pass")
        return 2

    gap = rr.unnamed_vocabulary()
    if failures:
        for f in failures[:25]:
            print(f"✗ {f}")
        print(f"\n  {len(failures)} leak(s) across {checked} explained "
              f"ratio-periods, {cases} reference companies.")
        return 1
    print(f"✓ no internal identifier on a rendered key: {checked} explained "
          f"ratio-periods across {cases} reference companies "
          f"({len(RAW_BY_CONTRACT)} keys raw by contract).")
    print(f"  vocabulary used by ratios: {gap['used_by_ratios']} · named "
          f"{gap['named']} · unnamed {len(gap['unnamed'])} "
          f"(renderable {len(gap['renderable'])}).")
    # ⭐ THE FALLBACKS ARE PRINTED, NOT MERELY PERMITTED. These are the tokens a
    # client actually sees as identifiers today; a registry gap that nobody
    # reads is a gap nobody closes.
    print("  rendered as identifiers (no owned name): "
          + (", ".join(sorted(fallbacks)) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
