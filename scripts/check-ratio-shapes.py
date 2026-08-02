#!/usr/bin/env python3
"""Find registry ratio arithmetic implemented outside its owner.

⭐ WHAT THIS IS AND IS NOT. It keys on ARITHMETIC SHAPE, never on identifier, and
it reports THREE coverage numbers before it reports a single duplicate:

    1. shapes derivable of N       a property of the REGISTRY (N read, not typed)
    2. detectable at all, of (1)   a property of the INSTRUMENT
    3. detectable UNAMBIGUOUSLY    the only number a zero may be read against

⭐ (3) IS LOW AND THAT IS ARITHMETIC, NOT A SHORTFALL. Thirteen registry ratios
are `@0/@1*100` — every margin is one division and a scale. A scan keyed on that
shape reports every percentage in the codebase. For that class duplication has to
be PREVENTED BY BOUNDARY — one module where margins are computed at all — not
detected by shape. A different class needs a different mechanism, not a harder
scan.

⭐ CHAINS ARE CALLS, NOT EXPANSIONS. `avg(axiom.invested_capital)` inside
`axiom.roic` stays a call. Expanding it would make a second ROIC that computes
its own denominator inline INVISIBLE — the inlined canonical form and the
duplicate would share a shape.

Every shape is run against a KNOWN-POSITIVE control before any zero is believed.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml
from ratio_shapes import complexity, detectable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "docs", "reference", "axiom_ratio_registry.yaml")
LIBRARY = os.path.join("services", "api", "modules", "financials", "ratios.py")
SCAN_ROOTS = ["services"]

TOK = re.compile(r'\b(?:is|bs|cf|mk|po|hc|sa)\.[a-z_0-9]+')
RAT = re.compile(r'\baxiom\.[a-z_0-9]+')
CHAIN_CALLS = {"ratio_lib", "ratios"}
FUNCS = {"avg", "prior", "abs", "min", "max"}


# ── canonical form, shared by both sides ────────────────────────────────────
def _flatten(node, canon, op_add=True):
    """Additive / multiplicative chains -> a sorted multiset with signs, so
    `equity + debt - cash` and `debt + equity - cash` are ONE shape. Operand
    ORDER is not arithmetic structure; treating it as such would split one
    duplicate into two 'unique' shapes and report a false zero."""
    terms = []

    def walk(n, sign):
        if isinstance(n, ast.BinOp):
            if op_add and isinstance(n.op, (ast.Add, ast.Sub)):
                walk(n.left, sign)
                walk(n.right, sign * (1 if isinstance(n.op, ast.Add) else -1))
                return
            if not op_add and isinstance(n.op, (ast.Mult,)):
                walk(n.left, sign); walk(n.right, sign)
                return
        terms.append((sign, canon(n)))
    walk(node, 1)
    return tuple(sorted(terms, key=repr))


def canon_factory():
    slots, chains = {}, {}

    def canon(n):
        if isinstance(n, ast.BinOp):
            if isinstance(n.op, (ast.Add, ast.Sub)):
                return ("add", _flatten(n, canon, True))
            if isinstance(n.op, ast.Mult):
                return ("mul", _flatten(n, canon, False))
            if isinstance(n.op, ast.Div):
                return ("div", canon(n.left), canon(n.right))
            if isinstance(n.op, ast.Pow):
                return ("pow", canon(n.left), canon(n.right))
            return ("op", type(n.op).__name__, canon(n.left), canon(n.right))
        if isinstance(n, ast.UnaryOp):
            return ("neg", canon(n.operand)) if isinstance(n.op, ast.USub) else canon(n.operand)
        if isinstance(n, ast.Constant):
            return ("num", float(n.value)) if isinstance(n.value, (int, float)) else ("const",)
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "?")
            holder = (f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else None)
            if holder in CHAIN_CALLS or name.startswith("__chain__"):
                key = f"{holder}.{name}"
                return ("chain", chains.setdefault(key, len(chains)))
            if name in FUNCS:
                return ("f", name, tuple(canon(a) for a in n.args))
            return ("leaf", slots.setdefault(_key(n), len(slots)))
        return ("leaf", slots.setdefault(_key(n), len(slots)))

    return canon


def _key(n):
    try:
        return ast.dump(n)
    except Exception:
        return repr(n)


def shape_of_expr(node):
    return canon_factory()(node)


def shape_of_formula(formula):
    """Registry formula -> the same canonical form, via a Python-parsable proxy."""
    s = " ".join(formula.split())
    ch = {}

    def sub_r(m):
        k = m.group(0)
        i = ch.setdefault(k, len(ch))
        return f"ratio_lib.__chain__{i}()"
    s = RAT.sub(sub_r, s)
    sl = {}

    def sub_t(m):
        k = m.group(0)
        i = sl.setdefault(k, len(sl))
        return f"t{i}"
    s = TOK.sub(sub_t, s)
    try:
        return shape_of_expr(ast.parse(s, mode="eval").body)
    except SyntaxError:
        return None


# ── registry side ───────────────────────────────────────────────────────────
def load():
    d = yaml.safe_load(open(REGISTRY, encoding="utf-8"))
    V = {t: m["source"] for g in d["vocabulary"].values() for t, m in g.items()}
    R = {r["id"]: r for r in d["ratios"]}
    memo = {}

    def ok(rid, st=()):
        if rid in memo:
            return memo[rid]
        if rid in st or rid not in R:
            return False
        f = R[rid]["formula"]
        res = (all(V.get(t) != "absent" for t in TOK.findall(f))
               and all(ok(c, st + (rid,)) for c in RAT.findall(f)))
        memo[rid] = res
        return res
    derivable = [r for r in d["ratios"] if ok(r["id"])]
    return d, derivable


# ── code side ───────────────────────────────────────────────────────────────
def iter_expressions(path, _src=None):
    """Every arithmetic expression, with `_n(lambda ...)` unwrapped to its body —
    the library's own absence-propagating form must be comparable to a bare one,
    or the wrapped canonical version and an unwrapped duplicate look different."""
    try:
        tree = ast.parse(_src if _src is not None
                         else open(path, encoding="utf-8").read())
    except SyntaxError:
        return
    # ⭐ ROOTS ONLY. Walking every BinOp yields SUB-EXPRESSIONS: `nn+dd-cc` is a
    # subtree of the five-term FCFE identity at engines.py:295, and matched
    # net_debt's three-term shape. Three of the first run's five false positives
    # were this. A chain is compared at its root or not at all.
    parent = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parent[ch] = n

    def same_class(a, b):
        if not (isinstance(a, ast.BinOp) and isinstance(b, ast.BinOp)):
            return False
        add = (ast.Add, ast.Sub)
        mul = (ast.Mult,)
        return ((isinstance(a.op, add) and isinstance(b.op, add))
                or (isinstance(a.op, mul) and isinstance(b.op, mul)))

    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm == "_n" and n.args and isinstance(n.args[0], ast.Lambda):
                yield n.args[0].body, getattr(n, "lineno", 0)
                continue
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            if same_class(n, parent.get(n)):
                continue                 # not the root of its chain
            yield n, getattr(n, "lineno", 0)


def scan(shapes, roots=None, sources=None):
    """shapes: {canonical_form: ratio_id} -> [(ratio_id, path, line)]

    ⭐ `sources` = {label: source_text}, scanned through the SAME code path as a
    file. The control passes sources so it never touches the filesystem.
    """
    hits = []
    for label, src in (sources or {}).items():
        for node, line in iter_expressions(label, _src=src):
            sh = shape_of_expr(node)
            if sh in shapes:
                hits.append((shapes[sh], label, line))
    # ⭐⭐ `roots is None` MEANS DEFAULT; `roots=[]` MEANS NONE. The previous
    # `(roots or SCAN_ROOTS)` treated an empty list as "unset", so a control
    # asking for sources-only silently scanned the entire codebase and found
    # real occurrences instead of its own plant — a control that cannot fail.
    for root in (SCAN_ROOTS if roots is None else roots):
        for dp, _, fs in os.walk(root):
            if "__pycache__" in dp:
                continue
            for fn in fs:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                for node, line in iter_expressions(p):
                    s = shape_of_expr(node)
                    if s in shapes:
                        hits.append((shapes[s], p, line))
    return hits


# ── known-positive control ──────────────────────────────────────────────────
def control(shapes, registry_by_id):
    """⭐ EVERY SHAPE IS PROVEN TO FIRE BEFORE ANY ZERO IS BELIEVED.

    Each registry formula is rendered as a synthetic Python expression and fed
    through the SAME code-side path the scanner uses. A shape whose control does
    not fire is excluded from the reported coverage — a scanner that has never
    seen a true positive has not been tested, and counting it as covered would
    put a zero over a floor of zero.
    """
    passed, failed = {}, {}
    for form, rid in shapes.items():
        f = registry_by_id[rid]["formula"]
        s = " ".join(f.split())
        ch = {}
        s = RAT.sub(lambda m: f"ratio_lib.__chain__{ch.setdefault(m.group(0), len(ch))}()", s)
        sl = {}
        s = TOK.sub(lambda m: f"v{sl.setdefault(m.group(0), len(sl))}", s)
        try:
            node = ast.parse(s, mode="eval").body
        except SyntaxError:
            failed[rid] = "control could not be parsed"
            continue
        got = shape_of_expr(node)
        if got == form:
            passed[rid] = form
        else:
            failed[rid] = "control did not reproduce the shape"
    return passed, failed


def end_to_end_control(shapes, by_id):
    """⭐ THE CONTROL THAT ACTUALLY MATTERS. The shape round-trip above proves a
    formula canonicalises consistently; it does NOT prove the scanner finds that
    shape sitting in a source file. This writes a synthetic duplicate of every
    shape into a throwaway module and runs the REAL scan over it. A shape whose
    duplicate is not found is excluded from coverage — a scanner that has never
    fired has not been tested, and its zero would be a floor of zero.
    """
    # ⭐⭐ BUILT AS STRINGS, NEVER WRITTEN. The previous form wrote one module
    # per shape into a temp dir; a kill left the directory behind. Nothing is
    # written now, so nothing can be stranded.
    sources = {}
    for i, (form, rid) in enumerate(shapes.items()):
        f = " ".join(by_id[rid]["formula"].split())
        ch = {}
        f = RAT.sub(lambda m: f"ratio_lib.__chain__{ch.setdefault(m.group(0), len(ch))}()", f)
        sl = {}
        f = TOK.sub(lambda m: f"v{sl.setdefault(m.group(0), len(sl))}", f)
        args = ", ".join(f"v{j}" for j in range(len(sl))) or "_"
        sources[f"<control-dup-{i}>"] = ("import ratio_lib\n"
                                         f"def dup_{i}({args}):\n"
                                         f"    return {f}\n")
    found = {rid for rid, _, _ in scan(shapes, roots=[], sources=sources)}
    want = set(shapes.values())
    return found & want, want - found


def main():
    d, derivable = load()
    by_id = {r["id"]: r for r in d["ratios"]}
    from collections import defaultdict
    groups = defaultdict(list)
    for r in derivable:
        groups[complexity(r["formula"])["shape"]].append(r["id"])

    det = [r for r in derivable if detectable(complexity(r["formula"]))]
    unamb = [r for r in det if len(groups[complexity(r["formula"])["shape"]]) == 1]

    shapes = {}
    collide = []
    for r in unamb:
        f = shape_of_formula(r["formula"])
        if f is None:
            continue
        if f in shapes:
            collide.append((shapes[f], r["id"]))
            continue
        shapes[f] = r["id"]

    passed, failed = control(shapes, by_id)
    e2e_ok, e2e_bad = end_to_end_control(shapes, by_id)
    for rid in e2e_bad:
        failed.setdefault(rid, "end-to-end control did not fire")
        passed.pop(rid, None)
    live = {f: rid for f, rid in shapes.items() if rid in passed}

    print("COVERAGE — before any duplicate count")
    # ⭐ THE DENOMINATOR IS READ, NEVER TYPED. It was the literal 79 and the
    # registry became 80 on 2 Aug — a coverage line whose denominator is a
    # constant stops describing the corpus the moment the corpus moves, and
    # reports the same reassuring fraction while drifting.
    print(f"  1. shapes derivable of {len(by_id):<17d}{len(derivable)}")
    print(f"  2. detectable at all, of {len(derivable):<3}             {len(det)}")
    print(f"  3. detectable UNAMBIGUOUSLY, of {len(derivable):<3}      {len(unamb)}")
    print(f"  4. known-positive control PASSES         {len(live)}   <- a zero may only be read against this")
    print(f"     (shape round-trip AND an end-to-end run over a synthetic duplicate)")
    if failed:
        print(f"     control FAILED, excluded from coverage: {sorted(failed)}")
    if collide:
        print(f"     canonical-form collisions after flattening: {collide}")
    print()

    hits = scan(live)
    outside = [(rid, p, ln) for rid, p, ln in hits if os.path.normpath(p) != os.path.normpath(LIBRARY)]
    owned = {rid for rid, pth, _ in hits if os.path.normpath(pth) == os.path.normpath(LIBRARY)}
    print("OWNERSHIP — and read the second line exactly as written")
    print(f"  found IN the library            : {len(owned)}  {sorted(r.replace('axiom.','') for r in owned)}")
    unowned = sorted(set(live.values()) - owned)
    print(f"  NOT LOCATED BY THIS SCAN       : {len(unowned)}")
    print(f"    {[r.replace('axiom.','') for r in unowned]}")
    print("    ⭐ THIS IS NOT 'unimplemented'. axiom.fcff is in that list AND is")
    print("      implemented at engines.py:291. The scan cannot see it because the")
    print("      NWC delta is a separate statement. At least one of these is a miss,")
    print("      so the list is a search result, not an inventory of absences.")
    print()
    print(f"DUPLICATES — matches outside {LIBRARY}")
    if not outside:
        print(f"  none, across {len(live)} shapes")
    for rid, p, ln in sorted(outside):
        print(f"  {rid:<32}{p}:{ln}")
    print()
    print("WHAT THIS SCAN CANNOT SEE")
    print(f"  · {len(derivable)-len(det)} derivable ratios are too bare to search for (@0/@1 and kin).")
    print(f"  · {len(det)-len(unamb)} more share a shape with another ratio — 13 ratios are @0/@1*100.")
    print("  · Python under services/ only. No frontend, no SQL, no notebooks.")
    print("  · Arithmetic written across statements (t = a - b; then t / c) is invisible.")
    print("    ⭐ DEMONSTRATED, NOT HYPOTHETICAL: axiom.fcff IS implemented at")
    print("      engines.py:291 and this scan does NOT find it, because d_nwc is")
    print("      computed on an earlier line instead of inline. FCFF is one of the")
    print("      14 shapes below, so the zero already contains one known miss.")
    print("  · A duplicate that reorders into an algebraically equal but structurally")
    print("    different form (a*(1-t) vs a - a*t) is not matched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
