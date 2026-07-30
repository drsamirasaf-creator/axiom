# → LOVABLE — `/free-pilot` PUBLIC PAGE
## Paste this whole block. 31 July 2026

Build a new public route `/free-pilot`. No authentication. Not in the app shell —
this is a marketing page, reachable from the site and from a direct link, and it
must render correctly for someone who has never seen AXIOM.

---

## DESIGN TOKENS — match the capabilities brochure exactly

```
--forest:   #123528   (header bar, dark cards, CTA block)
--forest-2: #1b4936   (borders inside dark cards)
--emerald:  #2f6b52   (italic accent in headlines)
--brass:    #a5823a   (eyebrows, step numbers, bullets)
--brass-lt: #c2a15f   (brass on dark backgrounds)
--sage:     #8fb3a1   (muted text on dark)
--cream:    #f4f0e4   (page background)
--card:     #fffefb   (light card background)
--ink:      #1c1c19   (headings)
--body:     #3d3d37   (body text)
--rule:     #d8d2c1   (dividers, card borders)
```

**Type.** Headings in a transitional serif (Charter, Caladea or Georgia
fallback), regular weight, with a key phrase in *italic emerald* — the brochure
pattern. Body in a humanist sans. Eyebrows and step labels in uppercase sans at
~7pt with `letter-spacing: .24em` in brass.

**Feel.** Editorial, not SaaS. Generous whitespace, thin rules, no gradients, no
drop shadows, no rounded-corner cards beyond 2px, no icons from an icon set. The
brochure is the reference — if it looks like a startup landing page, it is wrong.

---

## PAGE STRUCTURE

### 1 · Header bar
Full-bleed forest bar, ~72px. AXIOM logo left (use the existing white
transparent asset, ~30px tall). Right: `THE FREE PILOT` in sage, uppercase,
letter-spaced.

### 2 · Hero
Eyebrow, brass: `AXIOM FREE PILOT`

Headline, serif:
> We build it. *You judge it.*

Lede, max 5in wide:
> AXIOM's team sets up your company on the platform — your financials, your
> organisation, your assessment cycle, your reports — before you pay anything.
> Your executives review a working model of your own firm, not a canned demo.
> Nothing is watered down: the pilot runs the full engine.

### 3 · Video explainer
Full-width within the content column, max 46rem, 16:9, centred. Sits **after the
hero and before the seven steps.**

- **Embed via `youtube-nocookie.com`**, not `youtube.com`. Privacy-enhanced mode,
  no tracking cookie until play.
- **`rel=0`, no autoplay, no sound on load.** Autoplay on a CFO's laptop in an
  open-plan office is a close-tab event.
- **Lazy-load below the fold** so the embed never delays first paint.
- **Poster frame with a visible play control.** Not a bare iframe.
- Caption beneath, small, muted: *"Three minutes on how the pilot runs."*
  Adjust to the real runtime — an inaccurate duration is a small lie that costs
  more trust than it saves.
- **If the video fails to load, the page must be complete without it.** No empty
  black rectangle, no layout shift — the container collapses.

**The seven steps below stay in full.** The video does not replace them.
Most CFOs will not watch it: they will scan, and the text has to carry the whole
offer on its own. Treat the video as the version for people who prefer watching,
never as the primary channel.

> **One thing to decide before you shoot.** If the video shows the interface, it
> is wrong the moment §7r ships and wrong again at §7m — you will be re-shooting
> inside a quarter. A video about the *motion* — we load your data, your people
> assess, you review a model of your own firm, you decide — ages far better and
> is the thing this page is actually selling. Product footage belongs in a demo
> video that you expect to redo.

### 4 · The seven steps
Seven cards in a row on desktop, two columns on tablet, stacked on mobile.
Each: brass `STEP N` label, serif bold title, one sentence.

| | Title | Body |
|---|---|---|
| 1 | Scope | One call to agree which entity we model and which cycle we run. |
| 2 | We load | Statements, plan and organisation — handled for you, not homework. |
| 3 | Calibrate | Ratios, valuation, risk and forecasts computed on your own numbers. |
| 4 | Assess | Private links to the executives you choose. No accounts, no passwords. |
| 5 | Reports | Valuation, assessment and recommendations, ready to read. |
| 6 | Review | Walked through live with your leadership team. |
| 7 | Transfer | If you buy, the workspace moves to you complete. |

### 5 · What we need from you
Three light cards. Honest about effort — this is the section that decides
whether a CFO starts.

- **Your numbers.** Three to five years of statements, and your plan if you have
  one. One structured template, or your own export and we map it.
- **Your organisation.** Departments, heads and reporting lines. A list is fine.
- **Two hours of your executives' time.** The assessment is per person and takes
  about twenty minutes. Nothing else is asked of them.

### 6 · What happens to your data — ABOVE THE FORM, NOT IN A FOOTER
Dark forest card. **This placement is deliberate and must not be moved.** A CFO
handing over statements and letting us survey their leadership will ask, and the
answer arriving before the form is worth more than the answer being generous.

> **Your data, and what becomes of it**
>
> The pilot runs on your real financials and real answers from your named
> executives. That is not a demo dataset, and we treat it accordingly.
>
> - Every upload is versioned and the original file stays downloadable by you.
> - Assessment responses are protected by a minimum-respondent floor. No
>   individual is identifiable to anyone, including us.
> - **If you decide not to proceed, your workspace is frozen rather than
>   deleted** — access closed, data retained for twelve months, restored intact
>   if you come back within that window.
> - Deletion on written request, at any time, no conditions.

### 7 · The form
Single column, max 30rem. Labels above fields. No placeholder-only labels.

- Company name — required
- Your name — required
- Work email — required
- Phone — optional
- Country / jurisdiction — required, free text
- How many companies would you like modelled? — select: 1 / 2–4 / 5+
- Partner code — optional, with helper text: *"If a partner introduced you,
  enter their code so they are credited."*
- Anything we should know? — textarea, optional
- Consent checkbox — required, unticked by default:
  *"I'm happy for AXIOM to contact me about this pilot."*

Submit: `Request a pilot`. Brass outline button, forest fill on hover.

**Success state:** replace the form in place — do not navigate away.
> **Received.** We'll be in touch within two working days to arrange the scoping
> call. Nothing happens to your data until we've spoken.

**Error state:** inline, specific, above the field. Never a generic banner.

### 8 · Closing CTA
Forest block, centred.
> See your company as a *working model.*
> No cost, no commitment, no watered-down demo.

Footer bar matching the brochure: `AXIOM · Enterprise Optimization, Certified`
left, `axiomdynamics.app · support@axiomdynamics.app` right.

---

## ENTRY POINTS — build these too

The page is worthless if it is reachable only by direct link.

**Primary — main landing page.**
- Nav bar: `Free Pilot`, styled as the one brass-outlined item so it reads as
  the action rather than another section.
- Hero: secondary CTA beside the existing primary. `Request a free pilot`.
- One mid-page band, after whatever the landing page uses to establish
  credibility. Not more than these three — a CTA repeated five times reads as
  desperation to the audience this is aimed at.

**Highest-value and currently missing — inside the Meridian demo.**
Someone exploring the sample company is the warmest traffic AXIOM has, and today
there is nothing there to convert them. Add a persistent, quiet strip — not a
modal, not a popup:

> *You are looking at Meridian, our sample company.* **See this built on your
> own numbers →**

Anchored to the viewport bottom or sitting in the demo banner if one exists.
Dismissible, and it stays dismissed for the session.

**Brochure.** Page 9 already says *"Explore the sample company, or request a free
pilot."* In any web or PDF-with-links version, that phrase links here.

**Where NOT to put it.** Not inside an authenticated customer workspace — a
paying client seeing a free-pilot CTA is a jarring experience, and partner-held
CIDs would show it to a partner's client, which crosses a channel boundary.

---

## WHAT NOT TO BUILD

- **No countdown timers, no "3 pilot slots remaining", no fake urgency.** The
  audience is CFOs and boards; manufactured scarcity reads as amateur and costs
  more credibility than it buys.
- **No testimonials, no client logos, no case studies.** We have none to show and
  inventing them is not an option.
- **No pricing on this page.** The pilot is free; introducing $4,995 before the
  scoping call loses people who would have converted after seeing their own
  model.
- **No chat widget.**
- **Do not claim any capability.** This page sells the motion, not the feature
  set. The brochure sells features and is a separate document.

---

## HANDOFF NOTE — WHERE THIS STOPS

**Build the page and the form UI. Post to `POST /api/pilot-request` and render
whatever the endpoint returns.**

Do not implement the endpoint, and do not implement partner-code handling beyond
capturing the string and passing it through. Attribution is a contract —
first-touch capture, the 180-day window, and the rule that a code cannot be
applied retroactively all live server-side and belong to the Claude Code lane.
A partner code validated or attributed in the browser is a partner code that can
be edited in the browser.
