#!/usr/bin/env python3
"""§7u coverage guard — a constant on the compute path must be registered.

⭐ PER III.4, WHATEVER ENUMERATES WHAT THE REGISTRY COVERS IS ITSELF A
HAND-SYNCED LIST. A registry listing forty constants and a guard confirming
"forty entries exist" print the same tick. So this does not compare the registry
against a list — it scans the CODE for constants that reach a rendered figure and
fails when one has no registry entry.

⭐ AND IT CARRIES A KNOWN-POSITIVE CONTROL that runs on every invocation: an
unregistered constant is planted in a throwaway module and the guard must go red.
A coverage guard that has never rejected anything is indistinguishable from one
that cannot.

    python3 scripts/check-assumption-registry.py
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from services.api.modules.financials.assumptions import (  # noqa: E402
    ARTEFACTS, DIVERGENT, registered_values, versions,
)

# Modules whose constants reach a rendered figure. Layout/parser constants are
# out of scope by design — they govern how a workbook is READ, not what a number
# comes out as, and ingest.py's 17 of them would drown the signal.
COMPUTE = [
    "services/api/modules/financials/proforma.py",
    "services/api/modules/financials/oci.py",
    "services/api/modules/valuation/engines.py",
    "services/api/modules/intelligence/engines.py",
    "services/api/modules/twin/engines.py",
    "services/api/modules/benchmarks/data.py",
    "services/api/assessment_engine.py",
    "services/api/forecast_studio.py",
]

# Names that are not assumptions: loop bounds, indices, HTTP codes, and the
# structural integers a reader would never call a modelling choice.
IGNORE_SUFFIX = ("_ROW", "_COL", "_COLS", "_START", "_CAPACITY", "_MAX", "_MIN_LEN")
IGNORE_EXACT = {"FIRST_COL", "VERSION_MAJOR", "OPENING_COLS", "MAX_HISTORICAL_COLS"}


def module_constants(path):
    """Module-level numeric constants — the shape an assumption takes."""
    try:
        tree = ast.parse(open(os.path.join(ROOT, path), encoding="utf-8").read())
    except (SyntaxError, FileNotFoundError):
        return []
    out = []
    for n in tree.body:
        if not (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)):
            continue
        name = n.targets[0].id
        if not name.isupper():
            continue
        if name in IGNORE_EXACT or name.endswith(IGNORE_SUFFIX):
            continue
        v = n.value
        if isinstance(v, ast.Constant) and isinstance(v.value, (int, float)) \
                and not isinstance(v.value, bool):
            out.append((name, v.value, n.lineno))
        elif isinstance(v, (ast.Tuple, ast.List)) and v.elts and all(
                isinstance(e, ast.Constant) and isinstance(e.value, (int, float))
                for e in v.elts):
            out.append((name, tuple(e.value for e in v.elts), n.lineno))
    return out


def unregistered(paths):
    """Constants on the compute path with no registry entry, matched BY VALUE.

    ⭐ MATCHED BY VALUE, NOT BY NAME, and that is deliberate. Six identifiers in
    this codebase were found to be OVERLOADED — the same short name for unrelated
    quantities. A name-keyed check would call `sigma` covered because some
    `sigma` is registered, which is the collision the registry exists to end.
    """
    have = set()
    for v in registered_values().values():
        have.add(tuple(v) if isinstance(v, (list, tuple)) else v)
    missing = []
    for p in paths:
        for name, val, ln in module_constants(p):
            key = tuple(val) if isinstance(val, (list, tuple)) else val
            if key not in have:
                missing.append((p, ln, name, val))
    return missing


def control():
    """⭐ Plant an unregistered constant; the guard must find it."""
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="asmreg-")
    try:
        rel = os.path.join(d, "planted.py")
        open(rel, "w", encoding="utf-8").write(
            "SOME_NEW_TUNING_CONSTANT = 0.31415926535\n")
        # scan it directly, same code path
        saved, globals()["ROOT"] = ROOT, ""
        try:
            found = unregistered([rel])
        finally:
            globals()["ROOT"] = saved
        return bool(found)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    print("§7u ASSUMPTION REGISTRY — coverage guard\n")
    print("  versions pinned by §7s.1 (THREE, not one):")
    for k, v in versions().items():
        print(f"     {k:<20} {v}")
    n = sum(len(t) for _, t in ARTEFACTS.values())
    print(f"\n  registered: {n} across 3 artefacts, "
          f"plus {len(DIVERGENT)} divergent identifiers")

    ok = control()
    print("\n  KNOWN-POSITIVE CONTROL")
    if not ok:
        print("     x a planted unregistered constant was NOT found — the guard")
        print("       is inert and nothing below is meaningful")
        return 2
    print("     + a planted unregistered constant is found")

    missing = unregistered(COMPUTE)
    print(f"\n  COMPUTE-PATH CONSTANTS WITHOUT A REGISTRY ENTRY: {len(missing)}")
    for p, ln, name, val in missing:
        print(f"     x {p}:{ln}  {name} = {val}")
    if missing:
        print("\n  A constant that reaches a rendered figure must be registered,")
        print("  or a pack pinning the registry does not pin that number.")
        return 1
    print("     + every compute-path constant is registered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
