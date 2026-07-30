"""Rebuild Meridian's assessment surface from a committed fixture.

⭐ WITHOUT THIS, A REBUILT MERIDIAN HAS FINANCIALS AND NO CEI. seed_showcase()
restores the company, its datasets, its documents and its valuation runs — and
stops. The assessment cycle, the banded respondents, the sentiment and the
seniority gradient were created by calling API endpoints with request bodies
that existed nowhere in the repository, so 4 of 13 evidence surfaces rebuilt.
Meridian is the entire sales surface; a demo that cannot be rebuilt cannot be
restored.

⭐⭐ THE FIXTURE IS FAITHFUL, NOT IDEALISED, AND THAT IS A RULING NOT AN
OVERSIGHT. Measured against production before it was written, the live data
carries three things that look like defects:

  · cycle 37 has SIX departments and no Executive Management, while its own five
    history cycles have SEVEN including it — a department staffed with 6 people
    that reports for five quarters and then vanishes at the point a CFO reads
    first.
  · cycle 37 stores PRE-CANONICAL short forms ('Finance', 'HR', 'Technology',
    'Supply Chain'); cycles 48-52 store canonical ones. The same company holds
    two spellings of its own org chart in different periods.
  · the ledger records the headline CEI as 5.62. It is 6.3716, and nothing
    records what changed it.

All three are reproduced exactly. A seed that improves what it reproduces is not
a reproduction, and the verification becomes circular the moment the target is a
number the seed itself chose. Both are filed as defects against the DEMO, to be
fixed deliberately once it is reproducible — at which point the CEI moves on
purpose, with a recorded before and after.

⭐ THE SPELLING SPLIT IS KEPT ON PURPOSE FOR A SECOND REASON. Writing canonical
names throughout would produce a demo that never exercises CANONICAL_DEPT_RENAMES
— the alias path that runs on every read of the current cycle. A seed that avoids
the messy path tests a system nobody runs.

ROSTER: 30 AssessmentInvite rows with is_demo=True are created for the current
cycle, which production left at 7. That is §17.2's designed mechanism, and it is
what makes participation tracking demonstrable. Participant rows are deliberately
NOT written — seed_assessment_history's own contract is that seats stay untouched
and the roster stays real, and a showcase company falls back to
ASSESSOR_CAP_DEFAULT (50), so 30 demo invites sit inside the cap.

IDEMPOTENT BY CYCLE NAME, matching seed_assessment_history: a cycle whose name
already exists is skipped whole, so boot is safe and a partial run repeats.
"""
import gzip
import json
import os
import secrets
from datetime import datetime

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "meridian_assessment.json.gz")

SHOWCASE_NAME = "Meridian Industries, Inc."

# The 30 refs of the current cycle get a synthetic roster row each. Names are
# obviously fake and the domain is reserved by RFC 2606 so nothing can ever be
# delivered to them.
DEMO_DOMAIN = "example.invalid"


def _load():
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as f:
        return json.load(f)


def _showcase_company(db):
    """The showcase Meridian Enterprise.

    ⭐ Companies are Enterprise rows, not a `Company` model — and the showcase
    ones are identified by tenant, not by name alone. Matching on name only
    would find a real customer that happened to be called Meridian, which is
    exactly the reach seed_assessment_history refuses ("must be unable to reach
    a real tenant's assessment history by any path")."""
    from ..modules.enterprise_state.models import Enterprise
    from .seed import SHOWCASE_TENANT
    return (db.query(Enterprise)
            .filter(Enterprise.tenant == SHOWCASE_TENANT,
                    Enterprise.name == SHOWCASE_NAME).first())


def _synthetic_identity(ref, idx):
    """A roster identity that could not be mistaken for a real person."""
    return (f"Respondent {idx:02d} (demo)",
            f"respondent-{idx:02d}@{DEMO_DOMAIN}")


def seed_showcase_assessment():
    """Restore all six cycles, their responses, commentary and demo roster."""
    if os.environ.get("AXIOM_SEED_SHOWCASE", "true").strip().lower() in (
            "0", "false", "no", "off"):
        return {"skipped": "AXIOM_SEED_SHOWCASE is off"}
    if not os.path.exists(FIXTURE):
        return {"skipped": "fixture absent"}

    from .db import SessionLocal
    from ..accounts import (AssessmentCycle, AssessmentFramework, AssessmentItem,
                            AssessmentResponse, AssessmentOverall,
                            AssessmentInvite)

    data = _load()
    db = SessionLocal()
    out = {"cycles_created": [], "cycles_skipped": [], "responses": 0,
           "overall": 0, "invites": 0}
    try:
        co = _showcase_company(db)
        if not co:
            return {"skipped": "showcase company not present yet"}

        # ── framework + items ────────────────────────────────────────────────
        fw = (db.query(AssessmentFramework)
              .filter_by(company_id=co.id).order_by(AssessmentFramework.id.desc())
              .first())
        if not fw:
            fw = AssessmentFramework(company_id=co.id, revision=1)
            db.add(fw)
            db.flush()
        have_items = {i.code: i for i in
                      db.query(AssessmentItem).filter_by(framework_id=fw.id).all()}
        item_map = {}                       # fixture item id -> live item id
        for it in data["items"]:
            live = have_items.get(it["code"])
            if not live:
                live = AssessmentItem(framework_id=fw.id, level=it["level"],
                                      code=it["code"], title=it["code"],
                                      selected=bool(it["selected"]))
                db.add(live)
                db.flush()
                have_items[it["code"]] = live
            item_map[it["id"]] = live.id
        db.flush()

        # ── cycles, idempotent by name ───────────────────────────────────────
        existing = {(c.name or "").strip(): c for c in
                    db.query(AssessmentCycle).filter_by(company_id=co.id).all()}
        cycle_map = {}                      # fixture cycle id -> live cycle
        for spec in data["cycles"]:
            nm = (spec.get("name") or "").strip()
            if nm in existing:
                cycle_map[spec["id"]] = existing[nm]
                out["cycles_skipped"].append(nm)
                continue
            cyc = AssessmentCycle(
                company_id=co.id, framework_id=fw.id,
                revision=spec.get("revision") or 1,
                opened_at=_dt(spec.get("opened_at")),
                closed_at=_dt(spec.get("closed_at")),
                cadence=spec.get("cadence"),
                anonymity_mode=spec.get("anonymity_mode") or "anonymous",
                depth=spec.get("depth") or "standard", name=nm)
            db.add(cyc)
            db.flush()
            cycle_map[spec["id"]] = cyc
            out["cycles_created"].append(nm)
        db.flush()

        # ── responses (only for cycles we created) ───────────────────────────
        created_ids = {fid for fid, c in cycle_map.items()
                       if (c.name or "").strip() in out["cycles_created"]}
        for (cid, ref, item_id, score, comment, abstained, dept, sen) in data["responses"]:
            if cid not in created_ids:
                continue
            live_item = item_map.get(item_id)
            if live_item is None:
                continue
            db.add(AssessmentResponse(
                cycle_id=cycle_map[cid].id, participant_ref=ref,
                item_id=live_item, score=score, comment=comment,
                abstained=bool(abstained), department=dept, seniority=sen))
            out["responses"] += 1
        for (cid, ref, comment) in data["overall"]:
            if cid not in created_ids:
                continue
            db.add(AssessmentOverall(cycle_id=cycle_map[cid].id,
                                     participant_ref=ref, comment=comment))
            out["overall"] += 1
        db.flush()

        # ── demo roster for the CURRENT cycle ────────────────────────────────
        # The current cycle is the one carrying seniority — cycles 48-52 have it
        # NULL throughout, which is how the fixture distinguishes them.
        cur_fid = _current_cycle_id(data)
        if cur_fid in created_ids:
            cur = cycle_map[cur_fid]
            refs = _refs_with_bands(data, cur_fid)
            for idx, (ref, dept, sen) in enumerate(sorted(refs), start=1):
                name, email = _synthetic_identity(ref, idx)
                if db.query(AssessmentInvite).filter_by(
                        cycle_id=cur.id, email=email).first():
                    continue
                now = datetime.utcnow()
                db.add(AssessmentInvite(
                    cycle_id=cur.id, company_id=co.id, email=email, name=name,
                    department=dept, seniority=sen,
                    jti=secrets.token_urlsafe(16), invited_by=None,
                    participant_ref=ref, is_demo=True,
                    # AssessmentInvite has no `invited_at`; created_at IS the
                    # invitation time. Writing a column that does not exist
                    # raised and rolled back all 14,430 responses with it.
                    created_at=now, redeemed_at=now, submitted_at=now))
                out["invites"] += 1
        db.commit()
    except Exception as e:                       # never block boot
        db.rollback()
        out["error"] = f"{type(e).__name__}: {e}"
    finally:
        db.close()
    return out


def _dt(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v).replace("Z", "").strip())


def _current_cycle_id(data):
    """The cycle carrying seniority bands — the banded, commented one."""
    banded = {r[0] for r in data["responses"] if r[7]}
    return max(banded) if banded else max(c["id"] for c in data["cycles"])


def _refs_with_bands(data, cid):
    seen = {}
    for r in data["responses"]:
        if r[0] == cid and r[1] not in seen:
            seen[r[1]] = (r[1], r[6], r[7])
    return list(seen.values())
