# Meridian's four-period seed, mix shift, margin trend, and findings

4 August 2026. Backend `axiom`, frontend `optimization-anchor`.
Production write to Meridian — authorized in the dispatch, Meridian only.

---

## 1 · `--plan` before `--apply`

```
60 observations across 4 periods, 5 product lines, 3 measures
  2022 revenue      detail=  798.0342  statement=  906.8571  unallocated=108.8229 (12.0%)
  2022 direct_cost  detail=  431.3919  statement=  500.7429  unallocated= 69.3510 (13.8%)
  2022 direct_opex  detail=   29.0983  statement=  161.6571  unallocated=132.5588 (82.0%)
  2023 …                                                                          (12.0/13.4/82.0%)
  2024 …                                                                          (12.0/13.0/82.0%)
  2025 revenue      detail= 1242.0000  statement= 1380.0000  unallocated=138.0000 (10.0%)
```

⭐ **The statement figures were read from dataset 45, not from the refcase
fixture.** They differ — the fixture carries 1270.0 for 2024 revenue and the
live dataset carries 1198.6286. A seed reconciled against the fixture would
have failed against production on the first read.

## 2 · The four-period seed, and the reversal that develops

**PL-CTRL allocated EBIT: `+18.63 → +7.96 → −5.99 → −13.57`**

Healthy in 2022, thinning in 2023, negative in 2024, worse in 2025 — and its
gross margin stays above 32% throughout. That combination is the point: the
finding is not "this product got worse", it is "this product is fine and still
loses money once it is charged for what it consumes".

⭐⭐ **The cause is in the data, not in a comment.** PL-CTRL's share of the
support pool climbs **34% → 64%** and of logistics **30% → 56%**, while its
revenue share barely moves (15% → 14%). An analyst can read the driver off the
seed. A constant driver set would have produced a line that is simply
unprofitable, which nobody can act on — asserted by
`test_the_cause_of_the_reversal_is_in_the_data_not_only_in_a_comment`.

**The mix story, with two effects pointing opposite ways:**

| | share | gross margin |
|---|---|---|
| PL-AUTO | **19% → 27%** | **47% → 41%** — growth bought with price |
| PL-DRIVE | **36% → 32%** | **46% → 48%** — the opposite trade |

Neither can be mistaken for the other in the margin bridge.

**Actual periods only, never forecast.** Meridian holds five historical and five
forecast periods; the dimensional layer covers four actuals. Asserted: every
seeded period is in the historical list.

## 3 · §7o — the invariants, measured before and after

| | before | after |
|---|---|---|
| `income_statement` sha256 | `b8341c55…` | **identical** |
| full dataset payload sha256 | `71df6ea0…` | **identical** |
| pack content hashes (2 packs) | `fd0764c2…` | **identical** |
| dimension members | 5 | **same 5, same ids** |
| observations | 30 (2024–25) | 60 (2022–25) |

⭐ **The deletion rule had nothing to delete, and that is a measured fact.** The
profitability endpoint is the **only** reader of `ax_dimension_observation` in
the codebase and it computes at read time with no cache, so no derived artefact
exists over dimensional data. No boot-time mutation: the seed is an explicit
script. No showcase fast path was added.

## 4 · Mix shift and margin trend — rendered at last

T2 built `mix_shift` in the T2 lane and **the surface rendered none of it**, so
the module could say what the mix *is* and never what it *became*. A new
**What Changed** tab renders both:

- **Margin trend by line** — gross margin and allocated EBIT across all four
  periods, each with a direction, and a `diverging` badge where gross margin
  holds while allocated EBIT falls.
- **Revenue mix shift** — every consecutive pair (2022→23, 23→24, 24→25), in
  **points**, not percentages: a share *move* of two points is not "+2%".

⭐ **Direction is a comparison, not a difference.** "Fell in every period" needs
`<` on values T2 already produced; "fell by $24.6m" would need a subtraction
this layer does not own, so **that sentence is not said**. The AST guard now
covers all six functions on the path.

## 5 · Findings — derived, gated, and silent where nothing holds

Seven fire on the recorded fixture, each with the condition that produced it
printed beneath it on the page:

| severity | finding |
|---|---|
| 1 | *Beta Controls has lost allocated EBIT in every period since 2022, from 4.6 to −17.6, while its gross margin is still 31%. It is not a weak product — it is a product being charged more for shared cost every year than it earns.* |
| 2 | *The gross margin of Alpha Systems is holding while its allocated EBIT falls every period… its own pricing and direct cost are not the problem.* |
| 2 | *Gamma Instruments gained 2.0% of revenue share between 2024 and 2025 while its gross margin fell. The growth is being bought…* |
| 3 | *Alpha Systems gave up 2.0% of revenue share while improving its gross margin — the opposite trade…* |
| 3 | *3 of 5 lines carry 80% of revenue, and the largest alone is 38%.* |

**No text is keyed to any company** — asserted by walking the AST of `_findings`
for company names. **A company without the pattern produces nothing**: every
line healthy and steady returns `[]`. A findings engine that always finds
something is a horoscope, and that test is the most important one in the file.

**The trajectory sentence requires more than two periods.** With two, the module
may say "this is loss-making"; it may not say "this has been deteriorating for
three years". That gate is why the seed was extended.

## 6 · What the surface states it lacks

```
Dimensional detail covers 4 of 8 periods on file (2022–2025).
No product-line detail exists for 2018, 2019, 2020, 2021, so every panel below
is drawn over the periods that have it.
```

Meridian's real shape is four of ten. The fixture carries eight statement
periods against four dimensional ones so the browser can prove the sentence
renders — a fixture whose statement matched its detail exactly could not.

## 7 · The §8c renumbering — and it was not alone

Fixing the reported collision exposed **two more of exactly the same shape**:

| was | now | why it moved |
|---|---|---|
| §8c (T3 surface) | **§8f** | T1's §8c is **cited from code** — `dimensional_analytics.py`'s docstring reads "§8c (the T1 foundation)". Renumbering T1 would falsify a correct citation to fix a collision that is not its fault. |
| §8d (allocated-EBIT fix) | **§8g** | later of the pair; its two citations corrected in the same commit |
| §8e (queued T4 questions) | **§8h** | later of the pair; nothing cites it |

**The rule applied uniformly: the later section moves, and its citations move
with it.** Three duplicate pairs, all created on one day, none noticed. The
sequence §8a–§8h is now unique, asserted by a scan of the headings.

## 8 · Verification

| | |
|---|---|
| Backend suite | **1934 passed** (was 1914), 1 skipped, 3 xfailed |
| New tests | 20 |
| Gates | **29/29 green** |
| `tsc` / lint / ratchet | 0 · rc=0 · 819/819 unchanged |
| declared-absence guard | green — it caught two of my own new cells |
| Browser harness | **3 modes green**, 14/14 pinned still pinned |

Browser proof, by content: the findings card above the strip, the trajectory
sentence, `Derived:` beneath each finding, the coverage sentence, the What
Changed tab with `margin trend by line`, `revenue mix shift`, `diverging`,
`falling` and `pts`, `-$17.62M` on the reversing line, and the total row reading
**$45.00M** — the statement — not the **$29.00M** the visible rows sum to.

Tab strip **1080 × 42 px with 5 tabs** — still one row; sidebar 256 px;
`Profitability` link 232 × 38 px.

## 9 · Three defects this lane found in its own work

- **`_direction` reported a flat series as "mixed".** A gross margin held at
  exactly 31% arrives as `0.31, 0.3100000000000001, 0.31` because it is computed
  as `(revenue − cost) / revenue`. The trend panel's entire claim is that the
  margin is *holding*; float equality destroyed it. Rounded before comparing.
- **Strict monotonicity was the wrong test.** 50%, 50%, 51%, 52% is rising;
  `all(b > a)` rejected it for the one equal pair.
- **A 9%-margin line was being told its pricing was fine.** The divergence
  finding is now gated on a healthy gross margin — diverging by the arithmetic
  is not diverging by the meaning, and the sentence would have sent management
  after the wrong cause.

The fixture generator also **refused to record itself** when the shared pool
grew in step with revenue and nothing diverged — working exactly as intended.
