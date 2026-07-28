"""ONE number formatter for the board pack. Both artifacts import from here.

⭐ WHY THIS MODULE EXISTS. The PDF (`report_pdf.py`) and the PPTX
(`reporting.py`) render the SAME `board_report()` payload, and each had its own
money formatter. They disagreed:

    payload 4.07   ->  PDF "$4.1M"   PPTX "$4M"
    payload 82.64  ->  PDF "$82.6M"  PPTX "$83M"
    payload 17.5   ->  PDF "$17.5M"  PPTX "$18M"

A board reads both documents. The percent formatters were duplicated too and
happened to agree, which is not a safer state — it is the same defect one edit
away. The currency-symbol map was duplicated a third time, and those already
differed: the PDF knew JPY, CHF, CAD and AUD; the PPTX rendered them with no
symbol at all.

⭐ TWO DEFINITIONS IN AGREEMENT IS NOT ONE DEFINITION. Agreement is a property of
today's text, not of the design. So `_big`, `_fmt`, `_pc` and the second symbol
map are deleted rather than aligned, and both modules call these.

⭐ PRECISION IS TWO DECIMALS, TO MATCH THE SCREEN. §7.31 requires identical
presentation across every financial surface, and the frontend's canonical
`formatMoneyM` renders `$4.07M`. The PDF's one decimal and the PPTX's zero both
disagreed with the product a customer had just been looking at. Zero decimals was
also destroying information outright — 3.6, 4.0 and 4.4 all rendered "$4M", the
same collapse `shortMoney` produced on Scenario Analysis.

⭐ THE TIERS AND THE NEGATIVE CONVENTION NOW MATCH THE SCREEN EXACTLY.
`formatWithCode` in the frontend switches on the ACTUAL amount — 1e9 -> B,
1e6 -> M, 1e3 -> k — and writes the sign BEFORE the symbol ("-$4.40M"). This
module receives millions, so the same boundaries are 1000 / 1 / 0.001, and the
sign moved: it used to emit "$-4.40M", which is a third spelling of the same
figure.

Inputs are CANONICAL MILLIONS, as the board_report payload supplies them.
"""

# The board pack's currency symbols. One map; the PPTX's inline copy knew only
# three codes and rendered the rest bare.
CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
    "CHF": "CHF ", "CAD": "$", "AUD": "$",
}

DASH = "—"
MONEY_DECIMALS = 2
PERCENT_DECIMALS = 1


def currency_symbol(code) -> str:
    """Symbol for a currency code; the bare code with a space when unknown, so an
    unrecognised currency is still legible rather than silently unlabelled."""
    c = (code or "").upper()
    return CURRENCY_SYMBOLS.get(c, (c + " ") if c else "")


def money(x, sym: str = "") -> str:
    """A money figure in CANONICAL MILLIONS -> display string.

    Tier boundaries are the frontend's, restated in millions: the screen switches
    at 1e9 / 1e6 / 1e3 on the ACTUAL amount, which is 1000 / 1 / 0.001 here. Two
    decimals throughout, so figures a reader must tell apart stay apart.

    ⭐ SIGN BEFORE SYMBOL. `-$4.40M`, as the screen writes it. This emitted
    `$-4.40M`, which is the same number in a third spelling."""
    if x is None:
        return DASH
    a = abs(x)
    sign = "-" if x < 0 else ""
    if a >= 1000:                      # >= 1e9 actual
        body = f"{a/1000:,.{MONEY_DECIMALS}f}B"
    elif a >= 1:                       # >= 1e6 actual
        body = f"{a:,.{MONEY_DECIMALS}f}M"
    elif a >= 0.001:                   # >= 1e3 actual
        body = f"{a*1000:,.{MONEY_DECIMALS}f}k"
    else:                              # sub-thousand, plain
        body = f"{a*1_000_000:,.{MONEY_DECIMALS}f}"
    return f"{sign}{sym}{body}"


def percent(x, d: int = PERCENT_DECIMALS) -> str:
    """A ratio (0.134) -> '13.4%'. The input is a RATIO, never an already-scaled
    percentage — passing 13.4 here yields '1340.0%', which is the failure mode
    worth remembering."""
    if x is None:
        return DASH
    return f"{x*100:.{d}f}%"


def number(x, d: int = 2) -> str:
    """A plain number — ratios, multiples, counts. No unit, no symbol."""
    if x is None:
        return DASH
    return f"{x:,.{d}f}"


def kpi_value(k: dict, sym: str = "") -> str:
    """Format one KPI strip entry BY ITS DECLARED FORMAT.

    ⭐ THE SELECTION IS THE RISK, NOT THE FORMATTING. A margin of 0.134 rendered
    as money reads '$0.13M'; a $0.13M figure rendered as a percent reads '13.4%'.
    Both are plausible on the page and wrong by orders of magnitude, and neither
    looks like an error to anyone who does not already know the answer. So the
    mapping is defined once, here, rather than inline in each renderer.

    Unknown or missing formats fall through to money, which is what the PDF's
    original ternary did — preserved deliberately so this refactor changes no
    output, only where the decision lives."""
    fmt = (k or {}).get("format")
    v = (k or {}).get("current")
    if fmt == "percent":
        return percent(v)
    if fmt == "ratio":
        return number(v, 3)
    return money(v, sym)


def plan_value(statement: dict, key: str, kind: str):
    """The plan figure for a statement line.

    `kind == "stoch"` reads the stochastic block's `plan`; anything else reads the
    deterministic block. Getting this backwards swaps a planned figure for a
    modelled one — same magnitude, same units, no visible symptom."""
    if kind == "stoch":
        return statement["stochastic"][key]["plan"]
    return statement["deterministic"][key]


SCORE_DECIMALS = 1


def score(v, d: int = SCORE_DECIMALS) -> str:
    """A SCORE — health components, risk-heat-map cells, KPI scores.

    ⭐ A SEPARATE NAMED FUNCTION, NOT A REUSE OF `money`. These are points on a
    scale, not currency: no symbol, no k/M/B tier, and rescaling one as though it
    were millions would be nonsense. They are given their own name so nobody has
    to decide at the call site, and so a later change to money's precision cannot
    silently move every chart label.

    It was five spellings across the chart callers — `chart_bars`'s
    `fmt="{:,.1f}"` default plus a `fmt="{:.1f}"` passed at one site — which is
    the same duplication that let the PDF and PPTX money formatters drift."""
    if v is None:
        return DASH
    return f"{v:,.{d}f}"
