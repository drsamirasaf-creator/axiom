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

⭐ THE THREE WAYS A TEST TURNS OUT VACUOUS. Every instance found so far fell into
one of these, and every one was found by MUTATION, not by review — including by
the person who had just written the test.

  1. SHAPE-NOT-CONTENT — it asserts the return has the right keys or type, and
     the failure mode returns exactly that. `_department_sentiment_map`'s
     all-zero default carries "n" and "below_floor" like a real answer, so
     `assert "n" in rec` passed while the body never ran.

  2. WRONG-BINDING — it asserts something adjacent to the thing that can break.
     `assert rep._big_money is rf.money` checks the IMPORT, which stays true
     while `_big` is redefined on the next line. Assert the name the caller
     actually reaches.

  3. FAILURE-MODE-ACCEPTED — the assertion admits the broken state as one of its
     allowed outcomes. `assert out.get("has_data") is not False or "message" in
     out` accepts precisely what a drill returns when it finds no cycle; and an
     HTTP-level test allowing 401 beside 200 passes when auth rejects the request
     before the body runs.

A fifth, which the HARNESS itself can hide: ALWAYS-FAILING. A test that does not
pass on correct code kills every mutation paired with it and reports a confident
`killed`. The baseline pass in main() exists for that, and it caught an
end-to-end test raising KeyError on an incomplete fixture.

A fourth, adjacent: PASSING-FOR-THE-WRONG-REASON, where the input does not
discriminate. A lowercase department name still matched after case-insensitivity
was removed, because the lookup key was already lowered. The assertion was right;
the fixture could not tell the two behaviours apart.

The source file is restored after every mutation, including on failure.
"""
import subprocess, sys, shutil, os, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ING = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/modules/financials/ingest.py")
PDF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/report_pdf.py")
PER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/modules/financials/periods.py")
ENG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/modules/financials/engines.py")
RF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/report_format.py")
REP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/reporting.py")
PU = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/participant_upload.py")
PRO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services/api/modules/financials/proforma.py")
ACC = os.path.join(ROOT, "services/api/accounts.py")
VAL = os.path.join(ROOT, "services/api/modules/valuation/engines.py")
READ = "tests/unit/test_assessment_read_path_execution.py"
PUT = "tests/unit/test_participant_upload.py"
RFT = "tests/unit/test_report_format.py"
FPS = "tests/unit/test_forecast_period_succession.py"
PEL = "tests/unit/test_period_entry_and_labels.py"
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


    # ── participant_upload: every test paired with a plausible defect ────────
    ("version stamp gates the parse again (the removed customer-blocker)", PU,
     '    out["version"] = ver',
     '    if ver != VERSION:\n'
     '        out["errors"].append({"tab": None, "row": None,\n'
     '                              "message": "Template version stamp is invalid."})\n'
     '        return out\n    out["version"] = ver',
     f"{PUT}::test_a_workbook_whose_stamp_was_LOST_still_parses_completely"),

    ("role assignment overwrites instead of unioning", PU,
     '        if role not in p["roles"]:\n            p["roles"].append(role)',
     '        p["roles"] = [role]',
     f"{PUT}::test_one_person_on_two_tabs_unions_their_roles"),

    ("a later tab blanks the department an earlier one set", PU,
     '        if department:\n            p["department"] = department',
     '        p["department"] = department',
     f"{PUT}::test_a_later_tab_does_not_erase_the_department_set_earlier"),

    ("email is no longer case-folded, so one person becomes two", PU,
     '                email = vals[idx["Email"]].lower()',
     '                email = vals[idx["Email"]]',
     f"{PUT}::test_email_is_the_identity_key_and_is_case_folded"),

    ("department match becomes case-SENSITIVE", PU,
     '                    dept_match = dep_lookup.get(dept_raw.lower())',
     '                    dept_match = dep_lookup.get(dept_raw)',
     f"{PUT}::test_department_matches_case_insensitively_and_returns_the_ORG_CHART_spelling"),

    ("an unknown department is auto-created instead of colliding", PU,
     '                    if dept_match is None:',
     '                    if dept_match is None and False:',
     f"{PUT}::test_an_unknown_department_is_a_collision_and_is_never_auto_created"),

    ("the seniority vocabulary stops being closed", PU,
     '                    elif band not in SENIORITY_BANDS:',
     '                    elif False:',
     f"{PUT}::test_seniority_outside_the_five_bands_is_rejected"),

    ("assessors no longer require a department", PU,
     '                    if not dept_raw:\n                        rowerrs.append("Department is required for assessors")',
     '                    if False:\n                        rowerrs.append("Department is required for assessors")',
     f"{PUT}::test_assessors_require_department_and_band_others_do_not"),

    ("decision makers no longer require a title", PU,
     '                if tab == "Decision Makers" and not title:',
     '                if tab == "Decision Makers" and False:',
     f"{PUT}::test_decision_makers_require_a_title"),

    ("error rows are reported one line off", PU,
     '                        out["errors"].append({"tab": tab, "row": r, "email": email, "message": m})',
     '                        out["errors"].append({"tab": tab, "row": r - 1, "email": email, "message": m})',
     f"{PUT}::test_error_rows_point_at_the_row_the_admin_will_look_at"),

    ("duplicate emails on one tab stop being detected", PU,
     '                if email and email in seen_emails:',
     '                if False:',
     f"{PUT}::test_a_duplicate_on_one_tab_names_the_earlier_row"),

    ("the CEO flag is dropped on the way into the participant map", PU,
     '        if is_ceo:\n            p["is_ceo"] = True',
     '        if False:\n            p["is_ceo"] = True',
     f"{PUT}::test_is_ceo_survives_into_the_participant_map"),

    ("an unreadable file raises instead of being reported", PU,
     '    except Exception as e:\n        out["errors"].append({"tab": None, "row": None, "message": f"Not a readable .xlsx file ({e})."})\n        return out',
     '    except Exception as e:\n        raise',
     f"{PUT}::test_a_file_that_is_not_a_workbook_is_reported_not_raised"),


    # ── board pack §7.31 ─────────────────────────────────────────────────────
    ("money drops back to zero decimals (3.6/4.0/4.4 collapse again)", RF,
     '        body = f"{a:,.{MONEY_DECIMALS}f}M"',
     '        body = f"{a:,.0f}M"',
     f"{RFT}::test_the_three_collapsed_values_are_now_three_strings"),

    ("the PPTX re-grows its own money formatter, agreeing by luck not design", REP,
     "_big = _big_money",
     "def _big(v, sym=\"\"):\n    if v is None:\n        return \"—\"\n"
     "    if abs(v) >= 1000:\n        return f\"{sym}{v/1000:,.2f}B\"\n"
     "    return f\"{sym}{v:,.2f}M\"",
     f"{RFT}::test_both_artifacts_use_the_same_function_object"),

    ("the PPTX money formatter drifts by one decimal", REP,
     "_big = _big_money",
     "def _big(v, sym=\"\"):\n    if v is None:\n        return \"—\"\n"
     "    if abs(v) >= 1000:\n        return f\"{sym}{v/1000:,.2f}B\"\n"
     "    return f\"{sym}{v:,.1f}M\"",
     f"{RFT}::test_pdf_and_pptx_render_the_same_money_string"),

    ("the billion tier stops dividing by a thousand", RF,
     '        body = f"{a/1000:,.{MONEY_DECIMALS}f}B"',
     '        body = f"{a:,.{MONEY_DECIMALS}f}B"',
     f"{RFT}::test_the_billion_tier_divides_by_a_thousand_because_input_is_millions"),

    ("an unknown currency goes back to rendering bare", RF,
     '    return CURRENCY_SYMBOLS.get(c, (c + " ") if c else "")',
     '    return CURRENCY_SYMBOLS.get(c, "")',
     f"{RFT}::test_an_unknown_currency_is_labelled_not_left_bare"),

    ("KPI percent selection falls through to money", RF,
     '    if fmt == "percent":\n        return percent(v)',
     '    if False:\n        return percent(v)',
     f"{RFT}::test_kpi_selection_routes_each_declared_format_to_its_own_shape"),

    ("KPI ratio loses its third decimal", RF,
     '    if fmt == "ratio":\n        return number(v, 3)',
     '    if fmt == "ratio":\n        return number(v, 2)',
     f"{RFT}::test_ratio_keeps_three_decimals_and_percent_one"),

    ("plan selection reads the wrong block", RF,
     '    if kind == "stoch":\n        return statement["stochastic"][key]["plan"]',
     '    if kind != "stoch":\n        return statement["stochastic"][key]["plan"]',
     f"{RFT}::test_plan_selection_reads_the_block_its_kind_names"),


    ("the k tier is dropped, so 0.5M reads $0.50M not $500.00k", RF,
     '    elif a >= 0.001:                   # >= 1e3 actual\n'
     '        body = f"{a*1000:,.{MONEY_DECIMALS}f}k"',
     '    elif False:\n        body = f"{a*1000:,.{MONEY_DECIMALS}f}k"',
     f"{RFT}::test_the_k_tier_matches_the_screen_value_not_just_the_letter"),

    ("the k tier boundary drifts off the screen's 1e3", RF,
     "    elif a >= 0.001:                   # >= 1e3 actual",
     "    elif a >= 0.01:",
     f"{RFT}::test_the_pack_lands_in_the_same_tier_as_the_screen"),

    ("the sign goes back after the symbol ($-4.40M)", RF,
     '    return f"{sign}{sym}{body}"',
     '    return f"{sym}{sign}{body}"',
     f"{RFT}::test_negatives_put_the_sign_BEFORE_the_symbol_as_the_screen_does"),

    ("an unknown currency renders bare again", RF,
     '    return CURRENCY_SYMBOLS.get(c, (c + " ") if c else "")',
     '    return CURRENCY_SYMBOLS.get(c, "")',
     f"{RFT}::test_no_currency_ever_renders_a_bare_number"),

    ("score grows a currency symbol, becoming money by accident", RF,
     '    return f"{v:,.{d}f}"',
     '    return f"${v:,.{d}f}M"',
     f"{RFT}::test_score_is_not_money_and_carries_no_symbol_or_tier"),

    ("chart_bars takes a format string at the call site again", REP,
     "def chart_bars(labels, values, title=\"\", colors=None, horizontal=False, decimals=None):",
     "def chart_bars(labels, values, title=\"\", colors=None, horizontal=False, fmt=None, decimals=None):",
     f"{RFT}::test_chart_bars_uses_the_shared_score_formatter"),


    # ── forecast period succession ───────────────────────────────────────────
    ("forecast_periods goes back to integer +1 (Q5..Q9 return)", PER,
     "    out, p = [], last_historical\n    for _ in range(max(0, int(n))):\n"
     "        p = next_period(p, frequency)\n        out.append(p)\n    return out",
     "    return [last_historical + k for k in range(1, int(n) + 1)]",
     f"{FPS}::test_twelve_quarterly_historicals_ending_20224_produce_the_right_nine"),

    ("_historicals_only drops the frequency again (the actual cause)", PRO,
     '                      "frequency": (data.get("periods") or {}).get("frequency") or "annual"}',
     '                      }',
     f"{FPS}::test_historicals_only_CARRIES_THE_FREQUENCY"),

    ("auto_forecast stops asking the dataset its frequency", ENG,
     '"forecast": _fc_periods(hist[-1], horizon, _freq_of(data))},',
     '"forecast": _fc_periods(hist[-1], horizon, "annual")},',
     f"{FPS}::test_the_full_path_end_to_end_produces_no_impossible_quarter"),

    ("the quarter carry is lost, so Q4 is followed by Q5", PER,
     '        return (year + 1) * 10 + 1 if q == 4 else year * 10 + (q + 1)',
     '        return year * 10 + (q + 1)',
     f"{FPS}::test_each_year_boundary_carries"),

    ("annual succession picks up the quarterly rule", PER,
     "    return year + 1",
     "    return year * 10 + 1",
     f"{FPS}::test_annual_generation_is_plain_year_succession"),


    # ── period entry + labels ────────────────────────────────────────────────
    ("the parser stops accepting the spaced/reversed forms", PER,
     "    for rx in _QUARTER_FORMS:",
     "    for rx in _QUARTER_FORMS[:0]:",
     f"{PEL}::test_every_accepted_form_normalises_to_the_stored_integer"),

    ("legacy YYYYQ is rejected, refusing files already in the wild", PER,
     '    if _re.fullmatch(r"\\d{5}", text):',
     '    if False:',
     f"{PEL}::test_legacy_yyyyq_is_still_accepted"),

    ("an impossible quarter is accepted through the legacy path", PER,
     '        if not period_is_valid(val, "quarterly"):',
     '        if False:',
     f"{PEL}::test_genuine_ambiguity_is_rejected"),

    ("the interpretation stops naming the quarter", PER,
     '        return val, f"{y} Q{q}"',
     '        return val, str(val)',
     f"{PEL}::test_the_interpretation_is_reported_not_assumed"),

    ("quarterly row 4 goes back to a coercible number", ING,
     '                ws[f"{letter}4"].number_format = "@"\n'
     '                ws[f"{letter}4"] = _entry_label(sample_periods[i], frequency)',
     '                ws[f"{letter}4"] = sample_periods[i]',
     f"{PEL}::test_quarterly_row4_is_text_in_the_canonical_entry_form"),

    ("the PDF renders the raw period again", PDF,
     "    return [_fmt_period(y, frequency) for y in (periods or [])]",
     "    return [str(y) for y in (periods or [])]",
     f"{PEL}::test_the_pdf_column_headers_use_the_shared_formatter"),

    ("period_labels keys on the label instead of the raw value", PER,
     "    return {k: format_period(k, frequency) for k in keys}",
     "    return {format_period(k, frequency): k for k in keys}",
     f"{PEL}::test_period_labels_is_a_map_keyed_on_the_raw_value"),

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


def _purge_pycache():
    """⭐ A MUTATION THAT PRESERVES FILE SIZE CAN BE MASKED BY A STALE .pyc.

    Python invalidates cached bytecode on (mtime, size). `==` -> `!=` and
    `,.2f` -> `,.1f` are byte-for-byte the same length, so a rewrite inside the
    same mtime second is invisible and the ORIGINAL module is imported. Two real
    mutations were reported SURVIVED for exactly this reason, which would have
    been read as two weak tests rather than a broken harness.

    It fails in the loud direction — survivors are over-reported, never
    under-reported — but it is still wrong, so the caches go."""
    for base in ("services", "tests"):
        for dirpath, dirnames, _ in os.walk(os.path.join(ROOT, base)):
            for d in list(dirnames):
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)


def run(node):
    _purge_pycache()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-m", "pytest", node, "-q", "--no-header", "-x"],
                       cwd=ROOT, capture_output=True, text=True, timeout=900, env=env)
    return r.returncode == 0, (r.stdout + r.stderr)


# ⭐ A STALE ANCHOR IS NOT A PASS. When a refactor moves the code an anchor
# points at, the mutation silently stops testing anything — the harness would
# print SKIP, exit 0, and the test it was vouching for becomes unvouched without
# anyone noticing. One stale anchor after a refactor is normal. Three is rot, and
# the difference has to be enforced rather than left to whoever reads the log.
MAX_STALE = 2


def main():
    print(f"MUTATION CHECK — {len(MUTATIONS)} plausible defects\n")

    # ⭐ A TEST THAT FAILS ON CORRECT CODE KILLS EVERY MUTATION TRIVIALLY, and
    # the harness would report a confident PASS. It happened: an end-to-end test
    # raised KeyError on an incomplete fixture, so every mutation paired with it
    # "died" without the code under test ever running. Baseline first — if the
    # test does not pass unmutated, its mutation result means nothing.
    print("  baseline (each paired test must PASS unmutated):")
    broken = []
    for node in sorted({m[4] for m in MUTATIONS}):
        ok, _ = run(node)
        if not ok:
            broken.append(node)
            print(f"    ⚠ FAILS UNMUTATED  {node}")
    if broken:
        print(f"\n  FAIL — {len(broken)} paired test(s) fail on correct code. Every "
              f"mutation against them would report `killed` while proving nothing.")
        for n in broken:
            print(f"    {n}")
        return 1
    print(f"    all {len({m[4] for m in MUTATIONS})} paired tests pass unmutated\n")

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
