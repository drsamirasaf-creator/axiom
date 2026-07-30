# §7u — the assumption surface. SCOPE ONLY, nothing built.

Enumerated from code, classified, and measured against the live corpus.

⭐ **This lane also reproduced and diagnosed the psycopg failure, and the previous
repair lane's conclusion was wrong.** That is reported first because it changes
what the tooling entry in CORE says.

---

## ⭐ 0. The psycopg failure — actual cause, and a correction

The repair lane (`614ad3b`) concluded *"not reproducible; the environment has one
implementation and no fallback."* The second clause is true. **The first was
wrong, and the diagnosis was wrong.**

It reproduced here, immediately after the preflight passed in the same command.
The difference was **the directory the script runs from**.

    /scratchpad/bisect.py     ← shadows the stdlib `bisect` module
    line 2:  ROOT = sys.argv[1]

When a script runs from that directory, `sys.path[0]` is that directory. psycopg's
import chain pulls in `bisect`, Python resolves it to **my file**, executes it,
and `sys.argv[1]` raises **`IndexError: list index out of range`** — the exact
error, verbatim.

**Proved by deletion and restoration:**

    bisect.py present  → couldn't import psycopg 'binary': list index out of range
    renamed            → import OK
    restored           → failure returns

This explains every observation the repair lane could not:

- the exact error string — it was never a psycopg fault
- **why it began mid-lane** — the file was created during the bisect attempt
- why only some invocations failed — only those run *from the scratchpad*
- why the repair lane measured 45/45 successes — it tested `python3 -c`, where
  `sys.path[0]` is the cwd, not a scratchpad script

⭐ **And the preflight guard would not have caught it**, because the guard lives in
the repo and runs from the repo. **A guard that does not run from the same
directory as the lane cannot see the lane's `sys.path[0]`.** The scratchpad now
has no stdlib shadows; adding shadow detection to `check-db-client.py` is
**required and not built here** (this lane is report-only).

**Layer: neither the package, the system libpq, nor the manifest — the harness's
own working directory.**

---

## 1. The assumption surface, enumerated from code

### 1a · Module-level constants on the compute path

| module | constant | value |
|---|---|---|
| `assessment_engine` | `KFLOOR` · `CEI_GOOD_MIN` · `CEI_NEUTRAL_MIN` | 3 · 7.5 · 5.0 |
| `forecast_studio` | `MC_PATHS` · `MC_SEED` · `DIVERGENCE_CV` | 2000 · 26202 · 0.15 |
| `benchmarks/data` | `RAG_GREEN` · `RAG_AMBER` · `SCORE_CLAMP` | 1.1 · 0.9 · [0.5, 1.5] |
| `financials/proforma` | `SEED` · `SIGMA_G` · `SIGMA_M` | 26123 · 0.02 · 0.01 |
| `intelligence/engines` | `PHI_ADJUST` · `LEV_KD_KINK` · `LEV_KD_COEF` · `RAEV_LAMBDA` | 8.0 · 0.25 · 0.35 · 0.5 |
| `financials/oci` | `SEED` | 26124 |
| `twin/engines` | `SIM_SEED` · `OBS_SEED` | 26120 · 26122 |
| `valuation/engines` | `DEFAULT_SEED` | 26060 |
| `financials/template_policy` | `VERSION_MAJOR` · `MAX_HISTORICAL_COLS` · `OPENING_COLS` | 8 · 15 · 1 |
| `financials/ingest` | 17 layout constants (header rows, column windows, capacities) | — |

### 1b · Defaulted lookups — `obj.get("key", <number>)`

**~60 distinct** across the compute path. The ones that reach a rendered number:

    terminal_growth 0.025 · horizon 5 · n_paths 2000 · revenue_growth 0.03
    quantile_low 0.05 · quantile_high 0.95 · risk_aversion 0.5
    sigma_growth 0.02 · sigma_margin 0.01 · sigma 0.2 / 0.5
    flip_radius 0.125 · delta_max 0.4 · noise_sigma 0.4 · tol 0.0001

⭐ **Several keys carry two different defaults at different call sites** —
`K0` is 4.0 in one place and 10.0 in another; `T` is 5.0 and 12; `sigma` is 0.2
and 0.5; `mu` is 0.08 and 2.0; `revenue_growth` is 0.0 and 0.03; `a` is 0.9 and
3.0. **A registry keyed by name alone cannot represent these** without first
deciding whether they are one assumption or two.

### 1c · ⭐ Inline literals — the class the constant scan misses

`ratios.py:97`

    return kd_base + 0.01 * max(0.0, leverage - 1.0) ** 2

Two undocumented constants with **no name, no ADR, no registry entry** — already
recorded in the function's own docstring as placeholders.

⭐ **AND THE SAME ASSUMPTION EXISTS TWICE, WITH DIFFERENT VALUES AND A DIFFERENT
BASE.** `intelligence/engines.py:2343`

    kd_distress = kd0 + LEV_KD_COEF * max(0.0, d_ratio - LEV_KD_KINK) ** 2
    LEV_KD_KINK = 0.25   # debt/revenue beyond which distress bites
    LEV_KD_COEF = 0.35   # curvature of the distress spread

| | `ratios.py:97` | `intelligence:2343` |
|---|---|---|
| base | **leverage (D/E)** | **debt / revenue** |
| kink | 1.0 | 0.25 |
| coefficient | 0.01 | 0.35 |
| named? | no, inline | yes, with comments |

Same functional form — a quadratic distress spread past a kink — **expressed
twice, on different denominators, with unrelated constants.** This is a
two-sources-of-truth finding in the assumption layer, and it is exactly what a
registry exists to prevent.

### 1d · Already client-settable — `COMPANY_FIELDS`, 16 fields

    tax_rate · risk_free_rate · market_risk_premium · cost_of_debt · dlom
    beta · unlevered_industry_beta · size_premium · specific_risk_premium
    target_debt_to_equity · share_price · shares_outstanding
    (+ name, ownership, standard, currency — non-numeric)

---

## ⭐ 2. Measured, not read — every settable field varies across companies

36 datasets:

    field                     present  absent  distinct  values
    tax_rate                       36       0         3  0.21, 0.247, 0.25
    risk_free_rate                 36       0         5  0.035 … 0.07
    market_risk_premium            36       0         3  0.055, 0.057, 0.06
    cost_of_debt                   36       0         6  0.06 … 0.09
    dlom                           32       4         3  0.1, 0.12, 0.2
    unlevered_industry_beta        32       4         6  0.88 … 1.3
    size_premium                   32       4         4  0.018, 0.02, 0.03, 0.2
    specific_risk_premium          32       4         3  0.02, 0.025, 0.03
    target_debt_to_equity          32       4         4  0.35 … 0.6
    beta                            4      32         2  1.1, 1.6
    share_price                     4      32         2  6.0, 22.0
    shares_outstanding              9      27         5  60 … 12,500,000

**These are genuinely per-company and already differ in production.** Absences
are structural (public-only vs private-only fields), not gaps.

⭐ One outlier worth a look independently of §7u: **`size_premium` = 0.2** sits
among values of 0.018–0.03 — an order of magnitude out, and plausibly 20% entered
where 2% was meant.

---

## 3. Classification

| class | members | registry treatment |
|---|---|---|
| **A · Client-settable, already** | the 12 numeric `COMPANY_FIELDS` | already per-company; the registry **versions the DEFAULT and records which value a result used** |
| **B · Client-settable, not yet** | `terminal_growth` 0.025 · `horizon` 5 · market multiple defaults · `DIVERGENCE_CV` 0.15 · the kd kink pair | a client could reasonably set these differently; today they are module constants or call-site defaults |
| **C · Methodological — should NOT be client-settable** | `KFLOOR` 3 · `CEI_GOOD_MIN`/`NEUTRAL_MIN` · all seeds (26060, 26120–26124, 26202) · `SCORE_CLAMP` · ingest layout constants · `VERSION_MAJOR` | versioned and pinned, never exposed. ⭐ `KFLOOR` is a **privacy guarantee** — a client-settable k-anonymity floor is a client-settable disclosure risk |

⭐ **Seeds belong in C and must still be pinned.** They do not change a
methodology, but they determine a rendered number. A pack that pins every
assumption and not the seed does not reproduce.

---

## 4. Provenance today

| where it lives | count | does a stored result record it? |
|---|---|---|
| module constant | ~35 | **no** |
| call-site default | ~60 | **no** |
| inline literal | ≥2 known | **no** |
| `company` dict in the dataset payload | 16 | **partially** — the payload is stored, but it is **mutated in place at boot** for showcase rows with no write timestamp |
| `ValuationRun.params` | `assumptions`, `monte_carlo`, `basis_label`, `extended` | **only what the caller passed** — a default that filled in is not recorded |

⭐ **The gap is exactly the standing law.** `params` records *overrides supplied*,
not *values used*. A run that accepted `terminal_growth = 0.025` by default stores
nothing about it, so the same run cannot be re-explained after the default moves.
`auto_forecast` is the one exception — it writes `_forecast_provenance` with the
driver values it actually used, including `overrides_supplied`. **That is the
shape the rest of the surface lacks.**

---

## 5. What §7s.1 must pin

**Not one object. At minimum four, and they have different lifetimes:**

1. **Company assumptions** — the 16 `COMPANY_FIELDS` values in force at
   publication. Per-company, changes when the client edits.
2. **Platform defaults** — the ~60 call-site defaults and ~35 module constants.
   Global, changes when we deploy.
3. **Methodological constants** — floors, bands, clamps, layout. Global, changes
   rarely, **must be pinned anyway because they move rendered numbers**.
4. **Seeds** — global, and without them a Monte Carlo pack does not reproduce.

⭐ A single "assumptions version" string is sufficient **only if 2–4 are versioned
together as one artefact**, and 1 is captured per pack as values rather than as a
version. **Freezing a version of the registry does not freeze the client's own
inputs** — those are data, and belong in the pack's input snapshot alongside the
dataset.

---

## 6. The scope question — config-versioning or per-company stored assumptions

**They are different projects and the ruling is which one §7u is.**

**(a) Config-versioning.** Collect classes B, C and the seeds into one versioned
artefact — the same shape as the ratio registry. Code reads defaults from it;
every stored result records the version. *Does not* make anything newly
client-settable. **Cost: moderate.** The work is the enumeration (largely done
here), one loader, and threading a version onto stored results. **Risk: low** —
values do not change, so a diff should be empty and is checkable.

**(b) Per-company stored assumptions.** Class B becomes settable per company, with
storage, defaults, override tracking, validation and UI. **Cost: substantially
higher** — it is a product feature with a data model, and it inherits every
provenance requirement the law imposes. **Risk: higher** — a per-company
`terminal_growth` changes valuations for anyone who sets it.

⭐ **§7s.1's stated dependency is satisfied by (a) alone.** The Pack needs *a
version to pin*, not a settings feature. **(b) is a product decision that (a) does
not block and does not require.**

**Recommendation: §7u is (a).** Do (b) later, separately, if clients ask —
and note that (a) makes (b) cheaper, because the enumeration and the provenance
plumbing are the expensive parts of both.

---

## Not done

Nothing built, no registry created, no value changed. The `size_premium = 0.2`
outlier is reported, not corrected — it is customer data.
