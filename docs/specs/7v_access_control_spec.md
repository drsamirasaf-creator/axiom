# §7v — GRANULAR ACCESS CONTROL & INFORMATION PROTECTION
## Draft for founder ruling · 31 July 2026

Not locked until it is in the ledger.

**Origin.** Management may class business planning, valuation, initiatives and
KPI data as strategic secrets. Today's model is member / viewer / assessor, and
"viewer" is a single undifferentiated tier. A departmental viewer and a board
member see the same thing.

---

## 0. THE DISTINCTION THAT SHAPES THE WHOLE DESIGN

**Two problems are being asked about, and they are not the same problem.**

| | Solvable? | By what |
|---|---|---|
| **Who can reach the data** | **Yes, completely** | Server-side grants |
| **What they do once they can read it** | **No** | Deterrence and forensics only |

A person who can see a screen can photograph it, retype it, or describe it on a
call. **No permission system prevents that, and any vendor claiming otherwise is
lying.** Digital rights management on a web app is theatre; it stops the honest
and inconveniences everyone.

**So the architecture is four layers, and only the first is prevention:**

1. **Minimise** — deny by default, grant narrowly. The only true control.
2. **Attribute** — every view and export traceable to a named person and moment.
3. **Detect** — surface abnormal access patterns to the administrator.
4. **Revoke** — instantly, including live sessions and outstanding links.

**Say this to clients plainly.** A CFO who is told "we prevent leaks" and then
suffers one has been misled twice. A CFO who is told "we minimise exposure and
make any leak attributable to a named person" has been given something true,
and attribution is the mechanism that actually changes behaviour — people do not
leak what they know traces back to them.

---

## 1. THE MODEL: GRANTS, NOT ROLES

**Permission is a grant on a triple:**

```
(user, surface, scope)
```

- **Surface** — which tab or section.
- **Scope** — which slice of it: whole company, one department, own department
  only. A department head seeing their own function's OKRs is a different grant
  from seeing all of them, and the current model cannot express that.

**Roles are presets over grants, not a separate mechanism.** Roles ossify — the
first client who wants "board member, but also the operations cockpit" breaks a
pure role model. Presets solve the administration problem; grants remain the
truth.

### Grantable surfaces

| Surface | Typical sensitivity |
|---|---|
| Financial statements | High |
| Ratios & performance | High |
| Valuation & enterprise optimisation | Highest |
| Business planning & forecasting | Highest |
| Risk, viability & distress | High |
| Assumptions registry (§7u) | High — view separate from edit |
| Objectives & key results | Medium |
| KPIs | Medium |
| Initiatives & execution cockpit | Medium |
| Organisational structure | Low |
| Assessment results | Medium — plus anonymity floor |
| Documents & proposals | Medium |
| Innovation Hub | Low |
| Reports & exports | **Separate grant — see §3** |

---

## 2. DENY BY DEFAULT — THE SINGLE MOST IMPORTANT RULING

**Grants are additive from nothing. Never subtractive from an "all" baseline.**

This is not a preference. **You are mid-build with at least four surfaces
shipping — §7r ratios, §7m cockpit, §7s priorities, §7u assumptions.**

- Under a **subtractive** model, the day §7r ships, every existing viewer can see
  full financial ratios and the ROIC–WACC spread. Nobody granted it. Nobody was
  asked. It appears because it was not yet excluded.
- Under an **additive** model, it appears for nobody until someone grants it.

A new tab is the highest-risk moment in a permission system's life, and it
happens repeatedly over the next two quarters.

**Corollary: a new surface ships with zero grants and an administrator
notification.** Not an automatic assignment to any preset — the preset would
carry the same defect one level up.

---

## 3. THE DERIVATION LEAK — THE HARDEST PART

**Tab-level grants leak through composite surfaces**, and this is where the
design will fail if it fails.

Grant someone OKRs but not Financials. Then:

- A key result reads *"grow EBITDA margin from 14.2% to 18%"* — they now have
  your margin.
- An initiative in the cockpit carries a value-at-stake in currency — they have
  a valuation input.
- The executive brief cites expected value impact — they have the model's output.
- Evidence-derived SWOT cites financial signals with figures attached.
- Drill-down from department → objective → key result → the KPI's underlying
  ratio walks straight into the financials.

**Ruling: grants are enforced at field level on composite surfaces, not only at
tab level. A surface the user may see DEGRADES rather than leaks.**

Without the financial grant, the same key result renders as *"grow EBITDA margin
to target"* — progress percentage visible, absolute figures suppressed. The
objective remains meaningful; the number does not travel.

**And drill-down stops at the grant boundary.** Not a silent dead end — an
explicit *"further detail requires access you do not have."* Silent truncation
teaches people the data is absent; an honest boundary teaches them it is
restricted, which is the correct signal and reduces the workaround-seeking that
follows confusion.

**Every field on every surface carries a sensitivity classification.** This is
real work and it is the work that makes the feature true rather than nominal.

---

## 4. VIEW ≠ EXPORT

**Separate grants.** Most material loss is bulk, not observation — a PDF or CSV
leaves the building, a screen does not.

Someone may hold: view financials, no export. View OKRs, export OKRs. The
combination is common and today is inexpressible.

**Export covers:** PDF and presentation reports, CSV export, print, secure-link
share, and the API if a client has one.

**Print is an export.** Browsers cannot be prevented from printing, so the
control is that print-rendered output carries the same watermark and generates
the same audit entry as any other export. The document that leaves is marked.

---

## 5. ATTRIBUTION — WHAT MAKES THE UNPREVENTABLE COSTLY

**Every export carries the recipient's identity, the timestamp, and the
company — visibly, on every page.** Not a footer in grey 6pt. A leaked document
whose watermark can be cropped is an unwatermarked document.

**On-screen, a subtle persistent identity mark** on the high-sensitivity surfaces.
Enough that a photograph carries it. Light enough not to degrade reading.

**Full audit log, immutable, versioned via §P1:** who viewed which surface when,
every export with its parameters, every grant change with before and after,
every secure link created, followed and expired.

**The administrator sees this.** A leak investigation that requires a support
ticket to AXIOM is not a capability the client has.

---

## 6. DETECTION — FLAG, DO NOT BLOCK

Blocking on heuristics produces false positives that destroy trust in the tool.
**Surface to the administrator; let a human judge.**

Worth flagging: bulk export beyond a threshold; breadth of surfaces touched in one
session against that user's own baseline; first-ever access to a high-sensitivity
surface; access outside established hours for that user; a spike immediately
following a status change — **the resignation signal is the one clients most want
and least expect**, and it is trivially derivable if HR status is known.

Baselines are per-user, not global. "Unusual for this person" catches what
"unusual in general" does not.

---

## 7. REVOCATION

**Instant and total.** Grants revoked terminates live sessions, invalidates
outstanding secure links created by that user, and takes effect before the next
request completes.

**Offboarding is one action, not fourteen.** The administrator revokes a person,
not each grant — a partial offboarding is a full one that failed silently.

**Secure links are the hole in the current design.** Today "shareable by secure
link" bypasses the grant model entirely — an unauthenticated URL is a permission
grant to anyone who receives it. Ruling: **links inherit their creator's grants,
carry a mandatory expiry, are revocable individually, log every access, and
cannot be created by a user without the export grant on that surface.**

---

## 8. INTERACTIONS

**Assessment anonymity is unaffected and must stay that way.** The k-anonymity
floor and complement suppression are not permissions and cannot be granted
around. **No grant, including administrator, exposes an individual's assessment
responses.** An administrator who can turn off anonymity has an instrument that
was never anonymous.

**§7u assumptions: view and edit are separate grants.** Editing changes the
valuation; viewing is the audit trail behind numbers people have been shown.

**§7m cockpit** carries named accountability by design — that is the point of it,
and it is a reason to grant it narrowly rather than a reason to anonymise it.

**Tier 2 partner staff** accessing a client CID hold grants like anyone else,
issued by the client's administrator. **On transfer to client admin, all partner
grants terminate by default** and must be re-issued if the relationship
continues. Silent persistence after transfer is the worst possible default.

**Seat model:** grants are a property of the viewer seat, not an additional
charge. A 5-viewer client can shape those five precisely. Selling granularity per
seat would price clients out of the safe configuration.

---

## 9. PRESETS TO SHIP WITH

Starting points, all editable. **Every one of them additive from nothing.**

| Preset | Grants |
|---|---|
| **CXO** | All surfaces, company scope, export |
| **CFO / Finance** | Financials, ratios, valuation, planning, risk, assumptions (view), export |
| **Board / Adviser** | Valuation, risk, ratios, reports. **No operational detail, no assessment raw** |
| **Operating lead** | OKRs, KPIs, initiatives, org — **own department scope**. No financials, no export |
| **Department viewer** | OKRs and initiatives, own department, no export |
| **Assessor** | No surfaces. Assessment participation only, via private link |

**The Operating lead preset is the answer to the question as asked** — the
disgruntled-employee case. Departmental scope, no absolute financials, no export.
They can do their job and cannot take the strategy out of the building.

---

## ROUTING

**→ CLAUDE CODE**, without qualification. Every element is server-side: grant
resolution at the data layer, field-level suppression, export gating, watermark
injection, audit logging, session termination.

**Enforce at the query, not the route.** A hidden nav item with a live API
endpoint behind it is not access control — it is a UI preference that a browser
console removes.

**Sequencing:** depends on §P1 for audit and grant versioning. Should land
**before or with §7r**, because §7r is the first genuinely sensitive surface
shipping into an additive model that does not yet exist.

---

## OUTSTANDING

| # | Item | Default |
|---|---|---|
| 1 | Additive vs subtractive | **Additive. Deny by default.** New surfaces ship with zero grants |
| 2 | Field-level suppression on composite surfaces | Required — tab-level alone leaks |
| 3 | View / export as separate grants | Yes |
| 4 | Watermark prominence | Visible on every page; croppable = absent |
| 5 | Detection | Flag to administrator, never block |
| 6 | Secure links | Inherit creator's grants, expire, revocable, logged |
| 7 | Assessment anonymity | Not grantable around, by anyone |
| 8 | Partner grants on transfer | Terminate by default |
| 9 | Priced per seat? | No — pricing the safe configuration is a bad incentive |
