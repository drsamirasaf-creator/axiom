"""Urgent Items (Executive Brief tab) — threshold constants + signal registry.

ONE place for every threshold (Samir-ratifiable). The aggregation endpoint in
accounts.py reads these; no scattered literals. Strictly descriptive surface — the
registry names facts and magnitudes, never advice.
"""

# ── ratified threshold constants (values unchanged; one place, Samir-ratifiable) ──
VARIANCE_RED_PCT = 10        # KR/KPI plan-vs-actual unfavourable beyond this → red
FORECAST_GAP_RED_PCT = 10    # primary-forecast vs plan gap on key lines → red
OUTPERFORM_PCT = 10          # KPI/KR ahead of target by this → recognition
AGING_DAYS = 14              # undispositioned URGENT/HIGH proposal aging
STALE_DAYS = 21              # initiative with no cadence update in this many days
LOOKBACK_DAYS = 90           # recognition look-back for completed milestones/initiatives
RATING_RED_MAX = 2.5         # member star rating at/below this → red flag (I7)
PROGRESS_AHEAD_MIN = 70      # green initiative at/above this progress → "ahead" (R4)

# I4/I5 tracked line set — the client-plan lines compared against AXIOM's PRIMARY
# (ensemble) forecast. Keys are the model's own line keys (fcff = free cash flow,
# the "cash" line).
#   I5 = terminal-year POINT gap:  |plan − ensemble| / ensemble  ≥ FORECAST_GAP_RED_PCT
#   I4 = whole-horizon CUMULATIVE:  |Σ plan − Σ ensemble| / Σ ensemble ≥ CUMULATIVE_DIVERGENCE_PCT
# I4 is a different quantity from I5 (cumulative-over-the-plan, not a single year), so
# it carries its OWN, intentionally looser band — never overload FORECAST_GAP_RED_PCT.
FORECAST_TRACKED_LINES = ("revenue", "ebitda", "fcff")
CUMULATIVE_DIVERGENCE_PCT = 15   # I4: whole-horizon cumulative plan-vs-ensemble divergence → red

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "NOTABLE": 2}

# signal_id → (category, default severity, human label). category ∈ intervention|recognition
SIGNALS = {
    "I1": ("intervention", "CRITICAL", "Sentinel band"),
    "I2": ("intervention", "HIGH", "KPI vs target"),
    "I3": ("intervention", "HIGH", "Objective/KR red"),
    "I4": ("intervention", "HIGH", "Long-run divergence"),
    "I5": ("intervention", "HIGH", "Forecast vs plan"),
    "I6": ("intervention", "NOTABLE", "Undispositioned proposal"),
    "I7": ("intervention", "HIGH", "Initiative execution"),
    "I8": ("intervention", "HIGH", "Department sentiment"),
    "R1": ("recognition", "NOTABLE", "KPI ahead of target"),
    "R3": ("recognition", "NOTABLE", "Department sentiment"),
    "R4": ("recognition", "NOTABLE", "Execution ahead of plan"),
}


def sort_key(item):
    """Severity (CRITICAL>HIGH>NOTABLE), then magnitude descending."""
    mag = (item.get("magnitude") or {}).get("value")
    mag = abs(mag) if isinstance(mag, (int, float)) else 0
    return (SEVERITY_ORDER.get(item.get("severity"), 9), -mag)
