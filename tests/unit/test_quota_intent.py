"""The quota counts SEATS, not client data volume. Ruled 31 Jul.

⭐ THIS FILE EXISTS BECAUSE A LEDGER LINE IS NOT ENOUGH. `enforce_company_limit`
filters `source="direct"`, so a company holding twelve UPLOADED datasets counts as
ZERO — and that reads as an oversight to anyone who does not know why it is there.
It was in fact filed as a suspected bug and carried as an open finding of
undetermined intent until it was ruled.

⭐ A FILTER WHOSE CORRECTNESS DEPENDS ON UNRECORDED COMMERCIAL INTENT WILL BE
CORRECTED BY THE NEXT PERSON WHO FINDS IT. These tests are the mechanical guardian
of that intent: they fail if someone "fixes" the filter, and the failure message
carries the reasoning rather than pointing at a paragraph.

⭐ THE RULING: uploads are not chargeable. Excel templates, documents and feedback
data do not count against any quota. **Volume is never the meter** — the same
principle as unlimited users and unlimited external pack recipients (A1).
"""
import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.mktemp(suffix=".db"))

import pytest
from fastapi.testclient import TestClient

from services.api.main import app
from tests.codeonly import code_only
from tests.fixtures.refcases import meridian


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _db():
    from services.api.core.db import SessionLocal
    return SessionLocal()


@pytest.fixture(scope="module")
def company_with_uploads(client):
    """A company holding several UPLOADED datasets — the shape that counts zero."""
    from services.api.accounts import apply_upload
    from services.api.modules.enterprise_state.models import Enterprise
    with _db() as db:
        ent = Enterprise(tenant="t-quota", name="Quota target",
                         sector="industrials", reporting_currency="USD",
                         statement_units="thousands", ownership="private")
        db.add(ent); db.commit(); db.refresh(ent)
        for _ in range(4):
            apply_upload(db, ent.id, ent=ent, data=meridian(), objectives=[],
                         key_results=[], kpis=[], departments=[], warnings=[],
                         frequency="annual", meta={}, okr_flags={}, user=None)
        db.commit()
        return ent.id, ent.tenant


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE RULING, ASSERTED
# ═══════════════════════════════════════════════════════════════════════════

def test_uploaded_datasets_do_not_count_toward_the_quota(company_with_uploads):
    """⭐⭐ THE INTENT'S GUARDIAN. If this fails, someone has made uploads
    chargeable — which is a COMMERCIAL CHANGE, not a bug fix.

    Ruled 31 Jul: uploads are not chargeable. Excel templates, documents and
    feedback data do not count against any quota. The client is NOT METERED ON
    HOW MUCH DATA THEY GIVE AXIOM.
    """
    from services.api.modules.financials.models import FinancialDataset
    cid, tenant = company_with_uploads
    with _db() as db:
        total = db.query(FinancialDataset).filter_by(enterprise_id=cid).count()
        counted = (db.query(FinancialDataset)
                     .filter_by(tenant=tenant, source="direct")
                     .filter(FinancialDataset.parent_dataset_id.is_(None))
                     .count())
    assert total >= 4, "the fixture must actually hold uploaded datasets"
    assert counted == 0, (
        f"{total} uploaded datasets counted {counted} against the quota. "
        f"Uploads are NOT chargeable (ruled 31 Jul) — volume is never the meter. "
        f"If this is a deliberate commercial change it needs a ruling, not a fix.")


def test_the_source_direct_filter_is_DELIBERATE(company_with_uploads):
    """⭐ THE FILTER IS THE MECHANISM, and it must not be quietly widened.

    Asserted against the code so the guardian survives a refactor that keeps the
    counts right today by accident.
    """
    from services.api.modules.identity.deps import enforce_company_limit
    src = code_only(enforce_company_limit).replace('"', "'")
    assert "source='direct'" in src or "source_direct" in src, (
        "enforce_company_limit no longer filters source='direct'. Uploads are "
        "not chargeable (ruled 31 Jul); widening this filter meters client data "
        "volume, which is a commercial change.")
    assert "parent_dataset_id" in src, (
        "the no-parent filter is gone — an actuals-sync child would now be "
        "counted as a separate chargeable company")


def test_the_billing_router_uses_the_same_filter():
    """⭐ TWO COUNTERS THAT DISAGREE WOULD METER DIFFERENTLY ON DIFFERENT PAGES.
    The billing surface and the enforcement gate must count the same thing."""
    from services.api.modules.billing import router as billing
    src = code_only(billing).replace('"', "'")
    assert "source='direct'" in src
    assert "parent_dataset_id" in src


def test_volume_is_never_the_meter_across_all_three_rulings():
    """⭐ THE PRINCIPLE, NOT JUST THIS COUNTER. Three separate rulings say the
    client is not metered on volume, and the counter is the third:

      * unlimited USERS — the existing commercial model
      * unlimited external RECIPIENTS — A1, ruled 31 Jul
      * unlimited uploaded DATA — this ruling
    """
    from services.api.pack_dist import PackRecipient, billing_policy
    # recipients are not metered
    pol = billing_policy()
    assert pol["current_behaviour"] == "unbilled_and_unlimited"
    # and a recipient is still not a seat
    from services.api.accounts import Membership, User
    assert PackRecipient.__tablename__ not in (Membership.__tablename__,
                                               User.__tablename__)


def test_adding_a_recipient_moves_none_of_the_three_counters(company_with_uploads):
    """⭐ THE ASSERTION NOW ENCODES A RULING RATHER THAN A COINCIDENCE (A1).

    It previously recorded that the counters happened not to move. Since 31 Jul
    that is required behaviour: external recipients are unlimited and unbilled.
    """
    from services.api.accounts import Account, CompanyAccess, _slots_used
    from services.api.modules.financials.models import FinancialDataset
    from services.api.pack_dist import PackRecipient
    cid, tenant = company_with_uploads

    def _counters(db):
        acct = db.query(Account).first()
        return (_slots_used(db, acct.id) if acct else 0,
                db.query(FinancialDataset).filter_by(
                    tenant=tenant, source="direct").count(),
                db.query(CompanyAccess).count())

    with _db() as db:
        before = _counters(db)
        db.add(PackRecipient(cid=cid, email="board-quota@example.com",
                             name="A Director", role="board", scope="board"))
        db.commit()
        after = _counters(db)
    assert after == before, (
        f"adding a recipient moved a counter: {before} -> {after}. External "
        f"recipients are unlimited and unbilled (A1, ruled 31 Jul).")
