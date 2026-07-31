"""§7s.2 — the Brief. Seven lines, fixed order, matching the Pack's spine.

⭐ SEVEN LINES ALWAYS. A seven-line brief that silently becomes six lets the
reader infer completeness from length — the same fabrication by silence as a
missing Pack section, in the artefact most likely to be read alone. A line whose
input is absent renders as an EM DASH with a stated reason; it is never omitted.

⭐ TRACEABLE-OR-SILENT, LINE BY LINE. Each line is individually traceable to a
Pack section or it is not published as a figure. A number in a push summary that
cannot be walked back to its section is a claim with no owner.

⭐ IT READS THE FROZEN SNAPSHOT, NEVER LIVE STATE. The Brief summarises a
PUBLISHED pack. A Brief resolving live would state today's figures under
yesterday's pack's name, and the reader has no way to tell.
"""
from .pack_render import COMPONENTS, SPINE, FrozenSource, adjusted_figures

EM_DASH = "—"

# ⭐ THE SEVEN QUESTIONS, IN THE PACK'S CANONICAL ORDER. The Brief and the Pack
# answer the same seven questions at different depths; the order is the same
# object, not a parallel list that could drift.
QUESTIONS = [
    ("what_changed", "What changed"),
    ("why_ratios", "Why"),
    ("what_is_likely", "What is likely"),
    ("what_is_at_risk", "What is at risk"),
    ("initiatives", "Which initiatives are underperforming"),
    ("what_to_do_next", "What to do next"),
    ("value_bridge", "What it is worth"),
]

assert [q[0] for q in QUESTIONS] == SPINE, (
    "the Brief's order must BE the Pack's spine, not a copy of it — a copy is "
    "two lists that agree today")


# ── per-line summarisers ────────────────────────────────────────────────────
# Each returns a short string, or None to mean "no figure could be stated".
# ⭐ RETURNING None IS NOT AN ERROR. It is the traceable-or-silent rule firing,
# and the line still renders, as an em dash with the reason.

def _l_what_changed(body):
    pv = body or {}
    rows = pv.get("rows") or pv.get("variance") or []
    if isinstance(rows, list) and rows:
        return f"{len(rows)} line items compared against plan."
    if isinstance(pv, dict) and pv:
        keys = [k for k in pv if not k.startswith("_")]
        if keys:
            return f"Plan-versus-method comparison across {len(keys)} measures."
    return None


def _l_why(body):
    m = (body or {}).get("metrics") or {}
    if not m:
        return None
    named = [k for k in m if isinstance(m.get(k), (int, float))]
    if not named:
        return None
    return f"{len(named)} ratios computed on the frozen statements."


def _l_likely(body):
    af = (body or {}).get("auto_forecast")
    if isinstance(af, dict) and af:
        return "AXIOM's own projection is available for the frozen dataset."
    sets_ = ((body or {}).get("forecast_sets") or {})
    if sets_.get("present"):
        n = len(sets_.get("sets") or [])
        primary = [s for s in (sets_.get("sets") or []) if s.get("is_primary")]
        if n:
            return (f"{n} forecast set(s) on record"
                    + (", one marked primary." if primary else ", none primary."))
    return None


def _l_risk(body):
    v = (body or {}).get("viability")
    if isinstance(v, dict) and v:
        payload = v.get("payload") or {}
        band = payload.get("band")
        if band:
            return f"Viability band: {band}."
        return "A viability computation is on record."
    watch = (body or {}).get("watch") or {}
    if watch.get("present"):
        n = len(watch.get("events") or [])
        return f"{n} Sentinel event(s) recorded in the period."
    return None


def _l_initiatives(body):
    b = body or {}
    total = b.get("total")
    under = b.get("underperforming")
    if total is None:
        return None
    if not under:
        return f"No initiative is flagged; {total} tracked."
    return f"{len(under)} of {total} initiatives are underperforming."


def _l_next(body):
    o = (body or {}).get("optimisation")
    if isinstance(o, dict) and o:
        return "An optimisation result is available for this period."
    return None


def _l_worth(body):
    val = (body or {}).get("valuation") or {}
    det = val.get("deterministic") or {}
    ev = det.get("enterprise_value")
    if isinstance(ev, (int, float)):
        return f"Enterprise value on the frozen inputs: {round(ev, 2)}."
    return None


LINE_FN = {
    "what_changed": _l_what_changed,
    "why_ratios": _l_why,
    "what_is_likely": _l_likely,
    "what_is_at_risk": _l_risk,
    "initiatives": _l_initiatives,
    "what_to_do_next": _l_next,
    "value_bridge": _l_worth,
}


def _deep_link(pack_id, section_id, token=None):
    """⭐ EVERY LINE DEEP-LINKS TO THE PACK PAGE SUPPORTING IT, including the
    lines that render as an em dash — a reader who cannot see the figure must
    still be able to reach the section that explains why."""
    if token:
        # recipient-scoped, and it survives login because the capability is in
        # the token rather than in a session
        return f"/packs/shared/{token}#{section_id}"
    return f"/packs/{pack_id}#{section_id}"


def build(frozen, pack, *, token=None):
    """The Brief for a published pack. Always seven lines.

    ⭐ FrozenSource, NOT LiveSource, AND THE TYPE IS THE GUARANTEE. There is no
    argument here that could accidentally be a live session.
    """
    src = FrozenSource(frozen)
    adjustments = adjusted_figures(src)
    by_metric = {}
    for a in adjustments:
        by_metric.setdefault("all", []).append(a)

    lines = []
    for n, (section_id, question) in enumerate(QUESTIONS, start=1):
        section = COMPONENTS[section_id](src)
        text = None
        reason = None
        if not section["present"]:
            reason = section.get("missing") or "input not available"
        else:
            text = LINE_FN[section_id](section.get("body"))
            if text is None:
                # ⭐ TRACEABLE-OR-SILENT: the section rendered, but no figure in
                # it could be stated in one line. That is a DIFFERENT absence
                # from a missing input, and it says so.
                reason = ("the section rendered but no single figure in it is "
                          "traceable to a one-line claim")
        line = {
            "n": n,
            "question": question,
            "section_id": section_id,
            "text": text if text is not None else EM_DASH,
            "traceable": text is not None,
            "deep_link": _deep_link(getattr(pack, "id", None), section_id, token),
        }
        if text is None:
            line["reason"] = reason
        if section.get("gap"):
            # a declared structural gap travels into the Brief; a reader must
            # not infer from a rendered line that the machinery behind it exists
            line["gap"] = section["gap"]
        lines.append(line)

    # ⭐ PROVENANCE TRAVELS INTO THE BRIEF as it does into the Pack. §4x: an
    # adjusted figure reaching any surface bare is a fail, and a push summary is
    # the surface most likely to be forwarded without its document.
    return {
        "document": "brief",
        "pack_id": getattr(pack, "id", None),
        "period_type": getattr(pack, "period_type", None),
        "period_end": getattr(pack, "period_end", None),
        "version": getattr(pack, "version", None),
        "source_kind": src.kind,
        "lines": lines,
        "adjustments": adjustments,
        "adjustment_note": (
            "No figures in this period were adjusted." if not adjustments else
            f"{len(adjustments)} figure(s) carry an executive adjustment; each "
            f"is shown with its author and reason."),
        "absent_lines": [ln["n"] for ln in lines if not ln["traceable"]],
    }


def render_text(brief):
    """Plain-text Brief — seven lines, em dashes included.

    ⭐ THE EM DASH IS RENDERED, NOT SKIPPED. A text renderer that dropped
    untraceable lines would reintroduce the six-line brief at the last step,
    after every upstream guarantee held.
    """
    out = []
    for ln in brief["lines"]:
        suffix = "" if ln["traceable"] else f"   ({ln.get('reason', 'not available')})"
        out.append(f"{ln['n']}. {ln['question']}: {ln['text']}{suffix}")
    for a in brief.get("adjustments") or []:
        out.append(f"   adjusted: {a['attribution']}")
    return "\n".join(out)
