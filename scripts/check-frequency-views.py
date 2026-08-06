#!/usr/bin/env python3
"""Frequency views: every token classified, and interpolation cannot be frozen.

⭐⭐ THE CLASSIFICATION IS THE LANE'S LOAD-BEARING ARTEFACT (ruling 3). A token
that arrives without `aggregation` would fall to `aggregation_of() -> None` and be
DROPPED from every view — silently absent rather than wrongly summed, which is the
safer failure but still a line vanishing from a statement. This gate makes the
declaration a condition of adding a token.

⛔⭐⭐ AND THE PACK BOUNDARY IS STRUCTURAL, NOT POLICED BY REVIEW. Interpolation is
a READ-TIME view: `frequency_views` is imported by the read router and by nothing
that writes. If `pack.py`, `sentinel.py` or `watch.py` ever import it, an
interpolated figure can be frozen or can fire an alert — and CORE §8a's
reconciliation rests on exactly that not happening. Those three ACT on numbers
rather than displaying them, and an interpolated figure crossing a threshold
manufactures an event.

⭐ CONTROLS ARE IN MEMORY. Nothing is written to disk.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ⛔ The three that must never reach the view module. Named individually rather
# than by a pattern, so adding a fourth is a deliberate act.
FORBIDDEN_IMPORTERS = {
    "services/api/pack.py":
        "a pack FREEZES what it reads; an interpolated figure frozen into one is "
        "unrecoverable and the recipient never chose the method",
    "services/api/sentinel.py":
        "sentinel ACTS on numbers rather than displaying them — an interpolated "
        "figure crossing a threshold manufactures an event",
    "services/api/watch.py":
        "watch fires on movement, and an interpolated series has no real movement "
        "to detect",
}

MODULE = "frequency_views"


def main():
    import services.api.frequency_views as FV
    from services.api.modules.financials import ratio_registry as RR
    from services.api.modules.financials import dimensions as D

    fails = []
    vocab, _g, _r = RR._index()
    print(f"  {len(vocab)} registry token(s)")
    # ⭐ §III.4 — an empty corpus fails. 70 tokens are known to exist.
    if len(vocab) < 60:
        print(f"  ✗ only {len(vocab)} tokens read — the index has drifted")
        return 1

    valid = {"sum", "closing", "derived", "constant", "period_defined"}
    counts = {}
    for tok, meta in sorted(vocab.items()):
        agg = (meta or {}).get("aggregation")
        if agg is None:
            fails.append(f"{tok}: no `aggregation` declared. Every token states "
                         f"whether it sums, takes the closing position, or is "
                         f"recomputed — nothing infers it from the name.")
        elif agg not in valid:
            fails.append(f"{tok}: aggregation {agg!r} is not one of {sorted(valid)}")
        else:
            counts[agg] = counts.get(agg, 0) + 1
    print("   ", " · ".join(f"{k} {v}" for k, v in sorted(counts.items())))

    # ⭐⭐ THE CLASSIFICATION MUST STILL DISCRIMINATE. If every token ever took one
    # value, the field would have stopped saying anything and this gate would pass
    # while guarding nothing.
    if len(counts) < 3:
        fails.append(f"only {len(counts)} distinct aggregation kind(s) in use "
                     f"({counts}) — the field has stopped distinguishing lines")

    # ── the pack / alert boundary ─────────────────────────────────────────
    for rel, why in sorted(FORBIDDEN_IMPORTERS.items()):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            fails.append(f"{rel} does not exist — this gate's premise has changed")
            continue
        src = open(p, encoding="utf-8").read()
        # ⭐ §III.9 — comments are stripped first. These files DISCUSS the rule.
        body = re.sub(r"#[^\n]*", "", re.sub(r'""".*?"""', "", src, flags=re.S))
        if re.search(rf"\b{MODULE}\b", body):
            fails.append(f"{rel} references {MODULE} — {why}")
    print(f"  ✓ {len(FORBIDDEN_IMPORTERS)} write/alert path(s) checked; none "
          f"reaches the view module")

    # ── §8a's refusal must survive the reconciliation ─────────────────────
    if "imputed" in D.DATA_STATUSES:
        fails.append("`imputed` has become a status — §8a's refusal is what the "
                     "interpolation reconciliation rests on")
    if "imputed_status" not in D.FORBIDDEN:
        fails.append("`imputed_status` left FORBIDDEN")
    if D.INTERPOLATED not in D.DATA_STATUSES:
        fails.append("`interpolated` is not a declared status")

    # ── controls, in memory ───────────────────────────────────────────────
    # ⭐⭐ Each fails on its own input, and each READS THE APP DEFENSIVELY so a
    # missing field is reported rather than raising over the findings.
    assert FV.aggregation_of("nope.not_a_token") is None, \
        "control: an unknown token resolved to a rule"
    if FV.aggregation_of("is.revenue") != "sum":
        fails.append("control: a known flow no longer reads as `sum`")
    if FV.aggregation_of("bs.cash") != "closing":
        fails.append("control: a known stock no longer reads as `closing`")
    # a stock must not sum — exercised on the real function
    b = FV.bucket([20241, 20242, 20243, 20244], "quarterly", "annual")
    got = FV.aggregate_series({str(p): 1000.0 for p in
                               (20241, 20242, 20243, 20244)}, b, "closing")
    if got.get("2024") != 1000.0:
        fails.append(f"control: coarsening a stock gave {got} — a sum would be 4000")
    summed = FV.aggregate_series({str(p): 100.0 for p in
                                  (20241, 20242, 20243, 20244)}, b, "sum")
    if summed.get("2024") != 400.0:
        fails.append(f"control: coarsening a flow gave {summed}, expected 400")
    # ⭐ and the recogniser must SEE a forbidden import when there is one
    probe = "import services.api.frequency_views as X"
    assert re.search(rf"\b{MODULE}\b", probe), \
        "control: the import recogniser cannot see a real import"
    assert not re.search(rf"\b{MODULE}\b", "import services.api.pack"), \
        "control: the import recogniser matches an unrelated import"
    print("  ✓ controls: an unknown token has no rule; a stock does not sum and "
          "a flow does; the import recogniser sees one and not the other")

    for f in fails:
        print(f"      ✗ {f}")
    if fails:
        print(f"\n  ✗ {len(fails)} failure(s).")
        return 1
    print("\n  ✓ every token declares how it aggregates, and no write or alert "
          "path can reach an interpolated figure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
