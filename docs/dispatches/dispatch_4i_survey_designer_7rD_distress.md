# DISPATCHES — §4i SURVEY DESIGNER · §7r-D DISTRESS SCREENS
## 31 July 2026 · → CLAUDE CODE

Neither needs a fresh spec. §4i is already designed; the distress formulas,
fitted-population labels and the beside-not-into ruling are already in the ratio
registry. These are build dispatches against what exists, plus the contract
points that are not obvious from the existing material.

---

# DISPATCH 1 — §4i SURVEY DESIGNER

**Build:** progressive disclosure over the 13/78 instrument, custom category and
item CRUD, category weighting, preview before send.

## The issue that outranks everything else in this build

**Re-weighting breaks cycle-over-cycle comparability of the Effectiveness Index,
and it breaks it silently.**

The CEI is the headline number from the whole assessment. If a client changes
category weights between cycles, the index moves for a reason that has nothing to
do with the organisation, and every trend line, readiness dimension and
comparison built on it becomes a comparison of two different instruments.

**Contract:**

- **Weights are versioned per cycle**, never edited in place. Same rule as
  client-defined ratio formulas and CXO priority statements.
- **A cycle whose weights differ from the prior cycle is marked** on every
  surface showing the trend — chart, index, readiness dimensions, exports.
- **Show both numbers where the comparison is drawn:** the current cycle on
  current weights, and the current cycle recomputed on prior weights. The gap
  between those two is the weighting effect, isolated from the organisational
  effect. Without it a CEO cannot tell whether the organisation improved or the
  instrument did.
- **A cycle in progress cannot be re-weighted.** Weights lock at send.

## Custom items

- **Custom items have no benchmark and no peer data.** Absence propagates — an
  em dash and "custom item, no peer comparison", never a zero and never a
  silent exclusion from an aggregate that includes standard items.
- **A custom item added mid-cycle is not retro-answerable.** It applies from the
  next cycle. Adding it live would produce a practice with a response rate that
  looks like abstention but is not.
- **Deletion is hide, never delete** — the Innovation Hub moderation rule
  applies. A deleted practice with responses against it orphans those responses,
  and they were given under a participation guarantee.
- **Custom items count toward the k-anonymity floor like any other.** They do not
  get a relaxed threshold on the grounds of being new.

## The anonymity risk that is specific to this feature

**A custom item is a new slice, and slices intersect.** The existing floor is
enforced on combined slices with complement suppression, which is correct — but
that machinery was built against a fixed instrument. A client who adds a
narrowly-worded custom item ("effectiveness of the new regional structure") to a
department of six has built a de-anonymising question without intending to.

**Contract: the designer warns at authoring time**, before send, when a custom
item's expected respondent pool for any department or seniority band falls below
the floor. Warn, do not block — the client may legitimately intend a
whole-population question. But the warning has to arrive while the instrument is
still editable, not as a suppressed result after the cycle closes and everyone
has already answered.

## Progressive disclosure

13/78 default, 361 on request. Custom items sit **alongside** the standard set,
never renumbering it — the standard practice identifiers are how cycles compare
across companies and across time.

---

# DISPATCH 2 — §7r-D DISTRESS SCREENS

**Build:** Altman Z, Z′, Z″, Springate, Zmijewski. Formulas, coefficients and
fitted populations are in `axiom_ratio_registry.yaml` under
`category: Distress Screens`. **Consume the registry. Do not hand-write the
coefficients** — that is the two-owners shape, and these are the rows most likely
to be transcribed slightly wrong and never noticed.

## Non-negotiables already ruled

- **Screens sit BESIDE the viability kernel as an independent read. They do not
  feed it.** Injecting someone else's regression coefficients into the kernel
  means the band can no longer be explained from first principles, and it
  double-counts leverage and profitability the kernel already measures directly.
- **State indicators DO feed the kernel** — covenant headroom, cash runway,
  short-term debt share, floating-rate share. Those are constraint boundaries.
- **Agreement or divergence is the output.** "Altman Z′ screens distressed, the
  kernel bands FRAGILE" is corroboration a CFO can take to a board. "Altman
  clean, kernel CRITICAL" is the more interesting finding, and it only exists
  because they stayed independent.
- **Label as screens, never verdicts.** Every score states its fitted population
  in the explainer. A Z-score computed on a private services firm with public
  manufacturing coefficients is a number with no meaning.

## Three display traps

1. **Zmijewski's polarity is inverted.** Lower is safer; higher is worse — the
   opposite of every Altman variant sitting next to it. Any shared colour scale,
   arrow direction or sort order applied across the panel will render it
   backwards. It carries `polarity: lower_better` in the registry; the panel must
   read that per row rather than assume a panel-wide direction.

2. **Altman Z (original) requires market capitalisation** and is
   `requires_data`. Do not render it for private companies — not as an em dash in
   the panel, but on the "not available, requires market capitalisation" list.
   A private company should see Z′ as its applicable variant, not a blank beside
   a populated one.

3. **Ohlson O is deferred**, not omitted by oversight. It needs a GNP price
   deflator the industry-context layer does not yet supply. The registry holds an
   honest placeholder rather than a half-specified nine-term model. Leave it.

## Which variant applies

Z / Z′ / Z″ are not alternatives to display together indiscriminately — they are
fitted to different populations. **Select on company type and show the applicable
one prominently**, with the others available. Showing three Altman numbers that
disagree because they were fitted on three different populations is not three
opinions; it is one opinion rendered three times with different coefficients.

---

## SEQUENCING

Both are independent of Sessions 1 and 2 and of each other. §4i touches only the
assessment surface; §7r-D consumes the registry and the kernel output.

**§7r-D should not start before the ratio library exists** — it consumes the same
registry and would otherwise build its own reader.
