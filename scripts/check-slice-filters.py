#!/usr/bin/env python3
"""A handler that filters by department or seniority must go through _slice_filters().

⭐ THREE HANDLERS MADE THE SAME MISTAKE INDEPENDENTLY, WHICH IS WHAT MAKES IT A
CLASS RATHER THAN A BUG. Each one did:

    try:
        _sen = _norm_seniority(seniority)
    except HTTPException:
        _sen = None

and `None` does not mean "invalid" — it means NO FILTER. So `?seniority=C-suite`
(not one of the five real bands) returned the FULL UNSLICED SET while echoing
`seniority_filter: null`. The department id had the same shape: an id that did
not resolve, or belonged to another company, silently became "no department
filter" rather than an error.

⭐ A FILTER THAT SILENTLY BECOMES NO FILTER FAILS IN THE WORST DIRECTION. Failing
closed returns nothing and is obvious. Failing open returns MORE than was asked
for and looks like an answer — and on a k-floored surface, "more than was asked
for" is the definition of the thing the floor exists to prevent.

The fix was one helper. This gate is what stops the fourth handler, because the
next person to add a sliced endpoint will reach for the same try/except that is
still visible in the file's history and in every similar codebase.

⭐ CALIBRATED ONCE, AND THE CALIBRATION IS THE RULE. The first run flagged 8
handlers. Six take `department: int | None` and apply it as a DIRECT EQUALITY
FILTER — an id that does not exist yields ZERO rows, which fails CLOSED and is
the safe direction. They are not the defect and flagging them would have got this
gate muted, which is worse than not having it.

The defect needs a value that must be NORMALISED before use, because
normalisation is what can fail and be swallowed. That is `seniority` — a free
string matched against five bands — and `department` only where it is resolved
through a lookup whose failure yields None rather than an error. So the gate
tracks the resolver, not the parameter name.

WHAT IT CHECKS
  Any handler whose signature takes `seniority` must either
    (a) call `_slice_filters(...)`, or
    (b) call `_norm_seniority(...)` OUTSIDE a try/except that swallows
        HTTPException — i.e. let the 422 propagate.
  Swallowing HTTPException around either resolver is a hard failure.

⭐ ITS BLIND SPOTS, STATED:
  · It reasons over the AST of one module. A resolver called through an alias or
    a helper it cannot follow is invisible.
  · It does not check that the resolved values are actually APPLIED to the query
    — only that they were resolved without being silently discarded.
  · A handler that takes the params and deliberately ignores them is flagged;
    that is intended, because "deliberately ignores a filter" is worth saying out
    loud rather than inferring.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "services", "api", "accounts.py")
# `seniority` only: a string that must be normalised, where a swallowed failure
# silently becomes "no filter". `department: int` applied as an equality filter
# fails closed on its own — see the calibration note above.
SLICE_PARAMS = {"seniority"}
RESOLVERS = {"_norm_seniority", "_slice_filters"}


def _is_route_handler(fn):
    """A function mounted as an HTTP endpoint — the boundary untrusted input
    crosses. Internal helpers are out of scope by design."""
    for d in fn.decorator_list:
        f = d.func if isinstance(d, ast.Call) else d
        if isinstance(f, ast.Attribute) and f.attr in (
                "get", "post", "put", "patch", "delete"):
            return True
    return False


def _calls(node):
    return {n.func.id for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def _swallows_httpexception_around_resolver(fn):
    """True if a try/except HTTPException wraps a resolver call — the defect."""
    for node in ast.walk(fn):
        if not isinstance(node, ast.Try):
            continue
        body_calls = set()
        for stmt in node.body:
            body_calls |= _calls(stmt)
        if not (body_calls & RESOLVERS):
            continue
        for handler in node.handlers:
            names = []
            t = handler.type
            if isinstance(t, ast.Name):
                names = [t.id]
            elif isinstance(t, ast.Tuple):
                names = [e.id for e in t.elts if isinstance(e, ast.Name)]
            elif t is None:
                names = ["<bare except>"]
            if any(n in ("HTTPException", "Exception", "<bare except>") for n in names):
                # a handler that RE-RAISES is fine
                reraises = any(isinstance(s, ast.Raise) and s.exc is None
                               for s in handler.body)
                if not reraises:
                    return True
    return False


def main():
    tree = ast.parse(open(TARGET, encoding="utf-8").read())
    findings = []
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = {a.arg for a in node.args.args} | {a.arg for a in node.args.kwonlyargs}
        if not (args & SLICE_PARAMS):
            continue
        # ⭐ ROUTE HANDLERS ONLY. The second calibration: `_submit_responses` and
        # `_axis_comment_counts` also take a `seniority` argument, and both receive
        # a value their CALLER has already resolved — one stamps it onto rows, the
        # other filters on a band the handler validated. Requiring an internal
        # helper to re-resolve would be noise, and worse, would push the check away
        # from the boundary where untrusted input actually arrives.
        if not _is_route_handler(node):
            continue
        checked += 1
        calls = _calls(node)
        if _swallows_httpexception_around_resolver(node):
            findings.append((node.name, node.lineno,
                             "swallows the resolver's 422 — an invalid value "
                             "becomes NO FILTER"))
        elif not (calls & RESOLVERS):
            findings.append((node.name, node.lineno,
                             "takes a slice parameter but never resolves it "
                             "through _slice_filters()"))

    print(f"  {checked} route handler(s) take a seniority parameter")
    for name, line, why in findings:
        print(f"    accounts.py:{line}  {name}() — {why}")
    if findings:
        print(f"\nFAIL — {len(findings)} sliced handler(s) can fail OPEN. An invalid "
              f"filter must 422, never widen the result set.")
        return 1
    print("  ✓ every sliced handler resolves through the fail-closed path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
