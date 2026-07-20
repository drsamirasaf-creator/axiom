"""AXIOM board decks (PPTX) — comprehensive + executive — rendered from the same
board_report() payload the on-screen report uses, in the polished ivory board-
report visual language: dark deep-pine for cover / section dividers / closing;
ivory content slides with ink text and pine/brass accents; every content slide
carries a brass kicker, a serif HEADLINE stating the slide's finding, a chart or
card grid or report-styled table filling the content zone, and a slim footer
(company · issued · page). The PDF path lives in report_pdf.py.
"""
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def issued_line(issued_at: datetime, dataset_version) -> str:
    dv = f" · Data version {dataset_version}" if dataset_version is not None else ""
    return f"Issued {issued_at.strftime('%d %b %Y, %H:%M')}{dv}"


def report_filename(company: str, report_type: str, fmt: str, issued_at: datetime) -> str:
    safe = "".join(ch if (ch.isalnum() or ch in " -") else "" for ch in (company or "Company")).strip()
    safe = "_".join(safe.split()) or "Company"
    rt = "_".join((report_type or "Report").split())
    return f"{safe}_{rt}_{issued_at.strftime('%Y-%m-%d_%H%M')}.{fmt}"


# ============================================================================
# Palette — ivory report language
# ============================================================================
IVORY = "#F5F2EA"      # content background
IVORY2 = "#ECE7D8"     # zebra / raised panel
CREAM = "#FBF9F2"      # card face
INK = "#1E2A22"        # primary text on ivory
SLATE = "#5A6B60"      # secondary text on ivory
PINE = "#0E1F17"       # dark background (cover / divider / closing) + table header
IVORYTX = "#F4F1E6"    # text on dark
BRASS = "#B0894B"      # brass accent
PINEACC = "#2E6B4F"    # pine chart series
GREEN = "#1FA971"; AMBER = "#E0A82E"; RED = "#D9534F"
GRIDLT = "#DED8C8"     # light grid on ivory
_RGB = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
SERIF = "Georgia"
SANS = "Arial"


# ============================================================================
# Charts — ivory facecolor, ink axes, pine/brass series
# ============================================================================
def _fig(w=8.4, h=4.4):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    fig.patch.set_facecolor(IVORY); ax.set_facecolor(IVORY)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#B9B29C")
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(axis="y", color=GRIDLT, lw=0.9)
    return fig, ax


def _png(fig):
    buf = io.BytesIO(); fig.tight_layout(pad=0.7)
    fig.savefig(buf, format="png", facecolor=IVORY, bbox_inches="tight")
    plt.close(fig); return buf.getvalue()


def chart_fan(fan, title=""):
    if not fan:
        return None
    yrs = [p["year"] for p in fan]
    fig, ax = _fig()
    ax.fill_between(yrs, [p.get("p05") for p in fan], [p.get("p95") for p in fan], color=BRASS, alpha=0.16, lw=0)
    ax.fill_between(yrs, [p.get("p25") for p in fan], [p.get("p75") for p in fan], color=BRASS, alpha=0.30, lw=0)
    ax.plot(yrs, [p.get("p50") for p in fan], color=PINEACC, lw=2.6, marker="o", ms=5)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.set_xticks(yrs)
    return _png(fig)


def chart_lenses(dcf, real_options):
    labels, vals, cols = [], [], []
    if dcf:
        labels.append("DCF (intrinsic)"); vals.append(dcf.get("enterprise_value")); cols.append(PINEACC)
        mc = dcf.get("monte_carlo") or {}
        if mc.get("mean") is not None:
            labels.append("Monte Carlo mean"); vals.append(mc["mean"]); cols.append(BRASS)
        if mc.get("cvar95") is not None:
            labels.append("95% tail (CVaR)"); vals.append(mc["cvar95"]); cols.append(AMBER)
    try:
        labels.append("Real-opt expand"); vals.append(real_options["options"]["expand"]["flexibility_value"]); cols.append(SLATE)
    except (KeyError, TypeError):
        pass
    keep = [(l, v, c) for l, v, c in zip(labels, vals, cols) if v is not None]
    if not keep:
        return None
    fig, ax = _fig(7.8, 4.1)
    bars = ax.bar(range(len(keep)), [k[1] for k in keep], color=[k[2] for k in keep], width=0.62)
    ax.set_xticks(range(len(keep))); ax.set_xticklabels([k[0] for k in keep], fontsize=9, color=INK)
    for b, k in zip(bars, keep):
        ax.text(b.get_x() + b.get_width() / 2, k[1], f"{k[1]:,.0f}", ha="center", va="bottom", color=INK, fontsize=9)
    return _png(fig)


def chart_tornado(recs):
    items = [(r.get("title", r.get("move", "")), r.get("expected_ev_impact"))
             for r in (recs or []) if r.get("expected_ev_impact") is not None]
    if not items:
        return None
    items.sort(key=lambda t: abs(t[1]))
    fig, ax = _fig(8.4, 3.2 + 0.4 * len(items))
    vals = [t[1] for t in items]
    ax.barh(range(len(vals)), vals, color=[GREEN if v >= 0 else RED for v in vals], height=0.6)
    ax.set_yticks(range(len(vals))); ax.set_yticklabels([t[0][:42] for t in items], fontsize=9, color=INK)
    ax.axvline(0, color=SLATE, lw=0.9)
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:+,.1f}", va="center", ha="left" if v >= 0 else "right", color=INK, fontsize=8.5)
    ax.grid(axis="x", color=GRIDLT, lw=0.9); ax.grid(axis="y", visible=False)
    return _png(fig)


def chart_frontier(points, recommended):
    if not points:
        return None
    x = [p["safety_tail_margin"] for p in points]; y = [p["value_mean_ev"] for p in points]
    eff = [p.get("pareto_efficient") for p in points]
    fig, ax = _fig(8.2, 4.3)
    ax.plot(x, y, color="#C7C0AC", lw=1.2)
    ax.scatter([a for a, e in zip(x, eff) if e], [b for b, e in zip(y, eff) if e], color=PINEACC, s=42, zorder=4, label="Pareto-efficient")
    ax.scatter([a for a, e in zip(x, eff) if not e], [b for b, e in zip(y, eff) if not e], color="#C7C0AC", s=28, zorder=3)
    if recommended:
        ax.scatter([recommended["safety_tail_margin"]], [recommended["value_mean_ev"]], edgecolor=BRASS, facecolor="none", s=170, lw=2.4, zorder=5, label="recommended")
    ax.set_xlabel("tail solvency margin", fontsize=8.5, color=SLATE); ax.set_ylabel("expected EV", fontsize=8.5, color=SLATE)
    leg = ax.legend(fontsize=8.5, frameon=False)
    for t in leg.get_texts():
        t.set_color(SLATE)
    return _png(fig)


def chart_radar(l1):
    pts = [(o.get("title", o.get("code", "")), o.get("score")) for o in (l1 or []) if o.get("score") is not None]
    if len(pts) < 3:
        return None
    labels = [p[0][:16] for p in pts]; vals = [p[1] for p in pts]
    n = len(vals); ang = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    v2 = vals + vals[:1]; a2 = ang + ang[:1]
    fig = plt.figure(figsize=(5.8, 5.4), dpi=150); fig.patch.set_facecolor(IVORY)
    ax = fig.add_subplot(111, polar=True); ax.set_facecolor(IVORY)
    ax.plot(a2, v2, color=PINEACC, lw=2.2); ax.fill(a2, v2, color=BRASS, alpha=0.22)
    ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=7.5, color=INK)
    ax.set_ylim(0, 10); ax.set_yticks([2, 4, 6, 8, 10]); ax.tick_params(colors=SLATE)
    ax.grid(color=GRIDLT); ax.spines["polar"].set_color("#C7C0AC")
    return _png(fig)


def chart_trend(points, title=""):
    pts = [p for p in (points or []) if p.get("value") is not None]
    if len(pts) < 2:
        return None
    fig, ax = _fig(8.6, 4.1)
    hx = [p["year"] for p in pts if p.get("kind") != "fcst"]; hy = [p["value"] for p in pts if p.get("kind") != "fcst"]
    fx = [p["year"] for p in pts if p.get("kind") == "fcst"]; fy = [p["value"] for p in pts if p.get("kind") == "fcst"]
    if hx:
        ax.plot(hx, hy, color=PINEACC, lw=2.6, marker="o", ms=5, label="actual")
    if fx:
        bx = ([hx[-1]] + fx) if hx else fx; by = ([hy[-1]] + fy) if hx else fy
        ax.plot(bx, by, color=BRASS, lw=2.4, ls="--", marker="o", ms=5, label="forecast")
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.set_xticks([p["year"] for p in pts])
    if hx and fx:
        leg = ax.legend(fontsize=8.5, frameon=False, loc="upper left")
        for t in leg.get_texts():
            t.set_color(SLATE)
    return _png(fig)


def chart_mc_hist(hist, percentiles=None):
    if not hist or not hist.get("counts"):
        return None
    counts = hist["counts"]; start = hist.get("bin_start", 0); w = hist.get("bin_width", 1)
    xs = [start + i * w for i in range(len(counts))]
    fig, ax = _fig(8.6, 4.1)
    ax.bar(xs, counts, width=w * 0.92, color=PINEACC, alpha=0.85)
    for key, col in (("p05", RED), ("p50", BRASS), ("p95", GREEN)):
        v = (percentiles or {}).get(key)
        if v is not None:
            ax.axvline(v, color=col, lw=1.6, ls="--")
            ax.text(v, max(counts) * 0.97, key, color=col, fontsize=8, ha="center")
    return _png(fig)


def chart_bars(labels, values, title="", colors=None, horizontal=False, fmt="{:,.1f}"):
    keep = [(l, v) for l, v in zip(labels or [], values or []) if v is not None]
    if not keep:
        return None
    labels = [k[0] for k in keep]; values = [k[1] for k in keep]
    colors = colors or [BRASS] * len(values)
    fig, ax = _fig(8.6, max(3.2, 0.55 * len(values) + 1.6) if horizontal else 4.1)
    if horizontal:
        ax.barh(range(len(values)), values, color=colors, height=0.62)
        ax.set_yticks(range(len(values))); ax.set_yticklabels(labels, fontsize=9, color=INK)
        for i, v in enumerate(values):
            ax.text(v, i, " " + fmt.format(v), va="center", color=INK, fontsize=8.5)
        ax.grid(axis="x", color=GRIDLT, lw=0.9); ax.grid(axis="y", visible=False)
    else:
        ax.bar(range(len(values)), values, color=colors, width=0.62)
        ax.set_xticks(range(len(values))); ax.set_xticklabels(labels, fontsize=9, color=INK)
        for i, v in enumerate(values):
            ax.text(i, v, fmt.format(v), ha="center", va="bottom", color=INK, fontsize=8.5)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    return _png(fig)


def chart_grouped(labels, a, b, name_a, name_b, title=""):
    idx = [i for i, (x, y) in enumerate(zip(a, b)) if x is not None and y is not None]
    if not idx:
        return None
    labels = [labels[i] for i in idx]; aa = [a[i] for i in idx]; bb = [b[i] for i in idx]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = _fig(8.6, 4.1)
    ax.bar(x - w / 2, aa, w, color=PINEACC, label=name_a); ax.bar(x + w / 2, bb, w, color=BRASS, label=name_b)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5, color=INK)
    leg = ax.legend(fontsize=8.5, frameon=False)
    for t in leg.get_texts():
        t.set_color(SLATE)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    return _png(fig)


def chart_paths(sample_paths, years, title="", color=PINEACC, cap=40):
    if not sample_paths or not years:
        return None
    fig, ax = _fig(8.6, 4.1)
    for path in sample_paths[:cap]:
        if len(path) == len(years):
            ax.plot(years, path, color=color, lw=0.7, alpha=0.28)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.set_xticks(years)
    return _png(fig)


# ============================================================================
# Logos
# ============================================================================
from PIL import Image, ImageDraw, ImageFont
import matplotlib.font_manager as _fm


def _px_size(png):
    try:
        return Image.open(io.BytesIO(png)).size
    except Exception:
        return None


def _fit_box(iw, ih, mw, mh):
    if not iw or not ih:
        return mw, mh
    s = min(mw / iw, mh / ih)
    return iw * s, ih * s


def wordmark_png(text, bg_hex=PINE, fg_hex=IVORYTX, accent_hex=BRASS, w=680, h=260):
    img = Image.new("RGB", (w, h), _RGB(bg_hex)); d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(_fm.findfont("DejaVu Sans:bold"), 62)
    except Exception:
        font = ImageFont.load_default()
    bb = d.textbbox((0, 0), text, font=font); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x, y = (w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]
    d.text((x, y), text, fill=_RGB(fg_hex), font=font)
    d.rectangle([(w - tw) / 2, y + th + 18, (w - tw) / 2 + tw, y + th + 26], fill=_RGB(accent_hex))
    buf = io.BytesIO(); img.save(buf, "PNG"); return buf.getvalue()


def _logo_from_meta(meta):
    lg = (meta or {}).get("logo")
    if not lg:
        return None
    return (lg[0] if isinstance(lg, (tuple, list)) else lg.get("bytes")) or None


# ============================================================================
# PPTX design system
# ============================================================================
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

_C = lambda h: RGBColor.from_string(h.lstrip("#"))
EMU_IN = 914400
SW, SH = 13.333, 7.5


def _bgc(slide, color):
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = _C(color)


def _slide(prs, dark=False):
    s = prs.slides.add_slide(prs.slide_layouts[6]); _bgc(s, PINE if dark else IVORY)
    return s


def _text(slide, l, t, w, h, lines, size=13, color=INK, bold=False, font=SANS,
          align=PP_ALIGN.LEFT, italic=False, tracking=None, caps=False, anchor=None, line_spacing=None):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Pt(2); tf.margin_top = tf.margin_bottom = Pt(1)
    if anchor:
        tf.vertical_anchor = anchor
    items = lines if isinstance(lines, (list, tuple)) else [lines]
    for i, ln in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        r = p.add_run(); r.text = (str(ln).upper() if caps else str(ln))
        f = r.font; f.size = Pt(size); f.bold = bold; f.italic = italic; f.name = font; f.color.rgb = _C(color)
        if tracking is not None:
            r._r.get_or_add_rPr().set("spc", str(int(tracking * 100)))
    return box


def _rule(slide, l, t, w, color=BRASS, h=0.028):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = _C(color); sh.line.fill.background(); sh.shadow.inherit = False
    return sh


def _pic(slide, png, l, t, w, h):
    if not png:
        return
    sz = _px_size(png)
    if sz:
        fw, fh = _fit_box(sz[0], sz[1], w, h)
        l = l + (w - fw) / 2; t = t + (h - fh) / 2; w, h = fw, fh
    try:
        slide.shapes.add_picture(io.BytesIO(png), Inches(l), Inches(t), Inches(w), Inches(h))
    except Exception:
        pass


class Deck:
    def __init__(self, prs, company, issued, dsv, logo):
        self.prs, self.company, self.issued, self.dsv, self.logo = prs, company, issued, dsv, logo
        self.page = 0; self.phase = ""

    def _footer(self, s):
        self.page += 1
        iss = self.issued.strftime("%d %b %Y") if self.issued else ""
        _text(s, 0.62, 7.02, 9.5, 0.32, f"{self.company}   ·   Issued {iss}", size=8, color=SLATE)
        _text(s, 10.6, 7.02, 2.15, 0.32, str(self.page), size=8, color=SLATE, align=PP_ALIGN.RIGHT)

    def content(self, kicker, headline):
        s = _slide(self.prs); self._footer(s)
        _text(s, 0.62, 0.42, 12.0, 0.3, (self.phase + "  ·  " + kicker) if self.phase else kicker,
              size=10.5, color=BRASS, bold=True, caps=True, tracking=2.2)
        _text(s, 0.6, 0.74, 12.1, 1.0, headline, size=25, color=INK, bold=True, font=SERIF, line_spacing=1.02)
        _rule(s, 0.63, 1.72, 2.6)
        return s

    def divider(self, phase_no, name, desc, idx, total):
        self.phase = name
        s = _slide(self.prs, dark=True); self.page += 1
        _text(s, 0.9, 2.3, 3.0, 1.3, f"{phase_no:02d}", size=64, color=BRASS, bold=True, font=SERIF)
        _rule(s, 0.94, 3.72, 3.4, color=BRASS, h=0.045)
        _text(s, 0.9, 3.9, 11.4, 1.0, name, size=40, color=IVORYTX, bold=True, font=SERIF)
        _text(s, 0.94, 5.0, 11.0, 0.6, desc, size=16, color="#AEBEB0", italic=True)
        _text(s, 0.94, 7.0, 5.0, 0.3, f"Section {idx} of {total}", size=9.5, color="#8CA093", caps=True, tracking=2)
        return s

    def placeholder(self, kicker, headline, message):
        s = self.content(kicker, headline)
        pan = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.62), Inches(2.5), Inches(12.1), Inches(3.0))
        pan.fill.solid(); pan.fill.fore_color.rgb = _C(IVORY2); pan.line.color.rgb = _C(GRIDLT); pan.line.width = Pt(0.75); pan.shadow.inherit = False
        _text(s, 1.0, 2.95, 11.3, 0.4, "Available once this becomes active", size=12, color=BRASS, bold=True, caps=True, tracking=1.5)
        _text(s, 1.0, 3.5, 11.3, 1.6, message, size=15, color=SLATE, italic=True, line_spacing=1.15)
        return s

    def insight(self, s, text, top=6.35):
        _rule(s, 0.63, top - 0.04, 0.5, color=BRASS, h=0.03)
        _text(s, 0.63, top, 12.1, 0.55, text, size=12.5, color=SLATE, font=SERIF, italic=True, line_spacing=1.1)

    def cards(self, s, cards, top=2.15, cols=2, height=None, left=0.62, width=12.1):
        n = len(cards); rows = (n + cols - 1) // cols; gap = 0.28
        cw = (width - gap * (cols - 1)) / cols
        ch = height or min(1.95, (6.85 - top - gap * (rows - 1)) / rows)
        for i, (label, value, sub, accent) in enumerate(cards):
            r, c = divmod(i, cols)
            x = left + c * (cw + gap); y = top + r * (ch + gap)
            card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(cw), Inches(ch))
            card.fill.solid(); card.fill.fore_color.rgb = _C(CREAM); card.line.color.rgb = _C(GRIDLT); card.line.width = Pt(0.75); card.shadow.inherit = False
            _rule(s, x + 0.25, y + 0.26, 0.55, color=accent or BRASS, h=0.045)
            _text(s, x + 0.25, y + 0.4, cw - 0.5, 0.32, label, size=10, color=SLATE, bold=True, caps=True, tracking=1.2)
            _text(s, x + 0.23, y + 0.7, cw - 0.44, ch - 1.0, str(value), size=28, color=accent or INK, bold=True, font=SERIF)
            if sub:
                _text(s, x + 0.25, y + ch - 0.48, cw - 0.5, 0.4, sub, size=10.5, color=SLATE)

    def table(self, s, headers, rows, left=0.62, top=2.1, width=12.1, col_w=None, anchors=None, fsize=11, row_h=0.42):
        anchors = anchors or set()
        nrows, ncols = len(rows) + 1, len(headers)
        gt = s.shapes.add_table(nrows, ncols, Inches(left), Inches(top), Inches(width), Inches(row_h * nrows)).table
        gt.first_row = False; gt.horz_banding = False
        if col_w:
            for i, w in enumerate(col_w):
                gt.columns[i].width = Inches(w)
        for j, h in enumerate(headers):
            c = gt.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = _C(PINE); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = Pt(7); c.margin_top = c.margin_bottom = Pt(3)
            p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT if j else PP_ALIGN.LEFT
            r = p.add_run(); r.text = str(h); r.font.size = Pt(fsize); r.font.bold = True; r.font.name = SANS; r.font.color.rgb = _C(IVORYTX)
        for i, row in enumerate(rows, start=1):
            anchor = row[0] in anchors if row else False
            for j, val in enumerate(row):
                c = gt.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = _C(IVORY2 if (i % 2 == 0) else CREAM)
                c.vertical_anchor = MSO_ANCHOR.MIDDLE; c.margin_left = Pt(7); c.margin_top = c.margin_bottom = Pt(3)
                tf = c.text_frame
                main, chip = (val if isinstance(val, tuple) else (val, None))
                p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT if j else PP_ALIGN.LEFT
                r = p.add_run(); r.text = "" if main is None else str(main)
                r.font.size = Pt(fsize); r.font.bold = anchor; r.font.name = SANS; r.font.color.rgb = _C(INK)
                if chip:
                    pp = tf.add_paragraph(); pp.alignment = PP_ALIGN.RIGHT if j else PP_ALIGN.LEFT
                    rr = pp.add_run(); rr.text = chip; rr.font.size = Pt(max(fsize - 2.5, 7)); rr.font.bold = True; rr.font.name = SANS; rr.font.color.rgb = _C(AMBER)
        return gt

    def cover(self, subtitle):
        s = _slide(self.prs, dark=True); self.page += 1
        if self.logo:
            sz = _px_size(self.logo); w, h = _fit_box(sz[0], sz[1], 4.4, 1.5) if sz else (3.6, 1.2)
            try:
                s.shapes.add_picture(io.BytesIO(self.logo), Inches(0.9), Inches(1.15), Inches(w), Inches(h))
            except Exception:
                self.logo = None
        base = 3.35 if self.logo else 2.5
        _text(s, 0.9, base, 11.5, 0.4, "AXIOM", size=15, color=BRASS, bold=True, caps=True, tracking=3)
        _text(s, 0.9, base + 0.4, 11.6, 1.3, self.company, size=40, color=IVORYTX, bold=True, font=SERIF)
        _text(s, 0.92, base + 1.75, 11.5, 0.5, subtitle, size=17, color="#AEBEB0")
        _rule(s, 0.94, base + 2.4, 3.6, color=BRASS, h=0.04)
        _text(s, 0.92, base + 2.6, 11.5, 0.4, issued_line(self.issued, self.dsv), size=12, color="#8CA093")
        _text(s, 0.9, 6.95, 11.5, 0.35, "Confidential — prepared by AXIOM Dynamics", size=9.5, color="#6E8377", italic=True)
        return s

    def closing(self):
        s = _slide(self.prs, dark=True); self.page += 1
        _text(s, 0.9, 2.6, 11.5, 0.9, "AXIOM Dynamics", size=34, color=BRASS, bold=True, font=SERIF)
        _text(s, 0.92, 3.7, 11.5, 1.5, [
            "This deck was generated from your active dataset by AXIOM's certified engines.",
            issued_line(self.issued, self.dsv),
            "support@axiomdynamics.app   ·   axiomdynamics.app"], size=14, color="#AEBEB0", line_spacing=1.3)
        return s


def _full_chart(d, kicker, headline, png, insight=None):
    s = d.content(kicker, headline)
    _pic(s, png, 0.9, 1.95, 11.5, 4.25 if insight else 4.75)
    if insight:
        d.insight(s, insight)
    return s


def _chart_rail(d, kicker, headline, png, rail_cards=None, rail_bullets=None, insight=None):
    s = d.content(kicker, headline)
    _pic(s, png, 0.62, 1.95, 8.0, 4.5)
    rx = 8.85
    if rail_cards:
        d.cards(s, rail_cards, top=2.05, cols=1, left=rx, width=3.9, height=min(1.55, 4.4 / max(1, len(rail_cards)) - 0.18))
    elif rail_bullets:
        _text(s, rx, 2.05, 3.9, 4.4, [f"•  {b}" for b in rail_bullets], size=12.5, color=INK, line_spacing=1.28)
    if insight:
        d.insight(s, insight)
    return s


def _fmt(v, pct=False):
    if v is None:
        return "—"
    return f"{v*100:.1f}%" if pct else f"{v:,.1f}"


def _big(v, sym=""):
    if v is None:
        return "—"
    if abs(v) >= 1000:
        return f"{sym}{v/1000:,.2f}B"
    return f"{sym}{v:,.0f}M"


def _rag_accent(rag):
    return {"green": GREEN, "amber": AMBER, "red": RED}.get(rag, BRASS)


def _rag_word(rag):
    return {"green": "Green", "amber": "Amber", "red": "Red"}.get(rag, "—")


# ============================================================================
# Comprehensive board deck
# ============================================================================
def build_pptx_comprehensive(report, extras, meta, data=None) -> bytes:
    extras = extras or {}; data = data or {}
    prs = Presentation(); prs.slide_width = Emu(int(SW * EMU_IN)); prs.slide_height = Emu(int(SH * EMU_IN))
    S = {s["id"]: s for s in report.get("sections", [])}
    company = report.get("company", {}); cur = company.get("currency", "")
    sym = {"USD": "$", "EUR": "€", "GBP": "£"}.get(cur, "")
    cname = meta.get("company_name", company.get("name", "Company"))
    d = Deck(prs, cname, meta["issued_at"], meta.get("dataset_version"), _logo_from_meta(meta))

    def hist(line):
        try:
            hy = [int(y) for y in data["periods"]["historical"]]
            blk = (data.get("income_statement") or {}).get(line, {})
            return [{"year": y, "value": blk.get(str(y)), "kind": "hist"} for y in hy if blk.get(str(y)) is not None]
        except Exception:
            return []

    def fcst(line):
        return [{"year": st["year"], "value": ((st.get("stochastic") or {}).get(line) or {}).get("expected"), "kind": "fcst"}
                for st in (S.get("proforma", {}).get("statements") or [])
                if ((st.get("stochastic") or {}).get(line) or {}).get("expected") is not None]

    di = S.get("diagnostic", {}); sm = S.get("summary", {}); va = S.get("valuation", {})
    ou = S.get("outlook", {}); ac = S.get("actions", {}); bd = S.get("best_decision", {})
    pf = S.get("proforma", {}); ap = S.get("appendix", {})
    kpi = {k["kpi"]: k for k in di.get("kpi_strip", [])}
    dcf = va.get("dcf", {}); mc = dcf.get("monte_carlo", {})

    # ---- INTRO ----
    d.cover("Comprehensive Board Presentation")
    d.section = "Overview"
    s = d.content("Agenda", "What this deck covers")
    _text(s, 0.7, 2.05, 0.6, 4.5, "01", size=15, color=BRASS, bold=True, font=SERIF)
    _text(s, 1.35, 2.02, 5.4, 4.5, ["Diagnose", "Dashboard & Reports", "SWOT Analysis",
          "Corporate Effectiveness", "Valuation", "Financial Forecasts", "Risk Analysis", "Benchmarking"],
          size=14.5, color=INK, line_spacing=1.34)
    _text(s, 7.0, 2.05, 0.6, 4.5, "02", size=15, color=BRASS, bold=True, font=SERIF)
    _text(s, 7.65, 2.02, 5.2, 4.5, ["Optimize", "Enterprise Optimization", "Dynamics & Simulation",
          "Scenario Analysis", "Target-State Planner", "Key Initiatives", "Discussion", "Twin Monitoring"],
          size=14.5, color=INK, line_spacing=1.34)
    s = d.content("How to read this deck", "Bands, RAG, and valuation lenses")
    d.cards(s, [
        ("P05–P95 bands", "90%", "the range outcomes fall within", PINEACC),
        ("RAG status", "R·A·G", "off-track / watch / on-track", BRASS),
        ("Three lenses", "DCF·MC·×", "intrinsic, distribution, multiples", PINEACC),
        ("Dispositions", "Adopted", "each rec → an initiative ref", AMBER)], top=2.15, cols=2)

    # ================= DIAGNOSE =================
    d.divider(1, "Diagnose", "Where the company stands today", 1, 14)

    # Dashboard
    d.section = "Dashboard"
    cards = []
    for label, key in [("Revenue", "Revenue"), ("EBITDA", "EBITDA"), ("Net income", "Net Income"),
                       ("Free cash flow", "FCFF"), ("ROIC", "ROIC"), ("WACC", "WACC")]:
        k = kpi.get(key, {})
        v = k.get("current")
        val = _fmt(v, pct=True) if k.get("format") == "percent" else _big(v, sym)
        tr = k.get("trend")
        sub = (f"{tr*100:+.1f}% vs prior" if tr is not None else "")
        cards.append((label, val, sub, INK))
    s = d.content("Dashboard & Reports", "The company at a glance")
    d.cards(s, cards, top=2.05, cols=3)
    # health
    comps = (di.get("health") or {}).get("components") or {}
    hidx = (di.get("health") or {}).get("index", sm.get("scorecard", {}).get("health_index"))
    _chart_rail(d, "Diagnostic", f"A health index of {_fmt(hidx)} out of 100",
                chart_bars(list(comps.keys()), [comps[k] for k in comps], "Health components", horizontal=True, fmt="{:.1f}") if comps else None,
                rail_cards=[("Risk grade", sm.get("scorecard", {}).get("risk_grade", "—"), "", _rag_accent("green")),
                            ("Optimizer uplift", _big(sm.get("scorecard", {}).get("optimization_uplift"), sym), "available", BRASS)],
                insight=(di.get("narrative") or [""])[0][:150] if di.get("narrative") else None)
    _full_chart(d, "Dashboard & Reports", "Revenue trajectory, actual and forecast",
                chart_trend(hist("revenue") + fcst("revenue")),
                insight=f"Median revenue reaches {_big((fcst('revenue')[-1]['value'] if fcst('revenue') else None), sym)} by {fcst('revenue')[-1]['year'] if fcst('revenue') else ''}.")
    _full_chart(d, "Dashboard & Reports", "EBITDA holds its trajectory", chart_trend(hist("ebitda") + fcst("ebitda")))
    # margin + alerts
    margins = []
    for p in hist("revenue"):
        eb = (data.get("income_statement") or {}).get("ebit", {}).get(str(p["year"]))
        if eb is not None and p["value"]:
            margins.append({"year": p["year"], "value": 100 * eb / p["value"], "kind": "hist"})
    for st in (pf.get("statements") or []):
        r = ((st.get("stochastic") or {}).get("revenue") or {}).get("expected"); e = ((st.get("stochastic") or {}).get("ebit") or {}).get("expected")
        if r and e is not None:
            margins.append({"year": st["year"], "value": 100 * e / r, "kind": "fcst"})
    runway = ou.get("cash_runway", {})
    alerts = []
    if runway.get("burning_cash"):
        alerts.append("Cash is burning — monitor runway")
    if (runway.get("p_cash_below_zero_ever") or 0) > 0.05:
        alerts.append(f"P(cash < 0) ever: {_fmt(runway.get('p_cash_below_zero_ever'), pct=True)}")
    for h in (ap.get("risk_heat_map") or []):
        if h.get("rag") == "red":
            alerts.append(f"{h.get('category')} risk elevated")
    _chart_rail(d, "Dashboard & Reports", "Operating margin trajectory", chart_trend(margins, "EBIT margin (%)"),
                rail_bullets=(alerts or ["No material alerts"]))

    # SWOT
    d.section = "SWOT"
    swot = extras.get("swot")
    if swot and swot.get("has_data"):
        cnt = swot.get("counts", {})
        s = d.content("SWOT Analysis", "Strengths, weaknesses, and where to act")
        d.cards(s, [("Strengths", cnt.get("strengths", 0), "internal · strong", GREEN),
                    ("Weaknesses", cnt.get("weaknesses", 0), "internal · weak", RED),
                    ("Opportunities", cnt.get("opportunities", 0), "external · strong", BRASS),
                    ("Threats", cnt.get("threats", 0), "external · weak", AMBER)], top=2.15, cols=2)
        for lab, key in [("Strengths", "strengths"), ("Weaknesses", "weaknesses"), ("Opportunities", "opportunities"), ("Threats", "threats")]:
            items = swot.get(key, [])
            if not items:
                continue
            s = d.content("SWOT Analysis", lab)
            d.table(s, ["Item", "Title", "Score", "RAG", "Theme"],
                    [[e.get("item_code"), (e.get("title") or "")[:38], _fmt(e.get("mean")), _rag_word(e.get("score_rag")), (e.get("theme") or "—")[:32]] for e in items[:8]],
                    col_w=[1.2, 4.2, 1.4, 1.6, 3.7], anchors=set(), fsize=10.5, row_h=0.5)
    else:
        d.placeholder("SWOT Analysis", "SWOT appears after your first assessment",
                      "SWOT is derived from your latest closed assessment cycle — strengths, weaknesses, opportunities and threats, each with score, RAG, sentiment theme and linked initiatives.")

    # CEI
    d.section = "Corporate Effectiveness"
    cei = extras.get("cei")
    if cei and cei.get("cei") is not None:
        _chart_rail(d, "Corporate Effectiveness", f"Composite Excellence Index of {cei['cei']:.1f} / 10",
                    chart_radar(cei.get("l1_subscores")),
                    rail_cards=[("CEI", f"{cei['cei']:.1f}", "of 10", BRASS),
                                ("Participants", str(cei.get("n_participants", 0)), "in the latest cycle", PINEACC)])
        subs = cei.get("l1_subscores") or []
        s = d.content("Corporate Effectiveness", "Capability subscores")
        d.table(s, ["Category", "Score", "Dispersion"],
                [[o.get("title", "")[:44], _fmt(o.get("score")), _fmt((o.get("dispersion") or {}).get("std"))] for o in subs[:11]],
                col_w=[8.0, 2.0, 2.1], fsize=10.5, row_h=0.4)
    else:
        d.placeholder("Corporate Effectiveness", "Excellence index appears after your first cycle",
                      "The Composite Excellence Index scores your organization across 13 capability domains with a 361-point taxonomy — a trend, a radar, subscores, and comment-theme sentiment.")

    # Valuation
    d.section = "Valuation"
    s = d.content("Valuation", f"Intrinsic value: {_big(dcf.get('enterprise_value'), sym)}")
    d.cards(s, [("DCF enterprise value", _big(dcf.get("enterprise_value"), sym), "intrinsic", PINEACC),
                ("Monte Carlo mean", _big(mc.get("mean"), sym), "distribution", BRASS),
                ("95% tail (CVaR)", _big(mc.get("cvar95"), sym), "downside", AMBER),
                ("WACC", _fmt(dcf.get("wacc"), pct=True), "discount rate", INK)], top=2.15, cols=2)
    _full_chart(d, "Valuation", "Three independent lenses agree on the range", chart_lenses(dcf, va.get("real_options")))
    _full_chart(d, "Valuation", "The value as a distribution, not a point", chart_mc_hist(mc.get("histogram"), mc.get("percentiles")),
                insight="Monte Carlo turns a single DCF number into a full distribution of futures.")
    _full_chart(d, "Valuation", "Which levers actually move enterprise value", chart_tornado(ac.get("recommendations")))
    ro = va.get("real_options", {}); opts = ro.get("options", {})
    s = d.content("Valuation", "Managerial flexibility a static DCF omits")
    d.table(s, ["Real option", "Flexibility value", "% of EV"],
            [[k.title(), _big((opts.get(k) or {}).get("flexibility_value"), sym), _fmt((opts.get(k) or {}).get("flexibility_pct_of_ev"), pct=True)] for k in opts],
            col_w=[5.0, 4.0, 3.1], row_h=0.5)
    rs = va.get("rate_sensitivity") or {}
    rrows = [[k.replace("_", " ").title(), _fmt(v)] for k, v in rs.items() if isinstance(v, (int, float))][:7]
    if rrows:
        s = d.content("Valuation", "How sensitive the value is to the discount rate")
        d.table(s, ["Measure", "Value"], rrows, col_w=[6.0, 6.1], row_h=0.55)

    # Financial Forecasts
    d.section = "Financial Forecasts"
    stmts = pf.get("statements") or []; yrs = [st["year"] for st in stmts]

    def band_table(title, headline, lines):
        s = d.content("Financial Forecasts", headline)
        rows = []
        for lk, label, anch in lines:
            cells = [label]
            for st in stmts:
                b = (st.get("stochastic") or {}).get(lk) or {}
                if b:
                    p = b.get("p_meets_plan")
                    cells.append((f"{_big(b.get('plan'), sym)}", (f"P {p*100:.0f}%" if p is not None else None)))
                else:
                    cells.append("—")
            rows.append(cells)
        d.table(s, ["Line"] + [str(y) for y in yrs], rows, col_w=[2.4] + [ (9.7/len(yrs)) ]*len(yrs),
                anchors={l[1] for l in lines if l[2]}, fsize=10, row_h=0.62)
    band_table("IS", "Pro-forma income statement, with plan-attainment odds",
               [("revenue", "Revenue", True), ("ebit", "EBIT", True), ("ebitda", "EBITDA", True), ("net_income", "Net income", True)])
    band_table("BS", "Pro-forma balance sheet",
               [("total_assets", "Total assets", True), ("equity", "Equity", True), ("cash", "Cash", False)])
    band_table("CF", "Pro-forma cash flow",
               [("cfo", "Operating cash flow", True), ("fcff", "FCFF", True), ("fcfe", "FCFE", True)])
    sb = ou.get("simulation_baseline", {})
    _full_chart(d, "Financial Forecasts", "Revenue: the median path and its P05–P95 band", chart_fan(sb.get("revenue_fan")))
    _full_chart(d, "Financial Forecasts", "Free cash flow to the firm", chart_fan(sb.get("fcff_fan")))
    _full_chart(d, "Financial Forecasts", "The cash balance stays comfortably positive", chart_fan(sb.get("cash_fan")))
    pa = ou.get("plan_attainment") or {}
    s = d.content("Financial Forecasts", f"Only {(pa.get('p_all_three') or 0)*100:.0f}% odds of hitting all plan targets at once")
    d.cards(s, [("Revenue target", _fmt(pa.get("p_revenue_target"), pct=True), "year 1", PINEACC),
                ("Margin target", _fmt(pa.get("p_margin_target"), pct=True), "year 1", BRASS),
                ("FCFF target", _fmt(pa.get("p_fcff_target"), pct=True), "year 1", AMBER),
                ("All three", _fmt(pa.get("p_all_three"), pct=True), "simultaneously", RED if (pa.get("p_all_three") or 0) < 0.35 else GREEN)], top=2.15, cols=2)
    s = d.content("Financial Forecasts", "Comprehensive income under the accounting framework")
    _text(s, 0.62, 2.05, 12.1, 0.4, f"Accounting framework: {pf.get('accounting_framework', '—')}", size=13, color=BRASS, bold=True)
    _text(s, 0.62, 2.6, 12.1, 3.8, [f"•  {w}" for w in (pf.get("narrative") or [])[:4]], size=13.5, color=INK, line_spacing=1.3)

    # Risk
    d.section = "Risk Analysis"
    cov = ou.get("coverage", {}); rg = di.get("risk_grade", {})
    s = d.content("Risk Analysis", f"Risk grade {rg.get('grade', sm.get('scorecard', {}).get('risk_grade','—'))}, with solvency intact")
    d.cards(s, [("Risk grade", rg.get("grade", sm.get("scorecard", {}).get("risk_grade", "—")), "", GREEN),
                ("Distance to default", _fmt(cov.get("distance_to_default_sigmas")), "sigmas", PINEACC),
                ("P(EV < debt)", _fmt(cov.get("p_ev_below_debt"), pct=True), "", BRASS),
                ("Total debt", _big(cov.get("total_debt"), sym), "", INK)], top=2.15, cols=2)
    _full_chart(d, "Risk Analysis", "Where cash-flow variance actually comes from",
                chart_bars([h.get("category") for h in (ap.get("risk_heat_map") or [])], [h.get("score") for h in (ap.get("risk_heat_map") or [])],
                           "Risk heat map (variance share)", colors=[_rag_accent(h.get("rag")) for h in (ap.get("risk_heat_map") or [])], horizontal=True, fmt="{:.0f}"),
                insight=f"Distance to default is {_fmt(cov.get('distance_to_default_sigmas'))} sigmas from the barrier.")
    evt = ap.get("extreme_value_tail") or {}; covs = ap.get("covenants") or {}
    erows = [[k.replace("_", " ").title(), _big(v, sym) if abs(v) > 5 else _fmt(v)] for k, v in evt.items() if isinstance(v, (int, float))][:5]
    crows = [[k.replace("_", " ").title(), _fmt(v)] for k, v in (covs.items() if isinstance(covs, dict) else []) if isinstance(v, (int, float))][:5]
    if erows or crows:
        s = d.content("Risk Analysis", "Extreme-value tail and covenant headroom")
        if erows:
            d.table(s, ["Tail measure (EVT)", "Value"], erows, left=0.62, top=2.1, width=5.9, col_w=[3.6, 2.3], row_h=0.5)
        if crows:
            d.table(s, ["Covenant", "Value"], crows, left=6.85, top=2.1, width=5.9, col_w=[3.6, 2.3], row_h=0.5)

    # Benchmarking
    d.section = "Benchmarking"
    bench = di.get("benchmark", {}); bkpis = extras.get("benchmark_kpis") or []
    if bench and (bench.get("index") is not None or bkpis):
        s = d.content("Benchmarking", f"Benchmark index {_fmt(bench.get('index'))} versus the sector")
        _text(s, 0.62, 2.05, 12.1, 2.0, (bench.get("narrative") or "")[:360], size=13.5, color=INK, line_spacing=1.25)
        grp = [k for k in bkpis if k.get("score") is not None][:9]
        if grp:
            _full_chart(d, "Benchmarking", "Where the company leads and lags peers",
                        chart_bars([k.get("label", k.get("kpi", ""))[:16] for k in grp], [k.get("score") for k in grp],
                                   "Benchmark scores (1.0 = in line)", colors=[_rag_accent(k.get("rag")) for k in grp], horizontal=True, fmt="{:.2f}"))
            def _bv(k, key):
                v = k.get(key)
                return _fmt(v, pct=True) if k.get("format") == "percent" else _fmt(v)
            s = d.content("Benchmarking", "Company versus sector, KPI by KPI")
            d.table(s, ["KPI", "Company", "Sector", "RAG"],
                    [[k.get("label", k.get("kpi")), _bv(k, "actual"), _bv(k, "benchmark"), _rag_word(k.get("rag"))] for k in grp],
                    col_w=[5.0, 2.4, 2.4, 2.3], row_h=0.45, fsize=10.5)
    else:
        d.placeholder("Benchmarking", "Peer benchmarking appears with a sector set",
                      "Benchmarking compares your margins, growth, ROIC and leverage against a curated sector peer set.")

    # ================= OPTIMIZE =================
    d.divider(2, "Optimize", "What should change, and by how much", 8, 14)

    d.section = "Enterprise Optimization"
    plan = ac.get("optimizer_plan") or []
    s = d.content("Enterprise Optimization", (ac.get("takeaway") or "The optimizer's coordinated multi-year plan")[:80])
    d.table(s, ["Step", "Revenue growth", "Net borrowing %", "Revenue target"],
            [[f"Year {p.get('step')}", _fmt(p.get("growth"), pct=True), _fmt(p.get("net_borrowing_pct_rev"), pct=True), _big(p.get("revenue_target"), sym)] for p in plan[:6]],
            col_w=[2.0, 3.2, 3.2, 3.6], row_h=0.5)
    _text(s, 0.63, 6.4, 12, 0.5, f"Optimization uplift available: {_big(ac.get('optimization_uplift'), sym)} of value over the status quo.", size=13, color=BRASS, bold=True, font=SERIF, italic=True)
    _full_chart(d, "Enterprise Optimization", (bd.get("takeaway") or "The value–risk frontier over capital structure")[:80],
                chart_frontier((bd.get("frontier") or {}).get("points"), (bd.get("frontier") or {}).get("recommended")))
    s = d.content("Enterprise Optimization", "Recommendations, ranked — with their disposition")
    rr = []
    for r in (extras.get("recommendations") or [])[:7]:
        ini = r.get("initiative") or {}
        chip = {"adopted": f"Adopted → {ini.get('ref','')}" + (f", {_rag_word(ini.get('rag'))}" if ini.get('rag') else ""),
                "parked": f"Parked → {ini.get('ref','')}", "dismissed": "Dismissed", "none": "—"}.get(r.get("disposition"), r.get("disposition"))
        rr.append([(r.get("title") or "")[:44], _big(r.get("expected_ev_impact"), sym), chip])
    d.table(s, ["Recommendation", "EV impact", "Disposition"], rr, col_w=[6.6, 2.2, 3.3], row_h=0.5)
    ud = ac.get("uplift_derivation", {}).get("decomposition") if isinstance(ac.get("uplift_derivation"), dict) else None
    if isinstance(ud, dict) and ud:
        s = d.content("Enterprise Optimization", "Where the optimization uplift comes from")
        d.cards(s, [("Growth policy", _big(ud.get("growth_policy"), sym), "", PINEACC),
                    ("Financing policy", _big(ud.get("financing_policy"), sym), "", BRASS),
                    ("Interaction", _big(ud.get("interaction"), sym), "", AMBER),
                    ("Total uplift", _big(ud.get("total_deterministic_path") or ac.get("optimization_uplift"), sym), "over status quo", GREEN)], top=2.15, cols=2)
    sp = (bd.get("shadow_prices") or {})
    if sp:
        s = d.content("Enterprise Optimization", "The shadow price of each binding constraint")
        d.table(s, ["Constraint", "Shadow price"], [[k.replace("_", " ").title(), _big(v, sym)] for k, v in sp.items()], col_w=[7.0, 5.1], row_h=0.6)

    # Dynamics
    d.section = "Dynamics & Simulation"
    dy = ou.get("simulation_baseline", {}); pyrs = dy.get("years") or []
    _full_chart(d, "Dynamics & Simulation", "A thousand simulated revenue futures", chart_paths((dy.get("sample_paths") or {}).get("revenue"), pyrs, "Simulated revenue paths"))
    _full_chart(d, "Dynamics & Simulation", "Cash paths stay above zero in the base case", chart_paths((dy.get("sample_paths") or {}).get("cash"), pyrs, "Simulated cash paths", color=GREEN))
    _full_chart(d, "Dynamics & Simulation", "Free-cash-flow paths across the horizon", chart_paths((dy.get("sample_paths") or {}).get("fcff"), pyrs, "Simulated FCFF paths", color=AMBER))
    _full_chart(d, "Dynamics & Simulation", "The resulting distribution of enterprise value", chart_mc_hist(mc.get("histogram"), mc.get("percentiles")))

    # Scenario
    d.section = "Scenario Analysis"
    rec = ou.get("simulation_recession", {})
    s = d.content("Scenario Analysis", "Baseline versus a recession scenario")
    _pic(s, chart_fan(sb.get("revenue_fan"), "Baseline revenue"), 0.6, 2.0, 6.15, 4.4)
    _pic(s, chart_fan(rec.get("revenue_fan"), "Recession revenue"), 6.95, 2.0, 6.15, 4.4)
    _full_chart(d, "Scenario Analysis", "The frontier maps value against tail-safety",
                chart_frontier((bd.get("frontier") or {}).get("points"), (bd.get("frontier") or {}).get("recommended")),
                insight=f"Recession P(cash < 0) ever: {_fmt(rec.get('p_cash_below_zero'), pct=True)}.")

    # Target-State
    d.section = "Target-State Planner"
    if plan:
        base_rev = hist("revenue"); cur_rev = base_rev[-1]["value"] if base_rev else None
        tgt = plan[-1].get("revenue_target")
        s = d.content("Target-State Planner", "The gap between today and the target state")
        d.cards(s, [("Current revenue", _big(cur_rev, sym), "latest actual", INK),
                    ("Target revenue", _big(tgt, sym), "optimizer plan", PINEACC),
                    ("Revenue gap", _big((tgt - cur_rev) if (tgt and cur_rev) else None, sym), "to close", BRASS),
                    ("Optimizer uplift", _big(ac.get("optimization_uplift"), sym), "available", AMBER)], top=2.15, cols=2)
        _full_chart(d, "Target-State Planner", "The revenue ladder to the target",
                    chart_trend([{"year": p.get("step"), "value": p.get("revenue_target"), "kind": "fcst"} for p in plan], "Revenue target by step"))
    else:
        d.placeholder("Target-State Planner", "Set targets to quantify each gap",
                      "Define a desired future state and AXIOM quantifies each gap and maps it to the value-creating lever that closes it.")

    # Key Initiatives
    d.section = "Key Initiatives"
    inits = extras.get("initiatives") or []
    if inits:
        s = d.content("Key Initiatives", "The execution register, by priority band")
        d.table(s, ["Ref", "Band", "RAG", "Owner", "Status"],
                [[i.get("ref_code"), (i.get("current_priority") or "").title(), _rag_word(i.get("rag")), i.get("owner_name") or "—", (i.get("status") or "").replace("_", " ").title()] for i in inits[:10]],
                col_w=[1.3, 2.0, 1.6, 4.0, 3.2], row_h=0.5)
        csf = extras.get("csf_health") or {}
        s = d.content("Key Initiatives", "Critical-success-factor health")
        d.cards(s, [("Holding", csf.get("holding", 0), "on track", GREEN), ("At risk", csf.get("at_risk", 0), "watch", AMBER), ("Broken", csf.get("broken", 0), "action", RED)], top=2.2, cols=3, height=1.9)
    else:
        d.placeholder("Key Initiatives", "The execution register fills as you adopt",
                      "Turns decisions into tracked initiatives — banded by priority, with a RAG, an owner, critical success factors, and expected-vs-realized impact.")

    # Discussion
    d.section = "Discussion"
    disc = extras.get("discussion") or {}
    if disc.get("threads") or disc.get("pending_proposals"):
        s = d.content("Discussion", "The conversation, and what's pending")
        d.cards(s, [("Threads", disc.get("threads", 0), "open discussions", PINEACC),
                    ("Posts", disc.get("posts", 0), "contributions", INK),
                    ("Pending proposals", disc.get("pending_proposals", 0), "awaiting triage", BRASS)], top=2.2, cols=3, height=1.9)
    else:
        d.placeholder("Discussion", "The forum appears once conversations begin",
                      "Threads every report, initiative and topic; flagged posts become proposals the board can adopt.")

    # Twin
    d.section = "Twin Monitoring"
    d.placeholder("Twin Monitoring", "Actuals-vs-twin activates on your first sync",
                  "As actuals arrive, AXIOM compares them to the digital twin's projection — surfacing drift and auto-recalibrating.")

    # ================= CLOSE =================
    d.section = "Appendix"
    s = d.content("Methodology", "How these numbers are produced")
    _text(s, 0.63, 2.05, 12.1, 4.4, (ap.get("methodology") or
          "AXIOM runs a certified valuation, risk, optimization and simulation suite on your dataset. Every figure is reproducible from the active dataset version shown on the cover.")[:820],
          size=13.5, color=INK, line_spacing=1.3)
    s = d.content("Glossary", "Key terms")
    _text(s, 0.63, 2.05, 12.1, 4.4, [
        "EV — Enterprise Value.   DCF — Discounted Cash Flow.   WACC — Weighted Average Cost of Capital.",
        "CVaR — Conditional Value at Risk (expected loss in the worst 5%).",
        "CEI — Composite Excellence Index.   RAG — Red / Amber / Green status.",
        "P05–P95 — the 5th-to-95th percentile band of the simulated distribution.",
        "BPI — Benchmark Performance Index (100 = in line with sector)."], size=13.5, color=INK, line_spacing=1.5)
    d.closing()

    out = io.BytesIO(); prs.save(out)
    return out.getvalue()


# ============================================================================
# Executive deck — same system, 12 slides, tighter
# ============================================================================
def build_pptx(report, extras, meta) -> bytes:
    extras = extras or {}
    prs = Presentation(); prs.slide_width = Emu(int(SW * EMU_IN)); prs.slide_height = Emu(int(SH * EMU_IN))
    S = {s["id"]: s for s in report.get("sections", [])}
    company = report.get("company", {}); cur = company.get("currency", "")
    sym = {"USD": "$", "EUR": "€", "GBP": "£"}.get(cur, "")
    cname = meta.get("company_name", company.get("name", "Company"))
    d = Deck(prs, cname, meta["issued_at"], meta.get("dataset_version"), _logo_from_meta(meta))
    di = S.get("diagnostic", {}); sm = S.get("summary", {}); va = S.get("valuation", {})
    ou = S.get("outlook", {}); ac = S.get("actions", {}); bd = S.get("best_decision", {})
    dcf = va.get("dcf", {}); mc = dcf.get("monte_carlo", {}); kpi = {k["kpi"]: k for k in di.get("kpi_strip", [])}
    scd = sm.get("scorecard", {})

    d.cover("Executive Summary")
    d.phase = "Executive Summary"
    # 1. scorecard cards
    s = d.content("At a glance", (sm.get("takeaway") or "The company at a glance")[:82])
    d.cards(s, [(sm.get("headline_metric", {}).get("label", "Enterprise value"), _big(sm.get("headline_metric", {}).get("value"), sym), "intrinsic DCF", PINEACC),
                ("Health index", f"{scd.get('health_index', 0):.0f}/100", "diagnostic", BRASS),
                ("Risk grade", scd.get("risk_grade", "—"), "solvency", GREEN),
                ("Optimizer uplift", _big(scd.get("optimization_uplift"), sym), "available", AMBER)], top=2.15, cols=2)
    # 2. four answers
    s = d.content("The four questions", "AXIOM's answers, in one view")
    d.table(s, ["Question", "AXIOM's answer"],
            [[q, a] for q, a in zip(["How healthy is the company", "What is likely to happen next", "What should change", "The optimal first move"], sm.get("four_answers", []))],
            col_w=[3.6, 8.5], row_h=0.7)
    # 3. KPI cards
    cards = []
    for label, key in [("Revenue", "Revenue"), ("EBITDA", "EBITDA"), ("Free cash flow", "FCFF"),
                       ("ROIC", "ROIC"), ("WACC", "WACC"), ("Net debt", "Net Debt")]:
        k = kpi.get(key, {}); v = k.get("current")
        cards.append((label, (_fmt(v, pct=True) if k.get("format") == "percent" else _big(v, sym)), "", INK))
    s = d.content("Diagnostic", "Key performance indicators")
    d.cards(s, cards, top=2.05, cols=3)
    # 4. revenue fan
    sb = ou.get("simulation_baseline", {})
    _full_chart(d, "Outlook", "The probabilistic revenue forecast", chart_fan(sb.get("revenue_fan")))
    # 5. valuation lenses
    _full_chart(d, "Valuation", f"Enterprise value: {_big(dcf.get('enterprise_value'), sym)}, three ways", chart_lenses(dcf, va.get("real_options")))
    # 6. monte-carlo distribution
    _full_chart(d, "Valuation", "The value as a distribution, not a point", chart_mc_hist(mc.get("histogram"), mc.get("percentiles")))
    # 7. tornado
    _full_chart(d, "Actions", "The levers that move value most", chart_tornado(ac.get("recommendations")))
    # 7. frontier
    _full_chart(d, "Best decision", (bd.get("takeaway") or "The best risk-adjusted decision")[:82],
                chart_frontier((bd.get("frontier") or {}).get("points"), (bd.get("frontier") or {}).get("recommended")))
    # 8. recommendations w/ dispositions
    s = d.content("Recommendations", "What to do next — and its disposition")
    rr = []
    for r in (extras.get("recommendations") or [])[:6]:
        ini = r.get("initiative") or {}
        chip = {"adopted": f"Adopted → {ini.get('ref','')}", "parked": f"Parked → {ini.get('ref','')}", "dismissed": "Dismissed", "none": "—"}.get(r.get("disposition"), r.get("disposition"))
        rr.append([(r.get("title") or "")[:46], _big(r.get("expected_ev_impact"), sym), chip])
    if rr:
        d.table(s, ["Recommendation", "EV impact", "Disposition"], rr, col_w=[6.6, 2.2, 3.3], row_h=0.55)
    else:
        _text(s, 0.63, 2.3, 11, 0.6, "No value-creating recommendations for the active dataset.", size=13, color=SLATE)
    # 9. initiatives (if any) else risk cards
    inits = extras.get("initiatives") or []
    if inits:
        s = d.content("Execution", "Initiatives in flight")
        d.table(s, ["Ref", "Band", "RAG", "Owner", "Status"],
                [[i.get("ref_code"), (i.get("current_priority") or "").title(), _rag_word(i.get("rag")), i.get("owner_name") or "—", (i.get("status") or "").replace("_", " ").title()] for i in inits[:8]],
                col_w=[1.3, 2.0, 1.6, 4.0, 3.2], row_h=0.5)
    else:
        cov = ou.get("coverage", {})
        s = d.content("Risk", "Solvency and downside at a glance")
        d.cards(s, [("Risk grade", scd.get("risk_grade", "—"), "", GREEN),
                    ("Distance to default", _fmt(cov.get("distance_to_default_sigmas")), "sigmas", PINEACC),
                    ("MC 95% tail", _big(mc.get("cvar95"), sym), "CVaR", AMBER),
                    ("P(cash<0) ever", _fmt(ou.get("cash_runway", {}).get("p_cash_below_zero_ever"), pct=True), "", BRASS)], top=2.15, cols=2)
    d.closing()

    out = io.BytesIO(); prs.save(out)
    return out.getvalue()


# ============================================================================
# Board Report PDF — the polished report_pdf.py is the one and only builder.
# ============================================================================
def build_pdf(report: dict, extras: dict, meta: dict) -> bytes:
    from .report_pdf import build_board_pdf
    return build_board_pdf(report, extras, meta)
