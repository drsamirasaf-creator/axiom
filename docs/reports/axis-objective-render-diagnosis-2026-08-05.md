# Why the axis→objective block "never rendered"

**Diagnosis only. Nothing fixed, nothing shipped.** 5 Aug, on `d2826bf` / `0fc2330`.

---

## ⭐⭐ THE HEADLINE: IT ALWAYS RENDERED. THE HARNESS COULD NOT SEE IT.

Every layer was true, on the served bundle, measured in the browser:

| layer | verdict | evidence |
|---|---|---|
| route mounts the page | ✅ | axis page content present |
| page mounts the component | ✅ | `[data-probe]` node count **1** |
| component fires the request | ✅ | `/companies/20/axis-links` × 2 |
| response carries data | ✅ | **200**, both |
| component renders | ✅ | ⭐ `'OBJECTIVES ADDRESSING THIS AXIS\nLaunch the platform v2 architecture'` |

**There was no product defect.** The block mounted, fetched, received data and
painted the linked objective — on every one of the runs previously reported as
failures.

### The mechanism

The header carries Tailwind's `uppercase` class, i.e. `text-transform: uppercase`.

| accessor | returns |
|---|---|
| `inner_text()` — **rendered** text | `'OBJECTIVES ADDRESSING THIS AXIS'` |
| `text_content()` — **source** text | `'Objectives addressing this axis'` |

⭐⭐ **THE ASSERTION WAS A CASE-SENSITIVE `in` AGAINST `inner_text()`**, comparing
source casing to rendered casing. It could never match, on any run, for any data.
Measured directly:

    case-SENSITIVE   "Objectives addressing this axis" in body  ->  False
    case-INSENSITIVE same string, lowered                       ->  True

The objective-page block failed identically — `"Assessment axis this addresses"`
is in an `uppercase` div too.

### ⭐ AND THE EVIDENCE THAT LOOKED CONTRADICTORY WAS CONSISTENT

The previous lane recorded, as a puzzle, that *"the endpoint returned 200 in the
browser, confirmed three times, and the block never mounted."* ⛔ **A component
that never mounts cannot fire a request from its own effect.** The 200s were
proof the component was working; they were read as proof something was wrong.
**The instrument was never suspected because its output was a plain `False`.**

---

## 2 · The three known shapes — all three ruled out, by measurement

| shape | applies? | measured |
|---|---|---|
| `useAutoResolveCompany()` returns nothing, so `companyId` is null and every path early-returns (`a76d53a`) | ⛔ **NO** | the request fired **with company 20 in the URL** — the id was a value, not null |
| a cold visit never seats a dataset, so the page holds its skeleton with **no request in flight** (`d56d630`) | ⛔ **NO** | two requests completed, both 200; no skeleton was held |
| a component receiving a prop from a hook that **seats state rather than returning it** | ⛔ **NO** | `useActiveCompany()` returns a value; `active?.id` resolved to 20 |

⭐ **All three produce the same visible signature — an empty area — and none of
them was this.** The signature is shared; the cause was not. That is precisely
why matching on signature rather than measuring layer by layer sent the previous
attempt into a retry.

---

## 3 · The empty-payload guard — correct, and it was never the problem

An axis with no declared objective is a real state: **6 of 13 on the seed**.

    axis 8.0  (linked)   -> 'OBJECTIVES ADDRESSING THIS AXIS
                            Launch the platform v2 architecture'
    axis 11.0 (unlinked) -> 'OBJECTIVES ADDRESSING THIS AXIS
                            No objective is declared to address this axis.'

⭐ **The guard declares the absence rather than returning null on empty.** The
original `if (rows === null) return null` fires **only while the fetch is in
flight** — `rows === null` means *not yet answered*, whereas `rows === []` means
*answered, nothing there*, which falls through to the absent sentence.

⛔ **The relaxation applied during the failed lane was therefore unnecessary.** It
was a guess aimed at a symptom, and it changed nothing because the guard was
already right. **A fix that produces no change in behaviour is evidence the
diagnosis is wrong, and that signal was available and not read.**

---

## 4 · Would the harness have caught it? — ⛔ NO. THE HARNESS *WAS* THE FAULT.

| check | verdict |
|---|---|
| the load control added last lane | ⭐ **PASSED, and correctly** — it looked for `"Information Technology"`, which is not CSS-transformed. It proved the page rendered, which was true. |
| the block assertions | ⛔ **FAILED, and wrongly** — case-sensitive against transformed text |
| the endpoint-stub check | not applicable — this harness hit the live API |

### ⭐⭐ THIS IS A THIRD SHAPE, AND IT IS THE MIRROR OF THE OTHER TWO

The last two lanes fixed **false positives**:

1. assertions that **pass on a page that never loaded** (fixed by a load control)
2. assertions that pass against a **hand-written stub** (fixed by recorded fixtures)

⭐⭐ **THIS IS A FALSE NEGATIVE: AN ASSERTION THAT FAILS ON A PAGE THAT RENDERED
PERFECTLY.** Both earlier lessons say *"do not pass when nothing rendered."*
**Neither says "do not fail when everything did"** — and the load control, which
exists to catch exactly the first class, was itself passing while the verdict was
wrong. **A load control proves the page rendered; it says nothing about whether
the assertion can express what rendered.**

⭐ The cost of the asymmetry is visible: a false positive ships a defect, and this
project has built machinery against that. A false negative **reverted working
code and burned a lane**, and there was no machinery against it at all.

### What would have caught it

- comparing against `text_content()`, or casefolding both sides
- asserting on a **`data-*` probe** rather than on prose — the probe found the
  node instantly here, and is immune to styling
- ⭐ **a known-negative**: assert the marker is ABSENT on a page that should not
  have the block. It would have failed, revealing the matcher never matches
  anything — the same discipline as a scanner's known positive, run the other way.

---

## 5 · Not fixed here

The mechanism is a **two-character change in a test harness**, and the component
is unchanged from the reverted version. **It is not applied in this lane**, per
the dispatch. The scaffolding used to measure was reverted; both repositories are
clean at `d2826bf` / `0fc2330`.

⭐ **What is owed is small and now precisely specified**, which is what the
previous attempt lacked when it retried.
