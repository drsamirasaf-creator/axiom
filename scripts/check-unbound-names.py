#!/usr/bin/env python3
"""Standing gate: a name loaded in a function that nothing in scope binds.

⭐ THIS FILE'S FIRST VERSION FAILED ITS OWN CHECK, WHICH IS THE ARGUMENT FOR IT.
`out |= {...}` inside a closure is an AUGMENTED assignment, so Python treats `out`
as local to that closure and it raises UnboundLocalError — while `out.add(...)`
two lines above is a method call and works. Written, reviewed, and broken in the
same way as the code it was written to police. It now uses `.update()`, which
rebinds nothing.

⭐ WHY THIS IS A GATE AND NOT A LINT PREFERENCE. Splicing the cycle-selection out
of three functions deleted a local `from ... import apply_kfloor` along with the
loop beside it, and left `cycles` bound only inside a branch. The full test suite
stayed green through all three, and production returned HTTP 500 on two
companies. Every one of those was statically visible: a Load of a name that no
enclosing scope binds. Nothing was looking.

CLOSURE-AWARE. Scopes nest, so a nested function reading a name its parent binds
is fine — the first version of this sweep flagged eight such cases and would have
been switched off within a week for crying wolf.

⭐ ITS BLIND SPOTS, STATED RATHER THAN DISCOVERED LATER:
  · Conditional binding. `if x: y = 1` then `y` reads as bound. That is exactly
    the `cycles` defect, so this gate would NOT have caught #2 — only #1 and #3.
    Catching it needs flow analysis, not scope analysis.
  · Star-imports and names injected into globals() at runtime are invisible.
  · Attribute access (`mod.thing`) is not checked, only bare names.
  · Class bodies are treated as their own scope, which matches Python.

So it is a floor, not a proof. It catches the deleted-import class outright and
says plainly that it does not catch the conditional-binding class.
"""
import ast, builtins, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ⭐ ENUMERATED, NOT LISTED. This was twelve hardcoded module paths — a list that
# goes stale the moment a module is added, and then reports "✓ none" over files it
# has never opened. The same class as proxy-sweep's ROUTER_FILES, which let six
# 500s pass a green sweep. The tree is walked instead.
def _targets():
    out = []
    for dirpath, dirs, files in os.walk(os.path.join(ROOT, "services", "api")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.relpath(os.path.join(dirpath, f), ROOT))
    return sorted(out)


TARGETS = _targets()
BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "self", "cls"}



# ⭐ A COVERAGE FLOOR. A guard that finds NOTHING TO CHECK must be red, never
# green: "0 problems in 0 files" and "0 problems in 400 files" print the same
# tick and mean opposite things. Two of these gates already exited 0 with the
# frontend absent, having opened no file at all.
#
# The floor is the observed count at the time of writing. It is not a target —
# it is the assertion that the SELECTOR still selects. Raise it when the real
# number grows; lowering it is only correct alongside a deliberate deletion, and
# should be argued for in the commit that does so.
MIN_MODULES = 80


def bound_in(node):
    """Names this scope binds, WITHOUT descending into nested function scopes."""
    out = set()

    def walk(n, top=False):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(child.name)
                continue                      # its interior is its own scope
            if isinstance(child, ast.Lambda):
                continue
            if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                out.add(child.id)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                out.update((a.asname or a.name).split(".")[0] for a in child.names)
            elif isinstance(child, ast.ExceptHandler) and child.name:
                out.add(child.name)
            elif isinstance(child, (ast.Global, ast.Nonlocal)):
                out.update(child.names)
            walk(child)

    for a in getattr(getattr(node, "args", None), "args", []) or []:
        out.add(a.arg)
    for a in getattr(getattr(node, "args", None), "kwonlyargs", []) or []:
        out.add(a.arg)
    va = getattr(getattr(node, "args", None), "vararg", None)
    kw = getattr(getattr(node, "args", None), "kwarg", None)
    if va: out.add(va.arg)
    if kw: out.add(kw.arg)
    walk(node, top=True)
    return out


def loads_in(node):
    """Bare-name Loads in this scope, not descending into nested scopes."""
    out = []

    def walk(n):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                out.append((child.id, child.lineno))
            walk(child)

    walk(node)
    return out


def check(path):
    tree = ast.parse(open(path).read())
    module_scope = bound_in(tree)
    findings = []

    def visit(node, enclosing, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                own = bound_in(child)
                scope = enclosing | own
                for name, line in loads_in(child):
                    if name not in scope and name not in BUILTINS:
                        findings.append((f"{prefix}{child.name}", line, name))
                visit(child, scope, f"{prefix}{child.name}.")
            elif isinstance(child, ast.ClassDef):
                visit(child, enclosing | bound_in(child), f"{prefix}{child.name}.")
            else:
                visit(child, enclosing, prefix)

    visit(tree, module_scope, "")
    return findings


def main():
    total = 0
    for rel in TARGETS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        found = check(p)
        for fn, line, name in found:
            print(f"  {rel}:{line}  {fn}() loads unbound name {name!r}")
        total += len(found)
    scanned = sum(1 for rel in TARGETS if os.path.exists(os.path.join(ROOT, rel)))
    if scanned < MIN_MODULES:
        print(f"\nFAIL — inspected only {scanned} module(s), floor is {MIN_MODULES}. "
              f"The selector stopped selecting; a clean result over nothing is not a "
              f"clean result.")
        return 1
    if total:
        print(f"\nFAIL — {total} unbound name(s). Each is a NameError waiting for the "
              f"branch that reaches it.")
        return 1
    print(f"✓ unbound-names: {len(TARGETS)} modules, none. "
          f"(Blind to conditional binding — see the module docstring.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
