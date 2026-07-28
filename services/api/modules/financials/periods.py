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

def decode_period(value: int, frequency: str) -> tuple[int, int | None]:
    """YYYYQ -> (year, quarter) for quarterly; (year, None) for annual."""
    if frequency == "quarterly":
        year, q = divmod(int(value), 10)
        return year, q
    return int(value), None


def period_is_valid(value: int, frequency: str) -> bool:
    year, q = decode_period(value, frequency)
    if not (1900 <= year <= 2200):
        return False
    if frequency == "quarterly":
        return q is not None and 1 <= q <= 4
    return True


def next_period(value: int, frequency: str) -> int:
    """The period that must follow `value`. Carries the year on Q4."""
    year, q = decode_period(value, frequency)
    if frequency == "quarterly":
        return (year + 1) * 10 + 1 if q == 4 else year * 10 + (q + 1)
    return year + 1


def format_period(value: int, frequency: str) -> str:
    year, q = decode_period(value, frequency)
    return f"{year}Q{q}" if frequency == "quarterly" else str(year)


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


def frequency_of(data: dict) -> str:
    """The dataset's declared frequency, defaulting to annual.

    Datasets written before the key existed are annual, which is correct — and
    it is a DECLARATION, never inferred from how the periods happen to look."""
    return ((data or {}).get("periods", {}) or {}).get("frequency") or "annual"
