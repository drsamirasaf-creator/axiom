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

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "NOTABLE": 2}

# signal_id → (category, default severity, human label). category ∈ intervention|recognition
SIGNALS = {
    "I1": ("intervention", "CRITICAL", "Sentinel band"),
    "I2": ("intervention", "HIGH", "KPI vs target"),
    "I3": ("intervention", "HIGH", "Objective/KR red"),
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
