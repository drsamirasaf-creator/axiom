# T3 stops the lane — every committed pack carries a period identifier

**7 Aug 2026. NOTHING WRITTEN.** `axiom ac98f32` · `optimization-anchor 1e0ca08`,
both 0/0.

The dispatch's own stop condition: *"Report what this does to existing packs
BEFORE writing. If any committed pack carries a period identifier, say so and
stop."*

---

## ⛔ T3 · THE GATE FIRES. 24 OF 24.

| | |
|---|---|
| committed packs | **24** |
| status | **`published` — all 24** |
| carrying a `content_hash` | **24 / 24** |
| carrying an `input_snapshot_id` | **24 / 24** |
| **carrying a period identifier** | **24 / 24** |

`ax_packs` carries **two** period identifiers on every row:

- **`period_type`** — `monthly` × 16, `quarterly` × 8
- **`period_end`** — present on **24 / 24**

**Every one is published, hashed, and snapshotted.** There is no unpublished
pack to change safely.

### And `period_labels` is already a frozen input class

`pack.py:498` declares it, captured by `_cap_period_labels` (`pack.py:465`),
which freezes:

```python
return _present(periods=periods, frequency=ds.frequency)
```

⭐⭐ **It freezes the PERIODS DICT AND THE FREQUENCY — not display strings.** So
today's 24 hashes were computed over identifiers. **Adding a rendered label to
that class changes the captured value, and therefore `content_hash`, for every
pack produced afterwards.**

⛔ **That is the §7o leak path CORE names, arriving exactly where CORE said it
would** (`AXIOM_LEDGER_CORE.md:21362`): *"`period_labels` is a declared pack
INPUT_CLASS — the concrete §7o leak path."*

### What it does to existing packs — precisely

| | |
|---|---|
| the 24 already published | **unchanged.** Their hashes are over the snapshot they captured; nothing rewrites them |
| every pack published after the change | **a different `content_hash` for identical financial data** |
| what a reader comparing two packs sees | a hash change with **no figure change**, and nothing in the pack explaining it |

⭐ **The figures do not move. The hash does.** That is the worst shape for a
frozen artefact: a change that is invisible in the content and loud in the
identity.

---

## The ruling this needs before anything ships

**Which of these is the founder's intent?**

1. **The label is NOT a pack input.** Add it to the payload the *surface* reads,
   and keep `_cap_period_labels` freezing identifiers only. Pack hashes never
   move. ⭐ This matches the ruling's own words — *"the label is explicitly
   render-only"* — and render-only means it is not an input.
2. **The label IS a pack input.** Hashes move for all future packs, and the
   change needs a recorded reason so a reader comparing a June pack to a July
   one is not left to guess.

⭐ **On the ruling's own text, (1) is what was asked for** — but it is a decision
about a frozen artefact and CORE requires it be taken deliberately, not inferred
by me from a sentence written about the client.

---

## T1 · Measured, not built — both owners exist and neither has a caller

| owner | state |
|---|---|
| `templates.LABELS` | **26 line names in both frameworks, zero gaps either way** — measured by the statement-label lane |
| `periods.format_period` | **exists, and has no caller** |

⭐ **Neither needs writing. Both need wiring**, exactly as the dispatch says. No
second map and no second formatter would be created.

**The framework must travel too**, and the reason is measurable: `us_gaap` and
`ifrs` differ on **9 of 26** lines — `Cost of Goods Sold` / `Cost of Sales`,
`Interest Expense` / `Finance Costs`, `Short-Term Debt` / `Current Borrowings`.
A client holding only the key cannot pick between them, which is precisely why
decoding client-side is impossible rather than merely undesirable.

---

## T2 · The four keys, with their label state

Measured across **all 33 datasets**, not the showcase alone:

| key | in `LABELS` | registry token | values in data | binding gap |
|---|---|---|---|---|
| `bs.goodwill` | ✅ | ❌ | **0 / 33** | **DATA** |
| `bs.long_term_investments` | ✅ | ❌ | **0 / 33** | **DATA** |
| `bs.other_noncurrent_assets` | ✅ | ❌ | **0 / 33** | **DATA** |
| **`cf.net_borrowing`** | ✅ *"Net Borrowing (Issuance - Repayment)"* | ❌ | **33 / 33** | **AGGREGATION** |

⛔ **`cf.net_borrowing` must keep rendering as the suppressed line.** It is the
only one of the four carrying real data, its aggregation rule is **still
unruled**, and §8o ruling 3 forbids inferring one from the name. **A label
arriving without a rule would make a suppressed line look present** — absence
stays absence, and shipping labels must not quietly change that.

---

## T4 / T5 · Not started

Both are downstream of T1, which T3 gates. **No banner change, no browser
proof.**

⭐ The banner's two falsehoods stand as measured and remain worth fixing on
their own: it says *"between reported quarters"* on a dataset the same panel
calls **annual**, and it says **interpolation** when the arithmetic is
**allocation** (`433.7 / 12 = 36.14`) and **step** (stocks hold year-end flat).
**Neither requires touching the arithmetic** — only the sentence — so it is
separable from the label work if you want it moved to its own lane.

---

## ⚠️ One thing that did not reach me

A pasted block of ~51 lines arrived mid-lane as a placeholder with no readable
content. **I have not acted on it and have not guessed at it.**

---

## What was written

**This report only.** No payload change, no label wiring, no banner change, no
pack change.
