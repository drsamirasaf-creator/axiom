#!/usr/bin/env python3
"""§7s.1 — derive the Pack's input read set FROM CODE, not from a list.

⭐ WHY THIS IS AN INSTRUMENT AND NOT A LIST. CORE carries a nine-class input list
"derived by reading, not an enumeration the system asserts" — its own words. Per
III.4 a pack freezing four of nine classes and a test confirming "a snapshot was
taken" produce the same green. So this walks the transitive call graph from each
of the seven sections' computation entry points and reports every ORM model read
and every module-level constant reached.

⭐ IT IS A STARTING POINT FOR THE FREEZE, NOT THE FREEZE. Static reachability
over-approximates (a branch never taken still counts) and under-approximates
(dynamic dispatch, getattr, raw SQL). Both directions are reported rather than
silently resolved, because a scan that hides its own blind spots is the shape
that produced "5 identical payloads".

    python3 scripts/pack_input_scan.py            # the enumeration
    python3 scripts/pack_input_scan.py --classes  # collapsed to input classes
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "services", "api")

# The seven sections of the spine, plus valuation, named by their computation
# entry point. ⭐ The Value Bridge (§7s.5) is NOT BUILT — it is listed with a
# null entry point rather than omitted, because a section silently missing from
# a coverage scan is indistinguishable from one with no inputs.
ENTRY_POINTS = [
    # (section, file, function, takes_db)
    # ⭐ THE FOUR NAMES IN THE FIRST VERSION OF THIS LIST DID NOT EXIST. They were
    # guessed from the section titles and the scan reported them NOT FOUND, which
    # is the only reason they were caught. A scan that silently skipped an
    # unresolvable entry point would have reported a clean four-class read set.
    ("1 what changed",     "services/api/modules/financials/router.py", "compute_plan_vs_methods", False),
    ("2 why (ratios)",     None,                                        None,                      False),
    ("3 what is likely",   "services/api/forecast_studio.py",           "generate",                True),
    ("4 what is at risk",  "services/api/sentinel.py",                  "compute_viability",       True),
    ("4b sentinel",        "services/api/sentinel.py",                  "sentinel_recompute",      True),
    ("5 initiatives",      "services/api/accounts.py",                  "initiatives_cockpit",     True),
    ("6 what to do next",  "services/api/modules/intelligence/engines.py", "optimize_analytics",   False),
    ("7 value bridge",     None,                                        None,                      False),
    ("valuation",          "services/api/modules/valuation/engines.py", "run",                     False),
]



def _parse(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return ast.parse(fh.read())


def _index(rel):
    """{funcname: node} for every module-level and nested def in a file."""
    out = {}
    for node in ast.walk(_parse(rel)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(node.name, node)
    return out


def _all_modules():
    rels = []
    for dp, _, fs in os.walk(SRC):
        for f in fs:
            if f.endswith(".py"):
                rels.append(os.path.relpath(os.path.join(dp, f), ROOT))
    return sorted(rels)


def _model_names():
    """Every declarative model class in the tree — the read-set vocabulary."""
    names = {}
    for rel in _all_modules():
        try:
            tree = _parse(rel)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and any(
                    isinstance(b, ast.Name) and b.id in ("Base",) or
                    isinstance(b, ast.Attribute) and b.attr == "Base"
                    for b in node.bases):
                names[node.name] = rel
            # the older Column-style declarations do not always inherit `Base`
            elif isinstance(node, ast.ClassDef) and any(
                    isinstance(s, ast.Assign) and getattr(s.targets[0], "id", "") == "__tablename__"
                    for s in node.body if isinstance(s, ast.Assign) and s.targets):
                names[node.name] = rel
    return names


MODELS = _model_names()


def _resolve_imports(rel):
    """{local name: (module_rel, orig_name)} for cross-file call resolution.

    ⭐ THE FIRST VERSION OF THIS SCAN DID NOT FOLLOW CROSS-FILE CALLS AT ALL, and
    reported "models: —" for every pure engine. That is not "this engine reads
    nothing"; it is "this scan cannot see". The two print identically, which is
    the III.4 shape one level down — inside the coverage instrument itself.
    """
    tree = _parse(rel)
    pkg = os.path.dirname(rel).replace("/", ".")
    out, mods = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:                       # relative import
                parts = pkg.split(".")
                base_parts = parts[:len(parts) - node.level + 1]
                base = ".".join(base_parts + ([base] if base else []))
            for a in node.names:
                out[a.asname or a.name] = (base, a.name)
                mods[a.asname or a.name] = base + "." + a.name
        elif isinstance(node, ast.Import):
            for a in node.names:
                mods[a.asname or a.name] = a.name
    return out, mods


def _rel_for(dotted):
    """A dotted module path → a repo-relative .py path, or None."""
    cand = dotted.replace(".", "/") + ".py"
    if os.path.exists(os.path.join(ROOT, cand)):
        return cand
    cand2 = dotted.replace(".", "/") + "/__init__.py"
    if os.path.exists(os.path.join(ROOT, cand2)):
        return cand2
    return None


def reads_of(rel, func, depth=5, _seen=None):
    """ORM models and module constants reachable from `func`, ACROSS FILES.

    Follows same-file calls and resolvable cross-file calls to `depth`. What it
    cannot resolve is COUNTED AND REPORTED rather than dropped, because an
    unresolved edge and an edge that reads nothing print the same otherwise.
    """
    _seen = _seen if _seen is not None else set()
    key = (rel, func)
    if key in _seen or depth < 0:
        return set(), set(), set()
    _seen.add(key)
    try:
        idx = _index(rel)
        names, mods = _resolve_imports(rel)
    except (SyntaxError, FileNotFoundError):
        return set(), set(), {f"{rel} UNPARSEABLE"}
    node = idx.get(func)
    if node is None:
        return set(), set(), {f"{rel}:{func} NOT FOUND"}
    models, consts, unresolved = set(), set(), set()

    # module-level constants of this file count as inputs the function may read
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in MODELS:
            models.add(n.id)
        elif isinstance(n, ast.Attribute) and n.attr in MODELS:
            models.add(n.attr)
        elif isinstance(n, ast.Name) and n.id.isupper() and len(n.id) > 2:
            consts.add(n.id)
        elif isinstance(n, ast.Attribute) and n.attr.isupper() and len(n.attr) > 2:
            consts.add(n.attr)
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if isinstance(f, ast.Name):
            if f.id in idx and f.id != func:                     # same file
                m, c, u = reads_of(rel, f.id, depth - 1, _seen)
            elif f.id in names:                                  # from X import f
                mod, orig = names[f.id]
                r2 = _rel_for(mod)
                if r2 is None:
                    unresolved.add(f"{mod}.{orig}"); continue
                m, c, u = reads_of(r2, orig, depth - 1, _seen)
            else:
                continue
            models |= m; consts |= c; unresolved |= u
        elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            alias = f.value.id
            dotted = mods.get(alias)
            if dotted is None:
                continue
            r2 = _rel_for(dotted)
            if r2 is None:
                unresolved.add(f"{dotted}.{f.attr}"); continue
            m, c, u = reads_of(r2, f.attr, depth - 1, _seen)
            models |= m; consts |= c; unresolved |= u
    return models, consts, unresolved


# ── the nine classes CORE derived by reading, for comparison only ────────────
CORE_NINE = {
    "active financial dataset", "assessment cycle snapshot", "valuation runs",
    "CFO overrides in force", "documents / memo text",
    "departments, OKR, KPI rows", "initiatives and status",
    "ratio registry version", "period labels and frequency",
}

# Model → the input class it belongs to. ⭐ THIS MAP IS ITSELF A HAND-SYNCED
# LIST, which is why the scan prints EVERY model it found including the ones
# this map does not classify. An unclassified model is the finding.
CLASS_OF = {
    "FinancialDataset": "active financial dataset",
    "ValuationRun": "valuation runs",
    "AssessmentCycle": "assessment cycle snapshot",
    "AssessmentResponse": "assessment cycle snapshot",
    "AssessmentInvite": "assessment cycle snapshot",
    "Override": "CFO overrides in force",
    "MetricOverride": "CFO overrides in force",
    "EnterpriseDocument": "documents / memo text",
    "Department": "departments, OKR, KPI rows",
    "Objective": "departments, OKR, KPI rows",
    "KeyResult": "departments, OKR, KPI rows",
    "KPI": "departments, OKR, KPI rows",
    "KpiPlan": "departments, OKR, KPI rows",
    "Initiative": "initiatives and status",
    "InitiativeMilestone": "initiatives and status",
    "InitiativeCSF": "initiatives and status",
    "StrategicMove": "strategic move library",
    "Frontier": "strategic move library",
    "Viability": "viability cache",
    "Disposition": "dispositions",
    "Enterprise": "enterprise profile",
}


def main():
    print("§7s.1 — PACK INPUT SCAN, derived from code\n")
    print(f"  models in vocabulary: {len(MODELS)}\n")
    all_models, unfollowed = set(), set()
    for label, rel, func, takes_db in ENTRY_POINTS:
        if rel is None:
            why = ("the §7r ratio LIBRARY is not built — the registry yaml is "
                   "loaded only by a CI guard, never by production code"
                   if label.startswith("2") else "§7s.5, not built")
            print(f"  {label:<22} ⭐ NO ENTRY POINT — {why}")
            continue
        m, c, e = reads_of(rel, func)
        all_models |= m
        unfollowed |= {x for x in e if "NOT FOUND" in x}
        kind = "db-aware" if takes_db else "PURE (reads a payload, not rows)"
        print(f"  {label:<22} {rel.split('/')[-1]}:{func}   [{kind}]")
        print(f"     models    : {', '.join(sorted(m)) or '—'}")
        vers = sorted(x for x in c if any(k in x for k in
                      ("VERSION", "SEED", "REGISTRY", "KFLOOR", "RAG", "BAND", "SIG")))
        print(f"     versioned : {', '.join(vers) or '—'}")
        if any("NOT FOUND" in x for x in e):
            print(f"     ⭐ {[x for x in e if 'NOT FOUND' in x]}")
        if len(e) > 0:
            print(f"     unresolved edges: {len(e)}")
    print(f"\n  DISTINCT MODELS REACHED: {len(all_models)}")
    print(f"     {', '.join(sorted(all_models))}")
    unclassified = sorted(m for m in all_models if m not in CLASS_OF)
    classes = sorted({CLASS_OF[m] for m in all_models if m in CLASS_OF})
    print(f"\n  INPUT CLASSES DERIVED: {len(classes)}")
    for c in classes:
        marker = "  " if c in CORE_NINE else "⭐ NOT IN CORE'S NINE"
        print(f"     {marker} {c}")
    print(f"\n  CORE'S NINE NOT REACHED BY THIS SCAN: "
          f"{sorted(CORE_NINE - set(classes)) or '—'}")
    if unclassified:
        print(f"\n  ⭐ MODELS THIS MAP DOES NOT CLASSIFY ({len(unclassified)}) — the finding:")
        for m in unclassified:
            print(f"     {m}")
    if unfollowed:
        print(f"\n  ⭐ ENTRY POINTS NOT FOUND (the scan's own blind spot):")
        for u in sorted(unfollowed):
            print(f"     {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
