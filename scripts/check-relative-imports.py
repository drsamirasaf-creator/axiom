#!/usr/bin/env python3
"""Every relative import resolves to a module that exists.

⭐⭐ THE DEFECT, PRODUCTION, RELEASE 265aff5. `router.py` in
`services.api.modules.financials` wrote `from .... import frequency_views`.
Four dots is `services`; the module is at `services.api.frequency_views`, which
is three. `GET /datasets/{id}/frequency-view` returned 500 on every call it has
ever had.

## ⛔⭐⭐ WHY NO EXISTING GATE COULD SEE IT

The import is **inside the function body**. Python does not execute it at import
time, so:

  - the module imports cleanly,
  - `from services.api.main import app` builds the whole app cleanly,
  - **an import-time smoke test would pass**, and
  - 33 unit tests passed because they import `services.api.frequency_views`
    DIRECTLY and never go through the router.

⭐ So the instrument cannot be "import everything and see". It has to RESOLVE the
statement against the package tree — which is what this does, for every relative
import at any depth, module-level or function-level, by AST.

⛔ AND THE BROWSER PROOF WAS BLIND BY CONSTRUCTION: it stubs the HTTP endpoint at
the network layer, so the backend was never invoked. A green browser gate over a
stubbed endpoint says the SURFACE works, never that the endpoint does.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_ROOT = os.path.join(ROOT, "services")


def _module_name(path):
    rel = os.path.relpath(path, ROOT)[:-3]          # strip .py
    parts = rel.split(os.sep)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _exists(dotted):
    """Is `dotted` an importable module or package on disk?"""
    p = os.path.join(ROOT, *dotted.split("."))
    return os.path.isfile(p + ".py") or os.path.isfile(
        os.path.join(p, "__init__.py"))


def _binds(pkg_dotted, name):
    """Does `pkg/__init__.py` bind `name`? ⭐ `from . import x` is legal when x
    is defined or re-exported in the package's __init__, not only when it is a
    submodule — so both readings are checked before anything is reported."""
    init = os.path.join(ROOT, *pkg_dotted.split("."), "__init__.py") \
        if pkg_dotted else os.path.join(ROOT, "__init__.py")
    if not os.path.isfile(init):
        return False
    try:
        tree = ast.parse(open(init, encoding="utf-8").read())
    except SyntaxError:
        return True                     # unparseable: do not invent a failure
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                if (a.asname or a.name.split(".")[0]) == name:
                    return True
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if getattr(t, "id", None) == name:
                    return True
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                and n.name == name:
            return True
    return False


def _resolve(pkg, level, module):
    """PEP 328: `level` dots from `pkg`, then `module`.

    ⭐ `level` counts from the CURRENT PACKAGE, so one dot is the package the
    file lives in — which is why the arithmetic is `len(parts) - (level - 1)`
    and why four dots reached `services` from a four-deep package.
    """
    parts = pkg.split(".")
    base = parts[:len(parts) - (level - 1)]
    if len(parts) - (level - 1) < 0:
        return None, "climbs above the source root"
    return (".".join(base + ([module] if module else []))), None


def main():
    fails, n_files, n_imports, by_depth = [], 0, 0, {}
    for base, dirs, files in os.walk(PKG_ROOT):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            p = os.path.join(base, f)
            n_files += 1
            pkg = ".".join(_module_name(p).split(".")[:-1]) or _module_name(p)
            if f == "__init__.py":
                pkg = _module_name(p)
            try:
                tree = ast.parse(open(p, encoding="utf-8").read())
            except SyntaxError as e:
                fails.append(f"{os.path.relpath(p, ROOT)}: unparseable ({e})")
                continue
            # ⭐ ast.walk reaches FUNCTION-LEVEL imports, which is the whole
            # point — a module-level-only scan would have missed this defect.
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or not node.level:
                    continue
                n_imports += 1
                by_depth[node.level] = by_depth.get(node.level, 0) + 1
                dotted, err = _resolve(pkg, node.level, node.module)
                rel = os.path.relpath(p, ROOT)
                if err:
                    fails.append(f"{rel}:{node.lineno}: {'.' * node.level}"
                                 f"{node.module or ''} {err}")
                    continue
                # ⛔⭐⭐ `from ... import X` HAS module=None, AND X IS THE THING
                # BEING RESOLVED. A first version of this guard wrote
                # `if node.module is None: continue` and therefore SKIPPED the
                # exact statement it was written to catch — §III.11 in the
                # instrument itself: it passed on its own defect. The shipped
                # `from .... import frequency_views` is this form.
                if node.module is None:
                    for a in node.names:
                        target = dotted + "." + a.name
                        if _exists(target) or _binds(dotted, a.name):
                            continue
                        fails.append(
                            f"{rel}:{node.lineno}: `from {'.' * node.level}"
                            f"import {a.name}` resolves to {target!r}, which is "
                            f"neither a module nor a name bound in "
                            f"{dotted or '(root)'}/__init__.py")
                    continue
                if _exists(dotted):
                    continue
                fails.append(
                    f"{rel}:{node.lineno}: `from {'.' * node.level}"
                    f"{node.module} import ...` resolves to {dotted!r}, "
                    f"which does not exist")

    print(f"  {n_files} file(s) · {n_imports} relative import(s)")
    print("   by depth: " + " · ".join(f"{'.'*d} {c}"
                                       for d, c in sorted(by_depth.items())))
    # ⭐ §III.4 — an empty corpus fails.
    if n_imports < 50:
        print(f"  ✗ only {n_imports} relative imports found — the scan is wrong")
        return 1

    # ── controls, in memory ───────────────────────────────────────────────
    # ⭐⭐ THE EXACT DEFECT, RESOLVED BY THE SAME FUNCTION.
    pkg = "services.api.modules.financials"
    three, _ = _resolve(pkg, 3, "frequency_views")
    four, _ = _resolve(pkg, 4, "frequency_views")
    assert three == "services.api.frequency_views", \
        f"control: three dots resolved to {three!r}"
    assert four == "services.frequency_views", \
        f"control: four dots resolved to {four!r}"
    assert _exists(three), "control: the correct target does not exist on disk"
    assert not _exists(four), "control: the WRONG target resolves — the shipped " \
                              "import would pass this guard"
    # ⭐ and a function-level import must be reachable by the walker
    # ⭐⭐ THE FORM THAT WAS SKIPPED: module is None and the NAME carries it.
    nomod = ast.parse("from .... import frequency_views\n").body[0]
    assert nomod.module is None and nomod.names[0].name == "frequency_views", \
        "control: the module=None form is not what this guard thinks it is"
    assert not _exists("services.frequency_views") and \
        not _binds("services", "frequency_views"), \
        "control: the shipped wrong target reads as importable"
    probe = ast.parse("def f():\n    from ... import x\n")
    assert any(isinstance(n, ast.ImportFrom) and n.level == 3
               for n in ast.walk(probe)), \
        "control: the walker cannot see a function-level import"
    assert not any(isinstance(n, ast.ImportFrom) and n.level
                   for n in ast.walk(ast.parse("import os"))), \
        "control: an absolute import was counted as relative"
    print("  ✓ controls: three dots reach services.api and four reach services; "
          "the wrong target is absent; a function-level import is seen")

    for f in fails:
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(fails)} relative import(s) resolve to nothing.")
        return 1
    print("\n  ✓ every relative import resolves to a module on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
