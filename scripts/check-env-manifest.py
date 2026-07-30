#!/usr/bin/env python3
"""Every environment variable the code reads must appear in .env.example.

⭐ A MANIFEST NOBODY CHECKS IS A CLAIM, NOT A MANIFEST. The recoverability audit
found 58 variables by grep; an AST scan found 59, because the grep could not see
`os.environ["X"]` — the SUBSCRIPT form, which is precisely the class with no
default and therefore the class that stops the process. The one variable the
looser method missed was the only strictly required one in the codebase.

So this checks BOTH directions, on demand and in CI:

  · read by the code, absent from .env.example  -> a rebuilder cannot know it
  · in .env.example, read nowhere               -> the manifest describes a
                                                   variable that does nothing,
                                                   which is the same defect as a
                                                   guard clause that guards nothing

Scripts-only variables are recognised: they are documented in their own section
because they are not needed to RUN AXIOM, only to verify it.
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, ".env.example")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".pytest_cache"}


def _is_env_read(fn):
    """os.environ.get(...) | os.getenv(...) | environ.get(...) — and nothing else.

    ⭐ Matching any `.get()` was the first attempt and it reported EBITDA, ROIC,
    WACC and the risk-engine matrices A/B/H as environment variables. A counter
    that cannot tell os.environ.get from dict.get is measuring the wrong thing."""
    if not isinstance(fn, ast.Attribute):
        return False
    if fn.attr == "getenv":
        return isinstance(fn.value, ast.Name) and fn.value.id == "os"
    if fn.attr == "get":
        v = fn.value
        return ((isinstance(v, ast.Attribute) and v.attr == "environ")
                or (isinstance(v, ast.Name) and v.id == "environ"))
    return False


def read_by_code():
    """{name: 'app' | 'scripts'}"""
    found = {}
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(base, f)
            rel = os.path.relpath(path, ROOT)
            if rel == os.path.join("scripts", os.path.basename(__file__)):
                continue
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except Exception:
                continue
            names = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and _is_env_read(n.func) and n.args:
                    a = n.args[0]
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        names.add(a.value)
                elif isinstance(n, ast.Subscript):
                    v = n.value
                    if ((isinstance(v, ast.Attribute) and v.attr == "environ")
                            or (isinstance(v, ast.Name) and v.id == "environ")):
                        k = n.slice
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            names.add(k.value)
            scope = "scripts" if rel.startswith("scripts" + os.sep) else "app"
            for nm in names:
                if found.get(nm) != "app":
                    found[nm] = scope
    return found


def documented():
    if not os.path.exists(MANIFEST):
        return None
    src = open(MANIFEST, encoding="utf-8").read()
    # a name is documented if it appears as `NAME=` or is listed in the
    # scripts-only / platform-only prose sections
    out = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", src, re.M))
    # prose sections list one NAME per line, indented, then an explanation.
    # The column legend (REQUIRED / OPTIONAL / PLATFORM) is excluded by name —
    # it describes the format, it is not a variable.
    LEGEND = {"REQUIRED", "OPTIONAL", "PLATFORM"}
    out |= {m for m in re.findall(r"^#\s+([A-Z][A-Z0-9_]{3,})\s{2,}", src, re.M)
            if m not in LEGEND}
    return out


def main():
    code = read_by_code()
    doc = documented()
    if doc is None:
        print(f"  ✗ {MANIFEST} does not exist.")
        return 2

    missing = sorted(n for n in code if n not in doc)
    extra = sorted(n for n in doc if n not in code)

    print(f"  read by code : {len(code)}  "
          f"({sum(1 for v in code.values() if v == 'app')} app, "
          f"{sum(1 for v in code.values() if v == 'scripts')} scripts-only)")
    print(f"  documented   : {len(doc)}")

    rc = 0
    if missing:
        print(f"\n  ✗ READ BUT NOT DOCUMENTED ({len(missing)}) — a rebuilder "
              f"cannot know these exist:")
        for n in missing:
            print(f"      {n}  [{code[n]}]")
        rc = 1
    if extra:
        print(f"\n  ✗ DOCUMENTED BUT READ NOWHERE ({len(extra)}) — the manifest "
              f"describes variables that do nothing:")
        for n in extra:
            print(f"      {n}")
        rc = 1
    if rc == 0:
        print(f"\n  ✓ {len(code)} of {len(code)} read variables documented, "
              f"and nothing documented that is not read.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
