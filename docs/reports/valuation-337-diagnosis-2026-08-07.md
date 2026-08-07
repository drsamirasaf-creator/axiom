# engines.py:337 — the absent operand is not net_debt

**7 Aug 2026. DIAGNOSE ONLY. Nothing fixed.** Heads: backend `3569318` ·
frontend `b498a5f`, both clean, 0/0.

⛔ **THE LANE'S PREMISE IS WRONG AND THE LANE STOPS ON IT.** T1 directs the fix
to `net_debt`'s owner. Measured in the crashing frame, **`net_debt` is present**
and the absent operand is an **EV-grid cell**. A fix at `net_debt`'s owner would
change nothing and the 500 would survive it.

---

## A3 · The Walker — identified. **It is me.**

⭐⭐ **Not an external enumeration.** The Spider is this session's own
verification probe, run ~15 minutes before the dispatch.

| Sentry signal | This session |
|---|---|
| `browser = Python-urllib 3.12` | my probes use `urllib.request`; local `python3` is **3.12.7** |
| `device.family = Spider` | urllib's default UA, classified as a bot |
| two datasets, two endpoints, ~111s apart | one script looped `analytics/{3,4,5,42,43,45}` then `real-options/{3,4,5,42,43,45}` |
| release `35693180de6d…` | **the full SHA of `3569318`** — the commit I pushed minutes earlier |

**The complete walk, from my own command log** — every path, anonymous
(`X-AXIOM-Tenant: demo`, no `Authorization`), all GET:

```
/api/v1/valuation/analytics/{3, 20, 8, 999999, 4, 5, 42, 43, 45}
/api/v1/valuation/analytics-nope/45          (deliberate no-such-route control)
/api/v1/valuation/real-options/{3, 4, 5, 42, 43, 45}
/api/v1/financials/datasets/{3, 20, 8, 999999}
```

**The six 500s are `analytics/{3,4,5}` and `real-options/{3,4,5}`.** No POST was
issued; no production write occurred.

⛔ **So this is not evidence of an outside party enumerating the API.** The
separate question raised in the dispatch is real and remains unruled — it is
deliberately not restated here — but it must not be escalated on *this*
evidence, because this evidence is mine. ⭐ The instrument found a real defect,
and then its own traffic was read as an attacker.

---

## T1 · The absence, measured in the crashing frame

Inspected via the traceback frame's locals on dataset 3 — not inferred:

| operand at `:337` | value |
|---|---|
| `deterministic["net_debt"]` | **320.0 — PRESENT** |
| `deterministic["preferred_equity"]` | 0.0 |
| `deterministic["minority_interest"]` | 0.0 |
| **`cell`** (an `ev_grid` element) | **`None` — ABSENT** |

The TypeError reads `unsupported operand type(s) for -: 'NoneType' and 'float'`.
**`NoneType` is on the LEFT**, which is `cell`; `net_debt` is the right operand
and is a float. ⭐ The operand order in the exception text was the tell.

**Confirmation from the other direction:** dataset 45 *also* has
`company["_debt_book"] = None` in stored data and **does not crash**. Absence of
net_debt is therefore neither necessary nor sufficient — it is not the mechanism.

### ⭐⭐ Why the cell is absent — and it is correct (§7q)

`ev_grid` is 5 WACC × 5 terminal-growth = **25 cells, 4 absent (16%)**, and the
absent ones are exactly:

| wacc | g | |
|---|---|---|
| 0.025 | 0.025 | g ≥ wacc |
| 0.025 | 0.030 | g ≥ wacc |
| 0.025 | 0.035 | g ≥ wacc |
| 0.035 | 0.035 | g ≥ wacc |

**Gordon growth is undefined when g ≥ WACC** — the denominator is zero or
negative. The EV grid is *refusing correctly*: an absence with a plausible
reason, which §7q calls the most informative signal. **Nothing upstream is
broken.** The defect is solely that the equity grid consumes an absence-bearing
grid with raw arithmetic.

⛔ **The dispatch's `or 0` prohibition holds with more force than it was written
with.** Zeroing `net_debt` would have made equity equal EV. Zeroing the *cell*
would assert an enterprise value of zero at exactly the corners where the model
declines to answer — a valuation of nothing, rendered as a number.

---

## T2 · Dataset 3 — the question dissolves, and the fraction

**Neither debt nor cash is absent.** `net_debt = 320.0`, computed and present;
`preferred_equity` and `minority_interest` are both `0.0` legitimately. Dataset 3
is showcase-tenant. The real distinguishing property is its **WACC grid starting
at 2.5%**, which is at or below three of its five growth values.

### The fraction — denominator printed

Every stored dataset run through the production engine entry:

| | |
|---|---|
| datasets whose `ev_grid` carries an absent cell | **3 / 33 = 9.1%** |
| which | **3, 4, 5 — all showcase** |
| datasets that raise at `:337` | **3 / 33 = 9.1%** |

⭐⭐ **All three affected datasets are on the public demo.** 27 private datasets
and 3 of the 6 showcase datasets are unaffected.

---

## A1 · Blast radius — the page fails whole, not per-tab

**8 valuation paths are registered.** Engine entries exercised on dataset 3:

| endpoint | reaches `:337`? |
|---|---|
| `POST /valuation/run` | **yes** |
| `GET /valuation/analytics/{dataset_id}` | **yes** |
| `GET /valuation/real-options/{dataset_id}` | **yes** |
| `POST /valuation/real-option` | **yes** |
| `POST /valuation/stress` | **yes** |
| `POST /valuation/multiples` | no — separate bridge at `:593`, needs a sector |
| `GET /valuation/modes` | no |
| `GET /valuation/runs` | no |

**5 of 8 registered valuation endpoints — 5 of 6 engine entries tested — fail at
the same line.** ⭐ Confirmed: on datasets 3–5 the Valuation page fails **whole**,
not per-tab, and the two Sentry issues are one defect reached by two of five
routes.

---

## A2 · What each surface should say — reported, not built

⭐ **The granularity differs because the absence enters at a different depth.**

**`analytics` — per-cell absence, and it is honest.** The EV grid is valid and
should render its 21 populated cells. The equity grid should carry an em dash in
exactly the 4 positions where EV is absent, with one note naming the reason:
*terminal growth at or above WACC — no terminal value.* The reader learns the
model's boundary, which is real information about the assumption set.

⛔ **`real-options` — per-option em dashes would misread the cause.** `s0` is the
bridge output, so all three options share **one** missing input. Three em dashes
assert three independent failures. The honest shape is a **single refusal for the
suite**, naming the one cause — not three absences.

**Neither is built. No `or 0`, `?? 0`, or default anywhere.**

---

## T4 · The release tag resolves

| | |
|---|---|
| Sentry release | `35693180de6d59909662e797c42ff2fbffeb21c9` |
| `git cat-file -t` | **commit** |
| resolves to | **`3569318`** — *"Three recordings and one measurement"* |

⚠️ **Premise correction:** the dispatch states head is `6a84ec5`. Head is
`3569318`; `6a84ec5` is its parent. I pushed `3569318` in the previous lane and
Railway redeploys per push, so production moved before the Sentry events fired.
**The release field is set correctly and does map to a commit** — no triage gap
here. Line 337 matches head, as the dispatch says.

---

## T5 · Why nothing caught it

⭐ **`auth-regression` DOES call the path.** Line 1122 issues
`/api/v1/valuation/analytics/{active_ds}`. So this is not an unreached endpoint.

⛔ **It calls it for ONE dataset — `active_dataset_id` of the crawled company**
(line 1113–1114). Datasets 3, 4 and 5 are never the active dataset in any crawled
session, so the only three datasets that fail are the three the crawler cannot
select. **The hole is dataset coverage, not path coverage.**

### And the 404 finding from the earlier lane, corrected

`visit()` (line 682) treats **any** non-2xx/3xx during navigation as a route
failure, so a 404 on load **is** a finding. The blind spot is narrower and more
specific: the **interaction sweep** at lines 528 and 644 filters `c[2] >= 500`,
so a 404 raised by a *click* is recorded and discarded. `POST /valuation/run` is
click-triggered and sits in exactly that gap.

### The 404s themselves — explained

Both paths exist. `POST /api/v1/valuation/run` and
`GET /api/v1/valuation/analytics/{dataset_id}` are both registered among 340
paths, and neither URL appears anywhere in the 7 Lovable commits
(`2605c28..dfc264d`, 10 insertions / 12 deletions, zero matches for
`valuation` or `analytics`). **Neither side moved.**

Every 404 in the valuation router is the same line —
`if not ds or ds.tenant != tenant` — which **deliberately** conflates "does not
exist" with "not yours", because a 403 would confirm existence to an enumerator.
⭐ But the two are distinguishable in the body, which the dispatch's premise did
not assume: a handler refusal returns `{"detail":"dataset not found"}` and a
genuinely unregistered path returns `{"detail":"Not Found"}` (measured against a
deliberate control).

⛔ **`20` is not a dataset id.** Dataset ids run 3–57 with gaps and 20 is not
among the 33. It appears as `company_id` in 47 tables. A caller passing 20 into
`/valuation/analytics/{dataset_id}` is passing a **company id into a dataset
slot**, and receives the refusal 404 — exactly the dispatch's hypothesis, now
measured.

---

## What was and was not done

- **Nothing fixed.** The premise naming `net_debt` as the absent operand is
  measurably wrong; fixing at its owner would leave the 500 in place.
- **No production write.** All probes were GET; no POST was issued.
- **No `or 0` anywhere**, and none proposed.
- The ruling owed: **where the absence is honoured** — per-cell in the equity
  grid, and as a single suite-level refusal in real options.
