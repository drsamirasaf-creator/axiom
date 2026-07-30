"""Two questions, two resolvers, and the live computers may not ask the wrong one.

⭐ THE DEFECT THIS ENCODES. `resolve_active_cycle` was documented as "THE cycle
every results surface should read", and its test is `snapshot["cei"] is not
None`. Two surfaces took it literally while reading no snapshot at all:
`_dept_cei_map` and `_dept_coverage` compute from responses via `_cycle_cei`,
which never opens `cycle.snapshot`. They asked "has this been published?" when
they needed "is there anything to compute?".

The two questions agree wherever snapshots are written at close — everywhere in
production, measured: 9 of 9 closed cycles carrying responses had one, and 0
did not. They diverge on any database where responses were restored without
snapshots. A rebuilt showcase has 14,430 responses, a computable CEI and no
snapshots, so `assessment_summary` rendered a CEI while the departmental map
returned empty from identical rows.

⭐ CLASSIFY BY WHAT A FUNCTION NEEDS, NOT BY WHAT IT HAS. Counting fallbacks said
1 of 11 had one and the rest were omissions. Six of those "omissions" read the
snapshot and nothing else — for them there is nothing to fall back TO, and a
fallback would render an empty surface instead of an honest "no closed cycle
yet". Their absence of a guard is the contract.
"""
import ast
import os

ACCOUNTS = os.path.join(os.path.dirname(__file__), "..", "..",
                        "services", "api", "accounts.py")

PUBLICATION_GATED = "cycle_with_published_results"
RESPONSE_GATED = "current_cycle_with_responses"
LIVE_COMPUTE = "_cycle_cei"


def _functions():
    src = open(ACCOUNTS, encoding="utf-8").read()
    tree = ast.parse(src)
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            called = {n.func.id for n in ast.walk(fn)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
            yield fn.name, called


def test_no_live_computer_gates_on_publication():
    """⭐ THE INVARIANT. A function that derives its numbers by calling
    `_cycle_cei` must not decide whether to run by asking whether a snapshot was
    published — the snapshot is not its input.

    If this fails, do not add an exemption. Either the function should read the
    snapshot (then it is a publication surface and should stop computing live),
    or it should gate on `current_cycle_with_responses`.
    """
    offenders = [
        name for name, called in _functions()
        if LIVE_COMPUTE in called and PUBLICATION_GATED in called
        and name not in (PUBLICATION_GATED, RESPONSE_GATED)
    ]
    assert offenders == [], (
        f"live-computing function(s) gated on published results: {offenders}")


def test_both_resolvers_exist_and_are_used():
    """Form control. An invariant over an empty set passes trivially — if either
    resolver had no callers the assertion above would be vacuous."""
    names = {n for n, _ in _functions()}
    assert PUBLICATION_GATED in names and RESPONSE_GATED in names
    pub = [n for n, c in _functions() if PUBLICATION_GATED in c and n != PUBLICATION_GATED]
    resp = [n for n, c in _functions() if RESPONSE_GATED in c and n != RESPONSE_GATED]
    assert pub, "the publication-gated resolver has no callers"
    assert resp, "the response-gated resolver has no callers"


def test_the_two_live_computers_are_response_gated():
    """Named explicitly, because these are the two the defect was found in. A
    rename that quietly moved them back would otherwise pass the generic rule."""
    by_name = dict(_functions())
    for fn in ("_dept_cei_map", "_dept_coverage"):
        assert RESPONSE_GATED in by_name[fn], f"{fn} no longer resolves by responses"
        assert PUBLICATION_GATED not in by_name[fn], f"{fn} gates on publication again"


def test_the_old_name_is_not_callable():
    """`resolve_active_cycle` asserted "THE cycle every results surface should
    read", which is what invited two response-driven surfaces to use it. The name
    was the defect's carrier; leaving it as an alias would keep the invitation.

    ⭐ ASSERTED ON THE CALLABLE, NOT ON THE TEXT. The name still appears in
    `cycle_with_published_results`' docstring, explaining what was renamed and
    why — that prose is the point, and a raw substring check would forbid the
    history along with the function. What must not exist is something a caller
    can reach.
    """
    names = {n for n, _ in _functions()}
    assert "resolve_active_cycle" not in names, "the old resolver is still defined"
    callers = [n for n, called in _functions() if "resolve_active_cycle" in called]
    assert callers == [], f"the old resolver is still called by {callers}"


def test_the_invariant_can_fail():
    """Known-positive control: the scan must report a live computer that IS
    publication-gated when one exists. Constructed, not hypothetical."""
    src = ("def f():\n"
           "    latest = cycle_with_published_results(db, 1)\n"
           "    return _cycle_cei(db, latest)\n")
    tree = ast.parse(src)
    fn = tree.body[0]
    called = {n.func.id for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert LIVE_COMPUTE in called and PUBLICATION_GATED in called, (
        "the detector would not have caught the original defect")
