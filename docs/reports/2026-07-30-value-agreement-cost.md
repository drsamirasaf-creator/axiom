# The targeted assertion on wacc and roic — costed, and it has nothing to assert

**The comparison set is not 2. It is 0.** Both members dissolved on inspection,
and that is the report.

---

## 1. `wacc` — one owner, two inputs, and they are *meant* to differ

Both recompute sites call `ratios.wacc_at`:

    financials/engines.py:412   ratio_lib.wacc_at(leverage=leverage, ...)
    intelligence/engines.py:157 ratios.wacc_at(leverage=x, ...)

`intelligence/engines.py:143` already says so in its own docstring — *"SAME BLEND
AS fin.wacc — one implementation now, in ratios.wacc_at."*

They differ only in what leverage they are asked about: the company's actual
leverage, versus a swept curve point `x` from `[k * 0.05 for k in range(0, 61)]`.
**An assertion that they agree would be wrong** — the curve exists precisely to
evaluate WACC at leverage the company does not currently have. Asserting equality
would fail on every dataset and be suppressed within a week.

## 2. `roic` — one computation and one rescaling

    financials/engines.py:331   _n(lambda a, b: a / b, nopat, ic)      the ROIC
    benchmarks/engines.py:206   _n(lambda r, ic: r * ic, kpis["roic"],
                                   bases["invested_capital"])

The second is inside a dict named `actual_abs` — *"actual absolute on the same
scale"* — mapping each KPI to its currency-scale counterpart. `roic × invested
capital` is NOPAT. It is a **rescaling of the first**, not a second ROIC, and it
already carries a comment recording that an earlier `or 0` there fabricated a
zero NOPAT.

My classifier called it a recompute because a `BinOp` sits inside the `_n`.

---

## ⭐ 3. So sole ownership holds for all twelve

    12 of 12 policed quantities have ONE independent implementation.

That is the era's claim confirmed from a second direction — not by counting
consolidations performed, but by surveying producers and finding no second
implementation among them.

**Bounded by what the survey can see**, which is stated so the zero is honest:
dict-literal keys under `services/` only. A quantity computed inside a report or
PDF builder, assigned and returned rather than emitted as a key, or living in the
frontend, is invisible to it. `eva` and `operating_cash_flow` are already known
examples — computed, never emitted under those key names.

---

## 4. What the targeted assertion would cost — and why I do not recommend it

**Cost, if built anyway:** one pytest module, ~80 lines, running both `wacc`
call paths and both `roic` sites over the 16 reachable datasets, plus a planted
perturbation as control. Roughly 20–30 seconds per run; it could be a per-commit
gate rather than nightly, since it touches no Monte Carlo path.

**Recommended against, for a reason the cost does not capture:** there is no pair
of independent implementations for it to compare. It would assert that a function
agrees with itself, which is the failure mode already named in the design — *"a
differential test over routes that all call the same function agrees trivially
and forever, proving only that one function is deterministic."* Building it would
manufacture exactly the false assurance the design set out to avoid, and its
green would read as "the numbers are right".

## ⭐ 5. What is worth building instead, and it is prevention not detection

The risk is not that today's two sites disagree. It is that **a third
implementation appears** and nobody notices — which is how `_debt_book` happened.

**Run `scripts/route-table.py` as a CI gate with the independent counts
ratcheted**, exactly like the Class A margin boundary:

- a quantity whose independent-route count **rises** → fail
- a quantity whose count **falls** → fail, "lower it here"
- corpus not required; it is a static survey, so it costs ~1 second

**Cost: about half a day**, mostly writing the known-positive control — a planted
second implementation of a policed quantity that the gate must reject — and the
per-quantity declared counts.

This is the same conclusion Class A reached from the other side: where the
arithmetic cannot be told apart, and where there is nothing yet to compare,
duplication is **prevented by boundary rather than detected by comparison**.

---

## 6. Recommendation

1. **Do not build the value-agreement harness.** Comparison set is 0.
2. **Do build the route-table ratchet** — cheap, static, catches the emergence of
   a second implementation, which is the actual risk.
3. Revisit if the survey's blind spots are closed and a genuine second
   implementation is found in a report builder or the frontend.
