# Frequency-view coverage, `net_borrowing`, and a recorded override

**7 Aug 2026. READ-ONLY on production. No production write. No repository
visibility changed.** Heads at start: backend `fdb4570` · frontend `10a1818`,
both clean, 0 ahead / 0 behind, no stash.

---

## T1 · Proving the endpoint where it was never proven

Dataset **55** (non-showcase, **not** the denylisted customer; ids only below).

| mode | status | populated | shape |
|---|---|---|---|
| **anonymous** | **404** `dataset not found` | no | — |
| **member** | ⛔ **NOT RUN** | — | — |
| **operator** | ⛔ **NOT RUN** | — | — |

Dataset 57 behaves identically (404 anonymously). The showcase control on the same
path and mode returns **200**, so the 404 is tenant isolation refusing, not the
route being absent.

⭐ **The 404 is the expected result and is not coverage**, as the dispatch states.

### ⛔ WHY MEMBER AND OPERATOR WERE NOT RUN — SKIPPED LOUDLY, NOT DOWNGRADED

Neither mode is provable from this machine without one of:

1. **Real member/operator credentials** — `AXIOM_MEMBER_*` and `AXIOM_OPERATOR_*`
   are **unset** locally and are not in the service environment either.
2. **The production JWT signing secret** (`AXIOM_SECRET`), to mint a bearer.

⭐ **I did not take route 2.** `AXIOM_SECRET` signs every session token in the
product; pulling it onto a development machine to establish an endpoint's *shape*
is a permanent increase in credential exposure traded for a bounded, repeatable
check. The verification-read grant covers reading data; it does not make copying
the signing key proportionate.

⛔ **So this lane did NOT prove the population path for a non-showcase dataset.**
Recording that plainly, because a run labelled "three modes" that was one mode is
evidence of the wrong thing. **The unblocker is provisioning read-only member and
operator accounts** — a decision, not a build.

### Deep call-time imports, proven by a call

⚠ **The figure has moved: it is 20, not 17** — two more arrived since it was
measured.

| | count |
|---|---|
| functions holding a call-time relative import at depth ≥3 | **20** |
| of those, **HTTP handlers** (reachable by a call) | **6** |
| of those, **proven by an actual HTTP call in the suite** | **5** |
| never called | **1** — `eva_distribution_surface` (`/datasets/{id}/eva-distribution`) |
| helpers / dependencies, not directly callable | **14** |

⭐ `test_endpoints_reachable` lists **4 routes**, but one of them
(`optimal-range`) imports at **module** level, so it is not in this set. The four
it covers plus three pre-existing suites give **5 of 6**.

⛔ **The 14 helpers are covered only by the static resolver**
(`check-relative-imports`), never by a call. That is stated rather than implied.

---

## T2 · `net_borrowing` — REPORT ONLY

`CF_KEYS` (`engines.py:99`) is `["capex", "net_borrowing", "dividends"]` — the
three cash-flow lines the template stores.

| key | registry token | source | aggregation |
|---|---|---|---|
| `capex` | `cf.capex` | stored | **sum** |
| `dividends` | `cf.dividends_paid` | stored | **sum** |
| **`net_borrowing`** | ⛔ **NONE** | — | — |

⭐⭐ **The registry names `net_borrowing` twice and gives it no token.** Both
mentions are in the `requires:` prose of tokens that are **absent** *because of
it*:

> `cf.debt_raised` — *"only NET borrowing is stored (`net_borrowing`). Gross
> raised/repaid cannot be recovered from a net figure."*
> `cf.debt_repaid` — *"see `cf.debt_raised` — `net_borrowing` only."*

**The vocabulary knows the field exists, cites it as the reason two other tokens
cannot be modelled, and never models it.** That is why the frequency view reports
`unclassified: ["cash_flow.net_borrowing"]` and drops the line — the designed
behaviour when no rule is declared (§8o ruling 3: nothing infers an aggregation
from a name).

**Consumers measured: 30 occurrences across 6+ modules** (`proforma`,
`forecast_studio`, `reporting`, `report_pdf`, `seed`, `refcompanies`). The line is
live everywhere except the frequency view.

⛔ **Which bucket it belongs in is a ruling and is not made here.** The only
observation offered: its two `CF_KEYS` neighbours are both `sum`, and the token is
**missing entirely** rather than mis-classified — so the ruling is *"add a token,
with which rule"*, not *"correct a wrong one"*.

---

## T3 · The guard hits from the last lane, recorded

`check-theme-aware-strokes.py` exempted **three** decorative tokens. Measured:

| token | dark value | contrast vs card | verdict |
|---|---|---|---|
| **`--border`** | `#2a3a33` | **1.35:1** | ⭐ **genuine override — HIT**, 9 files |
| `--muted-foreground` | `#9aa39d` | 6.25:1 | ⛔ **never hit** — passes on merit |
| `--muted-gray` | `#9aa39d` | 6.25:1 | ⛔ **never hit** — passes on merit |

⛔⭐⭐ **Two of the three were allowlist entries added without cause.** They were
never overrides at all — the rule does not flag them. That is precisely the tell
ONBOARDING names: *an override nobody records is an allowlist that grows
silently*. Left alone, the list would have looked like it carried three
justifications when it carried one.

**Corrected:**

- The two unhit entries are **removed**.
- `--border` is recorded as **hit-and-override** with its **measured** contrast,
  its file count, and its reason — chart gridlines carry no value a reader must
  read, so WCAG's 3:1 for *content-bearing* graphical objects does not bind. ⛔ The
  map's edges **are** the content; that is the line the list draws.
- ⭐⭐ **The opposite ratchet is added** (the law recorded at §0.2): **an exemption
  that is never hit now FAILS**, so the list cannot grow silently again.

**Red-proofed both ways:** re-adding an unhit exemption → *"is exempt but no
longer fails the rule — remove it"*, exit 1. Emptying the list → 10 failures,
exit 1.

Guard output now states the override rather than hiding it:

```
283 source file(s) scanned · 16 tokenised stroke(s) · 1 exemption(s), 1 hit
  · --border OVERRIDDEN — measured 1.35:1 against the dark card
    (recorded 1.35:1, 9 file(s)) — chart gridlines and axes …
```

---

## Gates

Backend: `check-ledger-anchors`, `check-relative-imports`, `check-frequency-views`,
`check-two-frontiers`, `check-objective-labelled` all green; 39 tests in the two
touched suites pass. Frontend: lint clean, ratchets at ceiling, inbound refs green,
`check-theme-aware-strokes` green.

**Nothing about repository visibility was inspected, changed, or committed in this
lane.**
