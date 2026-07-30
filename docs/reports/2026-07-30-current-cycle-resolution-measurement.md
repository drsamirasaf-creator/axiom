# Which cycle is "current" — measurement. NOTHING BUILT.

Measured before proposing anything, and the framing I brought to it was wrong.
The split is not fallback-versus-no-fallback.

---

## 1. The population

Three resolvers, **11 functions**, 12 call sites.

| function | resolver | fallback | reads `.snapshot` | computes live |
|---|---|---|---|---|
| `_briefing_payload` | `closed_cycles_with_results` | – | **yes** | – |
| `_department_sentiment_map` | `closed_cycles_with_results` | – | **yes** | – |
| `assessment_axis_comments` | `closed_cycles_with_results` | – | **yes** | – |
| `assessment_item_drill` | `closed_cycles_with_results` | – | **yes** | – |
| `assessment_sentiment` | `closed_cycles_with_results` | – | **yes** | – |
| `assessment_swot` | `closed_cycles_with_results` | – | **yes** | yes |
| `seed_assessment_comments` | `closed_cycles_with_results` | – | – | – |
| `assessment_seats` | `newest_cycle_regardless_of_results` | – | – | – |
| **`_dept_cei_map`** | `resolve_active_cycle` | – | **–** | **yes** |
| **`_dept_coverage`** | `resolve_active_cycle` | – | **–** | **yes** |
| **`assessment_summary`** | `resolve_active_cycle` | **YES** | yes | yes |

**1 of 11 has a fallback.**

---

## ⭐ 2. The absence of a fallback is a CONTRACT in six of them

`_cycle_has_results()` tests `snapshot["cei"] is not None`. Six functions **read
`cycle.snapshot`** and nothing else. For them the gate is not a policy choice —
**with no snapshot there is literally nothing to return.** A fallback would hand
them a cycle whose snapshot is `{}` and they would render an empty surface with
no explanation instead of an honest "no closed cycle yet".

This is the participant case again: an absence that looks like an omission is a
statement of the contract. I was asked not to assume either side was the defect,
and the majority side turns out to be right.

---

## ⭐ 3. The real incoherence: a live computation gated on a stored artefact

`_cycle_cei()` computes the CEI **from the framework, weights and responses**. It
never reads the snapshot.

Two functions compute live and read no snapshot at all, yet gate on
`resolve_active_cycle`, whose entire test is snapshot presence:

    _dept_cei_map     computes via _cycle_cei    gates on snapshot["cei"]
    _dept_coverage    buckets responses by dept  gates on snapshot["cei"]

**They ask "has this cycle been published?" when what they need is "does this
cycle have responses?"** Those two questions agree in production and diverge on
any database where responses were restored without snapshots — which is exactly
the rebuild.

`assessment_summary` is the only one that does *both*: it computes live **and**
reads the snapshot, and it carries the fallback. That is why a rebuilt Meridian
renders a CEI on the summary and a blank departmental map from identical data.

The fallback is not a bug someone forgot to remove. It is deliberate and predates
the resolver — `7f18c6f`, "keeps first-run behaviour unchanged". It was preserved
when `resolve_active_cycle` was introduced.

---

## 4. Denominator: production is not affected

    cycles total                              11
    closed                                    10
    carrying responses                         9
    open cycles carrying responses             0
    closed + responses + snapshot cei          9
    ⭐ closed + responses + NO snapshot cei     0

**0 of 9.** Every closed production cycle that has responses has a snapshot,
because snapshots are written at close. Nothing a customer can see is wrong
today.

This is a **rebuild-only** defect. It is not latent-in-production; it is a
recoverability defect, in the same class as gap 3 and ranked by the same logic.

---

## 5. Two independent decisions, and they are not alternatives

### (a) Split the resolver — fixes the conflation

`resolve_active_cycle` answers one question and is used for two.

    cycle_with_published_results()   snapshot-gated   -> the 6 snapshot readers
    current_cycle_with_responses()   response-gated   -> _dept_cei_map, _dept_coverage

Each caller then gates on what it actually needs. The six keep their contract
unchanged; the two live-computing surfaces stop depending on an artefact they
never read. **Cost:** a resolver rename touching 11 sites, and
`assessment_summary` must choose which it is — it currently does both, and that
choice is a product question about whether an in-progress cycle should show a
headline CEI.

### (b) Write `snapshot` in the seed — fixes the rebuild

Makes a rebuilt database behave like production. **Does not** touch the
conflation: the two live-computing surfaces would still be gated on an artefact
they do not read, and the next restore path that omits snapshots reproduces this
exactly.

### Recommendation

**Both, in that order** — (a) is the defect, (b) is the reproducibility. Doing
only (b) buys a working demo and leaves the incoherence; doing only (a) leaves a
rebuilt Meridian with no departments, which is the separate open decision below.

---

## 6. Still open, and still yours: `Department` rows as a complement

A rebuild has **zero** `Department` rows. Neither (a) nor (b) creates any, and the
departmental slice cannot render without them regardless of which resolver runs.
Seeding them was rejected as an *alternative* to the resolver fix; whether it is
wanted as a *complement* is undecided, and I have not decided it.

Meridian's 7 departments and the `is_standard` flags are known and were measured;
one (`Sales & Marketing`) is not in `ingest.STD_DEPARTMENTS` and would have to be
written explicitly.

---

## 7. Not measured

- Whether `assessment_summary`'s fallback can surface an **open** cycle's partial
  results as the headline CEI. It selects `cycles[-1]` from *all* cycles, not
  closed ones, so structurally it can; production has 0 open cycles carrying
  responses, so it does not today. Whether that is intended is a product ruling.
- Non-assessment surfaces that pick a "current" period (financial, valuation).
  This sweep covered assessment cycle resolution only.
