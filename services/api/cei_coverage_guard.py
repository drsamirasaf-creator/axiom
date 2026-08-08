"""The two readers of one department's respondents must agree.

⛔⭐⭐ WHY THIS EXISTS — A SEED THAT LOWERED A SCORE.

`_dept_coverage` buckets responses by department ID **through the alias set**, so
it SUMS every spelling a department is known by. `_dept_cei_map` reads a slice out
of an aggregate that `compute_cei` already keyed by the name AS TYPED ON THE
RESPONSE, and `_pick_dept_slice` returns the FIRST variant that matches — it
cannot merge two, because by then the two spellings are two separate slices with
two separate means.

So the divergence is structural, not a bug in either function:

    coverage          sums   {"HR": 3, "Human Resources": 1}  ->  4
    _pick_dept_slice  picks  the first norm that hits          ->  1

Seeding Human Resources under its canonical name while its existing responses
carried "HR" split it across two keys. Coverage kept saying 4. The CEI map picked
the slice with 1, which is below KFLOOR, so the department went from **n=3 scored
to n=1 SUPPRESSED**. ⛔ **The seed lowered the score it was added to raise**, and
nothing failed — both functions returned confidently, and they disagreed.

⭐ THE ASSERTION IS THE AGREEMENT, NOT EITHER NUMBER. Neither reader can detect
this alone: coverage's 4 is right, the map's 1 is right *for the slice it found*,
and only the comparison is wrong. This is why the check compares two production
functions rather than recomputing a third answer of its own (§III.13-extended —
the control must be the same function as the assertion).

⭐ AND IT REPORTS THE DENOMINATOR. A disagreement list that is empty because zero
departments were examined is the §III.4 failure; `checked` carries every live
department, always, so an empty corpus is visible as an empty corpus.
"""
from __future__ import annotations


def cei_coverage_report(db, company_id: int) -> dict:
    """Every live department, with both readers' respondent counts side by side.

    Returns::

        {"company_id": int,
         "checked": [{department_id, name, cei_n, coverage_n, state, agrees}],
         "disagreements": [ ...the subset with agrees=False... ],
         "unattributed_respondents": int,
         "cycle_id": int | None}

    ⛔ `checked` is EVERY live department, including those at zero. A department
    nobody answered agrees at 0 == 0, and it belongs in the denominator: dropping
    the zeroes would shrink the corpus silently, which is the thing §III.4 names.

    ⛔ `unattributed_respondents` is reported rather than folded in. Those are
    people whose department string resolves to no live department — after a
    revoke, they belong to nothing — and they are invisible to `_dept_cei_map`
    entirely. That is a real gap, and it is NOT a disagreement between the two
    readers, so counting it as one would blame the wrong mechanism.
    """
    from .accounts import _dept_cei_map, _dept_coverage, live_departments

    deps = live_departments(db, company_id).all()
    cei = _dept_cei_map(db, company_id) or {}
    cov = _dept_coverage(db, company_id) or {}
    resp = cov.get("respondents") or {}

    checked = []
    for d in sorted(deps, key=lambda x: x.id):
        slice_ = cei.get(d.id) or {}
        cei_n = slice_.get("n") or 0
        cov_n = resp.get(d.id, 0)
        checked.append({
            "department_id": d.id,
            "name": d.name,
            "cei_n": cei_n,
            "coverage_n": cov_n,
            "state": slice_.get("state"),
            "agrees": cei_n == cov_n,
        })

    return {
        "company_id": company_id,
        "cycle_id": cov.get("cycle_id"),
        "checked": checked,
        "disagreements": [r for r in checked if not r["agrees"]],
        "unattributed_respondents": (cov.get("unattributed") or {}).get("respondents", 0),
    }


def format_report(rep: dict) -> str:
    """One line per department, ALWAYS — the denominator is part of the output.

    A guard that prints only its failures reads as green when it examined
    nothing, which is exactly the state this file was written after.
    """
    lines = [f"company {rep['company_id']}  cycle {rep['cycle_id']}  "
             f"departments checked: {len(rep['checked'])}"]
    for r in rep["checked"]:
        mark = "  " if r["agrees"] else "⛔"
        lines.append(f" {mark} {r['name'][:34]:<34} cei.n={r['cei_n']:<4} "
                     f"coverage.n={r['coverage_n']:<4} {r['state'] or '-'}")
    lines.append(f"disagreements: {len(rep['disagreements'])} of {len(rep['checked'])}")
    if rep["unattributed_respondents"]:
        lines.append(f"⛔ unattributed respondents (resolve to no live department): "
                     f"{rep['unattributed_respondents']}")
    return "\n".join(lines)
