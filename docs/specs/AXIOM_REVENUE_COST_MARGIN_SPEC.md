---
title: AXIOM Revenue, Cost & Profitability Intelligence Engine
source: AXIOM_Revenue_Cost_Profitability_Intelligence_SPEC.docx
committed: 2026-08-07
status: authoritative scope for Revenue Growth, Cost Structure, Profit Margins
---

**AXIOM**

**REVENUE, COST & PROFITABILITY\
INTELLIGENCE ENGINE**

*Claude Master Development Specification*

**Tabs Covered**

1\. Revenue Growth

2\. Cost Structure

3\. Profit Margins

# CLAUDE MASTER DEVELOPMENT SPECIFICATION

## AXIOM Revenue, Cost & Profitability Intelligence Engine

Develop the following three tabs as a single integrated analytical
architecture inside AXIOM: Revenue Growth, Cost Structure, and Profit
Margins.

  -----------------------------------------------------------------------
  **Core Architecture**\
  REVENUE ENGINE → COST-TO-SERVE ENGINE → MARGIN ENGINE → OPTIMAL
  ECONOMIC MIX → MANAGEMENT ACTIONS → FORECASTED ENTERPRISE IMPACT
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

These tabs must not behave as isolated dashboards. They must
collectively explain what changed, why it changed, whether the change is
economically desirable, what is likely to happen next, what hidden
structural forces are driving it, what management should do, and what
would happen if management acted.

The standard is deliberately high: a CEO, CFO, COO, or CMO should
experience analysis comparable to a sophisticated FP&A team, pricing
team, data-science function, and strategy consulting engagement
combined. The output must be decision intelligence, not chartware.

# PART I --- OVERARCHING DESIGN PRINCIPLES

## 1. No Data = No Fabricated Analysis

These three tabs require detailed customer-supplied operating data.
AXIOM must never invent detailed product, segment, customer, channel,
geographic, unit-volume, price, or cost data from consolidated financial
statements unless a mathematically defensible derivation exists.

If the required detailed customer data has not been uploaded, display a
clear blank-state message:

  -----------------------------------------------------------------------
  **Data Required**\
  Detailed revenue and cost data have not yet been provided for this
  analysis.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

-   Required datasets

-   Most recent upload date, if any

-   Data completeness %

-   Missing fields

-   Download Excel Template

-   Upload Data

-   Mapping Status

For the Meridian demonstration environment, create complete, realistic
demonstration data so that every capability described below is
functional and visually compelling.

## 2. Common Data Grain

The ideal analytical grain should support: Period × Legal Entity ×
Business Unit × Segment × Product Line × Product/SKU × Geography ×
Channel × Customer/Customer Group.

Do not force every customer to provide every dimension. AXIOM must
dynamically operate at the dimensional depth actually available. If a
client supplies only Segment, Product Line, and Month, analyze those
dimensions. If another client supplies Segment, Product, Geography,
Customer, Channel, and Week, perform a deeper analysis.

## 3. Time Granularity

-   Annual

-   Quarterly

-   Monthly

-   Weekly where available

-   Daily where appropriate

Minimum useful historical series: 12 months = limited; 24 months =
acceptable; 36 months = strong; 60+ months = preferred.

Forecast horizons should support the remaining current fiscal year, next
4 quarters, next 12 months, next 24 months, next 36 months, and longer
strategic forecasts where available.

## 4. Common Customer Data Template

Extend the AXIOM Excel input template. The customer should provide
underlying business observations; AXIOM performs the calculations and
modeling.

### Input Tab A --- Revenue Detail

-   Period

-   Legal Entity

-   Business Unit

-   Department, where applicable

-   Segment

-   Product Line

-   Product/SKU

-   Customer

-   Customer Group

-   Geography

-   Country

-   Channel

-   Salesperson/Account Owner, optional

-   Units Sold

-   Gross Revenue

-   Discounts

-   Rebates

-   Returns

-   Other Revenue Adjustments

-   Net Revenue

-   List Price

-   Average Selling Price

-   Contracted Price, optional

-   Currency

-   FX Rate

-   New/Existing Customer Flag

-   New/Existing Product Flag

-   Recurring/Nonrecurring Revenue Flag

-   Contract Start Date

-   Contract End Date

-   Customer Acquisition Date, optional

### Input Tab B --- Direct Cost Detail

-   Period

-   Segment

-   Product Line

-   Product/SKU

-   Units

-   Direct Material Cost

-   Direct Labor Cost

-   Freight

-   Logistics

-   Packaging

-   Royalties

-   Sales Commission

-   Payment Processing

-   Warranty

-   Returns Cost

-   Third-Party Service Cost

-   Cloud/Hosting Usage Cost

-   Other Direct Variable Cost

-   Other Direct Fixed Cost

-   Total Direct Cost

### Input Tab C --- Operating Expense Detail

-   Period

-   Cost Center

-   Department

-   Expense Category

-   Expense Subcategory

-   Vendor, optional

-   Fixed/Variable/Semi-Variable Classification, if known

-   Amount

-   Currency

-   Allocation Driver, optional

-   Segment Allocation, if known

-   Product Allocation, if known

-   Geography Allocation, if known

Typical expense categories include Sales, Marketing, R&D, G&A, IT, HR,
Facilities, Logistics, Customer Support, Professional Services,
Insurance, Legal, Finance, and Other.

### Input Tab D --- Cost Drivers

-   Production Units

-   Machine Hours

-   Labor Hours

-   Orders

-   Shipments

-   Customers Served

-   Transactions

-   Sales Calls

-   Support Tickets

-   Employees

-   Floor Area

-   Server Usage

-   API Calls

-   Delivery Miles

-   Warehouse Movements

-   Procurement Orders

-   Purchase Volume

-   Number of Products

-   Number of SKUs

-   Custom driver

### Input Tab E --- Capacity

-   Product

-   Product Line

-   Facility

-   Maximum Capacity

-   Practical Capacity

-   Current Utilization

-   Bottleneck Capacity

-   Lead Time

-   Minimum Production Quantity

-   Inventory Availability

### Input Tab F --- Revenue Forecast

-   Forecast Period

-   Segment

-   Product Line

-   Product

-   Geography

-   Channel

-   Customer Group

-   Forecast Units

-   Forecast Price

-   Forecast Revenue

-   Probability/Confidence

-   Forecast Scenario

-   Forecast Version

### Input Tab G --- Cost Forecast

-   Forecast unit costs

-   Variable costs

-   Fixed costs

-   Departmental operating expenses

-   Cost drivers

-   Inflation assumptions

-   Labor rates

-   Material prices

-   Freight assumptions

-   Vendor costs

## 5. Common Reconciliation Requirement

All detailed revenue and cost analyses must reconcile to AXIOM's core
financial statements. Reconciliation must be automatic and visible.

*Detailed Revenue Dataset ± Mapping Adjustments ± Unallocated Revenue ±
Eliminations = Income Statement Revenue*

*Revenue − Detailed COGS ± Cost Allocation/Reconciliation Items = Income
Statement Gross Profit*

*Gross Profit − Operating Expenses = Income Statement Operating Profit*

*Operating Profit ± Non-Operating Items − Interest − Tax = Net Income*

Display Reconciliation Status using GREEN = reconciles, AMBER =
immaterial variance within configured threshold, RED = material
variance, GRAY = insufficient data. No profitability analysis should be
presented as fully reliable where material reconciliation differences
exist.

# PART II --- TAB 1: REVENUE GROWTH

## 6. Purpose

The Revenue Growth tab must explain the economic anatomy of growth, not
merely report that revenue increased or decreased.

-   Where growth came from

-   Whether growth is high quality

-   Whether growth is accelerating or decelerating

-   Whether growth is price-led or volume-led

-   Whether growth comes from economically desirable products

-   Whether revenue mix is improving

-   Whether growth is profitable

-   Whether growth is sustainable

-   Whether one part of the company is masking deterioration elsewhere

-   Which revenue pools are emerging

-   Which revenue pools are losing relevance

-   What the future mix is likely to become

-   What the economically optimal mix should be

## 7. Top Executive Strip

Display approximately 8--10 decision-critical metrics, with deeper
detail below.

-   Revenue

-   YoY Growth

-   QoQ Growth

-   YTD Growth

-   Organic Growth

-   Forecast FY Growth

-   Growth Acceleration

-   Revenue Concentration

-   Mix Quality Score

-   Revenue at Risk

## 8. Basic Growth Calculations

*YoY Growth: g_YoY,t = R_t / R\_(t−1) − 1*

*QoQ Growth: g_QoQ,t = R_q / R\_(q−1) − 1*

*YTD Growth: sum(Current YTD Revenue) / sum(Prior-Year Comparable YTD
Revenue) − 1*

Also calculate seasonally adjusted QoQ where adequate history exists,
CAGR over 2/3/5 years and custom windows, and rolling 3-, 6-, and
12-month growth.

## 9. Growth Quality Decomposition

Decompose revenue growth where data permits into Price Effect, Volume
Effect, Mix Effect, FX Effect, Acquisition Effect, New Product Effect,
Product Discontinuation Effect, New Customer Effect, Existing Customer
Effect, and Channel Effect.

  -----------------------------------------------------------------------
  **Revenue Growth Bridge**\
  Prior Revenue + Price + Volume + Product Mix + Customer Mix + Channel
  Mix + Geographic Mix + New Products − Lost Products + FX +
  Acquisitions/Divestitures = Current Revenue
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

Use a waterfall chart with drill-down to the underlying hierarchy.

## 10. First Derivative --- Revenue Velocity

*V_R(t) = dR/dt*

Calculate at Enterprise, Segment, Product Line, Product, Geography,
Channel, and Customer Group levels. Identify positive growth, negative
growth, inflection, plateau, expansion, and contraction.

## 11. Second Derivative --- Revenue Acceleration

*A_R(t) = d²R/dt²*

Interpret the four economic states: revenue growing + accelerating =
strong expansion; revenue growing + decelerating = hidden warning;
revenue declining + decline decelerating = possible recovery; revenue
declining + decline accelerating = structural deterioration.

Create a Revenue Momentum Matrix with X-axis = Growth, Y-axis = Growth
Acceleration. Plot segments, products, geographies, and channels. Bubble
size = revenue; optional color = margin attractiveness.

## 12. Revenue Mix Analysis

*Mix_i,t = Revenue_i,t / Total Revenue_t*

Calculate current mix, prior-period mix, YoY mix change, QoQ mix change,
forecast mix, and long-term mix trend.

## 13. First Derivative of Mix

*dMix_i/dt*

This identifies the velocity of revenue-share migration. Example
insight: Enterprise Software represents 27.4% of revenue, but its share
has increased by an average 82 bps per quarter over the last six
quarters.

## 14. Second Derivative of Mix

*d²Mix_i/dt²*

Use this to determine whether mix migration itself is accelerating or
decelerating. Example: a product line may still be only 18% of revenue
but be gaining share at twice its historical rate.

## 15. Mix-Shift Attractiveness

Never treat increasing revenue share as automatically positive.
Cross-reference every mix shift against gross margin, contribution
margin, operating margin, incremental margin, cost-to-serve, capacity
requirements, customer acquisition economics, risk, working-capital
requirements, strategic value, and growth durability.

-   GREEN --- share is migrating toward economically superior business

-   AMBER --- share is increasing but economic contribution is ambiguous

-   RED --- share is migrating toward structurally inferior economics

  -----------------------------------------------------------------------
  **Required Insight Standard**\
  Revenue mix shifted 5.2 percentage points toward Product Group C. This
  increased reported revenue growth by 3.1 percentage points but reduced
  portfolio gross margin by approximately 120 bps because Product Group C
  generates materially lower gross margin than the displaced mix.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 16. Revenue Concentration

*HHI = Σ s_i²*

Calculate HHI across products, customers, segments, regions, and
channels, together with Top 1, Top 3, Top 5, Top 10, and Top 20
concentration. Determine whether growth is broad-based, moderately
concentrated, highly concentrated, or dependent on one
customer/product/channel.

## 17. Growth Breadth Index

*GBI = Σ w_i × I(g_i \> 0)*

Enhance the index by incorporating magnitude, persistence, margin, and
acceleration. Use it to distinguish healthy growth from fragile growth
dominated by a few sources.

## 18. Revenue Persistence

Estimate how persistent growth historically has been using
autoregressive coefficients, survival/hazard analysis, state-space
models, regime switching, and Bayesian persistence models where
justified. Classify streams as persistent, cyclical, episodic, volatile,
deteriorating, or emerging.

## 19. Structural Break Detection

Use change-point detection to identify when historical revenue
relationships changed. Candidate techniques include Bayesian Change
Point Detection, PELT, CUSUM, Bai-Perron-style structural break
analysis, and regime-switching models. Explain what changed, where, and
why it matters.

## 20. Forecasting Engine

Do not depend on a single model. Create a model-competition and ensemble
framework.

### Candidate Models

-   ETS

-   Holt-Winters

-   ARIMA

-   SARIMA

-   ARIMAX

-   VAR/VECM where appropriate

-   ANFIS

-   Gradient boosting

-   Random forest

-   XGBoost/LightGBM if available

-   Neural networks

-   State-space models

-   Dynamic regression

-   Bayesian structural time series

-   Regime-switching models

Use hierarchical forecasting so Product → Product Line → Segment →
Enterprise forecasts remain mathematically reconciled. Support
bottom-up, top-down, middle-out, and optimal reconciliation/MinT-type
logic where suitable.

Validate with rolling-origin backtesting using MAE, RMSE, MAPE, sMAPE,
WAPE, MASE, and Bias. Select either the best model or a weighted
ensemble at each hierarchy.

## 21. ANFIS

Use Adaptive Neuro-Fuzzy Inference Systems only where data
characteristics justify it. Candidate inputs include historical revenue,
price, units, marketing spend, channel mix, seasonality, macro
variables, customer counts, cost variables, and capacity. Require
sufficient observations, backtesting, benchmark comparison, and
performance validation. If ANFIS does not outperform simpler methods, do
not use it as the primary model.

## 22. Dynamic Product Portfolio Optimization (DPP)

Implement DPP explicitly as AXIOM's Dynamic Product Portfolio
Optimization Engine. Depending on the problem, use dynamic programming,
stochastic dynamic programming, constrained nonlinear optimization,
mixed-integer optimization, revenue-management optimization, or dynamic
assortment optimization.

*maximize E\[Revenue(x) − Variable Costs(x) − Incremental Fixed
Costs(x)\] − λ Risk(x)*

Subject to demand, production capacity, sales capacity, supply
constraints, resource availability, customer commitments, strategic
minimums, channel constraints, inventory, working capital, risk
tolerance, regulatory constraints, and pricing restrictions.

  -----------------------------------------------------------------------
  **Optimization Question**\
  What revenue mix creates the greatest risk-adjusted economic
  contribution given actual company constraints?
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 23. Current Mix vs Forecast Mix vs Optimal Mix

Create a signature AXIOM comparison table with Component, Current Mix,
Forecast Mix, Optimal Mix, and Gap. Include revenue, gross profit,
contribution, operating profit, capacity consumption, and risk. Prefer a
feasible optimal range where a single point would create false
precision.

## 24. Revenue Quality Score

Create a 0--100 composite score with transparent decomposition.
Candidate components: growth rate, acceleration, breadth, persistence,
diversification, margin quality, forecast confidence, recurring nature,
customer retention, price realization, concentration risk, cash
conversion, and cost-to-serve.

## 25. Revenue Growth Attribution Tree

Provide interactive drill-down: Enterprise Revenue Growth → Segment →
Product Line → Product → Geography → Channel → Customer. At every node
show Revenue, Growth, Acceleration, Mix Change, Gross Margin,
Incremental Margin, and Contribution to Enterprise Growth. No visual
should be a dead end.

## 26. Revenue Insight Engine

Generate approximately 3--7 high-value insights. Generic commentary is
unacceptable.

  -----------------------------------------------------------------------
  **Required Standard**\
  Although revenue increased 8.7%, only 41% of the portfolio generated
  positive growth. Approximately 63% of incremental revenue came from
  Product Line B, whose contribution margin is 9.2 percentage points
  below the portfolio average. Revenue growth is therefore stronger than
  economic growth; holding current mix trajectories constant, AXIOM
  estimates approximately 110--150 bps of gross-margin compression over
  the next four quarters.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 27. Revenue Management Questions

-   What are YoY, QoQ, YTD, CAGR, organic, price-adjusted, and volume
    growth?

-   Where is growth coming from?

-   Which products are gaining or losing share?

-   Is mix shift accelerating?

-   Is growth becoming more or less profitable?

-   Is growth concentrated?

-   Is pricing supporting growth?

-   Are customers becoming more expensive to serve?

-   Where is revenue heading?

-   What is forecast confidence?

-   What structural breaks exist?

-   Which segments are near inflection points?

-   Is forecast mix economically optimal?

-   What mix should management target?

-   What revenue is being sacrificed by resource constraints?

-   What low-quality revenue should management reconsider?

# PART III --- TAB 2: COST STRUCTURE

## 28. Purpose

The Cost Structure tab must explain what the company is economically
consuming to produce revenue and profit. Analyze cost level,
composition, behavior, drivers, migration, fixed/variable structure,
scalability, diseconomies, operating leverage, anomalies, structural
inflation, hidden cost pools, and cost-to-serve differences.

## 29. Top Executive Strip

-   Total Operating Cost

-   Cost Growth

-   Cost/Revenue

-   Variable Cost Ratio

-   Fixed Cost Ratio

-   Cost Inflation

-   Cost Efficiency Change

-   Operating Leverage

-   Cost Structure Score

-   Addressable Cost Opportunity

## 30. Cost Taxonomy

### Financial Classification

-   COGS

-   SG&A

-   R&D

-   Other operating costs

### Economic Classification

-   Fixed

-   Variable

-   Semi-variable

-   Step-fixed

### Functional Classification

-   Procurement

-   Manufacturing

-   Distribution

-   Sales

-   Marketing

-   Customer Support

-   IT

-   HR

-   Finance

-   Legal

-   Administration

### Controllability

-   Controllable

-   Partially controllable

-   Committed

-   Contractual

-   Regulatory

### Value Relationship

-   Value creating

-   Necessary support

-   Discretionary

-   Potentially avoidable

-   Non-value-adding

Do not automatically label overhead as waste.

## 31. Cost Mix

*CostMix_i,t = Cost_i,t / Total Cost_t*

Show current mix, historical mix, change, forecast mix, and structural
trend.

## 32. First and Second Derivative of Cost Mix

*dCostMix_i/dt*

*d²CostMix_i/dt²*

Identify cost pools gaining organizational weight and determine whether
the shift is strategic investment, inefficient scaling, temporary, or
structural.

## 33. Cost Growth vs Revenue Growth

*Elasticity_i = %Δ Cost_i / %Δ Revenue*

Interpret \<0 as inverse, 0--1 as slower than revenue, ≈1 as
proportional, and \>1 as faster than revenue. Track rolling elasticity.

  -----------------------------------------------------------------------
  **Example**\
  Revenue grew 12%, but customer-support cost grew 27%, producing cost
  elasticity of 2.25. Ticket volume rose only 8%, suggesting the increase
  is not explained by customer activity alone.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 34. Cost Function Estimation

*C = α + βQ + ε*

*C = α + β₁Q + β₂Q² + β₃X₃ + ... + ε*

Estimate fixed cost, marginal cost, nonlinear scale effects, step costs,
capacity thresholds, and diseconomies of scale using regression, robust
regression, piecewise regression, splines, quantile regression, and
machine learning where justified.

## 35. Cost Curvature

*Marginal Cost = dC/dQ*

*Cost Curvature = d²C/dQ²*

Detect improving economies, diminishing economies, diseconomies, and
capacity stress.

  -----------------------------------------------------------------------
  **Required Insight Standard**\
  Unit logistics costs remain below last year, but AXIOM detects positive
  cost curvature beyond approximately 86% warehouse utilization. Current
  forecast utilization reaches 91%, implying future cost growth is likely
  to accelerate even without further unit-price inflation.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 36. Activity-Based Costing

Where cost drivers are available, allocate cost based on orders,
transactions, machine hours, service calls, shipments, labor hours,
customers, deliveries, and other drivers. Calculate cost-to-serve by
Product, Customer, Segment, Geography, and Channel.

## 37. Machine-Learning Activity-Based Costing

Where sufficient observations exist, augment traditional ABC with
machine learning to estimate nonlinear relationships between resource
consumption, activities, output, customer characteristics, and product
complexity. Candidate models: Random Forest, Gradient Boosting, Neural
Networks, GAM, Elastic Net. Use explainability methods to identify which
drivers actually explain cost behavior.

## 38. Cost Driver Attribution

For each material cost change, attribute the movement to Volume,
Price/Inflation, Labor Rate, Efficiency, Mix, Utilization, Complexity,
Geography, Supplier, FX, Headcount, and Structural Change.

  -----------------------------------------------------------------------
  **Cost Bridge**\
  Prior Cost + Volume + Wage/Price Inflation + Product Mix + Operational
  Efficiency + Capacity + FX + Structural Additions + One-Off Items =
  Current Cost
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 39. Cost Inflation vs Cost Inefficiency

Distinguish external cost pressure from internal inefficiency. If raw
material costs rise 14% while benchmark inflation explains 11%, volume
explains 2%, and mix explains 1%, AXIOM should not label management
performance as deteriorating. Conversely, if cost rises 14% while
benchmark inflation is only 4% and volume is 2%, investigate the
residual.

## 40. Fixed-Cost Absorption

-   Revenue per fixed-cost dollar

-   Gross profit per fixed-cost dollar

-   Fixed-cost absorption

-   Break-even revenue

-   Capacity utilization

-   Margin of safety

Identify whether revenue growth is generating operating leverage.

## 41. Cost Concentration

Calculate category, vendor, geographic, department, and cost-driver
concentration. Flag single-vendor dependency, rapidly increasing vendor
exposure, and excessive cost concentration.

## 42. R/A/G Cost Engine

RAG must be contextual. Cost increase does not automatically mean Red.
Evaluate revenue growth, output growth, inflation, investment program,
unit economics, strategic necessity, forecast, benchmark, and margin.

  -----------------------------------------------------------------------
  **Example**\
  Cost rises 20%, but revenue rises 40% and unit cost falls 14%. Status
  should be GREEN, not RED.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 43. Cost Opportunity Engine

Estimate addressable opportunities across structural cost, productivity,
procurement, complexity reduction, capacity, channel migration,
automation, and working capital. Distinguish genuine cost reduction from
value destruction masquerading as cost reduction. Estimate likely
effects on revenue, quality, customer retention, project delivery, and
strategic capability.

## 44. Cost-to-Serve Matrix

Plot Revenue on X-axis and Cost-to-Serve on Y-axis. Bubble =
customer/product/segment. Overlay margin, growth, and strategic
importance. Identify high-revenue/low-cost, high-revenue/high-cost,
low-revenue/high-cost, and low-revenue/low-cost populations. Every
bubble must be clickable.

## 45. Cost Anomaly Detection

Use robust z-scores, isolation forest, change-point detection, seasonal
decomposition, and residual analysis. Identify unusual vendor payments,
department spikes, cost patterns inconsistent with volume, sudden step
changes, and unusual unit costs. Never imply fraud without evidence; use
language such as: "Cost behavior is statistically unusual relative to
historical operating drivers and merits review."

## 46. Cost Structure Insight Engine

Generate 3--7 high-value observations that explain the economic
mechanism behind the number.

  -----------------------------------------------------------------------
  **Example 1**\
  Distribution cost per unit fell 4.8%, which appears favorable. However,
  the improvement is entirely attributable to mix shifting toward
  high-density urban routes. On like-for-like routes, cost per delivery
  increased approximately 6.3%. The reported efficiency improvement
  therefore overstates underlying operational progress.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Example 2**\
  Corporate technology expense has increased 26% over two years, but
  approximately 71% of the increase is associated with transaction volume
  and automation projects that displaced an estimated \$4.2M of labor
  cost. AXIOM therefore classifies the increase as economically
  constructive rather than cost deterioration.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

# PART IV --- TAB 3: PROFIT MARGINS

## 47. Purpose

The Profit Margins tab must answer where the company's economic profit
actually comes from, why it is changing, and how management should
reshape the business to improve it. It should function as a Profit
Architecture Engine, not as a margin chart.

## 48. Financial Statement Reconciliation

*Gross Margin = (Revenue − COGS) / Revenue*

*Operating Margin = Operating Income / Revenue*

*Net Margin = Net Income / Revenue*

Also calculate EBITDA margin, EBIT margin, Contribution margin where
data permits, and Incremental margin. Enterprise-level numbers must
reconcile exactly to AXIOM's financial statements.

## 49. Segment and Product Profitability

For every dimension with sufficient data calculate Revenue, Gross
Profit, Gross Margin, Contribution Profit, Contribution Margin,
Allocated Operating Profit, Operating Margin, Net Profit where
defensibly allocable, and Net Margin.

Analyze Segment, Product Line, Product/SKU, Geography, Channel, and
Customer/Customer Group. Clearly distinguish directly measured costs
from allocated costs and avoid false precision at product/customer
net-profit level.

## 50. Profit Pool

*ProfitShare_i = Profit_i / Total Profit*

Compare Revenue Share versus Profit Share. Example: Product Line A
produces 19% of revenue but 38% of operating profit.

## 51. Profit Contribution Map

Create a matrix with X-axis = Revenue Growth, Y-axis = Margin, Bubble =
Revenue or Profit Contribution.

-   High Growth / High Margin --- Scale Aggressively

-   Low Growth / High Margin --- Protect / Reignite

-   High Growth / Low Margin --- Fix Economics Before Scaling

-   Low Growth / Low Margin --- Restructure / Harvest / Exit

Do not automatically recommend exiting strategically necessary products.

## 52. Price--Volume--Mix--Cost Profit Bridge

Decompose change in profit into Price, Volume, Product Mix, Customer
Mix, Channel Mix, Geography Mix, Variable Cost, Fixed Cost, FX,
Acquisitions, and One-Offs.

  -----------------------------------------------------------------------
  **Profit Bridge**\
  Prior Profit + Price Effect + Volume Effect + Mix Effect + Variable
  Cost Effect + Fixed Cost Effect + Other Effects = Current Profit
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 53. Margin Bridge

  -----------------------------------------------------------------------
  **Gross Margin Bridge**\
  Prior Gross Margin + Price + Product Mix + Customer Mix + Direct
  Material + Labor + Freight + Other = Current Gross Margin
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

Then bridge Gross Margin to Operating Margin through operating expense
effects, and Operating Margin to Net Margin through interest, tax, and
non-operating effects.

## 54. Margin Mix Effect

Separate Within-Component Margin Change from Portfolio Mix Change. This
distinction is crucial.

  -----------------------------------------------------------------------
  **Example A**\
  No major product line experienced material gross-margin deterioration.
  The company's 90-bp margin decline is primarily a portfolio-composition
  problem: faster growth occurred in lower-margin products.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Example B**\
  Mix improved by approximately 40 bps, masking approximately 150 bps of
  underlying margin deterioration within the company's largest segment.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 55. Incremental Margin

*Incremental Margin = Δ Profit / Δ Revenue*

Calculate for Gross Profit, EBITDA, Operating Profit, and Contribution
Profit. Highlight when incremental economics differ materially from the
average reported margin.

## 56. Margin Velocity and Acceleration

*dMargin/dt*

*d²Margin/dt²*

Identify expanding and accelerating, expanding but decelerating,
contracting but stabilizing, and contracting and accelerating states.

## 57. Margin Dispersion

Average margin can hide extreme heterogeneity. Calculate mean, median,
standard deviation, weighted dispersion, and percentile ranges across
products, customers, segments, channels, and geographies.

  -----------------------------------------------------------------------
  **Example**\
  Enterprise gross margin is stable at 34%, but margin dispersion across
  products has increased 42% during the last year. The aggregate result
  increasingly depends on a smaller group of high-margin products
  offsetting a growing low-margin tail.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 58. Customer Profitability

*Customer Contribution = Revenue − Product Cost − Logistics −
Commissions − Service/Support − Returns − Rebates − Customer-Specific
Costs*

Identify high-revenue but value-destroying customers, strategically
important loss leaders, highly profitable overlooked customers, and
customers with deteriorating cost-to-serve. Do not equate revenue
ranking with customer value.

## 59. Margin Concentration

Calculate the percentage of profit from top 5 products, top 10
customers, largest segment, and largest region. Calculate HHI for profit
pools. Use this to reveal earnings vulnerability.

## 60. Profitability Frontier

Create a distinctive visualization with X-axis = Growth, Y-axis =
Contribution Margin, bubble size = Revenue, and additional markers for
strategic importance/risk. Overlay an estimated Efficient Profitability
Frontier. Identify businesses economically dominated by alternatives
without automatically recommending elimination.

## 61. Shapley-Style Profit Attribution

Where multiple simultaneous factors drive profit movement, support
Shapley-value-style decomposition across Price, Volume, Product Mix,
Customer Mix, Cost, Channel, Geography, and FX. Present a user-friendly
explanation while retaining a mathematically rigorous backend.

## 62. Margin at Risk

Estimate profitability exposure under volume shock, price compression,
raw-material inflation, wage inflation, customer loss, product-mix
migration, channel migration, FX movement, capacity constraint, and
supplier disruption. Calculate EBITDA at Risk, Gross Profit at Risk, and
Operating Margin at Risk using scenario analysis, sensitivity analysis,
and Monte Carlo where appropriate.

## 63. Margin Elasticity

*ε_M,x = %Δ Margin / %Δ x*

Estimate margin elasticity to price, volume, material cost, wage,
freight, and mix. Tell management which levers matter most.

## 64. Margin Sensitivity Tornado

Generate a ranked tornado chart showing sensitivity to ASP, volume,
product mix, customer mix, direct material, labor, logistics,
commissions, fixed costs, and FX.

## 65. Economic Mix Optimization

This is where all three tabs converge. For each product define expected
demand, price, revenue, variable cost, contribution, capacity
consumption, fixed-cost requirement, working-capital requirement,
strategic requirement, and risk.

*maximize E\[Profit(x)\] − λ Risk(x)*

Subject to real business constraints. Output Current Mix, Management
Forecast Mix, AXIOM Optimal Mix, and Feasible Optimal Range.

## 66. Optimal Mix Must Not Mean Highest Margin

A high-margin product may have limited demand, higher acquisition cost,
high capital intensity, poor retention, capacity limits, greater risk,
or strategic constraints. Optimize the enterprise system, not one
metric.

*maximize \[Operating Profit + α Strategic Value − β Risk − γ Capital
Consumption\]*

## 67. Mix Gap

*MixGap_i = OptimalMix_i − ForecastMix_i*

*Opportunity_i ≈ MixGap_i × Revenue Base × Incremental Contribution_i*

Estimate opportunity only within feasible constraints and show a range
rather than false precision.

## 68. Profit Quality

Create a transparent Profit Quality Score using margin level, margin
stability, margin acceleration, diversification, recurring contribution,
pricing power, low cost-to-serve, cash conversion, concentration, and
downside resilience.

## 69. Key Takeaway Engine

The largest design requirement is that AXIOM must never use an obvious
observation as the principal takeaway. A seven-level insight chain
should define the standard:

1.  Observation --- what moved?

2.  Decomposition --- which components explain it?

3.  Diagnosis --- what operating factor caused it?

4.  Economic Explanation --- why does that factor affect economics?

5.  Forward Consequence --- what happens if the trend persists?

6.  Management Intervention --- what can management change?

7.  Quantified Impact --- what is the estimated financial effect?

  -----------------------------------------------------------------------
  **Example**\
  Gross margin declined 200 bps. 120 bps came from mix. Mix shifted
  toward Product C. Product C carries lower contribution because service
  cost is materially higher. Forecast mix implies another 80 bps of
  compression. Redirecting a portion of incremental volume to Product B
  could reduce compression while preserving most revenue growth.
  Estimated EBITDA impact: \$X--\$Y.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

# PART V --- CROSS-TAB INTELLIGENCE

## 70. The Three Tabs Must Talk to Each Other

Every Revenue Growth insight must query Cost Structure and Profit
Margins. Every Cost Structure insight must query Revenue, volume,
product mix, and margin. Every Profit Margin insight must query revenue
drivers, costs, mix, and operating leverage. Contradictory conclusions
are not acceptable.

## 71. Common Economic Causal Graph

-   Price → Volume → Revenue

-   Product Mix → Revenue → Direct Cost → Gross Margin

-   Customer Mix → Revenue → Cost-to-Serve → Contribution Margin

-   Volume → Capacity Utilization → Unit Cost

-   Capacity Utilization → Marginal Cost

-   Fixed Cost → Operating Leverage

-   Revenue Growth → Cost Growth → Incremental Margin

## 72. Cross-Tab Insight Examples

  -----------------------------------------------------------------------
  **Example 1**\
  Revenue growth accelerated to 11.8%, but the incremental operating
  margin fell to 4.7% versus the company's 13.2% average. Approximately
  72% of incremental revenue is coming from products whose cost-to-serve
  exceeds the portfolio median. AXIOM therefore classifies recent growth
  acceleration as economically low quality.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Example 2**\
  Gross margin appears stable at 31.6%. However, favorable product mix
  contributed approximately +90 bps while underlying unit-cost
  deterioration contributed −86 bps. Current margins therefore conceal
  weakening production economics.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Example 3**\
  Operating expenses increased 14%, apparently exceeding revenue growth
  of 9%. However, approximately \$6.1M of additional technology spending
  displaced an estimated \$4.8M of recurring manual operating cost and
  supports forecast revenue capacity approximately 18% above the current
  run rate. AXIOM therefore does not classify the increase as general
  cost deterioration.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Example 4**\
  Product A has the highest gross margin, but Product B creates greater
  incremental enterprise value because it requires materially less
  working capital and constrained production resource per dollar of
  contribution. The optimal growth mix therefore favors Product B despite
  its lower reported gross margin.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

# PART VI --- VISUAL DESIGN

## 73. Common Page Architecture

-   Row 1 --- Executive KPI strip

-   Row 2 --- Primary analytical visualization

-   Row 3 --- Economic decomposition

-   Row 4 --- Mix/portfolio visualization

-   Row 5 --- Forecast/optimization

-   Row 6 --- AXIOM Intelligence

-   Row 7 --- Recommendations/actions

Avoid endless scrolling of random charts. Every row should answer a
management question.

## 74. R/A/G Logic

RAG must be contextual and model-driven. Never use "Revenue up = Green,"
"Cost up = Red," or "Margin down = Red." Evaluate target, forecast,
historical regime, benchmark if available, economic context, mix, risk,
and strategy.

Every RAG item must be clickable and show Status, Why, Primary Drivers,
Financial Impact, Forward Risk, Recommended Response, and supporting
evidence.

## 75. Click-Through Architecture

Clicking a segment, product, customer, cost category, margin, RAG
status, chart point, anomaly, or recommendation must open a contextual
side panel or drill-down showing: Metric, History, Decomposition,
Drivers, Related Metrics, Forecast, Risks, AXIOM Interpretation, and
Recommended Action.

# PART VII --- AXIOM INTELLIGENCE PANEL

## 76. Intelligence Block

Each page must end with an AXIOM Intelligence section containing 3--7
ranked insights. Each insight must include Finding, Why It Matters,
Evidence, Expected Forward Effect, Recommended Management Action,
Estimated Financial Impact, Confidence, and Related Analysis.

## 77. Insight Significance Score

Rank findings using financial materiality, strategic importance,
statistical strength, persistence, forward consequence, management
actionability, and confidence. Surface only the highest-value items by
default.

# PART VIII --- RECOMMENDATION ENGINE

## 78. Recommendation Classes

-   Revenue --- reprice, increase price, reduce discounting, redirect
    sales effort, accelerate segment, improve retention, change channel
    mix

-   Portfolio --- increase product exposure, constrain low-value growth,
    rationalize SKU, enter adjacent segment, rebalance portfolio

-   Cost --- renegotiate supplier, redesign process, automate,
    consolidate vendor, improve capacity, address diseconomies

-   Margin --- change mix, change price, reduce cost-to-serve, modify
    channel, restructure product

## 79. Recommendation Economics

For every major recommendation calculate, where possible: Revenue
Effect, Cost Effect, Gross Profit Effect, EBITDA Effect, Operating
Profit Effect, Cash Effect, Implementation Cost, Time to Impact,
Confidence, and Risk. Never recommend action solely from statistical
correlation.

# PART IX --- SCENARIO ENGINE

## 80. What-If Controls

Allow CXOs to manipulate Revenue Growth, Units, Price, Discounts,
Product Mix, Customer Mix, Cost Inflation, Wages, Material Cost,
Capacity, Fixed Cost, Marketing Spend, and FX. Update Revenue, Gross
Profit, EBITDA, Operating Profit, Net Income, Margins, Mix, Capacity
Utilization, Forecast, and Risk dynamically.

## 81. Scenarios

-   Management Forecast

-   Base

-   Upside

-   Downside

-   Stress

-   AXIOM Recommended

-   Custom

# PART X --- DATA QUALITY

## 82. Data Completeness Score

For each tab show data completeness, for example Revenue Data 98%, Cost
Data 87%, Margin Allocation Confidence 81%. Clicking the score must show
missing fields and affected analyses.

## 83. Analytical Confidence

Clearly distinguish Observed, Calculated, Allocated, Estimated,
Forecast, and Optimized values. Every model-generated or
allocation-dependent output must expose its confidence and basis.

# PART XI --- MERIDIAN DEMONSTRATION

## 84. Meridian Data

Populate sufficient synthetic data to demonstrate every major feature.

-   5 years of historical monthly data

-   Quarterly and annual rollups

-   3 major segments

-   8--12 product lines

-   20+ products

-   Multiple geographies

-   Multiple channels

-   Customer groups

-   Detailed price and volume

-   Product-level direct costs

-   Departmental operating expenses

-   Cost drivers

-   Capacity

-   24-month forecast

Deliberately embed interesting business dynamics: a high-growth
low-margin product, a declining high-margin legacy product, a rapidly
emerging high-margin product, one hidden cost problem, one misleading
aggregate margin trend, one customer concentration problem, one
favorable mix shift, one unfavorable forecast mix shift, and one
capacity constraint.

## 85. Meridian Demo Story

8.  Meridian appears to have strong topline growth.

9.  Revenue acceleration is genuine.

10. A disproportionate amount of growth comes from a lower-contribution
    product family.

11. Aggregate gross margin appears relatively stable.

12. That stability masks improving mix in one segment and deteriorating
    underlying cost economics in another.

13. One emerging product has both accelerating revenue share and
    superior incremental contribution.

14. The management forecast underweights this product.

15. Capacity/resource constraints explain some of the gap.

16. AXIOM's optimized mix identifies an alternative portfolio.

17. The proposed mix improves EBITDA meaningfully without requiring the
    same percentage increase in revenue.

  -----------------------------------------------------------------------
  **Conceptual Centerpiece**\
  The question is not how fast Meridian can grow revenue. The question is
  which revenue Meridian should grow.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

# PART XII --- TECHNICAL REQUIREMENTS

## 86. Backend Analytical Services

Do not calculate everything in the frontend. Create backend analytical
services such as:

-   RevenueAnalyticsEngine

-   RevenueForecastEngine

-   RevenueMixEngine

-   CostAnalyticsEngine

-   CostDriverEngine

-   MarginAnalyticsEngine

-   ProfitBridgeEngine

-   MixOptimizationEngine

-   ScenarioEngine

-   InsightEngine

-   ReconciliationEngine

## 87. Precomputation

Expensive operations should be computed server-side and cached
appropriately, including model estimation, optimization, Monte Carlo,
large decompositions, anomaly analysis, and hierarchical forecasts. Do
not recompute complex models whenever the user moves a cursor or opens a
tooltip.

## 88. Model Registry

-   Model ID

-   Model Type

-   Training Data

-   Period

-   Hierarchy

-   Parameters

-   Validation Results

-   Forecast Accuracy

-   Model Version

-   Execution Date

Maintain reproducibility and governance.

## 89. Baseline and Version Control

Every analysis must reference Data Version, Financial Statement Version,
Forecast Version, Cost Allocation Version, and Scenario Version so
management can reproduce historical results.

# PART XIII --- TESTING

## 90. Reconciliation Tests

-   Detailed revenue = financial statement revenue

-   Costs reconcile

-   Gross profit reconciles

-   Operating income reconciles

-   Net income reconciles

## 91. Mathematical Tests

-   YoY

-   QoQ

-   YTD

-   CAGR

-   Derivatives

-   Mix

-   Mix derivatives

-   Price-volume-mix

-   HHI

-   Elasticity

-   Incremental margin

-   Cost functions

-   Profit contribution

-   Bridges

-   Optimization constraints

## 92. Forecast Tests

-   No look-ahead bias

-   Train/test separation

-   Rolling backtest

-   Forecast reconciliation

-   Model fallback

-   Missing data handling

-   Sparse histories

## 93. Optimization Tests

-   Revenue reconciles

-   Capacity constraints respected

-   Demand constraints respected

-   Negative quantities prohibited

-   Strategic constraints respected

-   Cost linkage correct

-   Profit calculations correct

-   Infeasible solutions handled correctly

# PART XIV --- FINAL PRODUCT STANDARD

## 94. Success Standard

These three tabs fail if they merely answer whether revenue, costs, or
margins are rising or falling. They succeed only if they answer the
following questions:

  -----------------------------------------------------------------------
  **Revenue Growth**\
  What kind of revenue is growing, why, how quickly is composition
  changing, is the change economically attractive, and what should the
  future revenue portfolio look like?
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Cost Structure**\
  What economic activities are consuming resources, how is that structure
  evolving, what is really driving cost, and which apparent changes are
  structural, inefficient, or strategically constructive?
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **Profit Margins**\
  Where is profit actually coming from, what hidden forces are changing
  it, what does the aggregate margin conceal, and how can management
  reshape the portfolio to create materially more economic value?
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

## 95. Final AXIOM Design Principle

  -----------------------------------------------------------------------
  **AXIOM Economic Dissection Engine**\
  Revenue → Growth → Growth Quality → Mix → Cost-to-Serve → Contribution
  → Profitability → Forward Mix → Optimal Mix → Action
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------

The CXO should not finish the analysis merely knowing more. The CXO
should finish knowing what to do differently --- and AXIOM should
quantify why.
