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
PRO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/modules/financials/proforma.py")
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

    # ⭐ ANCHORED ON CODE ONLY. This anchor used to include the two comment lines
    # above the assignment, so rewording a comment — a change with no behavioural
    # meaning whatsoever — would have gone stale and silently unvouched the test.
    # Comments are the least stable text in a file and the least informative to
    # match on.
    ("item_drill reverts to newest-closed regardless of results", ACC,
     "    closed = closed_cycles_with_results(db, company_id)\n"
     "    if not closed:\n        return {\"has_data\": False, \"item_code\": item_code,",
     "    closed = []\n"
     "    if not closed:\n        return {\"has_data\": False, \"item_code\": item_code,",
     f"{READ}::test_assessment_item_drill_body_executes"),

    ("_historicals_only stops stripping forecast VALUES (list only)", PRO,
     '            out[block] = {key: {y: v for y, v in (series or {}).items() if y in hist}',
     '            out[block] = {key: {y: v for y, v in (series or {}).items()}',
     "tests/unit/test_historicals_only.py::test_forecast_VALUES_are_stripped_from_every_block"),

    ("_historicals_only rounds the historical figures it copies", PRO,
     "    hist = {str(y) for y in data[\"periods\"][\"historical\"]}",
     "    hist = {str(y) for y in data[\"periods\"][\"historical\"]}\n"
     "    data = {**data, **{b: {k: {y: round(v, 1) for y, v in s.items()}\n"
     "                           for k, s in data[b].items()}\n"
     "                       for b in (\"income_statement\",)}}",
     "tests/unit/test_historicals_only.py::test_historical_values_are_copied_UNTOUCHED"),

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


# ⭐ A STALE ANCHOR IS NOT A PASS. When a refactor moves the code an anchor
# points at, the mutation silently stops testing anything — the harness would
# print SKIP, exit 0, and the test it was vouching for becomes unvouched without
# anyone noticing. One stale anchor after a refactor is normal. Three is rot, and
# the difference has to be enforced rather than left to whoever reads the log.
MAX_STALE = 2


def main():
    print(f"MUTATION CHECK — {len(MUTATIONS)} plausible defects\n")
    survived, killed, skipped = [], [], []
    for label, path, find, repl, node in MUTATIONS:
        src = open(path).read()
        if find not in src:
            skipped.append((label, node))
            print(f"  ⚠ STALE  {label}\n           anchor no longer present in {os.path.relpath(path, ROOT)}"
                  f"\n           -> {node.split('::')[-1]} is currently UNVOUCHED")
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

    # ⭐ ALWAYS PRINTED, PASS OR FAIL. The summary is the thing a reader scans;
    # burying "skipped 3" behind a green exit code is how the harness would come
    # to vouch for nothing while still looking like it works.
    print(f"\n  SUMMARY: {len(killed)} killed / {len(survived)} survived / "
          f"{len(skipped)} STALE-ANCHOR   (of {len(MUTATIONS)})")

    if skipped:
        print(f"\n  ⚠ STALE ANCHORS ({len(skipped)}) — these mutations tested NOTHING this run:")
        for l, n in skipped:
            print(f"    · {l}\n      unvouched test: {n}")

    if survived:
        print("\n  ⚠ THESE TESTS PROVE NOTHING ABOUT THEIR MUTATION:")
        for l, n in survived:
            print(f"    {n}\n      survives: {l}")

    fail = bool(survived)
    if len(skipped) > MAX_STALE:
        print(f"\n  FAIL — {len(skipped)} stale anchors exceeds the limit of {MAX_STALE}. "
              f"One after a refactor is normal; this is rot. Re-anchor them or delete "
              f"the mutations that no longer describe a plausible defect.")
        fail = True
    elif skipped:
        print(f"\n  (within the limit of {MAX_STALE} — re-anchor before it grows)")

    if survived:
        print(f"\n  FAIL — {len(survived)} mutation(s) survived.")
    if not fail:
        print("\n  PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
