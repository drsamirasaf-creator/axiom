# Consolidating twenty tabs into a dense structure

4 August 2026. **Report, then build.** Heads: backend `b2b0b24`, frontend `b24c951`.

---

## 1 · The strip, measured at six widths

Current surface, six tabs, `/profitability`:

| viewport | strip width | rows | tab content |
|---|---|---|---|
| 1920 px | 1216 px | **1** | 707 px |
| 1600 px | 1216 px | **1** | 707 px |
| 1400 px | 1080 px | **1** | 707 px |
| 1280 px | 960 px | **1** | 707 px |
| **1024 px** | **704 px** | **2** | 707 px |
| 768 px | 448 px | **2** | 707 px |

⭐⭐ **The break is between 1280 and 1024, and it is arithmetic, not taste:** at
1024 the strip is allotted **704 px** and the six tabs need **707**. Three
pixels.

**Capacity per row, derived from the same measurement** (≈118 px average tab):

| viewport | tabs that fit on one row |
|---|---|
| 1400 px | ~9 |
| 1280 px | ~8 |
| 1024 px | **~5** |

⭐ **So the ceiling is six** — matching today's behaviour exactly: one row on a
laptop, two on a narrow window. Twenty tabs would need **3.3 rows at 1400 px**.

**A second level is not needed at six.** Dashboard carries two levels
(`RouteTabs` + inner tabs) and is the precedent if the count ever grows, but
introducing one now would add a click to reach every panel in exchange for
nothing measurable.

## 2 · The consolidation — grouped by the reader's question

| Tab | The question | Absorbs |
|---|---|---|
| **Overview** | *What is true now?* | Overview ×2, Executive Insights ×2 (already renders above the strip as derived findings) |
| **Lines** | *Where does it come from, and by what cut?* | Segments · Product Lines · Segment Profitability · Product Profitability · **Customer Profitability** — **five tabs into one, plus a dimension selector** |
| **What Changed** | *What moved, and why?* | Margin Bridge · Variance Analysis ×2 · mix shift · margin trend |
| **Contribution** | *Does it cover its costs, and what leaves if it goes?* | Contribution · Cost Structure · **avoidability** · the §22 corrective |
| **Cost** | *How is shared cost charged, and what constrains us?* | Cost Allocation · Capacity & Cost-to-Serve |
| **Data Quality** | *Can I trust it, and what is missing?* | Data Quality & Reconciliation ×2 · the coverage statement · every declared absence |

**Six tabs. Nothing dropped.**

⭐⭐ **The Lines consolidation is the one that earns the structure.** Segments,
Product Lines and Customers are *the same capability over `dimension_type`* —
a column, not three code paths. A **selector** (product · segment · customer)
replaces five tabs, and a dimension with no data simply does not appear in it.

### ⭐ What a reader loses — stated, not defended

1. **Side-by-side dimensions.** With a selector, product and segment cannot be
   seen at once. ⭐ This loss is *aligned* with an existing ruling — `reconcile_
   across` refuses to combine dimension types without an `ax_dimension_map`
   row, because they are parallel decompositions of one revenue — but a reader
   who wanted to *look* at both is now switching.
2. **Executive Insights has no URL.** Findings lead the page rather than living
   at a destination; a reader who wants only the findings cannot link to them.
3. **The Cost tab is dense.** Allocation methods, grades, sensitivity, capacity
   and consumption in one place means scrolling past machinery to reach a grade.
4. **Two different comparisons share What Changed.** Variance is plan-versus-
   actual; mix shift is period-versus-period. Sections must be labelled
   explicitly or a reader will conflate them.

## 3 · What does not render, and why

Per the omission ruling — **no placeholders, no coming-soon**:

| Not rendered | Why |
|---|---|
| **Pipeline & Backlog** | zero files in `services/api` mention it |
| **Pricing** (Intelligence, Pricing & Margin) | prices are the deliberate absence; the capability declines |
| **Dimensional Forecasts / Scenarios** | the machinery exists at **company** grain only |
| **Customer Profitability** | absorbed into Lines' selector — it appears when the customer axis is seeded, not before |

⭐ A tab that opens onto "coming soon" teaches a reader that the others might be
empty too. The capability arrives with its tier or not at all.

## 4 · Cost Allocation stays — ruled

A later addendum omits it. **It ships, and the allocation vocabulary — method,
grade, prose assumption — is the module's differentiation.** Removing a working
capability because a document omits it is following the document over the
product.
