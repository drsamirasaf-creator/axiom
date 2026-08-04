# T5.1 — avoidability, and the four rulings

4 August 2026. Backend `axiom`, frontend `optimization-anchor`. No seed.

---

## 1 · The four rulings, recorded (CORE §8r)

**1 — The §22 corrective states its assumption now.** *"The company would be
worse off, not better"* rested on the premise that none of the allocated cost
disappears with the line. Absence declares; the assumption travels with the
number; an allocated figure never renders without its method. Leaving it
unstated is not a position, it is the defect continuing.

**2 — Blank is not a declaration; an explicit zero is.** A client entering 0 has
told you nothing disappears. A blank treated as zero avoidable is `or 0` on the
input that decides whether a line should be exited, and it would make every
line's stranded cost 100% of its allocated share — reproducing ruling 1's
premise, computed and therefore invisible.

**3 — No horizon.** Stranded cost is a standing annual amount. The multi-period
form starts discounting, and discounting is `prescience_decision`'s. Exit
economics to be discounted enters the move library and is valued once, there.

**4 — "Unprofitable customer" never renders**, even when correctly derived. It
is a verdict on a relationship, acted on faster than its qualifications are
read. Show contribution less cost-to-serve; let the reader name it.

## 2 · The declaration model — v13 → v14

**Cost Avoidability**, one row per cost pool per line:

| Column | What the client is told |
|---|---|
| Period · Frequency · Line Code · Cost Pool | which pool, for which line |
| **Avoidable Amount** | How much of this pool's charge to this line would actually STOP BEING SPENT if you discontinued the line. Enter 0 if none of it would — that is an answer. Leaving it blank is not, and AXIOM will say so rather than assume. |
| **Notice Period (months)** | How long before that saving starts. A contract you cannot exit for six months is not avoidable this year. |
| **Capacity Released** | What the line frees up if it stops — hours, space, headcount. Leave blank if nothing is freed. |
| **Capacity Re-usable?** | yes / no / unknown. Whether that freed capacity could be sold to someone else. AXIOM never assumes an answer to this. |

⭐ Ruling 2 is written into the client's own hint, not just into the code.
Prior versions parse identically — fifth time on that discipline, asserted by
comparing the same workbook with and without the sheet.

## 3 · What is computed, and what is refused

**Computed** — each an identity over a declaration:

- `stranded = allocated − avoidable` — the complement of a declaration is not an
  inference
- exit economics: contribution lost against cost saved, with `better_off`
- redistribution through **T2's own allocator**, carrying its method and grade
- `avoidable_this_year` — phasing from the notice period, **undiscounted**

**Refused** — never inferred:

- the avoidable share itself
- whether freed capacity is re-sold (`Capacity Re-usable?` collects the answer)
- whether customers of an exited line take others with them

⭐ Two guards enforce it: a declaration larger than the charge **declines**
rather than producing negative stranded cost, and an AST read asserts the module
never uses `npv`, `discount_rate`, `present_value` or `enterprise_value`.

## 4 · The revised corrective, in both states

**Without a declaration — it names its own premise:**

> Control Electronics covers its own variable cost. It contributes 53.5 before
> any share of fixed and shared cost, and it is negative at allocated EBIT
> (−13.6) only because of the share it is charged. Whether discontinuing it
> would help depends on how much of that share would actually stop being spent —
> and **AXIOM assumes none of that cost disappears with the line until you say
> otherwise**. Fill the 'Avoidable Amount' column on the 'Cost Avoidability'
> sheet to see the net effect.

**With one — it quantifies, and the conclusion can flip:**

> …would save **240.0** of avoidable cost and leave **610.0** stranded on the
> lines that remain. Against the contribution lost, the company would be
> **186.5 better off**.

> …would save **10.0** and leave **840.0** stranded. Against the contribution
> lost, the company would be **43.5 worse off**.

⭐⭐ **Same line, same contribution, opposite advice** — decided by a number only
the client holds. That is the whole reason ruling 1 exists, and it is why the
old sentence's certainty was the defect rather than its direction.

## 5 · What a seed would need — not seeded

Meridian carries no declaration, so every line renders the undeclared form.
A seed would need **one row per pool per line per period** — five pools × five
lines × four periods = **100 declarations** — each with an Avoidable Amount, and
a Notice Period where the saving is not immediate.

⭐ A stated "0 avoidable" for every pool is a legitimate seed and the cheapest
one, but it is the *least* interesting: it makes every conclusion "worse off"
and never exercises the flip. A seed worth having puts the two driver pools
(customer support, logistics) partly avoidable and the corporate residual at
zero — which is also what a real controller would answer.

## 6 · Verification

| | |
|---|---|
| Backend suite | **2030 passed** (was 2014), 1 skipped, 3 xfailed |
| New tests | 16, 15 red before |
| Gates | **29/29 green** |
| Version pins advanced | 6, as every prior bump did |
| Browser | 3 modes green, 14/14 pinned still pinned |

Constraints held: no margin outside `ratios.py`, no status outside
`weakest_status`, nothing added to the endpoint.

⭐ One pinned browser needle and one T4.2 unit test asserted the **old**
sentence. Both were updated to assert the property ruling 1 cares about — that
the page names its premise — rather than the phrasing it happened to have.
