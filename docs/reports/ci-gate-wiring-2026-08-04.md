# Wiring the absent gates into CI

Built 4 Aug on `13e2cdd`. **All 29 gates now run in CI.** Required status checks
**not** enabled — readiness reported only, per the dispatch.

---

## 1 · The twelve, and why each was absent

⭐⭐ **Every one of the twelve exits 0 on a runner with no database, no frontend
checkout and no corpus.** Measured with `env -i`, an empty `$HOME` and
`AXIOM_FRONTEND` pointed at a nonexistent directory — exit codes read without a
pipe, because `rc=$?` after `| tail` measures `tail`.

**Not one of them was absent because it could not run.** Eleven were simply never
added. The twelfth had an exit-code defect that would have made CI red.

| gate | why absent | needs |
|---|---|---|
| `check-no-internal-identifiers` | ⭐ **never added** — written this session, in the very lane that counted the gap | nothing |
| `check-customer-counts` | never added | nothing |
| `check-guard-coupling` | never added | nothing |
| `check-no-seat-caps` | never added | nothing |
| `check-pilot-viewer-readonly` | never added | nothing |
| `check-plain-subscript` | never added | nothing |
| `check-comparison-matrix` | never added; **assumed** to need a sibling checkout | nothing for its capability half |
| `check-in-development-marking` | ⛔ **returned 2 with no frontend checkout** — wiring it would have made CI permanently red | the fix in §3 |
| `check-single-active-dataset` | never added; runs its control, live half needs a DB | `--against-db` |
| `check-showcase-dataset` | never added; runs its control, live half needs a DB | `--against-db` |
| `check-ownership-agreement` | never added; runs its control, live half needs a DB | `--against-db` |
| `check-prospect-routes` | never added; runs its control, live half needs the app | `--against-app` |

⭐ **The "needs a database" reason was mostly wrong.** Four gates were assumed to
need one; all four carry a **structural control** that plants the defect they
exist to catch and requires themselves to go red. That control runs fully on a
runner. What they cannot do without a database is compare against **live rows**,
and each says so in its own output.

---

## 2 · What was wired

**All twelve.** Eleven needed no change. The workflow now runs 29 distinct
`scripts/check-*.py`, verified by counting the file against the workflow text.

⭐ **And the gap cannot silently reopen.** `tests/unit/test_ci_gate_wiring.py`
derives the gate list from `scripts/check-*.py` and the invocations from
`ci.yml`'s own text, and fails when one is missing — with a floor assertion so an
empty gate list cannot make it vacuously true. **Neither half is a
hand-maintained roster**, which is the §III.4 defect a roster would reintroduce.

---

## 3 · What takes the ruled non-run shape

**One gate needed the fix: `check-in-development-marking.py`.**

It returned **2** when no frontend checkout existed. ⛔ **That is a failure on a
condition it does not guard** — the gate guards whether an in-development marking
and the capability agree, **not whether a sibling repository happens to be
checked out beside this one.** Same shape as `94a7ce0` and `eb89ee8`; third
application.

**It was not weakened to a skip.** The half that can run now runs *first*:

- ⭐ **the capability-existence half is this repository's and runs
  unconditionally** — reported on every invocation
- the marking half is **named as NOT RUN**, with the output stating plainly that
  the run *"asserts NOTHING about whether the in-development marking is present.
  It is not a green."*
- ⭐ **and one violation is still enforced without the frontend**: if the
  capability has **shipped**, CORE §4z.1's stated exception should be retired,
  which is decidable here — so that path still **returns 1**
- ⛔ a failed control still returns **2**, unchanged — that *is* a condition the
  gate guards

Tests proven **red before** (3 of them) and green after.

---

## 4 · ⭐⭐ What CI enforces now, honestly

Measured CI-shaped, all 29:

| | before (`eb89ee8`) | after |
|---|---|---|
| gates in `ci.yml` | 17 of 29 | ⭐ **29 of 29** |
| enforce fully, nothing withheld | ~13 | ⭐ **19** |
| enforce a real half, name the other | 4 | **7** |
| assert nothing, and say so | 0 (they exited non-zero or lied) | **3** |
| non-zero on a clean runner | — | **0** |

**The seven partials, and what each still enforces:**

- `check-period-labels-published` — backend emitter cross-check **enforced**
- `check-comparison-matrix` — **16 capability claims resolved against live
  symbols**; only deep links unverified
- `check-in-development-marking` — capability existence **enforced**
- `check-single-active-dataset`, `check-showcase-dataset`,
  `check-ownership-agreement` — **known-positive control enforced**; live rows
  not consulted
- `check-prospect-routes` — structural control **enforced**; live app not fetched

**The three that assert nothing in CI, all by the ruled shape:**

- `check-assumption-bounds` — *"swept 0 datasets and asserts NOTHING"* (needs a corpus)
- `check-no-ts-period-format` — *"gate skipped, not passed"*
- `check-period-labels-consumed` — *"SKIPPED — this gate proved nothing"*

⭐ **26 of 29 gates now do real work in CI, against roughly 13 before.** That is
the number required status checks would rest on. **The remaining 3 are a corpus
and a frontend checkout away, and every one of them says so in its own output
rather than printing a tick.**

---

## 5 · Required status checks — ⛔ READY, NOT ENABLED

**Not wired, as instructed.** Recording readiness:

- ✅ CI is **green on a clean runner**: 29 gates, 0 non-zero, plus the suite
- ✅ no gate fails on a condition it does not guard — the class that made
  requiring a check impossible for three lanes
- ✅ ruleset `20368701` is active on `~DEFAULT_BRANCH` with `deletion` +
  `non_fast_forward`

⛔ **The blocker is no longer technical, it is a workflow ruling.** Required
checks apply to direct pushes, so enabling them **ends direct-to-main and makes
every lane a pull request.** That is the user's call and has not been made.

---

## 6 · What a corpus in CI would take — reported, not built

Three gates assert nothing in CI for want of one, and four more would upgrade
from control-only to live-row checks.

| shape | cost | verdict |
|---|---|---|
| **A · commit a redacted corpus fixture** | It is customer data; redaction must be *provable*, not asserted. And a committed fixture **goes stale silently** — the sweep would then assert about a corpus that no longer exists, which is the `FinancialDataset` defect in a new place. | ⛔ the strongest objection |
| **B · give CI a read-only `DATABASE_PUBLIC_URL` secret** | Production credentials reachable from CI. **A pull request from a fork could exfiltrate them**, and a database blip would red the build for reasons unrelated to the diff. | ⛔ not on PR runs |
| **C · generate a synthetic corpus from the seed scripts** | Cheap and safe, but it contains **only values the seeds produce** — and the gate exists precisely for **stored data that will never re-ingest**. It would prove the sweep runs, not that the corpus is clean. | ⭐ honest if labelled |

⭐ **The shape I would propose, if asked to build it:** **C on every push**
(labelled as synthetic, so a green is not read as a statement about production)
plus **B on a scheduled nightly job only** — never on pull requests, which keeps
the secret away from fork runs. **Neither is free, and C alone must not be
described as "the corpus gate now runs in CI."**

**Not built. This is a scoping note.**

---

## 7 · `ASSUMPTION_BOUNDS` moved into the §7u registry

Was a bare dict literal in `engines.py` with no version, no basis and no pack
pin. Now `ASSUMPTION_BOUNDS_REGISTRY` in `assumptions.py` at
**`7u-ab.1`**, the **fourth pinned artefact**; `engines.py` **derives** its table
so a ceiling cannot move without its basis moving with it.

### ⭐⭐ The word "calibrated" was corrected

The old comment claimed the bounds were *"calibrated against the live corpus —
8 of 321 field-values, 2.5%, every trip the one known incident."*

⛔ **That is a consistency check on a prior, not a calibration.** Counting how
many corpus values trip a ceiling you already chose derives nothing; and the
corpus holds exactly **one** incident, so the hit rate restates *"the eight I
already knew about."* **The same shape as `_calibrate_sigma`** (A4/B22).

Every ceiling now states its **class** and its **basis**:

| class | n | which |
|---|---|---|
| `house_prior` | **1** | `size_premium` — CRSP/handbook decile premia top near 6% |
| `declared_prior` | **9** | ⭐ **eight have NEVER FIRED**; corpus maxima sit at 0.12–0.42 of ceiling. `specific_risk_premium` borrows `size_premium`'s ceiling by association and now says so |
| `structural_floor` | **2** | `share_price`, `shares_outstanding` — exclude impossible values, assert **nothing** about magnitude |

⛔ **And the §7w blind spot is recorded in the registry rather than patched.**
`shares_outstanding` has no ceiling; the corpus spans **100 to 12,500,000 —
125,000× — all "in_bounds."** The one unit defect that reached a rendered figure
is invisible to a range check by construction. A magnitude ceiling is not
obviously right (share counts genuinely span orders of magnitude), so it is
**stated, not silently invented.**

**Bounds are deliberately excluded from `registered_values()`** — that set is
matched *by value* against compute-path constants, and folding range endpoints in
would let an unrelated tuple constant match a bound and count as registered.
Pinned by §7s.1, not value-swept.

### Two stale claims found while doing it

- `check-assumption-registry.py` printed **"versions pinned by §7s.1 (THREE, not
  one)"** — while printing four — and a hard-coded **"across 3 artefacts."** Both
  now counted, not spelled out. ⭐ *A hard-coded number in the output of a guard
  whose subject is hard-coded numbers.*
- `test_pack_freeze` and `test_provenance_preconditions` pinned the literal set
  `{platform_defaults, methodological, seeds}` and went red on a **correctly
  pinned fourth artefact.** ⭐ **A test naming the artefacts it expects fails when
  a new one is pinned — the opposite of its purpose.** Both now derive from
  `A.versions()`, with a floor so an empty registry cannot satisfy the equality.

### ⭐ §III.9, sixth occurrence

`test_no_caller_still_uses_the_old_name` was `grep -rn _calibrate_sigma` and went
**red the moment §7u.2's comments cited the old name to explain why "calibrated"
was wrong** — punishing the prose that states the rule. Converted to an **AST
read** (`Name` / `Attribute` / `FunctionDef` / non-docstring `Constant`, with
`ast.get_docstring(node, clean=False)`). ⛔ **This tightens the claim rather than
weakening it:** a caller is never a `#` comment, so it now asserts nobody *calls*
the old name rather than that nobody *mentions* it.

---

## 8 · The 8 breaching datasets, allowlisted

**Not corrected and not deleted** — both refusals are the ruling. Correcting
would leave **27 valuation runs contradicting their own inputs**; deleting would
destroy the only surviving record, and `original_filename` is null on all eight
so the source workbook is already gone.

⭐ **Keyed by `(dataset id, field)` AND matched on the stored value** — never
"ignore this dataset." A blanket dataset entry would silently absorb a *different*
field going out of bounds later, which is how an allowlist becomes a blind spot.
**If the stored value changes, the entry stops matching and the breach is
reported as new.**

The sweep now splits its findings and **reports stale allowlist entries** — an
entry that no longer matches is called out as *standing permission left behind*,
rather than quietly persisting. Measured on the live corpus:

    ADJUDICATED (§7u.2, 4 Aug): 8 of 8 allowlisted entries matched
    NEW, UNADJUDICATED BREACHES: 0

⛔ **It still returns 0 on a breach, and the allowlist did not change that.**
§7u.2 ruled the allowlist; it did **not** rule that this becomes a gate. With the
8 adjudicated the corpus is clean, so flipping `new_hits` to a non-zero exit is
now a one-line change — **but it is a ruling, and it is worth nothing until CI
can reach a corpus at all.** A gate that can only fail on one laptop is the
defect `eb89ee8` removed, pointed the other way.

---

## Verification

- **Suite: 2045 passed**, 1 skipped, 3 xfailed (from 2035 at `13e2cdd`).
- **29 gates CI-shaped: 0 non-zero.**
- New tests proven **red before** — 4 in `test_ci_gate_wiring.py`, 5 in
  `test_assumptions_registry.py` (run against the pre-lane source) — green after.
- **No gate weakened to a skip.** Guard controls in memory; nothing planted on
  disk.
- One env fetch via `scripts/lane-env.sh`; the URL was never printed.
- **No stored value modified.** No bound value changed — only its recorded basis.
