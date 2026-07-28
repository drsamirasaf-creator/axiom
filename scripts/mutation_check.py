#!/usr/bin/env python3
"""Prove a test is not vacuous by making the code wrong and watching it fail.

⭐ A TEST NEVER OBSERVED FAILING IS NOT EVIDENCE. Three of the assessment
read-path functions were covered by a green suite while returning HTTP 500 in
production, and two of the tests written to catch that passed against the broken
code on the first and second attempt — one because it allowed 401 beside 200, one
because its fixture seeded no framework so the body early-returned.

So each mutation below is a defect a REFACTOR would plausibly introduce — a
deleted local import, a reverted key, a dropped filter — not an arbitrary
character swap. If the paired test still passes with the mutation applied, the
test is not testing what it claims and the harness says so.

The source file is restored after every mutation, including on failure.
"""
import subprocess, sys, shutil, os, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACC = os.path.join(ROOT, "services/api/accounts.py")
VAL = os.path.join(ROOT, "services/api/modules/valuation/engines.py")
READ = "tests/unit/test_assessment_read_path_execution.py"
COV = "tests/unit/test_coverage_rename_and_suppression.py"

# (label, file, find, replace, test-node-id)
MUTATIONS = [
    ("resolver returns the newest cycle regardless of results", ACC,
     "    closed = closed_cycles_with_results(db, company_id)\n    return closed[-1] if closed else None",
     "    return newest_cycle_regardless_of_results(db, company_id)",
     f"{READ}::test_resolver_selects_the_populated_cycle"),

    ("_dept_cei_map loses its `cycles` binding (the live NameError)", ACC,
     "    cycles = (db.query(AssessmentCycle).filter_by(company_id=company_id)\n"
     "                .order_by(AssessmentCycle.opened_at).all())\n"
     "    latest = resolve_active_cycle(db, company_id)\n    if latest is None:\n        return empty",
     "    latest = resolve_active_cycle(db, company_id)\n    if latest is None:\n        return empty",
     f"{READ}::test_dept_cei_map_runs_and_classifies_every_shape"),

    ("coverage reverts to keying on the department NAME", ACC,
     '        respondents = cov["respondents"].get(d.id, 0)',
     '        respondents = cov["respondents"].get(d.name, 0)',
     f"{READ}::test_list_departments_consumer_reads_coverage_by_id"),

    ("coverage drops the alias resolution, matching raw names", ACC,
     "            did = norm_to_id.get(_norm_dept_name(r[1])) if r[1] else None",
     "            did = ({_norm_dept_name(d.name): d.id for d in deps}).get("
     "_norm_dept_name(r[1])) if r[1] else None",
     f"{READ}::test_dept_coverage_runs_and_bridges_the_rename"),

    ("assessment_summary loses the apply_kfloor import (the live 500)", ACC,
     "    from .assessment_engine import apply_kfloor, KFLOOR, suppression_block\n"
     "    current = _cycle_cei(db, latest) if latest else {}",
     "    current = _cycle_cei(db, latest) if latest else {}",
     f"{READ}::test_assessment_summary_body_executes"),

    ("_department_sentiment_map stops filtering for results", ACC,
     "    closed = closed_cycles_with_results(db, company_id)\n    latest = closed[-1] if closed else None\n"
     "    if latest is None or not (latest.snapshot or {}).get(\"sentiment_available\"):",
     "    closed = []\n    latest = None\n"
     "    if latest is None or not (latest.snapshot or {}).get(\"sentiment_available\"):",
     f"{READ}::test_department_sentiment_map_body_executes"),

    ("item_drill reverts to newest-closed regardless of results", ACC,
     "    # ⭐ CLOSED IS NOT THE SAME AS HAS-RESULTS. This took the newest closed cycle\n"
     "    # whatever it contained — the same defect as _dept_coverage, one surface away.\n"
     "    closed = closed_cycles_with_results(db, company_id)\n"
     "    if not closed:\n        return {\"has_data\": False, \"item_code\": item_code,",
     "    closed = []\n"
     "    if not closed:\n        return {\"has_data\": False, \"item_code\": item_code,",
     f"{READ}::test_assessment_item_drill_body_executes"),

    ("sigma reports the clamp as an estimate again", VAL,
     '            if sd < 0.15:\n                return 0.15, ("floor (0.15) — this company\'s historical revenue is too "\n'
     '                              "smooth to estimate volatility from")',
     '            if sd < 0.15:\n                return 0.15, "historical revenue log-growth"',
     "tests/numerical/test_phase15_checkpoints.py::test_sigma_calibration_from_history_and_floor"),

    ("quarterly discounting reverts to annual rates per period", VAL,
     "    ppy = periods_per_year(working)\n    wacc_period = to_period_rate(wacc_value, ppy)\n"
     "    g_period = to_period_rate(g_term, ppy)",
     "    ppy = 1\n    wacc_period = wacc_value\n    g_period = g_term",
     "tests/unit/test_period_length_correctness.py::test_quarterly_valuation_lands_in_the_same_band_as_annual"),
]


def run(node):
    r = subprocess.run([sys.executable, "-m", "pytest", node, "-q", "--no-header", "-x"],
                       cwd=ROOT, capture_output=True, text=True, timeout=900)
    return r.returncode == 0, (r.stdout + r.stderr)


def main():
    print(f"MUTATION CHECK — {len(MUTATIONS)} plausible defects\n")
    survived, killed, skipped = [], [], []
    for label, path, find, repl, node in MUTATIONS:
        src = open(path).read()
        if find not in src:
            skipped.append(label)
            print(f"  SKIP   {label}\n         (anchor not found — the code moved; mutation needs updating)")
            continue
        backup = tempfile.mktemp(suffix=".bak")
        shutil.copy(path, backup)
        try:
            open(path, "w").write(src.replace(find, repl, 1))
            ok, out = run(node)
        finally:
            shutil.copy(backup, path)
            os.unlink(backup)
        if ok:
            survived.append((label, node))
            print(f"  ⚠ SURVIVED  {label}\n              -> {node.split('::')[-1]} PASSED against broken code")
        else:
            killed.append(label)
            print(f"  killed  {label}")

    print(f"\n  killed {len(killed)} / survived {len(survived)} / skipped {len(skipped)}")
    if survived:
        print("\n  ⚠ THESE TESTS PROVE NOTHING ABOUT THEIR MUTATION:")
        for l, n in survived:
            print(f"    {n}\n      survives: {l}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
