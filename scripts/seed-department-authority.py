#!/usr/bin/env python3
"""Seed department authority on Meridian so the demo shows sign-off working.

⭐⭐ WHY THERE WAS NOTHING TO SEE. `ax_department_authority` held ZERO rows
company-wide, and on Meridian that was not a defect in the grant path — it was
two structural facts:

  1. ⭐ MERIDIAN HAD ZERO MEMBERSHIPS. `grant_department()` needs a `user_id`,
     and DepartmentAuthorityPanel builds its candidate list from
     `/companies/{id}/roster`. With no members there was NOBODY TO GRANT TO —
     the panel rendered, and offered an empty list.
  2. ⭐ THE ONLY PERSON WHO EVER OPENED MERIDIAN IS PLATFORM STAFF, and both
     `post_grant` and `grant_department` refuse platform staff DELIBERATELY:
     granting is how authoring is obtained, so being unable to author is
     worthless if we can grant ourselves a moment earlier.

So the path was never exercised, and zero rows was the correct consequence of
those two facts rather than a fault in the endpoints.

⭐⭐ THIS SEED GOES THROUGH `grant_department()`, THE PRODUCTION WRITER. Writing
rows directly would seed a state THE PRODUCT ITSELF REFUSES TO CREATE — it would
bypass the self-grant refusal and the platform-staff refusal, and the demo would
show something unreachable through the UI. A seed that reproduces a call path
measures its own reimplementation.

⛔ THE SEEDED USERS CARRY NO CREDENTIAL. `password_hash` is NULL and
`link_only` is set: they are magic-link shadow identities that exist to HOLD
authority, not to log in. Nothing here writes a password or a token.

⛔ EVERY WRITE IS SCOPED TO MERIDIAN BY EXACT COMPANY ID, and every delete-shaped
operation is absent entirely — this script only inserts, and re-running it is a
no-op.

    python3 scripts/seed-department-authority.py --dry-run
    python3 scripts/seed-department-authority.py --apply
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

COMPANY_ID = 20                     # Meridian Industrial Group (showcase)
COMPANY_NAME = "Meridian Industries, Inc."

# ⭐ THE GRANTER IS NOT A GRANTEE. §7.1's separation — the admin decides who
# speaks for a department and can never speak for one — is enforced inside
# `grant_department()`, and this seed is arranged to satisfy it rather than to
# work around it.
ADMIN = ("ops.admin@meridian-demo.example", "Meridian Administrator")

# ⭐ ONE DEPARTMENT WITH A HOLDER AND ONE WITHOUT IS THE POINT. A department with
# no holder CANNOT be signed off by anyone — including the admin — and that
# refusal is a real demonstration, not a gap in the demo.
GRANTS = [
    ("Information Technology", "sofia.ianni@meridian-demo.example",
     "Sofia Ianni", "Chief Technology Officer"),
    ("Finance and Accounting", "marcus.chen@meridian-demo.example",
     "Marcus Chen", "Chief Financial Officer"),
]
# Left deliberately unheld, and named so the omission is a decision on the
# record rather than an accident of which rows happened to be written:
LEFT_VACANT = ("Executive Management", "Operations", "Sales & Marketing",
               "Supply Chain and Logistics", "Human Resources")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not (a.apply or a.dry_run):
        print("Refusing to guess. Pass --dry-run or --apply.")
        return 2

    from services.api.accounts import (Department, Membership, SessionLocal,
                                      User)
    from services.api.modules.enterprise_state.models import Enterprise
    from services.api.overrides import DepartmentAuthority, grant_department

    db = SessionLocal()
    try:
        ent = db.get(Enterprise, COMPANY_ID)
        # ⭐ THE NAME IS CHECKED, NOT ASSUMED. A seed keyed on an integer alone
        # writes into whatever company happens to hold id 20 on the database it
        # is pointed at. This refused once already, correctly, when the constant
        # was wrong — which is the guard doing its job before any write.
        if ent is None or ent.name != COMPANY_NAME:
            print(f"  ✗ company {COMPANY_ID} is not {COMPANY_NAME!r} — refusing. "
                  f"This seed is scoped to one company by exact id.")
            return 1
        deps = {d.name: d for d in
                db.query(Department).filter_by(company_id=COMPANY_ID).all()}
        missing = [n for n, _e, _nm, _t in GRANTS if n not in deps]
        if missing:
            print(f"  ✗ departments not found: {missing}")
            return 1

        print(f"SEED DEPARTMENT AUTHORITY — company {COMPANY_ID}, "
              f"{'APPLY' if a.apply else 'DRY RUN'}\n")
        before = (db.query(DepartmentAuthority)
                    .filter_by(company_id=COMPANY_ID).count())
        print(f"  authority rows before: {before}")

        def upsert_user(email, name):
            u = db.query(User).filter_by(email=email).first()
            if u:
                return u, False
            u = User(email=email, name=name, org_name=COMPANY_NAME,
                     platform_role="user", status="active",
                     # ⛔ NO CREDENTIAL. Shadow identity, not a login.
                     password_hash=None, link_only=True, email_verified=False)
            db.add(u)
            db.flush()
            return u, True

        def upsert_member(uid, role):
            m = (db.query(Membership)
                   .filter_by(user_id=uid, company_id=COMPANY_ID).first())
            if m:
                return m, False
            m = Membership(user_id=uid, company_id=COMPANY_ID, role=role,
                           status="active")
            db.add(m)
            db.flush()
            return m, True

        admin, made = upsert_user(*ADMIN)
        upsert_member(admin.id, "admin")
        print(f"  admin (granter): user {admin.id} "
              f"{'created' if made else 'existing'} · role=admin")

        granted = []
        for dept_name, email, name, title in GRANTS:
            u, made_u = upsert_user(email, name)
            upsert_member(u.id, "viewer")
            # ⭐ THE PRODUCTION WRITER. It enforces the self-grant refusal, the
            # platform-staff refusal and the one-live-grant rule; re-running is
            # idempotent because it returns the existing live grant.
            row = grant_department(
                db, COMPANY_ID, deps[dept_name].id,
                user_id=u.id, granted_by=admin.id,
                role="cxo", role_label=title, actor=admin)
            granted.append((dept_name, u.id, name, title, row.id))
            print(f"  ⭐ {dept_name:<26} -> user {u.id} "
                  f"{'(created)' if made_u else '(existing)'} as {title} "
                  f"· grant {row.id}")

        print(f"\n  LEFT WITHOUT A HOLDER, deliberately ({len(LEFT_VACANT)}):")
        for n in LEFT_VACANT:
            print(f"     {n}")
        print("  ⭐ A department with no holder cannot be signed off by anyone, "
              "including\n     the admin — and that refusal is the other half of "
              "the demonstration.")

        if a.apply:
            db.commit()
            after = (db.query(DepartmentAuthority)
                       .filter_by(company_id=COMPANY_ID).count())
            print(f"\n  COMMITTED. authority rows after: {after}")
        else:
            db.rollback()
            print("\n  ROLLED BACK — dry run. Nothing was written.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
