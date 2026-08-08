# The four toggles onto the code — T1, REPORT ONLY

**8 Aug 2026.** T1 **measured**. T2 **measured, because its answer fell out of
T1's data**. ⛔ **Nothing built. No toggle exists in the code and none was
added.**
Proof origins: `src/lib/nav-index.generated.ts` **regenerated and confirmed
byte-identical**; `AppLayout.tsx`'s `businessSections`; the FastAPI app's own
`openapi()` and its route table, walked. **No production data was read or
written.**

---

# ⛔⭐⭐ THE HEADLINE — THE MAPPING IS NOT DERIVABLE, AND THAT IS THE FINDING

The dispatch said *derive; do not hand-list.* **I could not fully derive it, and
the reason is the answer**: nothing in the codebase records which module a
destination or a path belongs to.

| what carries module attribution today | |
|---|---|
| the sidebar's `businessSections` | ⭐ ANALYZE / STRATEGIZE / EXECUTE — **8 pages** |
| `nav-index.generated.ts` `section` field | ⛔ **11 of 106 destinations.** 95 are blank |
| the backend | ⛔ **nothing.** No module column, no tag, no decorator |

⛔ **So the route → toggle assignment below is MINE, not the code's.** Everything
downstream of it — the path counts, the overlaps — is derived and reproducible;
the assignment itself is an authored input. **Reporting it as derived would be
the §III.27 error**, and it is named here instead.

---

# T1 · THE 106 DESTINATIONS

**Regenerated and diffed: 106 = 33 pages + 73 tabs across 25 distinct routes**,
unchanged from the figure CORE carries.

| toggle | routes | ⭐ destinations |
|---|---|---|
| **internal feedback** | `/cei` (15) · `/stakeholder-engagement` (6) | **21** |
| ⛔ **external feedback** | — | ⛔ **0** |
| **STRATEGIZE** | `/target-state` (1) · `/optimization` (4) | **5** |
| **EXECUTE** | `/initiatives` (4) · `/initiative-impact` (1) | **5** |
| **ANALYZE — mandatory** | `/org-structure` (1) · `/dashboard` (5) · `/profitability` (5) · `/valuation` (9) | **20** |
| ⛔ **covered by no toggle** | 15 routes | ⛔ **55** |

**51 of 106 covered; 55 not.** The uncovered 55 are `/risk-analysis` (13),
`/scenario-analysis` (7), `/financial-forecasts` (7), `/prescience-ai` (5),
`/twin` (5), `/brief` (4), `/simulation` (4), `/my-axiom` (3) and seven singles.

⛔ **More than half the product sits outside the four toggles.** ⭐ That is not
an error in the ruling — **it is the ruling's consequence made visible**, and it
is the number the ruling has to be checked against: *is `/risk-analysis` meant to
be always-on, or does it belong to a fifth thing?*

## ⛔ AND THE ONE ATTRIBUTION THE CODE DOES CARRY IS WRONG IN 3 OF 11

`gen-nav-index.py` assigns a section by **carrying the last heading forward**
(line 89, `section = "WORKSPACE"` then overwritten on each heading). Three links
that sit after EXECUTE without their own heading inherit it:

| destination | section it carries | what it is |
|---|---|---|
| `/course` | ⛔ **EXECUTE** | the learning workspace |
| `/my-axiom` | ⛔ **EXECUTE** | the personal home |
| `/what-is-axiom` | ⛔ **EXECUTE** | ⛔ **a marketing explainer** |

⭐⭐ **A toggle built on this field would hide "What is AXIOM?" from a customer
who turned EXECUTE off** — the page that explains the product, removed by a
switch about project delivery. **The field looks like the answer and is 27%
wrong** (§III.18: a plausible wrong attribution is more dangerous than an absent
one), which is exactly why the assignment above was authored rather than read
out of it.

---

# T1 · THE OPENAPI PATHS — 343 SERVED

Ownership derived by walking the app's route table to each endpoint's defining
module:

| | |
|---|---|
| **`services/api/accounts.py`** | ⛔ **177 paths — 52% of the product in one module** |
| `modules/intelligence` | 25 |
| `modules/financials` | 22 |
| 31 further modules | 119 |

⛔ **Module structure cannot carry the toggles either.** A single file serving
half the paths spans all four; there is no boundary to switch on.

## ⭐ THE PATH MAP, MEASURED — AND WHY THE FIRST NUMBERS WERE WRONG

Attribution is by **transitive import closure** from each route file — every
API path literal reachable from the page, not just the ones written in it (the
route files themselves contain only 1–12 literals each; the calls live in
components).

⛔ **The first run over-counted badly**, because every page imports the app
shell and inherits auth, billing and platform paths:

| | raw | ⭐ net of shell |
|---|---|---|
| internal feedback | 48 | **21** |
| STRATEGIZE | 50 | **23** |
| EXECUTE | 57 | **30** |
| ANALYZE | 68 | **41** |
| ⛔ **STRATEGIZE ∩ EXECUTE** | **37 — "74% coupled"** | ⭐ **10** |

⭐⭐ **"STRATEGIZE and EXECUTE share 74% of their paths" was a measurement of the
page layout, not of the modules** (§III.22 — a census on a proxy). The shell
baseline is the 27 paths reachable from `/about` and `/login`, pages that belong
to no module; subtracting it leaves what the toggle would actually govern.

**Union net: 86 of 343 served paths.** ⛔ **257 paths — 75% — are reached from no
toggled page at all**, consistent with §III.28's 280-of-342.

---

# T2 · ⛔⭐⭐ STRATEGIZE AND EXECUTE ARE NOT INDEPENDENT, AND THE SHARED SET NAMES WHY

Net of shell, they share **exactly ten paths**, and the ten are not incidental:

```
/companies/{id}/objectives                      /companies/{id}/kpis
/companies/{id}/objectives/{key}                /companies/{id}/kpis/{kpi_id}
/companies/{id}/objectives/{key}/key-results    /companies/{id}/kpi-variance
/companies/{id}/objectives/{key}/initiatives    /companies/{id}/key-results/{kr_id}
/companies/{id}/initiatives                     /companies/{id}/people/detail
```

⭐⭐ **That is the OKR spine, entire.** objective → key result → KPI →
initiative. **STRATEGIZE writes it and EXECUTE reads it**, so the dependency is
not a wiring accident that could be refactored away — **it is the product's
central claim.** The five-hop chain this session just measured at 9 of 9 runs
straight through all ten.

⛔ **So EXECUTE without STRATEGIZE is a PMO with no objectives to serve** —
initiatives that trace to nothing, which is precisely the thing the repositioning
lane says AXIOM exists to prevent. ⭐ **STRATEGIZE without EXECUTE is coherent**:
plans you do not yet deliver against. **The dependency is one-directional**, and
a warning that treats it as symmetric would be wrong in one of its two forms.

⭐ **STRATEGIZE's 6 exclusive paths are all `intelligence/`** — frontier,
optimal-range, optimize, recommendations, target-state, optimization/unified.
**Turning STRATEGIZE off removes the solver, not the plan.**

---

# ⛔ WHAT T1 EXPOSES THAT THE RULING HAS TO ANSWER

1. ⛔⭐⭐ **`external feedback` toggles nothing.** 0 destinations, 0 paths, no
   register, no route. **It is a toggle for a module that does not exist** — and
   shipping it would put a switch in front of a customer that changes nothing
   they can see.
2. ⛔ **55 of 106 destinations belong to no toggle**, including the whole risk,
   scenario and forecasting surface. Always-on, or a fifth module?
3. ⛔ **`/cei` and `/stakeholder-engagement` are BOTH internal feedback, and
   `/cei` is not in the sidebar at all** — 15 destinations reachable only by
   search or a link. A toggle governing a surface with no nav entry is invisible
   in both states.
4. ⛔ **There is nothing to attach a toggle to.** No module field exists on either
   side. **T3–T5 cannot be built until the mapping above is ruled**, because they
   would each encode my authored assignment as if it were the product's.

⛔ **T3, T4 and T5 are NOT started**, per *"REPORT FIRST"*. The dependency
warning (T3) has its content — one-directional, EXECUTE needs STRATEGIZE, and
the ten shared paths are the reason — but it has no toggle to warn about yet.
