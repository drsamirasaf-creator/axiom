"""AXIOM report artifacts (Phase 7f): themed PPTX board deck + PDF, rendered
from the same board_report() engine payload the on-screen report uses.

AXIOM dark theme — deep pine backgrounds, ivory text, brass accents — mirroring
the brochure/PDF language. Charts are matplotlib PNGs, theme-matched.
"""
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np

# ---- palette ---------------------------------------------------------------
PINE = "#0E1F17"     # deep pine background
PANEL = "#15291F"    # raised panel
IVORY = "#F4F1E8"    # primary text
BRASS = "#C9A24B"    # accent
GREEN = "#4ADE80"    # positive
RED = "#F0776B"      # negative
AMBER = "#FBBF24"
MUTED = "#9FB3A8"    # secondary text
GRID = "#26402F"

_RGB = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def issued_line(issued_at: datetime, dataset_version) -> str:
    dv = f" · Data version {dataset_version}" if dataset_version is not None else ""
    return f"Issued {issued_at.strftime('%d %b %Y, %H:%M')}{dv}"


def report_filename(company: str, report_type: str, fmt: str, issued_at: datetime) -> str:
    safe = "".join(ch if (ch.isalnum() or ch in " -") else "" for ch in (company or "Company")).strip()
    safe = "_".join(safe.split()) or "Company"
    rt = "_".join((report_type or "Report").split())
    return f"{safe}_{rt}_{issued_at.strftime('%Y-%m-%d_%H%M')}.{fmt}"


# ---- matplotlib helpers ----------------------------------------------------
def _fig(w=8.0, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(PINE)
    ax.set_facecolor(PINE)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.title.set_color(IVORY)
    ax.xaxis.label.set_color(MUTED); ax.yaxis.label.set_color(MUTED)
    return fig, ax


def _png(fig) -> bytes:
    buf = io.BytesIO()
    fig.tight_layout(pad=1.1)
    fig.savefig(buf, format="png", facecolor=PINE, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def chart_fan(fan, title="Revenue — projection with P05–P95 band"):
    if not fan:
        return None
    yrs = [p["year"] for p in fan]
    p05 = [p.get("p05") for p in fan]; p25 = [p.get("p25") for p in fan]
    p50 = [p.get("p50") for p in fan]; p75 = [p.get("p75") for p in fan]
    p95 = [p.get("p95") for p in fan]
    fig, ax = _fig()
    ax.fill_between(yrs, p05, p95, color=BRASS, alpha=0.16, label="P05–P95")
    ax.fill_between(yrs, p25, p75, color=BRASS, alpha=0.34, label="P25–P75")
    ax.plot(yrs, p50, color=BRASS, lw=2.4, marker="o", ms=4, label="Median")
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.set_xticks(yrs)
    leg = ax.legend(loc="upper left", fontsize=8, frameon=False)
    for t in leg.get_texts(): t.set_color(MUTED)
    ax.grid(True, color=GRID, lw=0.5, alpha=0.6)
    return _png(fig)


def chart_valuation_lenses(dcf, real_options):
    labels, vals, cols = [], [], []
    if dcf:
        labels.append("DCF (EV)"); vals.append(dcf.get("enterprise_value")); cols.append(BRASS)
        mc = dcf.get("monte_carlo") or {}
        if mc.get("mean") is not None:
            labels.append("Monte Carlo\nmean"); vals.append(mc["mean"]); cols.append(GREEN)
        if mc.get("cvar95") is not None:
            labels.append("MC 95%\ntail (CVaR)"); vals.append(mc["cvar95"]); cols.append(AMBER)
    try:
        rov = real_options["options"]["expand"]["flexibility_value"]
        labels.append("Real-option\nexpand"); vals.append(rov); cols.append(MUTED)
    except (KeyError, TypeError):
        pass
    labels = [l for l, v in zip(labels, vals) if v is not None]
    cols = [c for c, v in zip(cols, vals) if v is not None]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    fig, ax = _fig(7.6, 4.0)
    bars = ax.bar(range(len(vals)), vals, color=cols, width=0.6)
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels, fontsize=8, color=MUTED)
    ax.set_title("Valuation — three independent lenses", loc="left", fontsize=11, fontweight="bold")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom",
                color=IVORY, fontsize=8)
    ax.grid(True, axis="y", color=GRID, lw=0.5, alpha=0.6)
    return _png(fig)


def chart_tornado(recs):
    items = [(r.get("title", r.get("move", "")), r.get("expected_ev_impact"))
             for r in (recs or []) if r.get("expected_ev_impact") is not None]
    if not items:
        return None
    items.sort(key=lambda t: abs(t[1]))
    labels = [t[0][:38] for t in items]; vals = [t[1] for t in items]
    cols = [GREEN if v >= 0 else RED for v in vals]
    fig, ax = _fig(8.0, 3.2 + 0.35 * len(items))
    ax.barh(range(len(vals)), vals, color=cols, height=0.6)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=8, color=IVORY)
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_title("Value drivers — EV impact of each lever ($M)", loc="left", fontsize=11, fontweight="bold")
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:+,.1f}", va="center", ha="left" if v >= 0 else "right",
                color=IVORY, fontsize=8)
    ax.grid(True, axis="x", color=GRID, lw=0.5, alpha=0.6)
    return _png(fig)


def chart_frontier(points, recommended):
    if not points:
        return None
    x = [p["safety_tail_margin"] for p in points]; y = [p["value_mean_ev"] for p in points]
    fig, ax = _fig(7.6, 4.0)
    ax.plot(x, y, color=BRASS, lw=1.6, marker="o", ms=3, alpha=0.8)
    if recommended:
        ax.scatter([recommended["safety_tail_margin"]], [recommended["value_mean_ev"]],
                   s=160, facecolor="none", edgecolor=GREEN, lw=2.2, zorder=5, label="recommended")
        leg = ax.legend(loc="lower right", fontsize=8, frameon=False)
        for t in leg.get_texts(): t.set_color(MUTED)
    ax.set_title("Value–risk frontier over capital structure", loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel("safety (tail margin)"); ax.set_ylabel("mean EV")
    ax.grid(True, color=GRID, lw=0.5, alpha=0.6)
    return _png(fig)


def chart_radar(l1_subscores):
    pts = [(o.get("title", o.get("code", "")), o.get("score")) for o in (l1_subscores or [])
           if o.get("score") is not None]
    if len(pts) < 3:
        return None
    labels = [p[0][:16] for p in pts]; vals = [p[1] for p in pts]
    n = len(vals); ang = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    vals2 = vals + vals[:1]; ang2 = ang + ang[:1]
    fig = plt.figure(figsize=(5.4, 5.4), dpi=150); fig.patch.set_facecolor(PINE)
    ax = fig.add_subplot(111, polar=True); ax.set_facecolor(PINE)
    ax.plot(ang2, vals2, color=BRASS, lw=2)
    ax.fill(ang2, vals2, color=BRASS, alpha=0.25)
    ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=7, color=MUTED)
    ax.set_ylim(0, 10); ax.set_yticks([2, 4, 6, 8, 10])
    ax.tick_params(colors=MUTED); ax.grid(color=GRID)
    ax.spines["polar"].set_color(GRID)
    ax.set_title("Composite Excellence Index — L1 subscores", color=IVORY, fontsize=11,
                 fontweight="bold", pad=18)
    return _png(fig)


from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as _fm


def _px_size(png: bytes):
    try:
        return Image.open(io.BytesIO(png)).size      # (w, h)
    except Exception:
        return None


def _fit_box(iw, ih, max_w, max_h):
    """Fit (iw,ih) inside (max_w,max_h) preserving aspect — never stretch."""
    if not iw or not ih:
        return max_w, max_h
    scale = min(max_w / iw, max_h / ih)
    return iw * scale, ih * scale


def wordmark_png(text, bg_hex=PINE, fg_hex=IVORY, accent_hex=BRASS, w=680, h=260):
    """A simple, tasteful text wordmark (for the showcase companies)."""
    img = Image.new("RGB", (w, h), _RGB(bg_hex))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(_fm.findfont("DejaVu Sans:bold"), 62)
    except Exception:
        font = ImageFont.load_default()
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x, y = (w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]
    d.text((x, y), text, fill=_RGB(fg_hex), font=font)
    d.rectangle([(w - tw) / 2, y + th + 18, (w - tw) / 2 + tw, y + th + 26], fill=_RGB(accent_hex))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def _logo_from_meta(meta):
    lg = (meta or {}).get("logo")
    if not lg:
        return None
    png = lg[0] if isinstance(lg, (tuple, list)) else lg.get("bytes")
    return png or None


# ============================================================================
# PPTX board deck
# ============================================================================
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

_C = lambda h: RGBColor.from_string(h.lstrip("#"))
EMU_IN = 914400
SW, SH = 13.333, 7.5


def _blank(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = _C(PINE)
    return s


def _tb(slide, l, t, w, h, text, size=14, color=IVORY, bold=False, align=PP_ALIGN.LEFT,
        italic=False):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Pt(2); tf.margin_top = tf.margin_bottom = Pt(2)
    lines = text.split("\n") if isinstance(text, str) else list(text)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
        r.font.color.rgb = _C(color); r.font.name = "Georgia"
    return box


def _rule(slide, l, t, w, color=BRASS, h=0.035):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = _C(color); sh.line.fill.background()
    return sh


def _panel(slide, l, t, w, h, color=PANEL):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = _C(color); sh.line.color.rgb = _C(GRID); sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh


def _header(slide, kicker, title, logo_png=None):
    _tb(slide, 0.6, 0.42, 10.5, 0.34, kicker.upper(), size=11, color=BRASS, bold=True)
    _tb(slide, 0.6, 0.74, 10.6, 0.9, title, size=26, color=IVORY, bold=True)
    _rule(slide, 0.62, 1.62, 3.2)
    if logo_png:                                     # small client mark, top-right corner
        sz = _px_size(logo_png)
        w, h = _fit_box(sz[0], sz[1], 1.25, 0.55) if sz else (1.1, 0.5)
        try:
            slide.shapes.add_picture(io.BytesIO(logo_png), Inches(13.333 - 0.5 - w),
                                     Inches(0.42), Inches(w), Inches(h))
        except Exception:
            pass


def _pic(slide, png, l, t, w, h):
    if not png:
        return
    slide.shapes.add_picture(io.BytesIO(png), Inches(l), Inches(t), Inches(w), Inches(h))


def _table(slide, headers, rows, l, t, w, col_w=None, fsize=11, row_h=0.34):
    nrows, ncols = len(rows) + 1, len(headers)
    h = row_h * nrows
    gt = slide.shapes.add_table(nrows, ncols, Inches(l), Inches(t), Inches(w), Inches(h)).table
    gt.first_row = False; gt.horz_banding = False
    if col_w:
        for i, cw in enumerate(col_w):
            gt.columns[i].width = Inches(cw)
    for j, htext in enumerate(headers):
        c = gt.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = _C(BRASS)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = str(htext); r.font.size = Pt(fsize); r.font.bold = True
        r.font.color.rgb = _C(PINE); r.font.name = "Georgia"
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = gt.cell(i, j); c.fill.solid()
            c.fill.fore_color.rgb = _C(PANEL if i % 2 else PINE)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]
            r = p.add_run(); r.text = "" if val is None else str(val)
            r.font.size = Pt(fsize); r.font.color.rgb = _C(IVORY); r.font.name = "Georgia"
    return gt


def _rag_word(rag):
    return {"green": "Green", "amber": "Amber", "red": "Red"}.get(rag, "—")


def _fmt(v, pct=False):
    if v is None:
        return "—"
    return f"{v*100:.1f}%" if pct else f"{v:,.1f}"


def build_pptx(report: dict, extras: dict, meta: dict) -> bytes:
    extras = extras or {}
    prs = Presentation()
    prs.slide_width = Emu(int(SW * EMU_IN)); prs.slide_height = Emu(int(SH * EMU_IN))
    S = {s["id"]: s for s in report.get("sections", [])}
    company = report.get("company", {})
    cur = company.get("currency", "")
    issued = meta["issued_at"]
    logo_png = _logo_from_meta(meta)

    # 1. Title — the client's logo leads (it's their board deck); AXIOM subordinate
    s = _blank(prs)
    if logo_png:
        sz = _px_size(logo_png)
        w, h = _fit_box(sz[0], sz[1], 5.2, 1.9) if sz else (4.4, 1.6)
        try:
            s.shapes.add_picture(io.BytesIO(logo_png), Inches(0.9), Inches(1.35),
                                 Inches(w), Inches(h))
        except Exception:
            logo_png = None
    if not logo_png:
        _tb(s, 0.9, 2.15, 11.5, 0.5, "AXIOM", size=18, color=BRASS, bold=True)
    top = 3.55 if _logo_from_meta(meta) else 2.75
    _tb(s, 0.9, top, 11.5, 1.4, meta.get("company_name", company.get("name", "Company")),
        size=40, color=IVORY, bold=True)
    _tb(s, 0.9, top + 1.35, 11.5, 0.6, meta.get("report_type", "Board Report"), size=22, color=MUTED)
    _rule(s, 0.94, top + 2.15, 4.0)
    _tb(s, 0.9, top + 2.35, 11.5, 0.5, issued_line(issued, meta.get("dataset_version")),
        size=13, color=MUTED)
    _tb(s, 0.9, 6.9, 11.5, 0.4, "Confidential — prepared by AXIOM Dynamics", size=10,
        color=MUTED, italic=True)

    # 2. Executive summary
    s = _blank(prs); _header(s, "Executive summary", "The company at a glance", logo_png)
    sm = S.get("summary", {}); sc = sm.get("scorecard", {}); hm = sm.get("headline_metric", {})
    _panel(s, 0.6, 1.95, 5.4, 2.0)
    _tb(s, 0.85, 2.15, 5.0, 0.4, hm.get("label", report.get("headline", {}).get("label", "Enterprise Value")),
        size=13, color=MUTED)
    _tb(s, 0.85, 2.55, 5.0, 0.9, f"{hm.get('value', report.get('headline', {}).get('value', 0)):,.0f} {cur}",
        size=34, color=BRASS, bold=True)
    _tb(s, 0.85, 3.5, 5.0, 0.35, sm.get("takeaway", "")[:120], size=11, color=MUTED, italic=True)
    cards = [("Health index", _fmt(sc.get("health_index"))),
             ("Risk grade", sc.get("risk_grade", "—")),
             ("Optimization", sc.get("optimization_status", "—")),
             ("Optimizer uplift", f"{sc.get('optimization_uplift', 0):,.0f} {cur}")]
    for i, (k, v) in enumerate(cards):
        cx = 6.35 + (i % 2) * 3.35; cy = 1.95 + (i // 2) * 1.05
        _panel(s, cx, cy, 3.15, 0.92)
        _tb(s, cx + 0.2, cy + 0.12, 2.8, 0.3, k.upper(), size=9, color=MUTED, bold=True)
        _tb(s, cx + 0.2, cy + 0.4, 2.8, 0.45, str(v), size=15, color=IVORY, bold=True)
    recs = extras.get("recommendations") or []
    n_pos = sum(1 for r in recs if (r.get("expected_ev_impact") or 0) > 0)
    _tb(s, 0.6, 4.2, 12, 2.6, [
        "The four answers:",
        *[f"•  {w}" for w in sm.get("four_answers", [])[:4]],
        f"Value-creating levers identified: {n_pos}",
    ], size=12, color=IVORY)

    # 3. Statement highlights (KPIs)
    s = _blank(prs); _header(s, "Financial highlights", "Latest actuals vs. prior period", logo_png)
    kpis = S.get("diagnostic", {}).get("kpi_strip") or []
    rows = [[k.get("kpi"), f"{k.get('current'):,.1f}" if k.get("current") is not None else "—",
             f"{k.get('previous'):,.1f}" if k.get("previous") is not None else "—",
             _fmt(k.get("trend"), pct=True)] for k in kpis[:8]]
    if rows:
        _table(s, ["KPI", "Current", "Prior", "Trend"], rows, 0.6, 2.0, 8.5,
               col_w=[3.4, 1.7, 1.7, 1.7])
    _tb(s, 9.4, 2.0, 3.4, 4.6, "Figures in " + (report.get("units_note", "$ millions")),
        size=10, color=MUTED, italic=True)

    # 4. Statement highlights — forecast bands (P05–P95)
    s = _blank(prs); _header(s, "Forecast bands", "Revenue distribution by year (P05–P95)", logo_png)
    fan = (S.get("outlook", {}).get("simulation_baseline", {}) or {}).get("revenue_fan") or []
    rows = [[p.get("year"), f"{p.get('p05'):,.0f}", f"{p.get('p25'):,.0f}",
             f"{p.get('p50'):,.0f}", f"{p.get('p75'):,.0f}", f"{p.get('p95'):,.0f}"] for p in fan]
    if rows:
        _table(s, ["Year", "P05", "P25", "Median", "P75", "P95"], rows, 0.6, 2.1, 11.0)
    else:
        _tb(s, 0.6, 2.3, 11, 0.6, "No probabilistic forecast available for this dataset.",
            size=13, color=MUTED)

    # 5. Forecast fan
    s = _blank(prs); _header(s, "Outlook", "Probabilistic revenue forecast", logo_png)
    _pic(s, chart_fan(fan), 0.7, 1.95, 11.9, 5.0)

    # 6. Valuation lenses
    s = _blank(prs); _header(s, "Valuation", "Three independent lenses", logo_png)
    va = S.get("valuation", {})
    _pic(s, chart_valuation_lenses(va.get("dcf"), va.get("real_options")), 0.9, 1.95, 8.0, 4.7)
    dcf = va.get("dcf", {}); mc = dcf.get("monte_carlo", {})
    _panel(s, 9.2, 2.0, 3.5, 4.5)
    _tb(s, 9.42, 2.2, 3.1, 4.2, [
        "DCF enterprise value",
        f"{dcf.get('enterprise_value', 0):,.0f} {cur}", "",
        "Monte Carlo mean",
        f"{mc.get('mean', 0):,.0f} {cur}", "",
        "95% tail (CVaR)",
        f"{mc.get('cvar95', 0):,.0f} {cur}", "",
        f"WACC {(_fmt(dcf.get('wacc'), pct=True))}",
    ], size=12, color=IVORY)

    # 7. Value drivers / tornado
    s = _blank(prs); _header(s, "Value drivers", "EV impact of each lever", logo_png)
    _pic(s, chart_tornado(S.get("actions", {}).get("recommendations")), 0.7, 1.9, 11.9, 5.1)

    # 8. Risk indicators
    s = _blank(prs); _header(s, "Risk", "Key risk indicators", logo_png)
    rg = S.get("diagnostic", {}).get("risk_grade", {})
    runway = S.get("outlook", {}).get("cash_runway", {})
    cov = S.get("outlook", {}).get("coverage", {})
    cards = [("Risk grade", rg.get("grade", sm.get("scorecard", {}).get("risk_grade", "—"))),
             ("P(cash < 0) ever", _fmt(runway.get("p_cash_below_zero_ever"), pct=True)),
             ("Months to zero", (f"{runway.get('deterministic_months_to_zero'):,.0f}"
                                 if runway.get("deterministic_months_to_zero") is not None else "—")),
             ("Burning cash", "Yes" if runway.get("burning_cash") else "No")]
    for i, (k, v) in enumerate(cards):
        cx = 0.6 + (i % 4) * 3.15
        _panel(s, cx, 2.1, 2.95, 1.4)
        _tb(s, cx + 0.2, 2.32, 2.6, 0.4, k.upper(), size=10, color=MUTED, bold=True)
        _tb(s, cx + 0.2, 2.78, 2.6, 0.55, str(v), size=18, color=IVORY, bold=True)
    _tb(s, 0.6, 3.9, 12, 2.6, [f"•  {w}" for w in (S.get("outlook", {}).get("narrative") or [])[:4]],
        size=12, color=IVORY)

    # 9. CEI + SWOT
    s = _blank(prs); _header(s, "Organizational excellence", "Assessment & SWOT", logo_png)
    cei = extras.get("cei"); swot = extras.get("swot")
    if cei and cei.get("cei") is not None:
        _pic(s, chart_radar(cei.get("l1_subscores")), 0.7, 1.85, 5.2, 5.2)
        _tb(s, 6.2, 2.0, 6.4, 0.6, f"CEI  {cei.get('cei'):.1f} / 10", size=22, color=BRASS, bold=True)
        if swot and swot.get("has_data"):
            cnt = swot.get("counts", {})
            rows = [["Strengths", cnt.get("strengths", 0)], ["Weaknesses", cnt.get("weaknesses", 0)],
                    ["Opportunities", cnt.get("opportunities", 0)], ["Threats", cnt.get("threats", 0)],
                    ["Watch list", cnt.get("watch_list", 0)]]
            _table(s, ["SWOT quadrant", "Items"], rows, 6.2, 2.9, 5.2, col_w=[3.4, 1.8])
    else:
        _tb(s, 0.6, 2.4, 11.5, 1.2,
            "No closed assessment cycle yet — the Composite Excellence Index and SWOT "
            "appear here once the organization completes its first assessment.",
            size=15, color=MUTED, italic=True)

    # 10. Recommendations + dispositions
    s = _blank(prs); _header(s, "Recommendations", "AXIOM levers & decisions", logo_png)
    rows = []
    for r in (extras.get("recommendations") or [])[:8]:
        disp = r.get("disposition", "none")
        ini = r.get("initiative") or {}
        d = {"none": "—", "adopted": f"Adopted → {ini.get('ref', '')}"
             + (f", {ini.get('status')}" if ini.get("status") else "")
             + (f", {_rag_word(ini.get('rag'))}" if ini.get("rag") else ""),
             "parked": f"Parked → {ini.get('ref', '')}", "dismissed": "Dismissed"}.get(disp, disp)
        rows.append([r.get("title", "")[:48], f"{r.get('expected_ev_impact', 0):+,.1f}", d])
    if rows:
        _table(s, ["Recommendation", "EV impact", "Disposition"], rows, 0.6, 2.0, 12.1,
               col_w=[6.6, 2.0, 3.5])
    else:
        _tb(s, 0.6, 2.3, 11, 0.6, "No value-creating recommendations for the active dataset.",
            size=13, color=MUTED)

    # 11. Initiatives status board
    s = _blank(prs); _header(s, "Execution", "Key initiatives status board", logo_png)
    rows = [[i.get("ref_code"), (i.get("current_priority") or "").title(),
             _rag_word(i.get("rag")), i.get("owner_name") or "—",
             (i.get("status") or "").replace("_", " ").title()]
            for i in (extras.get("initiatives") or [])[:10]]
    if rows:
        _table(s, ["Ref", "Band", "RAG", "Owner", "Status"], rows, 0.6, 2.0, 12.1,
               col_w=[1.3, 2.0, 1.6, 4.0, 3.2])
    else:
        _tb(s, 0.6, 2.3, 11, 0.6, "No initiatives yet.", size=13, color=MUTED)

    # 12. Closing
    s = _blank(prs)
    _tb(s, 0.9, 2.6, 11.5, 0.9, "AXIOM Dynamics", size=32, color=BRASS, bold=True)
    _tb(s, 0.9, 3.6, 11.5, 1.4, [
        "This deck was generated from your active dataset by AXIOM's certified engines.",
        issued_line(issued, meta.get("dataset_version")),
        "support@axiomdynamics.app · axiomdynamics.app"], size=14, color=MUTED)

    out = io.BytesIO(); prs.save(out)
    return out.getvalue()


# ============================================================================
# PDF (issued, themed) — reportlab
# ============================================================================
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors as _rc
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image as RLImage, PageBreak)

_PINE = _rc.HexColor(PINE); _IVORY = _rc.HexColor(IVORY); _BRASS = _rc.HexColor(BRASS)
_MUTED = _rc.HexColor(MUTED); _PANEL = _rc.HexColor(PANEL)


def _pdf_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(_PINE)
    canvas.rect(0, 0, letter[0], letter[1], stroke=0, fill=1)
    canvas.setFillColor(_MUTED); canvas.setFont("Helvetica", 8)
    canvas.drawString(0.75 * inch, 0.5 * inch, "AXIOM Dynamics — Confidential")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(report: dict, extras: dict, meta: dict) -> bytes:
    extras = extras or {}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.9 * inch,
                            bottomMargin=0.8 * inch, leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Title"], textColor=_IVORY, fontSize=26, leading=30)
    KICK = ParagraphStyle("KICK", parent=ss["Normal"], textColor=_BRASS, fontSize=11, leading=13, spaceAfter=2)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=_IVORY, fontSize=16, leading=19, spaceBefore=10)
    BODY = ParagraphStyle("BODY", parent=ss["Normal"], textColor=_IVORY, fontSize=10.5, leading=15)
    MUT = ParagraphStyle("MUT", parent=ss["Normal"], textColor=_MUTED, fontSize=10, leading=14)
    company = report.get("company", {}); cur = company.get("currency", "")
    S = {s["id"]: s for s in report.get("sections", [])}
    issued = meta["issued_at"]
    story = []

    # cover — client logo leads (their board deck), AXIOM subordinate
    logo_png = _logo_from_meta(meta)
    story.append(Spacer(1, 1.1 * inch))
    if logo_png:
        sz = _px_size(logo_png)
        w, h = _fit_box(sz[0], sz[1], 3.6, 1.5) if sz else (3.0, 1.2)
        try:
            story += [RLImage(io.BytesIO(logo_png), width=w * inch, height=h * inch),
                      Spacer(1, 0.4 * inch)]
        except Exception:
            logo_png = None
    if not logo_png:
        story += [Spacer(1, 0.5 * inch), Paragraph("AXIOM", KICK)]
    story += [Paragraph(meta.get("company_name", company.get("name", "Company")), H1),
              Spacer(1, 0.15 * inch),
              Paragraph(meta.get("report_type", "Board Report"), MUT),
              Spacer(1, 0.1 * inch),
              Paragraph(issued_line(issued, meta.get("dataset_version")), MUT),
              Spacer(1, 0.3 * inch),
              Paragraph("Prepared by AXIOM Dynamics", MUT),
              PageBreak()]

    def tbl(headers, rows, widths):
        data = [headers] + rows
        t = Table(data, colWidths=[w * inch for w in widths])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _BRASS),
            ("TEXTCOLOR", (0, 0), (-1, 0), _PINE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 1), (-1, -1), _IVORY),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_PINE, _PANEL]),
            ("GRID", (0, 0), (-1, -1), 0.4, _MUTED),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return t

    # executive summary
    sm = S.get("summary", {}); sc = sm.get("scorecard", {}); hm = sm.get("headline_metric", {})
    story += [Paragraph("EXECUTIVE SUMMARY", KICK), Paragraph("The company at a glance", H2),
              Spacer(1, 0.1 * inch),
              Paragraph(f"<b>{hm.get('label', 'Enterprise Value')}:</b> "
                        f"{hm.get('value', 0):,.0f} {cur}", BODY),
              Paragraph(sm.get("takeaway", ""), MUT), Spacer(1, 0.12 * inch),
              tbl(["Metric", "Value"],
                  [["Health index", _fmt(sc.get("health_index"))],
                   ["Risk grade", sc.get("risk_grade", "—")],
                   ["Optimization", sc.get("optimization_status", "—")],
                   ["Optimizer uplift", f"{sc.get('optimization_uplift', 0):,.0f} {cur}"]],
                  [2.4, 3.6]),
              Spacer(1, 0.15 * inch)]
    for w in sm.get("four_answers", [])[:4]:
        story.append(Paragraph("• " + w, BODY))

    # valuation
    va = S.get("valuation", {}); dcf = va.get("dcf", {}); mc = dcf.get("monte_carlo", {})
    lenses = chart_valuation_lenses(dcf, va.get("real_options"))
    story += [PageBreak(), Paragraph("VALUATION", KICK),
              Paragraph("Three independent lenses", H2), Spacer(1, 0.1 * inch)]
    if lenses:
        story.append(RLImage(io.BytesIO(lenses), width=6.4 * inch, height=3.4 * inch))
    story += [Spacer(1, 0.1 * inch),
              tbl(["Lens", "Value"],
                  [["DCF enterprise value", f"{dcf.get('enterprise_value', 0):,.0f} {cur}"],
                   ["Monte Carlo mean", f"{mc.get('mean', 0):,.0f} {cur}"],
                   ["95% tail (CVaR)", f"{mc.get('cvar95', 0):,.0f} {cur}"],
                   ["WACC", _fmt(dcf.get("wacc"), pct=True)]], [3.0, 3.0])]

    # forecast fan
    fan = (S.get("outlook", {}).get("simulation_baseline", {}) or {}).get("revenue_fan") or []
    fanpng = chart_fan(fan)
    if fanpng:
        story += [PageBreak(), Paragraph("OUTLOOK", KICK),
                  Paragraph("Probabilistic revenue forecast", H2), Spacer(1, 0.1 * inch),
                  RLImage(io.BytesIO(fanpng), width=6.6 * inch, height=3.5 * inch)]

    # recommendations
    rrows = []
    for r in (extras.get("recommendations") or [])[:8]:
        ini = r.get("initiative") or {}
        disp = {"adopted": f"Adopted → {ini.get('ref', '')}", "parked": f"Parked → {ini.get('ref', '')}",
                "dismissed": "Dismissed", "none": "—"}.get(r.get("disposition"), r.get("disposition"))
        rrows.append([r.get("title", "")[:46], f"{r.get('expected_ev_impact', 0):+,.1f}", disp])
    if rrows:
        story += [PageBreak(), Paragraph("RECOMMENDATIONS", KICK),
                  Paragraph("AXIOM levers & decisions", H2), Spacer(1, 0.1 * inch),
                  tbl(["Recommendation", "EV impact", "Disposition"], rrows, [3.4, 1.2, 1.9])]

    doc.build(story, onFirstPage=_pdf_bg, onLaterPages=_pdf_bg)
    return buf.getvalue()
