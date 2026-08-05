#!/usr/bin/env python3
"""No cap on users may return, in either of its two shapes.

⭐⭐ RULED 1 Aug (§5a): unlimited users, both tiers. No caps of any kind, and
therefore NO OVERAGE — ⭐ AN OVERAGE PRICE IS A CAP WEARING A DIFFERENT NAME, so
a guard that watches only for refusals would miss the shape that sells relief
from the limit instead of enforcing it.

⭐ THE CAPS WERE LIVE AND REFUSING INVITES until this lane. `_enforce_seat_cap`
raised HTTP 402 `assessor_cap_reached` from both assessor-invite paths, the
Stripe webhook provisioned `assessor_cap` from the plan line, and the UI sold
+50 assessors at $495 per cycle.

⭐⭐ TWO SHAPES, BOTH CAUGHT:
  1. ENFORCEMENT — refusing on a count (402/403 keyed to a headcount)
  2. MONETISATION — a per-head or per-block price for more of them

⭐ KEYED ON BEHAVIOUR VIA AN AST READ, NOT ON A WORD (§III.9). Five times this
era a guard banned a token and struck the prose explaining the rule — including
this file's own subject matter. A docstring saying "seat caps are struck" must
not fail the build.

⭐ CONTROLS PLANTED IN MEMORY, never on disk (§III.10).

⭐ `company_slots` IS NOT A USER CAP. One company per workspace is still the
model, and a guard that swept it up would be the substring error with a bigger
blast radius.
"""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHED = ("services/api/accounts.py",)

# ⭐ The retired names. Their REAPPEARANCE as a definition is the tell — not
# their appearance in a comment recording that they were struck.
RETIRED = {"ASSESSOR_PLAN_CAPS", "ASSESSOR_CAP_DEFAULT",
           "ASSESSOR_OVERAGE_BLOCK", "ASSESSOR_OVERAGE_PRICE"}
RETIRED_FUNCS = {"_enforce_seat_cap", "_seat_status", "_assessor_cap"}

# ⭐ NOT a user cap — named so the guard cannot swallow it by accident.
ALLOWED = {"company_slots", "_slots_used", "companies_allowed"}


def offences(src):
    """-> [(line, kind, detail)]. AST only; prose is never evidence."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [(getattr(e, "lineno", 0), "syntax", str(e))]

    for n in ast.walk(tree):
        # ── shape 1a: a retired constant is DEFINED again ──────────────────
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in RETIRED:
                    out.append((n.lineno, "constant", f"{t.id} is defined again"))
                # ── shape 1b: the purchase flow provisions a cap ───────────
                if isinstance(t, ast.Attribute) and t.attr in (
                        "assessor_cap", "assessor_overage"):
                    out.append((n.lineno, "provision",
                                f"a cap is written to .{t.attr}"))
        # ── shape 1c: a retired enforcer returns ───────────────────────────
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                n.name in RETIRED_FUNCS:
            out.append((n.lineno, "enforcer", f"{n.name}() is back"))
        # ── shape 1d: an Account constructed WITH a cap ────────────────────
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg in ("assessor_cap", "assessor_overage"):
                    out.append((n.lineno, "provision",
                                f"constructed with {kw.arg}"))
    return out


def monetisation(src):
    """⭐⭐ SHAPE 2 — selling MORE HEADS. A price attached to a count of people.

    Detected as a string literal that prices a per-head or per-block unit, which
    is the form the overage door took. ⭐ A LITERAL IS THE ARTEFACT HERE — the
    copy a customer reads IS the offer, so matching it is matching behaviour and
    not prose about behaviour.
    """
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if not isinstance(n, ast.Constant) or not isinstance(n.value, str):
            continue
        v = n.value.lower()
        if "$" not in v and "usd" not in v:
            continue
        if any(w in v for w in ("per assessor", "per seat", "per viewer",
                                "assessors per cycle", "per user",
                                "per additional", "per member")):
            out.append((n.lineno, "monetisation", v[:60]))
    return out


def _control():
    """⭐⭐ THE KNOWN POSITIVE — planted in memory, nothing written."""
    fails = []
    cases = [
        ("ASSESSOR_CAP_DEFAULT = 50\n", True, "a retired constant redefined"),
        ("def _enforce_seat_cap(db, c, y):\n    pass\n", True, "the enforcer returns"),
        ("account.assessor_cap = 50\n", True, "the purchase flow provisions a cap"),
        ("Account(owner_user_id=1, assessor_overage=50)\n", True,
         "an Account constructed with overage"),
        # ⭐ the three that must NOT fire
        ('"""Seat caps are struck entirely; assessor_cap is retired."""\n', False,
         "⭐ a DOCSTRING recording the strike"),
        ("account.company_slots += slots\n", False,
         "⭐ company_slots — NOT a user cap"),
        ("used = _slots_used(db, a.id)\n", False, "⭐ the company-slot counter"),
    ]
    for src, should_flag, label in cases:
        if bool(offences(src)) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}")

    money = [
        ('q = "Add more at $495 per 50 assessors per cycle."\n', True,
         "the overage offer"),
        ('q = "$100/mo per additional member"\n', True, "a per-head price"),
        ('q = "$4,995 / company / month"\n', False,
         "⭐ the FLAT COMPANY PRICE — the ruled model, not a cap"),
        ('q = "Unlimited users are included."\n', False, "⭐ the ruling stated"),
    ]
    for src, should_flag, label in money:
        if bool(monetisation(src)) != should_flag:
            fails.append(f"{label}: expected flag={should_flag}")
    return fails


def main():
    fails = _control()
    if fails:
        print("✗ check-no-seat-caps: THE CONTROL FAILED")
        for f in fails:
            print("   ", f)
        return 1
    print("  ✓ control: flags a redefined constant, the enforcer, a provisioned "
          "cap, and a per-head price; accepts a docstring recording the strike, "
          "company_slots, and the flat per-company price")

    checked, bad = 0, []
    for rel in WATCHED:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f"✗ watched file missing: {rel}")
            return 1
        src = open(p, encoding="utf-8").read()
        checked += 1
        for ln, kind, detail in offences(src) + monetisation(src):
            bad.append((rel, ln, kind, detail))

    # ⭐ COVERAGE PRINTED. "0 offences in 0 files" and "0 in 1" print the same
    # tick and mean opposite things (III.4).
    print(f"  files checked: {checked}")
    if not checked:
        print("✗ zero files checked — a broken selector, not a clean result")
        return 1

    if bad:
        print(f"✗ {len(bad)} cap offence(s):")
        for rel, ln, kind, detail in bad:
            print(f"   {rel}:{ln}  [{kind}] {detail}")
        print("\n  Unlimited users, both tiers (§5a). An overage price is a cap "
              "wearing a different name.")
        return 1

    # ⭐⭐ AND THE ADJACENT QUANTITY MUST SURVIVE — a sweep that removed
    # company_slots would be over-broad, and this guard would have let it.
    acct = open(os.path.join(ROOT, "services/api/accounts.py"), encoding="utf-8").read()
    if "company_slots" not in acct or "_slots_used" not in acct:
        print("✗ company_slots was swept up. One company per workspace is still "
              "the model, and a company slot is not a user seat.")
        return 1

    # ═══════════════════════════════════════════════════════════════════
    # ⭐⭐ THE THIRD SHAPE — A CAP IN PROSE (added 5 Aug).
    #
    # ⛔ THIS GUARD WATCHED ONE PYTHON FILE AND READ ITS AST. The pricing page
    # carried "10 full members · 5 view-only users · 50 assessors per assessment
    # cycle" for both tiers, plus a per-seat add-on table pricing an extra member
    # at $100/mo, a viewer at $50/mo and assessors at $495 per 50 — the exact
    # MONETISATION shape this file already refuses in code. It survived the 1 Aug
    # consequence sweep and this gate, because neither looked at copy.
    #
    # ⭐ A CAP IN PROSE IS THE SAME CLAIM WHERE THE GUARD DOES NOT LOOK — and it
    # is the one a customer actually reads.
    #
    # ⭐⭐ COMMENTS ARE STRIPPED FIRST, AND THAT IS LOAD-BEARING. This file's own
    # docstring warns that five guards this era banned a token and struck the
    # prose explaining the rule. The corrected copy quotes the struck text in a
    # JSX comment so the strike is legible — and a scan that read comments would
    # fail the very file that records the fix. It happened once during this lane,
    # to the author's own verification.
    rc = _copy_half()
    if rc:
        return rc

    print("✓ no cap on users, in any of the three shapes; company_slots intact")
    return 0


# ── the prose half ────────────────────────────────────────────────────────
CAP_PROSE = (
    (re.compile(r"\b\d+\s+full members\b", re.I), "a member cap in copy"),
    (re.compile(r"\b\d+\s+view-only users\b", re.I), "a viewer cap in copy"),
    (re.compile(r"\b\d+\s+assessors?\s+per\b", re.I), "a per-cycle participant cap in copy"),
    (re.compile(r"additional\s+(full member|view-only user|assessors?)", re.I),
     "a per-seat add-on priced in copy"),
    (re.compile(r"\$\s?\d[\d,]*\s*per\s*\d+\s*,?\s*per assessment cycle", re.I),
     "an overage price in copy"),
)


def _strip_comments(src: str) -> str:
    """⭐ JSX and block comments removed BEFORE any match. The struck text is
    quoted in comments deliberately, so the strike is legible in the diff."""
    src = re.sub(r"\{/\*.*?\*/\}", " ", src, flags=re.S)
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    # ⭐⭐ AND `//` LINE COMMENTS TOO — §III.9, THE EIGHTH OCCURRENCE, and this
    # time inside a guard whose OWN docstring warns about it. The first form of
    # this scan stripped only block comments and fired on
    # stakeholder-engagement.tsx, where a `//` comment RECORDS that the $495-per-50
    # door was removed. A guard that reads the note saying "this was struck" and
    # calls it a breach punishes the fix for being documented.
    # ⛔ `(?<!:)` so a URL's `//` is not mistaken for a comment.
    src = re.sub(r"(?<!:)//[^\n]*", " ", src)
    return src


def _copy_half() -> int:
    fe = os.environ.get("AXIOM_FRONTEND",
                        "/Users/samirasaf/dev/optimization-anchor")
    base = os.path.join(fe, "src")
    if not os.path.isdir(base):
        # ⭐ THE RULED SHAPE (94a7ce0, eb89ee8): report what did not run and
        # exit 0. This gate guards seat caps, not whether a sibling repo is
        # checked out beside it.
        print(f"  ⚠ COPY HALF NOT RUN — no frontend at {fe}. This run asserts "
              f"NOTHING about caps in commercial copy.")
        return 0
    hits, n = [], 0
    for d, dirs, names in os.walk(base):
        dirs[:] = [x for x in dirs if x not in ("node_modules", ".git")]
        for fn in names:
            if not fn.endswith((".tsx", ".ts")):
                continue
            fp = os.path.join(d, fn)
            try:
                txt = _strip_comments(open(fp, encoding="utf-8").read())
            except OSError:
                continue
            n += 1
            for pat, why in CAP_PROSE:
                for m in pat.finditer(txt):
                    hits.append((os.path.relpath(fp, fe),
                                 txt[:m.start()].count("\n") + 1, why,
                                 m.group(0)[:60]))
    print(f"  copy files checked: {n}")
    if not n:
        print("✗ zero copy files checked — a broken selector, not a clean result")
        return 1
    if hits:
        print(f"✗ {len(hits)} cap(s) in commercial copy:")
        for rel, ln, why, txt in hits:
            print(f"   {rel}:{ln}  [{why}] {txt!r}")
        return 1
    print("  ✓ no cap or per-seat price in commercial copy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
