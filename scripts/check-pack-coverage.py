#!/usr/bin/env python3
"""§7s.1 — the freeze must capture every input a computation entry point reads.

⭐ BOTH SIDES ARE DERIVED FROM CODE. The read set comes from walking the call
graph of the seven sections' entry points; the captured set comes from walking
`pack.INPUT_CLASSES`' own capture functions. Neither is a hand-written list, so
neither can go stale silently.

⭐ WHY NOT COMPARE AGAINST THE PACK DEFINITION. CORE's own correction: "enumerate
from what the RENDERER actually reads — not from the pack definition. A pack
definition is a hand-synced list one level up, subject to III.4 exactly like any
other hand-written list." A guard that read `INPUT_CLASSES` to decide what SHOULD
be captured would be a list checking itself.

⭐ AND A CONTROL PROVING ONLY THAT A SNAPSHOT WAS TAKEN PROVES NOTHING — it is
"0 problems in 0 files" with a publication attached. The known-positive here adds
a real read to a real entry point and requires the guard to go red.

    python3 scripts/check-pack-coverage.py
"""
import ast
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pack_input_scan import ENTRY_POINTS, MODELS, reads_of  # noqa: E402

PACK_MODULE = "services/api/pack.py"

# Models that are not pack inputs even though an entry point touches them:
# infrastructure rather than a figure the pack renders.
# ⭐ EVERY EXEMPTION IS NAMED AND REASONED. A blanket "ignore caches" would have
# hidden the viability cache, which IS an input — CORE's nine missed it and this
# guard is the reason it is captured.
NOT_AN_INPUT = {
    "NightlyLock": "a concurrency lock; holds no figure",
    "FrontierJob": "job bookkeeping; the RESULT is captured via computed_caches",
    "AuditLog": "an append-only trail; nothing renders from it",
}


def captured_models():
    """Models the freeze actually reads, derived from pack.py's own captures."""
    with open(os.path.join(ROOT, PACK_MODULE), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    fns = {n.name: n for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef)}
    # the capture functions are exactly the values of INPUT_CLASSES
    names = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and node.targets
                and getattr(node.targets[0], "id", "") == "INPUT_CLASSES"
                and isinstance(node.value, ast.Dict)):
            names = [v.id for v in node.value.values if isinstance(v, ast.Name)]
    if not names:
        raise SystemExit("pack.INPUT_CLASSES not found — the guard cannot derive "
                         "the captured set and must not pass")
    out = set()
    for fname in names:
        node = fns.get(fname)
        if node is None:
            continue
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and n.id in MODELS:
                out.add(n.id)
            elif isinstance(n, ast.Attribute) and n.attr in MODELS:
                out.add(n.attr)
    return out, names


def read_models():
    """Models the seven sections' entry points read."""
    out, missing_entry = set(), []
    for label, rel, func, _db in ENTRY_POINTS:
        if rel is None:
            missing_entry.append(label)
            continue
        m, _c, _u = reads_of(rel, func)
        out |= m
    return out, missing_entry


def gaps(read, captured):
    return sorted(m for m in read
                  if m not in captured and m not in NOT_AN_INPUT)


def control():
    """⭐ KNOWN-POSITIVE — add a read to an entry point and require red.

    A copy of a real entry-point module gains a read of a model the freeze does
    not capture. The guard must find it. Run on every invocation, because a
    coverage guard that has never rejected anything is indistinguishable from one
    that cannot.
    """
    rel = "services/api/sentinel.py"
    # ⭐⭐ PLANTED IN MEMORY. Nothing is copied, written or restored — see
    # pack_input_scan.OVERRIDES for why the previous form could not be made safe.
    import pack_input_scan as _pis
    text = _pis._source(rel)
    marker = "def compute_viability(db, company_id, use_cache=True):"
    if marker not in text:
        return None, "control anchor not found — the control is inert"
    planted = text.replace(
        marker,
        marker + '\n    from .accounts import AssessmentWeight\n'
                 '    _planted = db.query(AssessmentWeight).first()', 1)
    _pis.OVERRIDES[rel] = planted
    try:
        captured, _ = captured_models()
        read, _ = read_models()
        found = "AssessmentWeight" in gaps(read, captured)
        return found, None
    finally:
        # ⭐ popping a dict entry is not a restore — if this never runs, the
        # process is gone and the override died with it.
        _pis.OVERRIDES.pop(rel, None)


def main():
    print("§7s.1 — PACK INPUT COVERAGE GUARD\n")
    captured, class_names = captured_models()
    read, missing_entry = read_models()

    print(f"  input classes in the freeze : {len(class_names)}")
    print(f"  models the freeze captures  : {len(captured)}")
    print(f"  models the sections read    : {len(read)}")

    if missing_entry:
        # ⭐ A SECTION WITH NO ENTRY POINT IS REPORTED, NOT SKIPPED. Two of the
        # seven spine sections are not built; a guard that omitted them would
        # report full coverage of a partial spine.
        print(f"\n  SECTIONS WITH NO COMPUTATION ENTRY POINT ({len(missing_entry)}):")
        for label in missing_entry:
            print(f"     • {label} — not built; nothing to freeze yet")

    ok, why = control()
    print("\n  KNOWN-POSITIVE CONTROL")
    if why:
        print(f"     x {why}")
        return 2
    if not ok:
        print("     x a planted read of an uncaptured model was NOT detected —")
        print("       the guard is inert and nothing below is meaningful")
        return 2
    print("     + a read added to an entry point is detected")

    missing = gaps(read, captured)
    print(f"\n  READ BUT NOT CAPTURED BY THE FREEZE: {len(missing)}")
    for m in missing:
        print(f"     x {m}")
    if missing:
        print("\n  A computation entry point reads an input the freeze does not")
        print("  capture. A pack rendering that figure would drift when it moves.")
        return 1
    print("     + every model a section reads is captured by the freeze")
    if NOT_AN_INPUT:
        print(f"\n  EXEMPT, each with a stated reason ({len(NOT_AN_INPUT)}):")
        for k, v in sorted(NOT_AN_INPUT.items()):
            print(f"     {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
