#!/usr/bin/env python3
"""§7s.1 Stage 2 — the export must carry every surface the app renders.

⭐ THE SAME CORRECTION AS STAGE 1'S COVERAGE GUARD, FROM THE OPPOSITE DIRECTION.
Stage 1 asks "does the freeze capture everything the sections READ". This asks
"does the export carry everything the app RENDERS". Both sides derived from code;
neither compares against a hand-written list.

⭐ THE DEFECT THIS EXISTS FOR. The export's section list is a literal inside
`board_report`, hand-maintained, and it went stale SILENTLY against everything
that shipped this year — an export missing a surface does not fail, it just
quietly stops being the thing it claims to be ("a reader without app access sees
what a user sees").

⭐ HOW THE APP'S SURFACES ARE DERIVED. An app surface is an ENGINE FUNCTION that a
router endpoint returns to a caller. That is mechanically discoverable: walk each
`@router` handler and collect the engine-module functions it calls. Nothing is
read from a list of section names.

    python3 scripts/check-export-coverage.py
"""
import ast
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SRC = os.path.join(ROOT, "services", "api")

# Modules whose public functions are "surfaces" — the compute layer. A router
# calling one of these is rendering something a reader should see in the export.
ENGINE_FILES = [
    "services/api/modules/financials/engines.py",
    "services/api/modules/valuation/engines.py",
    "services/api/modules/intelligence/engines.py",
    "services/api/modules/twin/engines.py",
    "services/api/modules/risk/engines.py",
    "services/api/modules/benchmarks/engines.py",
    "services/api/modules/optimization/engines.py",
]

# The export's renderers. ⭐ BOTH the legacy board_report AND the Stage 2
# component library, because the export is the union of what they carry — and a
# guard checking only one would go green while the other rotted.
EXPORT_ROOTS = [
    ("services/api/modules/intelligence/engines.py", "board_report"),
    ("services/api/pack_render.py", "render_export"),
]

# ⭐ EVERY EXEMPTION IS NAMED AND REASONED. A blanket skip would hide exactly the
# surface this guard exists to catch.
NOT_A_SURFACE = {
    "run": "a dispatcher, not a surface; its branches are the surfaces",
    "stress": "reached through the valuation section's own payload",
    "self_check": "an internal consistency probe, never rendered",
    "validate_dataset": "an ingest-time check; its result rides on the row",
    "balance_audit": "rendered via the dataset's stored validation block",
    "assumption_audit": "rendered via the dataset's stored validation block",
    # ⭐ THE FOLLOWING ARE NOT SECTIONS. Each is named with WHY, because a
    # blanket exemption would hide exactly what this guard exists to catch.
    "sectors": "a picker's option list, not a figure a reader consumes",
    "sync": "a WRITE path (actuals ingest); it produces a dataset, not a section",
    "solve": "an optimisation RUN endpoint; its result renders via `levers`",
    "build_analysis_user_text": "composes an AI prompt; never rendered to a reader",
    "gate_suggestions": "the approval gate's filter, not a rendered figure",
    "assemble_assumptions": "assembles inputs FOR a surface; the surface renders",
}


# ⭐⭐ IN-MEMORY SOURCE OVERRIDES. A control may plant ONLY here. Guards used to
# copy production source aside, write a modified file and restore it in a
# `finally` — and ⭐ A `finally` DOES NOT SURVIVE A KILL. Four times a timeout
# landed between the write and the restore and stranded a live NameError in
# production source. ⭐ FOUR OCCURRENCES IS A MECHANISM, NOT FOUR ACCIDENTS.
_OVERRIDES = {}


def _parse(rel):
    if rel in _OVERRIDES:
        return ast.parse(_OVERRIDES[rel])
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return ast.parse(fh.read())


def engine_functions():
    """{name: file} for every public top-level engine function."""
    out = {}
    for rel in ENGINE_FILES:
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        for n in _parse(rel).body:
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
                out.setdefault(n.name, rel)
    return out


ENGINES = engine_functions()


def _called_names(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _reachable(rel, func, depth=4, seen=None):
    """Engine functions reachable from `func`, following same-file calls."""
    seen = seen if seen is not None else set()
    if (rel, func) in seen or depth < 0:
        return set()
    seen.add((rel, func))
    try:
        tree = _parse(rel)
    except (SyntaxError, FileNotFoundError):
        return set()
    idx = {n.name: n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    node = idx.get(func)
    if node is None:
        return set()
    names = _called_names(node)
    out = {n for n in names if n in ENGINES}
    for n in names:
        if n in idx and n != func:
            out |= _reachable(rel, n, depth - 1, seen)
    return out


def app_surfaces():
    """Engine functions a ROUTER endpoint renders — derived, not listed."""
    out = {}
    for dp, _, fs in os.walk(SRC):
        for f in fs:
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), ROOT)
            try:
                tree = _parse(rel)
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                decorated = any(
                    isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr in ("get", "post", "put", "patch", "delete")
                    for d in n.decorator_list)
                if not decorated:
                    continue
                for name in _reachable(rel, n.name):
                    out.setdefault(name, set()).add(f"{rel}:{n.name}")
    return out


def export_carries():
    """⭐ THE ROOTS THEMSELVES COUNT AS CARRIED. `board_report` appeared in the
    first run's gap list because it is a root and a root is not reachable from
    itself — the guard was reporting the export for not carrying the export."""
    out = {func for _rel, func in EXPORT_ROOTS}
    for rel, func in EXPORT_ROOTS:
        out |= _reachable(rel, func, depth=6)
    # every component in the library is part of the export
    out |= _reachable("services/api/pack_render.py", "render_export", depth=2)
    for name in _component_names():
        out |= _reachable("services/api/pack_render.py", name, depth=4)
    return out


def _component_names():
    """Component functions, derived from the COMPONENTS registry itself."""
    tree = _parse("services/api/pack_render.py")
    names = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and node.targets
                and getattr(node.targets[0], "id", "") == "COMPONENTS"
                and isinstance(node.value, ast.Dict)):
            names |= {v.id for v in node.value.values if isinstance(v, ast.Name)}
        # COMPONENTS.update({...}) additions count too
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "update"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "COMPONENTS" and node.args
                and isinstance(node.args[0], ast.Dict)):
            names |= {v.id for v in node.args[0].values if isinstance(v, ast.Name)}
    return names


def gaps(surfaces, carried):
    return sorted(s for s in surfaces
                  if s not in carried and s not in NOT_A_SURFACE)


def control():
    """⭐ KNOWN-POSITIVE — give the app a surface the export does not carry.

    A copy of a real router gains a call to a real engine function the export
    does not reach. The guard must go red. Run every invocation: a coverage guard
    that has never rejected anything is indistinguishable from one that cannot.
    """
    rel = "services/api/modules/benchmarks/router.py"
    src = os.path.join(ROOT, rel)
    if not os.path.exists(src):
        return None, "control anchor missing"
    # pick an engine function the export genuinely does not carry today
    carried = export_carries()
    candidates = [n for n in ENGINES
                  if n not in carried and n not in NOT_A_SURFACE]
    if not candidates:
        return None, "no uncarried engine function exists to plant"
    planted_name = sorted(candidates)[0]
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines(keepends=True)
    # find the first router-decorated def and inject a call in its body
    out, injected = [], False
    for i, ln in enumerate(lines):
        out.append(ln)
        if (not injected and ln.lstrip().startswith("def ")
                and i > 0 and "@router." in "".join(lines[max(0, i - 4):i])):
            indent = " " * (len(ln) - len(ln.lstrip()) + 4)
            # ⭐ A CALL, NOT A NAME REFERENCE. The first version of this control
            # planted a bare `_planted = fn`; the walker collects ast.Call nodes,
            # so the plant was invisible and the control reported the guard
            # inert. The control was wrong, not the guard — and it said so.
            out.append(f"{indent}_planted = {planted_name}()\n")
            injected = True
    if not injected:
        return None, "no router handler found to plant into"
    # ⭐⭐ THE PLANT NEVER REACHES DISK. This is the whole fix: the modified
    # source exists only as a string in this process.
    _OVERRIDES[rel] = "".join(out)
    try:
        found = planted_name in gaps(app_surfaces(), export_carries())
        return found, (None if found else
                       f"planted {planted_name} was not detected")
    finally:
        # ⭐ popping is not a restore — if this never runs the process is gone
        # and the override went with it. Nothing survives to be committed.
        _OVERRIDES.pop(rel, None)


def main():
    print("§7s.1 — EXPORT COVERAGE GUARD\n")
    surfaces = app_surfaces()
    carried = export_carries()
    print(f"  engine functions in vocabulary : {len(ENGINES)}")
    print(f"  surfaces the app renders       : {len(surfaces)}")
    print(f"  surfaces the export carries    : {len(carried)}")

    ok, why = control()
    print("\n  KNOWN-POSITIVE CONTROL")
    if why and not ok:
        print(f"     x {why}")
        return 2
    print("     + a surface added to the app is detected as uncarried")

    missing = gaps(surfaces, carried)
    print(f"\n  RENDERED BY THE APP, NOT CARRIED BY THE EXPORT: {len(missing)}")
    for m in missing:
        where = sorted(surfaces[m])[:2]
        print(f"     x {m}  ({ENGINES.get(m, '?').split('/')[-1]})  ← {where}")
    if missing:
        print("\n  The export claims a reader without app access sees what a user")
        print("  sees. Each surface above breaks that claim, silently.")
        return 1
    print("     + the export carries every surface the app renders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
