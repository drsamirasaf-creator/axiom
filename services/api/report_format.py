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

KNOWN REMAINING DIVERGENCE FROM THE SCREEN, recorded rather than silently
carried: the frontend has a `k` tier below 1M (0.5M renders "$500.00k") and this
does not — it renders "$0.50M". Changing the tier boundary alters every small
figure in the board pack and is a presentation ruling, not a refactor, so it is
left alone and stated here.

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

    Two decimals, so figures a reader must tell apart stay apart. The B tier
    divides by 1000 because the input is already in millions."""
    if x is None:
        return DASH
    if abs(x) >= 1000:
        return f"{sym}{x/1000:,.{MONEY_DECIMALS}f}B"
    return f"{sym}{x:,.{MONEY_DECIMALS}f}M"


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
