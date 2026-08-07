# Three recordings and one measurement

**7 Aug 2026.** Heads at start: backend `6a84ec5` · frontend `e02f8b3`, both
clean, 0 ahead / 0 behind. No new surfaces. No production write.

---

## T1 · The four keys that cannot render

⭐ **Classified by the BINDING gap — the one whose closure changes the output.**
Three of the four are missing a registry token *and* have no data; adding a token
would make them render **absent**, not render. Only one is suppressed while
carrying real figures.

| key | in `LABELS` | registry token | values in the dataset | **binding gap** |
|---|---|---|---|---|
| `bs.goodwill` | ✅ | ❌ none | **0** | **DATA** |
| `bs.long_term_investments` | ✅ | ❌ none | **0** | **DATA** |
| `bs.other_noncurrent_assets` | ✅ | ❌ none | **0** | **DATA** |
| `cf.net_borrowing` | ✅ *"Net Borrowing (Issuance - Repayment)"* | ❌ none | **10** | **AGGREGATION** |

**Denominator: 33 stored datasets**, every one checked — not the showcase alone.

| key | present in | carrying values in |
|---|---|---|
| `goodwill` | **0 / 33** | 0 |
| `long_term_investments` | **0 / 33** | 0 |
| `other_noncurrent_assets` | **0 / 33** | 0 |
| `net_borrowing` | **33 / 33** | **33 / 33** |

⭐⭐ **The three are not a labelling failure and not an aggregation failure. They
are template rows no dataset has ever populated** — `LABELS` promises a line the
data has never carried, in every dataset that exists. Their absence from the
frequency view is correct twice over.

⛔ **`cf.net_borrowing` is the only real suppression.** It is in `LABELS`, it
carries values in all 33 datasets, and it is dropped from every frequency view
solely because no vocabulary token declares its aggregation rule — §8o ruling 3
forbids inferring one from the name, so the drop is the designed behaviour of a
missing declaration, not a bug in the view.

**Which bucket it takes is still owed and is not taken here.** The two candidate
readings are a `sum` (issuance less repayment is a flow over the period) and a
refusal (it is a *net* of two flows that the template does not carry separately,
so a token would name a quantity nothing can decompose). ⛔ Report only.

---

## T2 · The adjacency ruling — §4u-c stands, and is now tested

**The argument is NOT satisfied within the tab.**

§4u-c: *"the order is the argument: the department's own people speak first, and
the aggregate tone sits beside the words that produced it."*

Measured against what the Feedback tab actually renders:

| element on the tab | is it "the words"? |
|---|---|
| overall sentiment label + score | no — aggregate |
| 13 axes: sentiment, RAG, score, `n`, divergence | no — aggregate |
| issue titles (`#id`, title, status) | no — a curated management object |
| idea titles | no — a curated management object |
| **verbatim comment text** | **absent by ruling** |

⭐⭐ **The tab carries the aggregate WITHOUT the words**, because §4u-c's own
ruling is that verbatim text does not travel. So the feature that looked like it
might supersede the adjacency is the one that most *depends* on it: a reader
landing on Feedback sees a number with no route back to what produced it except
the tab immediately to its left.

**Recorded as NOT SUPERSEDED. The position was already restored; the missing test
is now written.**

### ⛔ The comment claimed a test that did not exist

After the 7 Aug lane moved the tab back by hand, `DEPT_TABS` carried:

> *"…and a test asserts the two are IMMEDIATE neighbours."*

**There was no such test, in either repo.** A comment claiming an assertion is
worse than silence — the next lane reads it and believes the position is
defended. The comment now names the guard and states what was untrue.

### The test

`scripts/check-voice-sentiment-adjacency.py` (frontend), CI-wired.

- **Asserts geometry, not membership** (§III.13): `index(sentiment) −
  index(voice) == 1`. "Both tabs exist" passes with six tabs between them.
- **Parser scoped to `DEPT_TABS`'s `k:` keys.** The URL-param whitelist earlier
  in the same file lists `voice, feedback, sentiment` in a *different* order; a
  bare-word match would read the wrong list and pass by accident. A control
  asserts a foreign array is not matched.
- **Denominator printed** (10 tabs), and fewer than 8 fails as a parser error
  rather than passing.
- **Controls in memory**, each failing on its own input: the ruled order passes;
  a tab inserted between them fails; `sentiment` before `voice` fails (adjacency
  is not symmetry — the words come first); a missing tab fails.

**Red proof — on the exact 7 Aug defect:**

| state | result |
|---|---|
| current file | **exit 0** — voice at 4, sentiment at 5 |
| Feedback re-inserted between them | **exit 1** — *"voice at 4, sentiment at 6 (delta 2), with ['feedback'] between them"* |
| restored | **exit 0** |

---

## T3 · The department-level disclosure — measured

**Denominator: 45 department-cycle pairs carrying any response. 12 distinct
departments.** Ids hashed; hash basis `sha256("axdept:" + department)[:4]`.

| | count |
|---|---|
| department-cycles with any rating | **45** |
| … clearing the floor (n ≥ 3) | **42** |
| … **below the floor (n < 3)** | **3** |
| department-cycles with no rating at all | **0** |

### Every department-cycle below the floor, with its n

| cycle | dept | n rated | n commented |
|---|---|---|---|
| 24 | `<6f27>` | **1** | 1 |
| 24 | `<a550>` | **2** | 2 |
| 37 | `<cc2a>` | **2** | 2 |

- distinct departments ever below the floor: **3 of 12**
- **below the floor in every cycle they appear: 2** (`<a550>`, `<cc2a>`)
- n distribution below the floor: `{1: 1, 2: 2}`
- n distribution at/above: `{3: 2, 4: 22, 5: 15, 6: 2, 9: 1}`

### ⛔ What the emptiness discloses

At question grain the floor is all-or-nothing per department. So a withheld
ratings surface does not disclose "somewhere below 3" — **it discloses a value
from a two-element set, `n ∈ {1, 2}`.** The observed distribution above the floor
starts at 3 and is concentrated at 4–5, so a reader who knows the shape learns
the department has **one or two** respondents.

⭐⭐ **And for two of the three, it discloses across every cycle they appear in** —
a persistent signal, not a one-cycle accident.

⛔ **REPORT ONLY.** Whether the ratings surface publishes its count the way §4u-c
publishes the comment count is a founder ruling and is not taken here. The
measurement bears on it in one direction only: publishing the count discloses
`n ∈ {1,2}` **explicitly**, and withholding the surface discloses the same set
**implicitly** — so on these numbers the choice is not between disclosing and not
disclosing, but between disclosing plainly and disclosing by inference.

---

## T4 · The banner

The dispatch text for T4 **arrives truncated** — it ends at *"Report the smallest
change that"*. Reported below is the smallest change that makes the banner true
at every grain; if a different property was intended, this is the wrong answer to
the right area.

**Today.** `frequency_views.METHOD_LABEL` is a module-level dict keyed on
**method alone**:

```python
METHOD_LABEL = {
    LINEAR: "estimated by linear interpolation between reported quarters, "
            "not reported data",
}
```

On an annual dataset the source figures are **annual**, and the banner says
*"between reported quarters"* — wrong in both interpolated views (annual→quarterly
and annual→monthly).

**Two leak points, not one.** `router.py` serves the whole dict as
`method_labels` on **every** response (line 651) — including responses that are
not interpolated at all — and then `method_label` on the interpolated one (664).
Correcting only the second leaves the wrong sentence on the payload.

**Smallest change: make the label a function of the grain it interpolates FROM,
and pass the base frequency the router already holds.**

```python
def method_label(method, from_freq):
    return (f"estimated by linear interpolation between reported "
            f"{_NOUN[from_freq]}, not reported data")
```

- `base` is already in scope at both call sites — no new lookup, no new state.
- No signature change to `interpolate_statements`; the banner is presentation.
- The label stops being constructible without a grain, which is what allowed the
  wrong one to ship.

⛔ **Not built.** No new surface this lane, and the dispatch is report-only.

---

## What changed

| | |
|---|---|
| CORE | §4u-c gains **"THE ADJACENCY — NOT SUPERSEDED, AND NOW TESTED"** |
| frontend | `scripts/check-voice-sentiment-adjacency.py` (new), CI-wired; `DEPT_TABS` comment corrected |
| backend | this report |

Backend suite **2,356 passed**, 1 skipped, 3 xfailed. `check-ledger-anchors`
green — 8 known collisions held, no new one taken. `check-report-exposure` green.
**No production write. No figure moved. No customer name or figure recorded.**
