# Ratio registry, stage 1 — defects and the guard

2026-08-02. Registry **7r.7 → 7r.8**. Scoped at `383b9e0`.
**No figure moved, and that is proven below rather than argued.**

---

## 1 · The precondition — the guard now scans YAML

`check-sole-owner.py` walked `.py` files under `services/api` and nothing else
(line 483, `if not f.endswith(".py"): continue`). Under **R7** the registry is
read at compute time, at which point each formula that restates a guarded
quantity is a second implementation. The guard would have printed
*"✓ sole ownership holds"* throughout.

It now parses every registry formula and runs **the same shape recognisers**
against them. A registry token is an Attribute (`bs.cash`) where Python writes a
Subscript (`bs["cash"]`); once `_key_of` reads both, a duplicate that changes
file format is still a duplicate.

**What it catches — five, not the four the scope report predicted:**

| quantity | registry site |
|---|---|
| net debt | `axiom.net_debt` |
| total debt | `bs.total_debt` |
| invested capital | `axiom.invested_capital` |
| ROIC | `axiom.roic` |
| **EVA** | **`axiom.eva`** |

`axiom.eva` is the addition. The scope report said the guard would miss it, and
gave the reason correctly — EVA has two standard spellings, `nopat - wacc*ic`
and `(roic - wacc)*ic`, algebraically identical and structurally unrelated, and
the guard knew only the first. The registry uses the second. **A named blind
spot is a shape to add, not a limitation to restate**, so `_spread_eva` was
written and the fifth duplicate is now visible.

`axiom.wacc` is correctly **not** among them: its formula is
`wacc_at(actual_leverage)` — it already delegates to the owner. The registry
solved this for the hardest of the five and did not carry it to the other four.

### The exemption is tied to non-execution, and measured

While nothing reads the file at runtime these five are **specification**.
`registry_readers()` measures that rather than trusting it. The day a module
under `services/` loads the registry, the build fails until each formula
delegates — **R2 enforced at exactly the moment it starts to matter, and not one
lane before.**

```
REGISTRY  docs/reference/axiom_ratio_registry.yaml  (90/95 expressions parsed;
          5 unparseable: axiom.common_size_bs, axiom.common_size_is,
          axiom.ohlson_o, po.cost_of_equity, po.days_in_period)
  runtime readers under services/: NONE — the registry is inert
  NET_DEBT          axiom.net_debt             [specification]
  TOTAL_DEBT        bs.total_debt              [specification]
  INVESTED_CAPITAL  axiom.invested_capital     [specification]
  ROIC              axiom.roic                 [specification]
  EVA               axiom.eva                  [specification]
```

The five unparseable expressions are **named, never silently skipped** — three
are R3's placeholders and two are the prose exprs. A skip that prints nothing is
indistinguishable from a clean pass.

⭐ **A zero here is the failure mode, not the goal.** The scan fails the build if
it matches *nothing*: four formulas are known to restate guarded quantities, so
zero means the parser broke, not that the registry became clean.

---

## 2 · The shape-check fix — and what else it caught

### The breach

```python
# services/api/modules/benchmarks/engines.py:100
out["roic"] = ebit * (1 - tax_rate) / (td + te - cash)
```

The guard reported **ROIC 1 site · expected 1 · ✓** while this sat in the tree.

`_roic_shape` required operands literally **named** `nopat` and `ic`. The peer
site names neither — its locals come from
`ta, te, td = g("total_assets"), g("total_equity"), g("total_debt")`. The
registry's own `enumeration_guard` stanza declared `keys_on: arithmetic_shape`
and `not_keyed_on: identifier`, and **for this quantity that was false**.

### The fix

Local names are resolved to **what they were bound from**, so `td + te - cash`
reads as debt + equity − cash however it is spelled. Three properties matter:

- **It does not follow arithmetic.** `debt = std + ltd` binds a name to an
  expression; calling that alias `short_term_debt` would assert an operand
  identity the code does not have.
- **A name rebound from a different key is dropped, not guessed.** A wrong alias
  is worse than an absent one — it produces a confident match on the wrong
  quantity.
- **The alias lookup is last and can only ADD detections.** No existing site can
  be lost. This is the standing law that a counter falling when code improves is
  a silently loosened guard.

`_roic_shape` also now recognises NOPAT written out (`<ebit> * (1 - <tax>)`)
rather than only a variable already called `nopat` — the site least likely to be
a stray copy is the one somebody bothered to name.

### What else it caught

**The inline invested capital beside it**, at `benchmarks:99` — `td + te - cash`,
invested capital on a **reduced basis**, without preferred equity or minority
interest. `_ic_shape` had missed it for two reasons at once: the naming, and
arity — three operands where the owner has five.

Nothing else. Every other count is unchanged: net debt 1, total debt 17, EVA 1,
WACC 1. The fix added exactly two detections and removed none.

### Both are allowlisted under R5 — conditionally

R5 keeps both ROICs and requires the peer figure to be labelled. The allowlist
entry is therefore **not an excuse**: `label_control()` fails the build if the
served disclosure stops naming the reduced basis. An allowlist that outlives its
reason is how a guard becomes decoration.

The disclosure is additive text on the peer `source.note`, which already carried
the tax-rate caveat and not this one:

> *"…peer ROIC uses the subject's tax rate, **and divides by invested capital on
> a reduced basis — total debt plus total equity less cash, excluding preferred
> equity and minority interest, which peer disclosures rarely carry. The
> subject's own ROIC includes both, so the two are not computed on identical
> definitions.**"*

---

## 3 · Three instrument defects, found by the controls rather than the output

⭐⭐ **`is` is a Python keyword.** `is.gross_profit / is.revenue * 100` raises
`SyntaxError`. **Every income-statement formula** — the largest token group,
carrying EBIT, PAT and every margin — was landing in `except SyntaxError` and
being skipped. *Nothing about the output looked wrong*: the scan still found the
net-debt and total-debt duplicates, which live in the `bs.` namespace and parse
fine. Only a **known positive** catches this. A smoke test does not.

**§III.9, ninth instance — inside a control written in the same lane as the rule
it enforces.** `registry_readers()` was a substring search and reported
`services/api/pack_render.py` as a runtime reader, failing the build. That module
does not load the registry: its **docstring** says the registry is loaded by
nothing but a CI guard, and the search matched the sentence describing the
absence. Now an AST read that excludes docstrings.

**The non-descent law was not carried into the new scan.** `axiom.net_debt` is
`bs.short_term_debt + bs.long_term_debt - bs.cash`; walking every node counted it
once as NET_DEBT and again as TOTAL_DEBT for its own inner add-chain, then
reported the second as an *"UNEXPECTED registry site"*. One expression, two
accusations.

⭐ A fourth was caught by the label control itself: the disclosure spans **seven
adjacent string literals**, so `"reduced basis"` falls across a line break and a
text search over the file reported it missing while the **shipped string
contained it**. An AST read gets what Python assembles — and avoids matching the
explanatory comment above it, which would have passed the check on prose no
reader ever sees.

**Controls are in memory. Nothing was written to disk.** Each carries a positive
that must fire *and* a negative that must not, because a recogniser matching
everything passes a positive-only control.

---

## 4 · The five defects

| | defect | fix | why it was not a ruling |
|---|---|---|---|
| 1 | `is.ebit` expr read `is.ebitda - depreciation_amortization` | `is.ebitda - is.dep_amort` | that is the **storage field name** of `is.dep_amort`. 7r.7 collapsed `is.depreciation + is.amortisation` into one token, renamed the key and missed this expr. `evaluation.forbidden` already prohibits "any token not present in vocabulary" — the registry violated its own contract at its most-used token. **Blocked 29 ratios, six headline.** |
| 2 | `bs.noncurrent_assets` undeclared but referenced | declared `stored` | the field **is** collected; `templates.py:411` derives it at ingest from five components with absence propagating, and `derive_series` reads it on every dataset |
| 3 | `bs.other_noncurrent_liabilities` undeclared but referenced | declared `stored`, `optional: true` | collected as *"Other Non-Current Liabilities"*; a v8 optional key, so absence is legitimate |
| 4 | `axiom.roic` produced a fraction under `unit: percent` | `… * 100` | **two independent constraints agree**: its own `unit` field, and `axiom.eva`'s `/100`, which is only correct if both operands already arrive as percent. `eva` was right; `roic` was under-specified |
| 5 | `axiom.ebit_growth_yoy` referenced by `axiom.operating_leverage`, absent | defined | written from its two identically-shaped siblings, differing only in the line measured. The one alternative — deleting `operating_leverage` — destroys the more useful of the two |

⭐ **Defect 2 was nearly re-committed as itself.** The first draft declared
`bs.noncurrent_assets` as `derived` with
`expr: bs.ppe_net + bs.goodwill + bs.intangibles + bs.long_term_investments +
bs.other_noncurrent_assets` — introducing **three new undeclared tokens** while
fixing a defect whose entire content is an undeclared token. It is a stored
field; the component derivation is an *ingest* rule and stays owned where it is
written.

### Also applied

**R4** — `avg()` and `basis: average` removed from ROA, ROE and ROIC; all three
now `point_in_time`. Applied here because step 3 asks whether the ROIC-basis
change moves a rendered figure, which requires the change to exist.

**R5's disclosure** — applied because the guard's new allowlist entry is
conditional on it, and shipping the exemption without the disclosure would have
made the silence permanent and green.

**`enumeration_guard`** — expected counts updated (`axiom.roic: 2`,
`axiom.invested_capital: 2`), the five registry duplicates enumerated, the R5
peer entry recorded with its enforcing control, and a `why_it_was_missed` stanza
stating plainly that `not_keyed_on: identifier` was false for ROIC.

**`check-ratio-shapes.py`** — its coverage line printed the literal `79`. The
registry is now 80. A denominator that is typed rather than read stops describing
the corpus the moment the corpus moves, while reporting the same reassuring
fraction. Now `len(by_id)`.

### Registry state

```
version   7r.7 -> 7r.8
ratios    79   -> 80
headline  14   -> 14   (unchanged, as ruled)
```

---

## 5 · Recomputability

| | 7r.7 | 7r.8 |
|---|---|---|
| **computable today** | **41 / 79** | **45 / 80** |
| blocked by an absent input | 31 | 24 |
| placeholder formula | 3 | 3 |
| unresolved token | 4 | 8 |

The unresolved-token column rises because the count is now honest about two
things the earlier resolver folded into other buckets:

- **`nwc`** — 5 ratios. **R1 rules the definition** (operating, ex-cash,
  ex-debt) but the token is not yet declared. Declaring it is stage 2.
- **`actual_leverage`** — 3 ratios (`axiom.wacc`, `axiom.roic_wacc_spread`,
  `axiom.eva`). **R2 rules delegation the pattern**; the argument token has no
  declaration yet.

Both are ruled and neither is built, so they are reported as outstanding rather
than counted as computable.

---

## 6 · The no-figure-moved proof

The production `derive_series` and `dashboard_metrics` were run over **all 33
stored datasets** in two trees — the working tree at 7r.8 and a clean worktree
at `383b9e0` — against the same database.

```
                         BEFORE (383b9e0)      AFTER (7r.8)
datasets                 33                    33
leaf values hashed       28,455                28,455
call failures            0                     0
digest                   c116dcfd…5f8edcc6     c116dcfd…5f8edcc6   ← identical
```

The peer benchmark path — the one Python file this lane edited — was
fingerprinted on **numbers only**, since R5's disclosure is a string and is
*supposed* to change:

```
                         BEFORE                AFTER
datasets compared        33                    33
numbers hashed           2,798                 2,798
digest                   635bf136…c322e93b     635bf136…c322e93b   ← identical
```

⭐ **The fingerprint was controlled before either digest was believed.**
Perturbing a single value by **1e-9** changes the digest, so the match is a
measurement and not a vacuity. It hashes values reached by walking the returned
structures, not a printed summary — two summaries agree whenever both round the
same way.

**Why nothing moved, stated plainly:** the registry is not read at runtime. The
guard measures that (`runtime readers: NONE`) rather than assuming it. R4 changed
a *specification* to match an engine that was already authoritative, which is why
the correct result was zero movement — had anything moved, the ruling's premise
would have been wrong and this lane would have stopped.

---

## 7 · The regression test, and how it nearly shipped vacuous

Three of the five defects were one defect — a token referenced and never
declared — and nothing would have caught a fourth. `evaluation.forbidden`
already prohibited exactly this ("any token not present in `vocabulary`") and
had no instrument, so the rule sat in the file being violated by the file for
five registry versions.

`tests/unit/test_ratio_registry_integrity.py`, five tests. **Validated by
running against `383b9e0`'s registry**, where three of them fail:

| test | on 7r.7 | on 7r.8 |
|---|---|---|
| `test_every_referenced_token_is_declared` | **FAIL** | pass |
| `test_every_canonical_chain_resolves` | **FAIL** | pass |
| `test_percent_ratios_scale_to_percent` | **FAIL** | pass |
| `test_coverage_floor` | pass | pass |
| `test_the_control_would_catch_a_new_undeclared_token` | pass | pass |

⭐⭐ **The first draft passed on the pre-fix registry — all five green against
the very defects it was written for.** Two independent reasons, both worth
recording because both are the same mistake in different clothes:

1. **The token pattern required a namespace.** It matched
   `(is|bs|cf|mk|po|hc|sa)\.name`. Every one of defects 1–3 was a **bare** name
   — `depreciation_amortization`, `noncurrent_assets`,
   `other_noncurrent_liabilities` — carrying no namespace at all, *which is
   precisely why they were undeclared*. A pattern keyed on the namespace can
   only find tokens that have one.
2. **The percent test's exemption was assumed, not checked.** "Chains into a
   ratio" was treated as "chains into a percent", so `axiom.roic`'s
   `avg(axiom.invested_capital)` — a **currency** quantity — bought it an
   exemption from the rule it was breaking. Now the chained ratios must
   themselves be `unit: percent`.

A regression test that does not fail on the regression is a spelling check. Both
were found by running the tests against the old file rather than by reading them.

**Four references remain unresolved and are named individually, not waved
through** — a blanket skip would also hide a sixth appearing tomorrow:

- `axiom.wacc` → `actual_leverage` (R2, ruled, stage 2)
- `cf.operating_cash_flow` → `nwc` (R1, ruled, stage 2 — blocks 5 ratios
  including the headline `cash_conversion_quality`)
- `po.cost_of_equity`, `po.days_in_period` — the two prose exprs; their
  disposition is a ruling, not a fix

The pending list is **shrink-only in both directions**: an entry that stops
firing fails the test, so declaring `nwc` in stage 2 forces the list to be
updated rather than quietly outliving its reason.

---

## 8 · What is ruled but not built

Recorded in CORE §7r-R, implementations owed:

- **R1** — declare `nwc` on the operating basis (+5 ratios), and move
  `axiom.fcff` off the inclusive basis. *FCFF feeds the DCF and renders in the
  KPI strip; this is the third registry-versus-engine disagreement.*
- **R2** — declare `actual_leverage` and `cagr`'s horizon (+3 ratios).
- **R3** — remove both common-size entries from the registry's arithmetic;
  `ohlson_o` waits.
- **R6** — the template split (+6 ratios, the largest single unblock).
- **R7** — execution itself, which is what the guard extension was built ahead of.

Stage 1 deliberately stops before any of these: step 3 is a report gate, and
each of the above changes either what the 80 contains or what the engine renders.
