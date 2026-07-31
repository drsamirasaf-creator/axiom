"""Period arithmetic — ONE definition, for every site that touches a period.

⭐ WHY IT MOVED OUT OF ingest.py. The decode/encode helpers were written there
for the upload validator, and `ingest` imports `engines`, so `engines` could not
reach them. Five other sites therefore kept doing integer `+1`:

    engines.auto_forecast   hist[-1] + k        -> 20225 after 20224
    router.py x2            hist_last + k, plan_last + k
    twin.engines            hist[-1] + k
    forecast_studio         hist[-1] + k

The validator rejected an impossible quarter on upload while the forecast path
GENERATED five of them. Fixing the validator and leaving the generators is what
made this a live defect rather than a caught one — so the logic lives here, where
everything can import it, and `ingest` re-exports for its existing callers.

⭐ THERE IS NO SECOND IMPLEMENTATION. Any site that needs the next period calls
`next_period` or `forecast_periods`. A site that writes `+ 1` is a defect.
"""

# ⭐ QUARTERLY PERIODS ARE NOT INTEGERS THAT COUNT BY ONE. They are YYYYQ — a
# packed (year, quarter) pair — and the succession rule has a carry:
#     20204 -> 20211   is CONSECUTIVE (+7 as an integer)
#     20205             does not exist; there is no fifth quarter
#
# The validator used to do `expected = last + 1` unconditionally. On a quarterly
# plan that REJECTED every correct year boundary and would have ACCEPTED an
# impossible 20205. It was latent only because quarterly forecast labels ship
# blank, so the path had never run.
#
# Decoding is done here, once, rather than at each comparison site, so annual and
# quarterly cannot drift apart the way the two halves of a duplicated rule do.

# ⭐ MONTHLY IS YYYYMM — SIX DIGITS, and that is what makes the three
# frequencies STRUCTURALLY DISTINGUISHABLE rather than a matter of trust:
#
#     2024      4 digits   annual
#     20241     5 digits   quarterly   (year, quarter)
#     202401    6 digits   monthly     (year, month)
#
# The encodings cannot collide, so `derive_frequency` below can read the data
# rather than believe a label. That property is why monthly uses YYYYMM and not,
# say, YYYYM — a five-digit 20241 would then mean both 2024 Q1 and 2024 Jan.
SUBPERIODS = {"annual": 1, "quarterly": 4, "monthly": 12}


def decode_period(value: int, frequency: str) -> tuple[int, int | None]:
    """YYYYQ -> (year, quarter); YYYYMM -> (year, month); YYYY -> (year, None)."""
    if frequency == "quarterly":
        year, q = divmod(int(value), 10)
        return year, q
    if frequency == "monthly":
        year, m = divmod(int(value), 100)
        return year, m
    return int(value), None


def period_is_valid(value: int, frequency: str) -> bool:
    year, q = decode_period(value, frequency)
    if not (1900 <= year <= 2200):
        return False
    if frequency == "quarterly":
        return q is not None and 1 <= q <= 4
    if frequency == "monthly":
        return q is not None and 1 <= q <= 12
    return True


def next_period(value: int, frequency: str) -> int:
    """The period that must follow `value`. Carries the year on Q4."""
    year, q = decode_period(value, frequency)
    if frequency == "quarterly":
        return (year + 1) * 10 + 1 if q == 4 else year * 10 + (q + 1)
    if frequency == "monthly":
        # ⭐ THE SAME CARRY, AT A DIFFERENT MODULUS. 202412 -> 202501, and
        # 202413 does not exist — the quarterly lesson at twelve instead of four.
        return (year + 1) * 100 + 1 if q == 12 else year * 100 + (q + 1)
    return year + 1


_MONTH_ABBR = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def format_period(value: int, frequency: str) -> str:
    year, q = decode_period(value, frequency)
    if frequency == "quarterly":
        return f"{year}Q{q}"
    if frequency == "monthly":
        return f"{_MONTH_ABBR[q]} {year}" if q and 1 <= q <= 12 else str(value)
    return str(year)


def advance(period: int, n: int, frequency: str) -> int:
    """The period `n` steps after `period`.

    ⭐ A COUNT IS NOT A PERIOD AND CANNOT BE ADDED TO ONE. `hist_last + hz` reads
    as "hz periods later" and is not: 20224 + 10 is 20234, which is 2023 Q4 —
    three quarters later, not ten. Correct for years by coincidence, because
    there the encoding and the count share a unit."""
    p = period
    for _ in range(max(0, int(n))):
        p = next_period(p, frequency)
    return p


def period_span(earlier: int, later: int, frequency: str) -> int:
    """How many periods separate two encoded periods. Negative if `later` precedes.

    ⭐ SUBTRACTION IS NOT A COUNT. `20244 - 20224` is 20; the true distance is 8
    quarters. The difference is right for annual and wrong for quarterly by a
    factor that varies with how many year boundaries the range crosses, so it
    produces a plausible number rather than an obviously broken one — which is
    how it survived from d3c70cb until a live 500.

    Walks rather than computing, so the rule lives in `next_period` alone."""
    if earlier == later:
        return 0
    if later < earlier:
        return -period_span(later, earlier, frequency)
    n, p = 0, earlier
    limit = 4000                       # ~1000 years; a runaway guard, never reached
    while p < later and n < limit:
        p = next_period(p, frequency)
        n += 1
    if p != later:
        # `later` is not on the lattice — an invalid quarter, say. Say so rather
        # than return a count that silently describes a different period.
        raise ValueError(f"{later} is not a valid {frequency} period after {earlier}")
    return n


def forecast_periods(last_historical: int, n: int, frequency: str) -> list[int]:
    """The `n` periods that follow `last_historical`, in that frequency.

    ⭐ THE ONE CALL EVERY FORECAST GENERATOR SHOULD MAKE. Written out, the
    integer form is `[last + k for k in range(1, n + 1)]`, which is right for
    years and produces Q5..Q9 for quarters. Chaining `next_period` carries the
    year instead."""
    out, p = [], last_historical
    for _ in range(max(0, int(n))):
        p = next_period(p, frequency)
        out.append(p)
    return out


def derive_frequency(values) -> str | None:
    """The frequency the PERIOD VALUES actually are, or None if undecidable.

    ⭐ FREQUENCY IS DERIVED, NOT TRUSTED. A stored label is metadata and can be
    wrong; the encoded values are the data. Because the three encodings differ in
    DIGIT COUNT and cannot collide, this is a reading rather than a guess.

    Returns None for an empty or mixed set rather than picking one — a dataset
    whose periods are not all the same shape has no single frequency, and
    choosing the majority would silently discard the rest.
    """
    widths = {len(str(int(v))) for v in (values or []) if str(v).strip().lstrip("-").isdigit()}
    if not widths or len(widths) > 1:
        return None
    return {4: "annual", 5: "quarterly", 6: "monthly"}.get(next(iter(widths)))


def period_ordinal(value: int) -> float:
    """A comparable position in time for a period of ANY frequency.

    ⭐ COMPARING ENCODINGS NUMERICALLY IS INVALID ACROSS FREQUENCIES, and the
    failure is silent. A quarterly 20243 is numerically SMALLER than a monthly
    202401, so `max()` over a mixed series returns the wrong period and reports a
    stale figure as the newest one. Found by the mixed-series test, not by
    reading.

    Returns years-with-fraction: 2024 -> 2024.0, 2024Q3 -> 2024.5, Mar 2024 ->
    2024.1667. Comparable across all three.
    """
    f = derive_frequency([value])
    if f is None:
        return float("-inf")
    year, sub = decode_period(int(value), f)
    if sub is None:
        return float(year)
    return float(year) + (sub - 1) / SUBPERIODS[f]


def newest_period(values):
    """The latest period in a possibly MIXED set, or None."""
    cands = [v for v in (values or []) if derive_frequency([v]) is not None]
    return max(cands, key=period_ordinal) if cands else None


def frequency_check(data: dict) -> dict:
    """Declared against derived. ⭐ REPORTED, NEVER SILENTLY RECONCILED.

    A label disagreeing with its own periods is a live inconsistency, and this
    codebase already carries the consequence of choosing wrongly between annual
    and quarterly rates — measured at 4.66x. Adding a third frequency without a
    check would widen exactly that.
    """
    periods = (data or {}).get("periods", {}) or {}
    declared = periods.get("frequency")
    values = list(periods.get("historical") or []) + list(periods.get("forecast") or [])
    derived = derive_frequency(values)
    return {"declared": declared, "derived": derived,
            "effective": derived or declared or "annual",
            "agree": (derived is None or declared is None
                      or derived == declared),
            "reason": (None if (derived is None or declared is None
                                or derived == declared)
                       else f"declared {declared!r} but the period values are "
                            f"{derived!r}")}


def frequency_of(data: dict) -> str:
    """The frequency to COMPUTE with.

    ⭐ CHANGED 31 Jul: this returns the DERIVED frequency where the values decide
    it, falling back to the declaration only when they cannot. The previous
    docstring said frequency is "a DECLARATION, never inferred" — which was safe
    while there were two frequencies and no way to tell them apart from the
    values. There is now: 4, 5 and 6 digits are annual, quarterly and monthly and
    cannot collide.

    ⭐ THE DISCOUNTING PATH IS WHY. The divisor must match the ACTUAL period
    spacing or the arithmetic is wrong no matter what the label says, and being
    wrong there is the 4.66x defect. A disagreement is surfaced by
    `frequency_check`, not resolved by preferring the label.

    Measured before changing: all 36 stored datasets agree across column,
    payload and values, so this changes no existing result.
    """
    chk = frequency_check(data)
    return chk["effective"]


# ── entry parsing (Part B) ──────────────────────────────────────────────────
import re as _re

_QUARTER_FORMS = (
    _re.compile(r"^(?P<y>\d{4})\s*[-/ ]?\s*[Qq](?P<q>[1-4])$"),   # 2024Q1, 2024-Q1, 2024 Q1
    _re.compile(r"^[Qq](?P<q>[1-4])\s*[-/ ]?\s*(?P<y>\d{4})$"),   # Q1 2024, Q1-2024
)


class PeriodParseError(ValueError):
    """Raised with a message naming what was seen and what forms are accepted."""


def parse_period(raw, frequency: str) -> tuple[int, str]:
    """Customer-typed period -> (stored integer, human interpretation).

    ⭐ IT RETURNS THE INTERPRETATION, NOT JUST THE VALUE. A parser that silently
    accepts "2024Q1" leaves the customer to trust that AXIOM read it the way they
    meant. Handing back "read '2024Q1' as 2024 Q1" lets them check, which matters
    most for the forms that are genuinely near-ambiguous.

    Accepted quarterly forms: 2024Q1, 2024-Q1, 2024 Q1, Q1 2024, 2024q1, and the
    legacy 5-digit 20241. Annual: a 4-digit year, as an int or a string.

    ⭐ LEGACY YYYYQ IS STILL ACCEPTED because files in the wild carry it — the
    template shipped that form and customers have those workbooks. Rejecting it
    would repeat the version-stamp mistake: refusing a real, complete file over a
    representation AXIOM itself chose earlier."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise PeriodParseError("period is empty")

    if frequency != "quarterly":
        try:
            y = int(str(raw).strip())
        except (TypeError, ValueError):
            raise PeriodParseError(
                f"'{raw}' is not a year — enter a four-digit year such as 2024")
        if not (1900 <= y <= 2200):
            raise PeriodParseError(f"'{raw}' is not a plausible year")
        return y, str(y)

    text = str(raw).strip()

    # legacy 5-digit YYYYQ, and the integer Excel hands back for a typed number
    if _re.fullmatch(r"\d{5}", text):
        val = int(text)
        if not period_is_valid(val, "quarterly"):
            year, q = decode_period(val, "quarterly")
            raise PeriodParseError(
                f"'{text}' has quarter {q} — quarters run 1 to 4. "
                f"Enter it as {year}Q1 … {year}Q4")
        y, q = decode_period(val, "quarterly")
        return val, f"{y} Q{q}"

    for rx in _QUARTER_FORMS:
        m = rx.fullmatch(text)
        if m:
            y, q = int(m.group("y")), int(m.group("q"))
            if not (1900 <= y <= 2200):
                raise PeriodParseError(f"'{text}' is not a plausible year")
            return y * 10 + q, f"{y} Q{q}"

    raise PeriodParseError(
        f"'{text}' is not a period AXIOM can read. Use 2024Q1 "
        f"(2024-Q1, 2024 Q1 and Q1 2024 are also accepted)")


def entry_label(value: int, frequency: str) -> str:
    """The CANONICAL ENTRY FORM — what the template asks a customer to type.

    Distinct from `format_period`, which is the DISPLAY label. They are the same
    string today for quarters ("2024Q1" vs "2024Q1"), and they are separate
    functions because they answer different questions and could reasonably
    diverge — a display might gain a space or a fiscal-year prefix without
    changing what the workbook accepts."""
    year, q = decode_period(value, frequency)
    return f"{year}Q{q}" if frequency == "quarterly" else str(year)


def period_labels(values, frequency: str) -> dict:
    """`{20231: "2023Q1", …}` — ONE map per response, for the six LIST-shaped
    payloads (periods, years, chart_data.years, forecast_years,
    historical_years, simulation_baseline.years).

    ⭐ THE ASYMMETRY WITH `year_label` IS DELIBERATE — DO NOT HARMONISE THEM.
    Statement ROWS carry a per-row `year_label` because Recharts reads its axis
    key off each datum, so a parallel array cannot serve a chart and the
    alternative is a tickFormatter at ~10 TS call sites, which is the seventh
    money-formatter waiting to happen. LIST responses have no such constraint, so
    they get one map instead of six sibling fields.

    Two shapes, two reasons. Collapsing them either puts a redundant field on
    every row of every list, or puts period formatting back in TypeScript."""
    keys = []
    for v in (values or []):
        try:
            keys.append(int(v))
        except (TypeError, ValueError):
            continue
    return {k: format_period(k, frequency) for k in keys}
