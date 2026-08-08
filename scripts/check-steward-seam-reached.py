#!/usr/bin/env python3
"""Every widened endpoint must reach `_steward_or_admin`.

⛔⭐⭐ THE HOLE THIS CLOSES. A handler that FORGOT to call the seam looks
identical, from the outside, to one that called it and refused — both return
data to an admin and both look correct in every test that uses an admin
credential. The seam's own tests prove the seam; they cannot prove a handler
consulted it.

⭐ THE SET IS DERIVED FROM THE ROUTE TABLE AND THE HANDLER'S AST, NOT A LIST:

    a route is IN SCOPE when it is a WRITE, is NOT gated by
    `require_company_admin`, and its handler MUTATES a model that carries a
    `department_id`.

So a lane that widens a fourth endpoint enters the denominator by writing the
code, not by remembering to add itself here. ⛔ A list would have to be updated
by the same person who forgot the call.

⭐ THE DENOMINATOR IS PRINTED EVERY RUN, with each handler and its verdict — a
guard that printed only failures reads identically at 3-of-3 and 0-of-0.
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

SEAM = "_steward_or_admin"
WRITE = {"POST", "PUT", "PATCH", "DELETE"}


def _routes(app):
    out = []

    def walk(routes, prefix=""):
        for r in routes:
            if type(r).__name__ == "_IncludedRouter":
                ctx = getattr(r, "include_context", None)
                walk(r.original_router.routes, prefix + (getattr(ctx, "prefix", "") or ""))
                continue
            p = prefix + (getattr(r, "path", "") or "")
            fn = getattr(r, "endpoint", None)
            if fn is None:
                continue
            dep = getattr(r, "dependant", None)
            deps = {getattr(getattr(d, "call", None), "__name__", "")
                    for d in (dep.dependencies if dep else [])}
            for m in (getattr(r, "methods", None) or []):
                if m in WRITE:
                    out.append((m, p, fn, deps))
    walk(app.routes)
    return out


def department_scoped_models(A) -> set[str]:
    """Every mapped class whose table carries a `department_id`.

    ⭐ Derived from the metadata, so a model that gains the column joins the
    rule automatically.
    """
    names = set()
    for name in dir(A):
        obj = getattr(A, name, None)
        t = getattr(obj, "__table__", None)
        if t is not None and "department_id" in {c.name for c in t.columns}:
            names.add(name)
    return names


def mutates(fn, models: set[str]) -> set[str]:
    """Model names this handler MUTATES — constructed, deleted, or whose loaded
    row it assigns to.

    ⛔ A read of a department-scoped model is NOT a mutation. A guard that fired
    on reads would demand an authorization check on every list endpoint and be
    switched off within a week.
    """
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return set()
    src = "\n".join(src.splitlines())
    try:
        tree = ast.parse(src.lstrip())
    except SyntaxError:
        try:
            tree = ast.parse(inspect.cleandoc(src))
        except SyntaxError:
            return set()
    hit = set()
    for node in ast.walk(tree):
        # db.add(Model(...))  /  Model(...) constructed
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in models:
                hit.add(node.func.id)
        # db.delete(x) where x came from a Model query — approximated by the
        # presence of a delete call in a handler that names the model at all.
        if isinstance(node, ast.Attribute) and node.attr == "delete":
            for n2 in ast.walk(tree):
                if isinstance(n2, ast.Name) and n2.id in models:
                    hit.add(n2.id)
    # assignment to a loaded row's attribute, e.g. `kpi.department_id = ...`
    if any(isinstance(n, ast.Assign) and
           any(isinstance(t, ast.Attribute) for t in n.targets)
           for n in ast.walk(tree)):
        for n2 in ast.walk(tree):
            if isinstance(n2, ast.Name) and n2.id in models:
                hit.add(n2.id)
    return hit


def main() -> int:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from services.api.main import app
        from services.api import accounts as A

    models = department_scoped_models(A)
    print(f"models carrying department_id ({len(models)}): {sorted(models)}")

    # ⭐ THE OTHER ROW-LEVEL SEAMS THIS CODEBASE ALREADY HAS. A handler guarded by
    # one of these is NOT unguarded — it is guarded by a different per-row rule,
    # and demanding `_steward_or_admin` there would be a second mechanism for one
    # question. Derived as names, checked in the handler's own source.
    ROW_LEVEL = (SEAM, "_leader_or_admin", "may_revoke_leadership",
                 "_is_company_admin", "invited_email")

    scoped, company_wide, unguarded = [], [], []
    for m, p, fn, deps in sorted(_routes(app), key=lambda x: (x[1], x[0])):
        if "require_company_admin" in deps:
            continue                      # still binary — correct, and not widened
        touched = mutates(fn, models)
        if not touched:
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):
            src = ""
        row = [n for n in ROW_LEVEL if n in src]
        row_ok = bool(row)
        # ⛔ A CAPABILITY DEPENDENCY IS AUTHORIZATION, AND IT IS COMPANY-WIDE.
        # `require_capability(...)` arrives as a closure, so the dependency's
        # name is the local it was bound to — the presence of a non-plumbing
        # dependency is the signal, not its spelling.
        # ⛔⭐⭐ `require_company_member` IS NOT AUTHORIZATION FOR A WRITE. It
        # asserts membership, nothing more. Counting it here made this guard
        # unable to fire: removing the seam from a converted handler simply
        # reclassified it as "company-wide" and the check stayed green — an
        # assertion that could never fail (§III.11), caught by red-proofing it.
        PLUMBING = {"get_db", "get_current_user", "require_company_member", ""}
        cap = bool({d for d in deps} - PLUMBING)
        rec = (m, p, fn.__name__, sorted(touched), row)
        if row_ok:
            scoped.append(rec)
        elif cap:
            company_wide.append(rec)
        else:
            unguarded.append(rec)

    total = len(scoped) + len(company_wide) + len(unguarded)
    print(f"\nWIDENED WRITES TOUCHING A DEPARTMENT-SCOPED MODEL: {total}")
    print(f"\n⭐ reached a ROW-LEVEL seam ({len(scoped)}):")
    for m, p, name, touched, row in scoped:
        print(f"     {m:<7} {p:<54} {name}  via {row}")
    print(f"\n⚠️  authorized COMPANY-WIDE, not per department ({len(company_wide)}):")
    for m, p, name, touched, _ in company_wide:
        print(f"     {m:<7} {p:<54} {name}  {touched}")
    print("     ⛔ Not a failure and not safe either: a decision-maker in one "
          "department can mutate another's row.\n        This is the widening "
          "backlog, named rather than counted as covered.")

    if unguarded:
        print(f"\n⛔ {len(unguarded)} handler(s) mutate a department-scoped model "
              f"with NO authorization at all:")
        for m, p, name, touched, _ in unguarded:
            print(f"     {m} {p}  ({name}) touches {touched}")
        print("\n   A handler that forgot the seam is indistinguishable from one "
              "that called it and refused.")
        print(f"\nFAILED — {len(unguarded)} unguarded")
        return 1
    print(f"\nOK — every widened write reaches an authorization check; "
          f"{len(scoped)} of {total} are department-scoped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
