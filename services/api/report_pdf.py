"""AXIOM Board Report — the polished ~25-page ivory PDF (restored as the one and
only board-report PDF builder). Ported from the original showcase-era generator
into a company-parameterized function: reads everything from board_report() +
meta (company name, currency, units, ownership all flow from the payload), with
the 7f-era additions — an issued-date line and the client logo on the cover.

Sections: cover, key findings, executive summary (four questions), diagnostic
(KPI strip, risk grade, benchmark), forward view (fans, plan attainment,
solvency), action plan (recommendations, optimizer), year-by-year forecast,
stochastic IS/BS/CF with P>=plan chips, comprehensive income, best decision
(value-risk frontier, ke regime map), valuation (three lenses, Monte Carlo,
real options), the AXIOM difference (Nine Techniques), risk heat map + tails,
glossary, legal (safe-harbor/EULA), Regent contact back cover.
"""
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle, PageBreak,
                                Image, HRFlowable, NextPageTemplate, PageTemplate,
                                BaseDocTemplate, Frame)

_ASSETS = os.path.join(os.path.dirname(__file__), "assets")
WHITE_LOGO = os.path.join(_ASSETS, "axiom_white.png")
COLOR_LOGO = os.path.join(_ASSETS, "axiom_color.png")

NAVY = colors.HexColor("#0B1F3A"); TEAL = colors.HexColor("#12B5A5")
SLATE = colors.HexColor("#5A6B7B"); LIGHT = colors.HexColor("#EEF2F6")
INK = colors.HexColor("#22303C")
GREEN = colors.HexColor("#1FA971"); AMBER = colors.HexColor("#E0A82E"); RED = colors.HexColor("#D9534F")
RAGHEX = {"green": "#1FA971", "amber": "#E0A82E", "red": "#D9534F", "A": "#1FA971",
          "B": "#1FA971", "C": "#E0A82E", "D": "#D9534F", "E": "#D9534F"}
SEVCOL = {"opportunity": TEAL, "insight": NAVY, "risk": RED, "strength": GREEN, "action": AMBER}
_SYM = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CHF": "CHF ", "CAD": "$", "AUD": "$"}


def _pc(x, d=1):
    return "—" if x is None else f"{x*100:.{d}f}%"


def _num(x, d=2):
    return "—" if x is None else f"{x:,.{d}f}"


# ---------- chart helpers (theme-matched, ~150 DPI) ----------
def _style(ax):
    ax.tick_params(labelsize=7, colors="#5A6B7B")
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#C7D0D9")
    ax.grid(axis="y", color="#EEF2F6", lw=0.8)


def _img(fig, w=5.9, h=2.7):
    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig); buf.seek(0)
    return Image(buf, width=w * inch, height=h * inch)


def _png_img(png, w=5.9):
    """Wrap raw PNG bytes (e.g. a shared deck chart) as a reportlab Image, preserving aspect ratio."""
    iw, ih = ImageReader(io.BytesIO(png)).getSize()
    return Image(io.BytesIO(png), width=w * inch, height=w * inch * ih / iw)


def _fan(fandata, sample=None, color="#12B5A5", title=""):
    yrs = [b["year"] for b in fandata]
    fig, ax = plt.subplots(figsize=(6.0, 2.5))
    ax.fill_between(yrs, [b["p05"] for b in fandata], [b["p95"] for b in fandata], color=color, alpha=0.13, lw=0)
    ax.fill_between(yrs, [b["p25"] for b in fandata], [b["p75"] for b in fandata], color=color, alpha=0.22, lw=0)
    ax.plot(yrs, [b["p50"] for b in fandata], color=color, lw=2.2, zorder=5)
    for p in (sample or [])[:10]:
        ax.plot(yrs, p, color="#8895A2", lw=0.5, alpha=0.45)
    ax.set_title(title, fontsize=9, color="#0B1F3A", fontweight="bold", loc="left"); _style(ax)
    fig.tight_layout(pad=0.3); return _img(fig, 5.9, 2.4)


def _barchart(labels, values, cols, title=""):
    fig, ax = plt.subplots(figsize=(6.0, 2.4))
    ax.bar(range(len(values)), values, color=cols, width=0.6)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=7, color="#5A6B7B")
    ax.set_title(title, fontsize=9, color="#0B1F3A", fontweight="bold", loc="left"); _style(ax)
    fig.tight_layout(pad=0.3); return _img(fig, 5.9, 2.3)


def _frontier_chart(points, rec):
    fig, ax = plt.subplots(figsize=(6.0, 2.6))
    xs = [p["safety_tail_margin"] for p in points]; ys = [p["value_mean_ev"] for p in points]
    eff = [p["pareto_efficient"] for p in points]
    ax.plot(xs, ys, color="#C7D0D9", lw=1)
    ax.scatter([x for x, e in zip(xs, eff) if e], [y for y, e in zip(ys, eff) if e], color="#12B5A5", s=44, zorder=4, label="Pareto-efficient")
    ax.scatter([x for x, e in zip(xs, eff) if not e], [y for y, e in zip(ys, eff) if not e], color="#C7D0D9", s=30, zorder=3, label="dominated")
    ax.scatter([rec["safety_tail_margin"]], [rec["value_mean_ev"]], edgecolor="#0B1F3A", facecolor="none", s=150, lw=2, zorder=5, label="recommended")
    ax.set_xlabel("Tail solvency margin", fontsize=7.5, color="#5A6B7B")
    ax.set_ylabel("Expected EV", fontsize=7.5, color="#5A6B7B")
    ax.set_title("Value–Risk Frontier over capital structure", fontsize=9, color="#0B1F3A", fontweight="bold", loc="left")
    ax.legend(fontsize=6.5, frameon=False); _style(ax); ax.grid(color="#EEF2F6", lw=0.8)
    fig.tight_layout(pad=0.3); return _img(fig, 5.9, 2.5)


def _hist_chart(h):
    counts = h["counts"]; start = h["bin_start"]; w = h["bin_width"]
    xs = [start + w * i for i in range(len(counts))]
    fig, ax = plt.subplots(figsize=(6.0, 2.3))
    ax.bar(xs, counts, width=w * 0.9, color="#12B5A5", alpha=0.85)
    ax.set_title("Enterprise value — Monte Carlo distribution", fontsize=9, color="#0B1F3A", fontweight="bold", loc="left")
    ax.set_xlabel("Enterprise value", fontsize=7.5, color="#5A6B7B"); _style(ax)
    fig.tight_layout(pad=0.3); return _img(fig, 5.9, 2.2)


def build_board_pdf(report: dict, extras: dict, meta: dict) -> bytes:
    R = report
    sec = {s["id"]: s for s in R["sections"]}
    company = R["company"]
    sym = _SYM.get((company.get("currency") or "").upper(), (company.get("currency") or "") + " ")
    issued = meta.get("issued_at")
    dsv = meta.get("dataset_version")
    logo = (meta or {}).get("logo")           # (bytes, content_type) or None
    units_note = f"Figures in {sym.strip() or company.get('currency','')} millions unless otherwise noted."

    def M(x):
        if x is None:
            return "—"
        if abs(x) >= 1000:
            return f"{sym}{x/1000:,.2f}B"
        return f"{sym}{x:,.1f}M"

    PC, NUM = _pc, _num
    KF = R.get("key_findings", [])
    PFsec = sec.get("proforma", {})
    CIsec = PFsec.get("comprehensive_income")

    styles = getSampleStyleSheet()

    def addS(n, **k):
        styles.add(ParagraphStyle(n, parent=styles["Normal"], **k))
    addS("H1", fontName="Helvetica-Bold", fontSize=21, textColor=NAVY, spaceAfter=3, leading=22)
    addS("H2", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY, spaceBefore=8, spaceAfter=4, leading=16)
    addS("Kick", fontName="Helvetica-Bold", fontSize=9.5, textColor=TEAL, spaceAfter=2)
    addS("Take", fontName="Helvetica-Oblique", fontSize=12.5, textColor=SLATE, spaceAfter=9, leading=15)
    addS("Body", fontName="Helvetica", fontSize=11, textColor=INK, leading=16, spaceAfter=5)
    addS("Sm", fontName="Helvetica", fontSize=9, textColor=SLATE, leading=12.5)
    addS("CardV", fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, leading=19, spaceAfter=4)
    addS("CardL", fontName="Helvetica", fontSize=8.5, textColor=SLATE, leading=11)
    addS("Find", fontName="Helvetica-Bold", fontSize=12.5, textColor=NAVY, leading=14, spaceAfter=2)

    def kicker(kick, title, take):
        out = [Paragraph(kick.upper(), styles["Kick"]), Paragraph(title, styles["H1"]),
               HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=7)]
        if take:
            out.append(Paragraph(take, styles["Take"]))
        return out

    def cards(items):
        avail = (6.9 / len(items)) * inch - 18  # usable cell width (left/right padding), pts
        row = []
        for l, v, r in items:
            s = str(v)
            fs = 16.0  # shrink the value to keep it on one line at this card width (e.g. long ranges)
            while fs > 10.5 and stringWidth(s, "Helvetica-Bold", fs) > avail:
                fs -= 0.5
            vst = ParagraphStyle("cv", parent=styles["CardV"], fontSize=fs, leading=fs + 3,
                                 textColor=(colors.HexColor(RAGHEX[r]) if r else NAVY))
            row.append([Paragraph(s, vst), Paragraph(l, styles["CardL"])])
        t = Table([row], colWidths=[(6.9 / len(row)) * inch] * len(row))
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("INNERGRID", (0, 0), (-1, -1), 6, colors.white),
                   ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 11),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 11), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    def datatable(header, rows, widths):
        data = [[Paragraph(f"<b>{h}</b>", styles["Sm"]) for h in header]]
        for r in rows:
            data.append([Paragraph(str(c), styles["Body"]) for c in r])
        t = Table(data, colWidths=[w * inch for w in widths])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1, NAVY), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
                   ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    # ---------------- page furniture (cover / frame / closing) ----------------
    def _draw_client_logo(c, x_right, y, box_w=1.7, box_h=0.55):
        if not logo:
            return
        try:
            img = ImageReader(io.BytesIO(logo[0] if isinstance(logo, (tuple, list)) else logo.get("bytes")))
            iw, ih = img.getSize()
            scale = min(box_w * inch / iw, box_h * inch / ih)
            w, h = iw * scale, ih * scale
            c.drawImage(img, x_right - w, y, width=w, height=h, mask="auto", preserveAspectRatio=True)
        except Exception:
            pass

    def cover(c, doc):
        c.saveState(); c.setFillColor(NAVY); c.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        c.setFillColor(TEAL); c.rect(0, letter[1] - 4, letter[0], 4, fill=1, stroke=0)
        try:
            c.drawImage(WHITE_LOGO, 0.9 * inch, letter[1] - 1.5 * inch, width=2.6 * inch, height=0.52 * inch,
                        mask="auto", preserveAspectRatio=True)
        except Exception:
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 22); c.drawString(0.9 * inch, letter[1] - 1.35 * inch, "AXIOM")
        _draw_client_logo(c, letter[0] - 0.9 * inch, letter[1] - 1.45 * inch)   # client logo, top-right
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 29)
        c.drawString(0.9 * inch, 6.0 * inch, company["name"])
        c.setFont("Helvetica", 14); c.setFillColor(colors.HexColor("#AEBECE"))
        c.drawString(0.9 * inch, 5.58 * inch, "Enterprise Diagnostic & Valuation Report")
        c.setFont("Helvetica", 9.5)
        c.drawString(0.9 * inch, 5.33 * inch,
                     f"{company['ownership'].title()} · {company['standard'].upper()} · "
                     f"{company.get('sector') or 'Unclassified'} · {units_note}")
        c.setStrokeColor(TEAL); c.setLineWidth(2); c.line(0.9 * inch, 5.05 * inch, 3.1 * inch, 5.05 * inch)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 38)
        c.drawString(0.9 * inch, 4.15 * inch, M(R["headline"]["value"]))
        c.setFont("Helvetica", 12); c.setFillColor(TEAL); c.drawString(0.9 * inch, 3.85 * inch, R["headline"]["label"])
        scd = sec["summary"]["scorecard"]
        c.setFillColor(colors.HexColor("#AEBECE")); c.setFont("Helvetica", 10.5)
        c.drawString(0.9 * inch, 3.15 * inch,
                     f"Health {scd['health_index']:.0f}/100      Risk grade {scd['risk_grade']}      "
                     f"Optimization uplift {M(scd['optimization_uplift'])} available      Flexibility {PC(scd['flexibility_pct_of_ev'])}")
        # 7f addition: issued date + data version, in the cover's own language
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold", 10)
        issued_line = ("Issued " + issued.strftime("%d %b %Y")) if issued else "Issued —"
        if dsv is not None:
            issued_line += f"  ·  Data version {dsv}"
        c.drawString(0.9 * inch, 2.78 * inch, issued_line)
        # safe harbor block
        shs = ParagraphStyle("sh", fontName="Helvetica", fontSize=6.6, textColor=colors.HexColor("#7C8B9A"), leading=8.6)
        sh = Paragraph("<b>SAFE HARBOR & DISCLAIMER.</b> " + R["safe_harbor"], shs)
        fr = Frame(0.9 * inch, 1.35 * inch, letter[0] - 1.8 * inch, 1.15 * inch,
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
        fr.addFromList([sh], c)
        c.setFont("Helvetica", 8.5); c.setFillColor(colors.HexColor("#8895A2"))
        c.drawString(0.9 * inch, 1.02 * inch, f"Prepared by {R['brand']['prepared_by']}   ·   {R['brand']['contact_email']}")
        c.drawString(0.9 * inch, 0.82 * inch, f"Generated {R['generated_at_utc']}   ·   {R['brand']['powered_by']}")
        c.restoreState()

    def frame(c, doc):
        c.saveState()
        try:
            c.drawImage(COLOR_LOGO, 0.9 * inch, letter[1] - 0.72 * inch, width=1.15 * inch, height=0.23 * inch,
                        mask="auto", preserveAspectRatio=True)
        except Exception:
            c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 11); c.drawString(0.9 * inch, letter[1] - 0.66 * inch, "AXIOM")
        c.setStrokeColor(LIGHT); c.setLineWidth(1); c.line(0.9 * inch, letter[1] - 0.78 * inch, letter[0] - 0.9 * inch, letter[1] - 0.78 * inch)
        c.setFont("Helvetica", 7.5); c.setFillColor(SLATE)
        c.drawRightString(letter[0] - 0.9 * inch, letter[1] - 0.66 * inch, company["name"])
        c.line(0.9 * inch, 0.72 * inch, letter[0] - 0.9 * inch, 0.72 * inch)
        c.drawString(0.9 * inch, 0.54 * inch, "Confidential — Board of Directors")
        c.drawRightString(letter[0] - 0.9 * inch, 0.54 * inch, f"Page {doc.page} · Powered by AXIOM")
        c.restoreState()

    def closing(c, doc):
        frame(c, doc)
        c.saveState()
        c.setFillColor(NAVY); c.rect(0.9 * inch, 4.2 * inch, letter[0] - 1.8 * inch, 3.0 * inch, fill=1, stroke=0)
        try:
            c.drawImage(WHITE_LOGO, 1.3 * inch, 6.5 * inch, width=2.2 * inch, height=0.44 * inch, mask="auto", preserveAspectRatio=True)
        except Exception:
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 18); c.drawString(1.3 * inch, 6.55 * inch, "AXIOM")
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 12)
        c.drawString(1.3 * inch, 6.15 * inch, "Bring AXIOM to your organization")
        c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#DCE4EC"))
        for i, ln in enumerate(["Regent Financial", "14590 Via Bergamo, San Diego, CA 92127, United States",
                                "Tel: (949) 409-7437", "Email: samir@theregentfinancial.com",
                                "Powered by AXIOM — axiomdynamics.app"]):
            c.drawString(1.3 * inch, 5.8 * inch - i * 0.24 * inch, ln)
        c.restoreState()

    story = [PageBreak()]

    # ===== KEY FINDINGS =====
    story += kicker("What matters most", "Key Findings at a Glance",
                    "The insights below are auto-extracted from this company's certified results, ranked by decision relevance.")
    for f in KF:
        col = SEVCOL.get(f["severity"], NAVY)
        box = Table([[Paragraph(f["severity"].upper(), ParagraphStyle("sev", parent=styles["Sm"], textColor=col, fontName="Helvetica-Bold")),
                      Paragraph(f["headline"], styles["Find"])],
                     ["", Paragraph(f["detail"], styles["Body"])]], colWidths=[1.15 * inch, 5.65 * inch])
        box.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("SPAN", (0, 0), (0, 1)),
                     ("LINEBEFORE", (0, 0), (0, -1), 3, col), ("LEFTPADDING", (0, 0), (0, -1), 8),
                     ("LEFTPADDING", (1, 0), (1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 4),
                     ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FafBfC"))]))
        story.append(box); story.append(Spacer(1, 6))
    story.append(PageBreak())

    # ===== EXECUTIVE SUMMARY =====
    s = sec["summary"]
    story += kicker("Question 1 · Executive Summary", "Executive Summary", s["takeaway"])
    story.append(cards([(s["headline_metric"]["label"], M(s["headline_metric"]["value"]), None),
                        ("Health Index", f"{s['scorecard']['health_index']:.0f}/100", "green" if s['scorecard']['health_index'] >= 85 else "amber"),
                        ("Risk Grade", s["scorecard"]["risk_grade"], s["scorecard"]["risk_grade"]),
                        ("Flexibility", PC(s["scorecard"]["flexibility_pct_of_ev"]), None)]))
    story.append(Spacer(1, 12))
    ql = ["How healthy is the company", "What is likely to happen next", "What should change", "The optimal first move"]
    story.append(datatable(["The four questions", "AXIOM's answer"],
                 [[f"<b>{a}</b>", ans] for a, ans in zip(ql, s["four_answers"])], [1.9, 4.9]))
    if s.get("top_recommendation"):
        tr = s["top_recommendation"]; story.append(Spacer(1, 10))
        b = Table([[Paragraph(f"<b>Priority action:</b> {tr['title']} — expected value impact "
                    f"{M(tr['expected_ev_impact'])} ({PC(tr['expected_ev_impact_pct'])}). {tr['description']}", styles["Body"])]], colWidths=[6.9 * inch])
        b.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F7F4")), ("BOX", (0, 0), (-1, -1), 1, TEAL),
                   ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        story.append(b)
    story.append(PageBreak())

    # ===== DIAGNOSTIC (2 pages) =====
    s = sec["diagnostic"]
    story += kicker("Question 1 · Diagnostic", "Where the Company Stands Today", s["takeaway"])

    def fmtkpi(k):
        f = k["format"]; v = k["current"]
        return PC(v) if f == "percent" else NUM(v, 3) if f == "ratio" else M(v)
    kp = s["kpi_strip"]
    krows = [[k["kpi"], fmtkpi(k), (f"{k['trend']*100:+.1f}%" if k.get("trend") is not None else "—")] for k in kp]
    half = (len(krows) + 1) // 2
    left = krows[:half]; right = krows[half:]
    while len(right) < len(left):
        right.append(["", "", ""])
    merged = [l + r for l, r in zip(left, right)]
    story.append(datatable(["KPI", "Value", "Δ", "KPI", "Value", "Δ"], merged, [1.35, 1.0, 0.75, 1.35, 1.0, 0.75]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Full KPI definitions are provided; every metric is computed from the "
                 "statements on file and reproducible from published formulas.", styles["Sm"]))
    story.append(PageBreak())
    story += kicker("Question 1 · Diagnostic (continued)", "Risk Grade & Peer Position",
                    "The company's financial risk graded against four published bands, and its standing versus sector peers.")
    rg = s["risk_grade"]
    story.append(Paragraph(f"Risk grade <b>{rg['grade']}</b> — {rg['score']}/8 points across four indicators.", styles["Body"]))
    grows = []
    for ind in rg["indicators"]:
        cc = RAGHEX.get(ind["rag"], "#5A6B7B")
        grows.append([ind["indicator"].replace("_", " ").title(), NUM(ind["value"], 3) if ind["value"] else "—",
                      f'<font color="{cc}">● {ind["rag"].upper() if ind["rag"] else "N/A"}</font>',
                      f"{ind['bands']['direction'].replace('_',' ')}, green ≥ {ind['bands']['green']}"])
    story.append(datatable(["Indicator", "Value", "Status", "Band"], grows, [1.9, 1.1, 1.3, 2.6]))
    story.append(Spacer(1, 8))
    bm = s["benchmark"]
    if "index" in bm:
        story.append(Paragraph(f"<b>Benchmark performance index: {NUM(bm['index'],1)}</b> "
                     f"(100 = sector-typical). {bm.get('narrative','')}", styles["Body"]))
    story.append(PageBreak())

    # ===== OUTLOOK (2 pages) =====
    s = sec["outlook"]
    story += kicker("Question 2 · Forward View", "What Is Likely to Happen Next", s["takeaway"])
    sb = s["simulation_baseline"]
    story.append(_fan(sb["revenue_fan"], sb["sample_paths"]["revenue"], "#12B5A5", f"Revenue — projection with volatility ({sym.strip()}M)"))
    story.append(Spacer(1, 4))
    story.append(_fan(sb["fcff_fan"], sb["sample_paths"]["fcff"], "#0B7A8F", f"Free cash flow to firm — projection ({sym.strip()}M)"))
    story.append(PageBreak())
    story += kicker("Question 2 · Forward View (continued)", "Plan Attainment & Solvency",
                    "The probability of hitting next year's plan, and the firm's distance from financial distress.")
    story.append(_fan(sb["cash_fan"], sb["sample_paths"]["cash"], "#12B5A5", f"Cash balance — projection ({sym.strip()}M)"))
    story.append(Spacer(1, 6))
    pa = s["plan_attainment"]
    story.append(cards([("Revenue ≥ target", PC(pa["p_revenue_target"], 0), None), ("Margin ≥ target", PC(pa["p_margin_target"], 0), None),
                        ("FCFF ≥ target", PC(pa["p_fcff_target"], 0), None),
                        ("All three", PC(pa.get("p_all_three"), 0), "amber" if (pa.get("p_all_three") or 0) < 0.35 else "green")]))
    story.append(Spacer(1, 8))
    dd = s["coverage"]
    story.append(Paragraph(f"<b>Solvency:</b> distance to default {NUM(dd['distance_to_default_sigmas'],1)} standard deviations; "
                 f"probability enterprise value falls below debt {PC(dd['p_ev_below_debt'],2)}. Recession cash-negative probability "
                 f"{PC(s['simulation_recession']['p_cash_below_zero'],0)}. Plan source: {pa['plan_source']}.", styles["Body"]))
    story.append(PageBreak())

    # ===== ACTION PLAN (2 pages) =====
    s = sec["actions"]
    story += kicker("Question 3 · Action Plan", "What Should Change — The Full Action Plan", s["takeaway"])
    rows = []
    for r_ in s["recommendations"]:
        rows.append([str(r_["rank"]), f"<b>{r_['title']}</b><br/><font size=8 color='#5A6B7B'>{r_['description']}</font>",
                     M(r_["expected_ev_impact"]), PC(r_["expected_ev_impact_pct"])])
    story.append(datatable(["#", "Recommended move", "EV impact", "%"], rows, [0.4, 4.5, 1.1, 0.9]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Each move is evaluated independently on the certified valuation kernel; impacts are "
                 "not strictly additive, as several act on the same drivers.", styles["Sm"]))
    story.append(PageBreak())
    story += kicker("Question 3 · Action Plan (continued)", "The Optimizer's Multi-Year Plan",
                    "Beyond single moves, the stochastic dynamic optimizer prescribes a coordinated multi-year policy.")
    op = s["optimizer_plan"]
    oprows = [[f"Year {p['step']}", PC(p['growth']), PC(p['net_borrowing_pct_rev']), NUM(p['debt_intensity_after'], 3)] for p in op]
    story.append(datatable(["Step", "Revenue growth", "Net borrowing (% rev)", "Debt intensity after"], oprows, [1.3, 1.8, 1.9, 1.7]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Optimization uplift available: {M(s['optimization_uplift'])}</b> of equity value over the status quo.", styles["Body"]))
    dec = s["uplift_derivation"]["decomposition"]
    story.append(Paragraph(f"<b>How this value is derived:</b> {s['uplift_derivation']['how']}", styles["Sm"]))
    story.append(Spacer(1, 4))
    story.append(datatable(["Source of uplift", "Value"],
                 [["Growth policy", M(dec["growth_policy"])], ["Financing policy", M(dec["financing_policy"])],
                  ["Interaction", M(dec["interaction"])], ["Deterministic total", M(dec["total_deterministic_path"])]], [3.5, 2.0]))
    story.append(PageBreak())

    # ===== PRO FORMA STATEMENTS =====
    # 7L: the print report caps pro-forma tables at the first 5 forecast years so
    # wide horizons (up to 15) never overflow the page; the full horizon lives in
    # the app. A note is appended when the horizon is truncated here.
    _pfy_all = PFsec["forecast_years"]; _pfs_all = PFsec["statements"]
    _PF_CAP = 5
    pfy = _pfy_all[:_PF_CAP]; pfs = _pfs_all[:_PF_CAP]
    YHDR = [str(y) for y in pfy]
    _pf_truncated = len(_pfy_all) > _PF_CAP
    _PF_NOTE = (f"Showing the first {_PF_CAP} of {len(_pfy_all)} forecast years — "
                f"the full {len(_pfy_all)}-year horizon is available in the AXIOM app."
                if _pf_truncated else None)

    def _plan(st, key, kind):
        return st["stochastic"][key]["plan"] if kind == "stoch" else st["deterministic"][key]

    def stmt_page(kicker_txt, title, take, lines, note=None, extra=None):
        loc = kicker(kicker_txt, title, take)
        head = [f"{sym.strip()}M"] + YHDR
        data = [[Paragraph(f"<b>{h}</b>", styles["Sm"]) for h in head]]
        for label, key, kind, emph in lines:
            row = [Paragraph((f"<b>{label}</b>" if emph else label), styles["Body"])]
            for st in pfs:
                val = _plan(st, key, kind)
                if kind == "stoch":
                    p = st["stochastic"][key]["p_meets_plan"]
                    cc = "#1FA971" if p >= 0.55 else "#E0A82E" if p >= 0.40 else "#D9534F"
                    cell = f'<b>{M(val)}</b><br/><font size=7 color="{cc}">P {p*100:.0f}%</font>'
                else:
                    cell = M(val)
                row.append(Paragraph(cell, styles["Sm"]))
            data.append(row)
        w = [1.85] + [1.0] * len(pfy)
        t = Table(data, colWidths=[x * inch for x in w])
        ts = [("LINEBELOW", (0, 0), (-1, 0), 1, NAVY), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F7FA")),
              ("ALIGN", (1, 0), (-1, -1), "RIGHT")]
        for i, (label, key, kind, emph) in enumerate(lines, start=1):
            if emph:
                ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FafBfC")))
        t.setStyle(TableStyle(ts)); loc.append(t)
        if note:
            loc.append(Spacer(1, 7)); loc.append(Paragraph(note, styles["Sm"]))
        if extra:
            loc.append(Spacer(1, 8)); loc += extra
        loc.append(PageBreak())
        return loc

    PROB_LEGEND = ("Each stochastic line shows the plan figure with P (probability the "
                   "actual meets or beats plan) beneath: <font color='#1FA971'>green ≥55%</font>, "
                   "<font color='#E0A82E'>amber 40-55%</font>, <font color='#D9534F'>red &lt;40%</font>. "
                   "Deterministic lines show the plan figure only.")

    story += kicker("Financial Projections", "Year-by-Year Forecast",
                    "The deterministic plan across the forecast horizon, with compound growth rates.")
    fgrid = [[Paragraph(f"<b>{h}</b>", styles["Sm"]) for h in [f"{sym.strip()}M"] + YHDR]]
    for label, key, kind, emph in [("Revenue", "revenue", "stoch", True), ("COGS", "cogs", "det", False),
                                   ("Operating expense", "opex", "det", False), ("D&A", "da", "det", False), ("EBIT", "ebit", "stoch", True),
                                   ("EBITDA", "ebitda", "stoch", True), ("Interest", "interest", "det", False), ("Net income", "net_income", "stoch", True),
                                   ("FCFF", "fcff", "stoch", True), ("FCFE", "fcfe", "stoch", True)]:
        fgrid.append([Paragraph((f"<b>{label}</b>" if emph else label), styles["Body"])] + [Paragraph(M(_plan(st, key, kind)), styles["Sm"]) for st in pfs])
    ft = Table(fgrid, colWidths=[1.85 * inch] + [1.0 * inch] * len(pfy))
    ft.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1, NAVY), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F7FA"))]))
    story.append(ft); story.append(Spacer(1, 8))
    if _PF_NOTE:
        story.append(Paragraph(_PF_NOTE, styles["Sm"])); story.append(Spacer(1, 8))
    cg = PFsec["plan_cagr"]
    story.append(Paragraph(f"<b>Compound annual growth (plan):</b> revenue {PC(cg['revenue'])}, "
                 f"EBIT {PC(cg['ebit'])}, net income {PC(cg['net_income'])}, FCFF {PC(cg['fcff'])}. "
                 f"Because the plan sits near the centre of the simulated distribution, each single-year "
                 f"target is roughly a coin toss; meeting the revenue target in EVERY forecast year has "
                 f"probability {PC(PFsec['cumulative_attainment']['revenue']['p_meets_plan_every_year'],0)}.", styles["Body"]))
    story.append(PageBreak())

    story += stmt_page("Pro Forma · Stochastic", "Income Statement",
                       "The projected income statement across the plan horizon, with the probability each line meets or beats plan.",
                       [("Revenue", "revenue", "stoch", True), ("COGS", "cogs", "det", False),
                        ("Operating expense", "opex", "det", False), ("D&A", "da", "det", False),
                        ("EBIT", "ebit", "stoch", True), ("EBITDA", "ebitda", "stoch", True),
                        ("Interest", "interest", "det", False), ("Pre-tax income", "ebt", "det", False),
                        ("Tax", "tax", "det", False), ("Net income", "net_income", "stoch", True)], note=PROB_LEGEND)
    story += stmt_page("Pro Forma · Stochastic", "Balance Sheet",
                       "The projected balance sheet; it balances (assets = liabilities + equity) on every simulated path.",
                       [("Cash", "cash", "stoch", False), ("Other current assets", "oca", "det", False),
                        ("Non-current assets", "nca", "det", False), ("Total assets", "total_assets", "stoch", True),
                        ("Current liabilities", "cl", "det", False), ("Short-term debt", "st_debt", "det", False),
                        ("Long-term debt", "lt_debt", "det", False), ("Total equity", "equity", "stoch", True)], note=PROB_LEGEND)
    story += stmt_page("Pro Forma · Stochastic", "Cash Flow Statement",
                       "The projected cash-flow statement, linked coherently to the income statement and balance sheet.",
                       [("Operating cash flow", "cfo", "stoch", True), ("Capital expenditure", "capex", "det", False),
                        ("Investing cash flow", "cfi", "det", False), ("Financing cash flow", "cff", "det", False),
                        ("Free cash flow to firm", "fcff", "stoch", True), ("Free cash flow to equity", "fcfe", "stoch", True)],
                       note=PROB_LEGEND,
                       extra=[Paragraph("<b>Multi-year plan attainment</b> — probability of meeting the plan in EVERY "
                              f"forecast year: revenue {PC(PFsec['cumulative_attainment']['revenue']['p_meets_plan_every_year'],0)}, "
                              f"net income {PC(PFsec['cumulative_attainment']['net_income']['p_meets_plan_every_year'],0)}, "
                              f"FCFF {PC(PFsec['cumulative_attainment']['fcff']['p_meets_plan_every_year'],0)}.", styles["Body"])])

    if CIsec:
        ciy = CIsec["statements"]
        cidata = [[Paragraph(f"<b>{h}</b>", styles["Sm"]) for h in [f"{sym.strip()}M"] + [str(s["year"]) for s in ciy]]]
        cidata.append([Paragraph("<b>Net income</b>", styles["Body"])] + [Paragraph(M(s["net_income"]["plan"]), styles["Sm"]) for s in ciy])
        labelmap = {"fx_translation": "OCI: FX translation", "securities": "OCI: FVOCI securities",
                    "pension": "OCI: Pension remeasurement", "hedge": "OCI: Cash-flow hedges"}
        for k in ["fx_translation", "securities", "pension", "hedge"]:
            row = [Paragraph(labelmap[k], styles["Body"])]
            for s in ciy:
                ln = s["oci_lines"][k]
                row.append(Paragraph(M(ln["expected"]) if ln["present"] else "<font color='#9AA7B4'>— n/a</font>", styles["Sm"]))
            cidata.append(row)
        cidata.append([Paragraph("<b>Total OCI</b>", styles["Body"])] + [Paragraph(M(s["total_oci_expected"]), styles["Sm"]) for s in ciy])
        cidata.append([Paragraph("<b>Comprehensive income</b>", styles["Body"])] + [Paragraph(M(s["comprehensive_income_expected"]), styles["Sm"]) for s in ciy])
        cit = Table(cidata, colWidths=[1.85 * inch] + [1.0 * inch] * len(ciy))
        cit.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1, NAVY), ("LINEBELOW", (0, 1), (-1, -1), 0.4, LIGHT),
                     ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                     ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F7FA")), ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FafBfC")),
                     ("BACKGROUND", (0, 6), (-1, 7), colors.HexColor("#FafBfC"))]))
        story += kicker("Pro Forma · Stochastic", "Statement of Comprehensive Income",
                        f"Net income plus Other Comprehensive Income, under {CIsec['framework']}. OCI is modeled "
                        "stochastically where drivers are on file, never fabricated.")
        badge = Table([[Paragraph(f"<b>Accounting framework: {CIsec['framework']}</b>", styles["Sm"])]], colWidths=[6.9 * inch])
        badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F7F4")), ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
                       ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story.append(badge); story.append(Spacer(1, 8)); story.append(cit); story.append(Spacer(1, 8))
        rc = CIsec.get("ifrs_reclassification", {})
        if rc.get("applies"):
            story.append(Paragraph(f"<b>IFRS reclassification (IAS 1):</b> recycled to profit or loss — "
                         f"{', '.join(rc['will_be_reclassified'])}; never reclassified — "
                         f"{', '.join(rc['will_not_be_reclassified'])}.", styles["Sm"]))
        else:
            story.append(Paragraph("<b>US GAAP (ASC 220):</b> OCI presented as a single section; "
                         "reclassification adjustments recognized when the underlying items are realized.", styles["Sm"]))
        story.append(PageBreak())

    # ===== BEST DECISION =====
    s = sec["best_decision"]
    story += kicker("Question 4 · Optimal Decision", "The Best Risk-Adjusted Decision", s["takeaway"])
    story.append(_frontier_chart(s["frontier"]["points"], s["frontier"]["recommended"]))
    story.append(Spacer(1, 6))
    story.append(cards([("Recommended D/E", NUM(s["frontier"]["recommended"]["de"], 2), None),
                        ("Current D/E", NUM(s["frontier"]["current_de"], 2), None),
                        ("Distress headroom", M(s["shadow_prices"]["distress_headroom_per_0p1"]) + "/0.1", None),
                        ("Friction shadow price", M(s["shadow_prices"]["transformation_friction_per_unit_phi"]), None)]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Cost-of-equity regime map</b> — how the optimal strategy shifts with the hurdle rate:", styles["Body"]))
    story.append(datatable(["Cost of equity", "Optimal growth", "Optimal borrowing", "Equity value"],
                 [[PC(r["cost_of_equity"]), PC(r["optimal_growth"]), PC(r["optimal_borrowing"]), M(r["equity_value"])] for r in s["ke_regime_map"]], [1.7, 1.6, 1.7, 1.7]))
    story.append(PageBreak())

    # ===== VALUATION (2 pages) =====
    s = sec["valuation"]
    story += kicker("Question 4 · Valuation", "Valuation — Three Independent Lenses", s["takeaway"])
    ev = s["dcf"]["enterprise_value"]; mult = s.get("multiples")
    # One chart truth: reuse the deck's four-lens chart (DCF intrinsic / Monte Carlo mean /
    # 95% tail CVaR / real-option expand) — theme-colored bars with value labels.
    from .reporting import chart_lenses
    _lens = chart_lenses(s["dcf"], s.get("real_options"))
    if _lens:
        story.append(_png_img(_lens, 5.9))
    story.append(Spacer(1, 6))
    story.append(cards([("DCF enterprise value", M(ev), None), ("Equity value", M(s["dcf"]["equity_value"]), None),
                        ("Value / share", (f"{sym}{NUM(s['dcf']['value_per_share'],2)}" if s['dcf'].get('value_per_share') is not None else "—"), None),
                        ("WACC", PC(s["dcf"]["wacc"], 2), None)]))
    story.append(Spacer(1, 6))
    if mult:
        story.append(Paragraph(f"<b>Multiples cross-check:</b> comparable-company multiples imply "
                     f"{M(mult['implied_ev_range']['low'])}–{M(mult['implied_ev_range']['high'])} "
                     f"(EV/EBITDA {NUM(mult['methods'][0]['multiple'],1)}x, EV/EBIT {NUM(mult['methods'][1]['multiple'],1)}x); "
                     f"the intrinsic DCF is {M(mult['intrinsic_dcf_ev'])}.", styles["Body"]))
    story.append(PageBreak())
    story += kicker("Question 4 · Valuation (continued)", "Monte Carlo & Real Options",
                    "The valuation as a distribution, and the flexibility value that static DCF omits.")
    mc = s["dcf"]["monte_carlo"]
    story.append(_hist_chart(mc["histogram"]))
    story.append(Spacer(1, 4))
    story.append(cards([("Mean EV", M(mc["mean"]), None), ("P05–P95", f"{M(mc['percentiles']['p05'])}–{M(mc['percentiles']['p95'])}", None),
                        ("VaR 95%", M(mc["var95"]), None), ("RAEV (λ=0.5)", M(mc["raev"]), None)]))
    story.append(Spacer(1, 8))
    ro = s["real_options"]
    story.append(Paragraph("<b>Real options — flexibility value on top of the DCF:</b>", styles["Body"]))
    rorows = [[v["label"], M(v["underlying_enterprise_value"]), M(v["option_inclusive_value"]), M(v["flexibility_value"]), PC(v["flexibility_pct_of_ev"])] for v in ro["options"].values()]
    story.append(datatable(["Real option", "Baseline", "Incl. option", "Flex. value", "% of EV"], rorows, [2.3, 1.2, 1.2, 1.1, 0.9]))
    story.append(PageBreak())

    # ===== THE AXIOM DIFFERENCE (2 pages) =====
    ad = R.get("axiom_difference", [])
    story += kicker("Why AXIOM", "The AXIOM Difference",
                    "The techniques below are core to AXIOM and largely absent from conventional financial-analysis and BI tools.")
    for tech in ad[:4]:
        box = Table([[Paragraph(f"<b>{tech['technique']}</b>", styles["H2"])], [Paragraph(tech["what"], styles["Body"])],
                     [Paragraph(f"<b>Why it's different:</b> {tech['why_unique']}", styles["Sm"])]], colWidths=[6.8 * inch])
        box.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, -1), 3, TEAL), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                     ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FafBfC"))]))
        story.append(box); story.append(Spacer(1, 7))
    story.append(PageBreak())
    if ad[4:]:
        story += kicker("Why AXIOM (continued)", "The AXIOM Difference",
                        "Advanced analytics, digital-twin learning, and fuzzy-logic readiness assessment.")
        for tech in ad[4:]:
            box = Table([[Paragraph(f"<b>{tech['technique']}</b>", styles["H2"])], [Paragraph(tech["what"], styles["Body"])],
                         [Paragraph(f"<b>Why it's different:</b> {tech['why_unique']}", styles["Sm"])]], colWidths=[6.8 * inch])
            box.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, -1), 3, TEAL), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                         ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FafBfC"))]))
            story.append(box); story.append(Spacer(1, 7))
        story.append(PageBreak())

    # ===== APPENDIX (2 pages) =====
    s = sec["appendix"]
    story += kicker("Appendix", "Advanced Analytics — Risk", s["takeaway"])
    hrows = []
    for h in s["risk_heat_map"]:
        cc = RAGHEX.get(h["rag"], "#5A6B7B") if h["rag"] else "#5A6B7B"
        hrows.append([h["category"], "—" if h["score"] is None else NUM(h["score"], 0),
                      f'<font color="{cc}">● {h["rag"].upper() if h["rag"] else "N/A"}</font>',
                      f"<font size=7 color='#5A6B7B'>{h['basis']}</font>"])
    story.append(datatable(["Risk category", "Score", "Status", "Basis"], hrows, [1.8, 0.7, 1.0, 3.3]))
    story.append(PageBreak())
    story += kicker("Appendix (continued)", "Advanced Analytics — Tails, Attribution, Sensitivity",
                    "Extreme value theory, variance attribution, and interest-rate sensitivity.")
    evt = s["extreme_value_tail"]; so = s["sobol_attribution"]; dc = s["duration_convexity"]
    story.append(Paragraph("<b>Extreme Value Tail (EVT — Generalized Pareto):</b>", styles["Body"]))
    story.append(datatable(["Measure", "Value"], [["Tail index ξ", NUM(evt["tail_index_xi"], 3)],
                 ["FCFF 1-in-100", M(evt["fcff_1_in_100"])], ["FCFF 1-in-1000", M(evt["fcff_1_in_1000"])],
                 ["Empirical p01", M(evt["empirical_p01"])]], [3.5, 2.0]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Sobol Variance Attribution:</b>", styles["Body"]))
    story.append(datatable(["Source", "Share of variance"], [["Growth uncertainty", PC(so["growth_uncertainty"], 0)],
                 ["Margin uncertainty", PC(so["margin_uncertainty"], 0)], ["Interaction", PC(so["interaction"], 0)]], [3.5, 2.0]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Interest-rate sensitivity:</b> effective duration {NUM(dc['effective_duration'],2)}, "
                 f"convexity {NUM(dc['convexity'],1)}, DV01-like {M(dc['dv01_like'])}.", styles["Body"]))
    story.append(PageBreak())

    # ===== GLOSSARY =====
    arows = [[f"<b>{a}</b>", d] for a, d in R.get("acronyms", [])]
    half = (len(arows) + 1) // 2
    story += kicker("Reference", "Glossary of Terms & Acronyms", "Every acronym used in this report, defined.")
    story.append(datatable(["Term", "Definition"], arows[:half], [1.0, 5.8]))
    story.append(PageBreak())
    story += kicker("Reference (continued)", "Glossary of Terms & Acronyms", "")
    story.append(datatable(["Term", "Definition"], arows[half:], [1.0, 5.8]))
    story.append(PageBreak())

    # ===== LEGAL =====
    story += kicker("Legal", "Important Notice, Disclaimer & Licence",
                    "Please read this notice carefully. Your use of this report and the AXIOM platform is subject to the terms below.")
    story.append(Paragraph("<b>Safe Harbor & Disclaimer</b>", styles["H2"]))
    story.append(Paragraph(R["safe_harbor"], styles["Body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>End User License Agreement (Summary)</b>", styles["H2"]))
    story.append(Paragraph(R["eula_summary"], styles["Body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>No Reliance.</b> This document is not an offer, solicitation, recommendation, or advice "
                 "to buy, sell, hold, restructure, finance, or transact in any security, business, or asset. Recipients "
                 "must make their own independent assessment and obtain their own professional advice before acting. "
                 "Regent Financial accepts no responsibility for decisions taken in reliance on this report.", styles["Sm"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Confidentiality.</b> This report is confidential and intended solely for the board and "
                 "executive team of the subject company. It may not be reproduced, distributed, or disclosed to any third "
                 "party without the prior written consent of Regent Financial, except as required by law.", styles["Sm"]))

    # ===== CONTACT / CLOSING =====
    story.append(NextPageTemplate("closing"))
    story.append(PageBreak())
    story += kicker("Contact", "Bring AXIOM to Your Organization",
                    f"This report was generated by AXIOM from {company['name']} figures on file. "
                    "Every number is reproducible from published formulas and seeds.")
    story.append(Spacer(1, 8))
    story.append(Paragraph(R["brand"]["methodology_note"], styles["Body"]))

    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                          topMargin=1.0 * inch, bottomMargin=0.95 * inch)
    frameF = Frame(0.9 * inch, 0.95 * inch, letter[0] - 1.8 * inch, letter[1] - 1.95 * inch, id="main")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[Frame(0.9 * inch, 0.9 * inch, letter[0] - 1.8 * inch, letter[1] - 1.8 * inch)], onPage=cover),
        PageTemplate(id="body", frames=[frameF], onPage=frame),
        PageTemplate(id="closing", frames=[frameF], onPage=closing),
    ])
    doc.build([NextPageTemplate("body")] + story)
    return buf.getvalue()
