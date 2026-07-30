"""Survey for the shape that produced the enterprise defect.

THE SHAPE: a function whose name describes one concern, whose body has an early
return/continue guarded on the availability of THAT concern's dependency, and
which also performs writes belonging to a DIFFERENT concern behind that guard.
The guard is correct for what it names; the second concern dies silently with it.

Reports only. Deliberately noisy on the guard side and filtered on the write
side — a function with no writes behind its guard cannot exhibit the defect.
"""
import ast, os, sys

ROOTS = ["services", "scripts"]

# A guard is "dependency-shaped" if its test mentions an external/optional thing
# rather than the loop's own subject.
DEP_HINTS = ("client", "storage", "r2", "s3", "bucket", "key", "token", "url",
             "enabled", "configured", "api", "conn", "session", "cfg", "config",
             "settings", "env", "available", "installed", "boto")

WRITE_CALLS = ("add", "add_all", "merge", "bulk_save_objects", "execute")


def guards(fn):
    """Early return/continue statements in the top two statement levels."""
    out = []
    for st in fn.body:
        if isinstance(st, ast.If):
            for sub in st.body:
                if isinstance(sub, (ast.Return, ast.Continue)):
                    out.append(st)
        if isinstance(st, (ast.For, ast.While)):
            for inner in st.body:
                if isinstance(inner, ast.If):
                    for sub in inner.body:
                        if isinstance(sub, (ast.Return, ast.Continue)):
                            out.append(inner)
    return out


def dep_shaped(node):
    src = ast.dump(node.test).lower()
    return any(h in src for h in DEP_HINTS)


def _ctor_bindings(fn):
    """local name -> constructed class, for `x = Model(...)`.

    ⭐ WITHOUT THIS THE SCAN IS BLIND TO ITS OWN MOTIVATING CASE. The defect it
    was built to find writes `ent = Enterprise(...)` then `db.add(ent)` two lines
    later; matching only `db.add(Model(...))` reports it clean. Counting by the
    inline form rather than the shape is the same error as counting by
    identifier — it prints a tick over a floor of zero.
    """
    b = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            f = n.value.func
            cls = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else None)
            if cls and cls[:1].isupper():
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        b[t.id] = cls
    return b


def writes_after(fn, guard):
    """Model names written after the guard's line."""
    binds = _ctor_bindings(fn)
    seen = set()
    for n in ast.walk(fn):
        if not isinstance(n, ast.Call) or getattr(n, "lineno", 0) <= guard.lineno:
            continue
        f = n.func
        if isinstance(f, ast.Attribute) and f.attr in WRITE_CALLS:
            for a in n.args:
                t = a
                if isinstance(t, ast.Call):
                    t = t.func
                if isinstance(t, ast.Name):
                    seen.add(binds.get(t.id, t.id))
                elif isinstance(t, ast.Attribute):
                    seen.add(t.attr)
                elif isinstance(t, (ast.List, ast.Tuple)):
                    for e in t.elts:
                        if isinstance(e, ast.Name):
                            seen.add(binds.get(e.id, e.id))
    return {s for s in seen if s[:1].isupper()}


hits = []
for root in ROOTS:
    for dirpath, _, files in os.walk(root):
        if "node_modules" in dirpath or "__pycache__" in dirpath:
            continue
        for fname in files:
            if not fname.endswith(".py"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except SyntaxError:
                continue
            for fn in ast.walk(tree):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for g in guards(fn):
                    if not dep_shaped(g):
                        continue
                    w = writes_after(fn, g)
                    if w:
                        hits.append((path, fn.lineno, fn.name, g.lineno, sorted(w)))

print(f"{len(hits)} guard/write pairs\n")
for path, fl, name, gl, w in sorted(hits):
    print(f"{path}:{fl}  {name}()")
    print(f"    guard line {gl} -> writes {', '.join(w)}")
