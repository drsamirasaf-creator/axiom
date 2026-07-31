#!/usr/bin/env python3
"""G13 backfill — establish each account's Stripe mode BY LOOKUP, and record it.

⭐⭐ ONLY WHAT IS KNOWABLE. An account whose mode cannot be established from
Stripe is left NULL — UNKNOWN — not False. Classing an account as test because it
"looks like one" is the inference-from-appearance that produced the eleventh wrong
entry, run backwards.

⭐⭐ HOW A LIVE SUBSCRIPTION IS DETECTED WITH A TEST KEY, WHICH IS THE WHOLE TRICK.
Stripe distinguishes three outcomes, and the middle one is the useful one:

    200 OK                                     -> the object is in THIS key's mode
    "a similar object exists in live mode,     -> ⭐ the object EXISTS and is LIVE
     but a test mode key was used"
    "No such subscription"                     -> ⭐ UNKNOWN — cannot be established

So a test-mode key can prove an account is LIVE without ever holding a live key.
⭐ WITHOUT THIS DISTINCTION THE BACKFILL WOULD MARK EVERY LIVE ACCOUNT "unknown"
and the count would understate real customers — the failure this lane exists to
prevent, in the direction that flatters us.

Read-only against Stripe. Writes only the two new columns. Never prints a key.

    source scripts/lane-env.sh
    python3 scripts/backfill-livemode.py            # report only
    python3 scripts/backfill-livemode.py --write    # persist
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WRITE = "--write" in sys.argv

LIVE_HINT = re.compile(r"similar object exists in (live) mode", re.I)
TEST_HINT = re.compile(r"similar object exists in (test) mode", re.I)


def _stripe_key():
    k = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not k:
        print("STRIPE_SECRET_KEY not in this shell — cannot establish any mode.")
        print("Every account would be UNKNOWN, which is a true but useless run.")
        sys.exit(1)
    # ⭐ the MODE of the key is reported; the key never is.
    return k, ("test" if k.startswith(("sk_test_", "rk_test_")) else
               "live" if k.startswith(("sk_live_", "rk_live_")) else "unrecognised")


def lookup(key, sub_id):
    """-> (livemode | None, evidence string). None means UNKNOWN."""
    import httpx
    try:
        r = httpx.get(f"https://api.stripe.com/v1/subscriptions/{sub_id}",
                      auth=(key, ""), timeout=30)
    except Exception as e:                       # network, not evidence
        return None, f"lookup failed: {type(e).__name__}"
    if r.status_code == 200:
        d = r.json()
        lm = d.get("livemode")
        if lm is None:
            return None, "200 but no livemode field"
        return bool(lm), f"200 livemode={lm}"
    msg = ((r.json() or {}).get("error") or {}).get("message", "") or r.text[:120]
    if LIVE_HINT.search(msg):
        # ⭐ THE OBJECT EXISTS AND IS LIVE. A test key cannot read it, but
        # Stripe's refusal states its mode, and that IS the evidence.
        return True, "cross-mode: object exists in LIVE mode"
    if TEST_HINT.search(msg):
        return False, "cross-mode: object exists in TEST mode"
    if "No such subscription" in msg:
        return None, "no such subscription in either mode"
    return None, f"unhandled: {msg[:80]}"


def main():
    key, key_mode = _stripe_key()
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_PUBLIC_URL", ""))
    from sqlalchemy import create_engine, text

    from services.api.core.config import database_url
    eng = create_engine(database_url())
    print(f"Stripe key mode: {key_mode}   (the key itself is never printed)")
    print(f"mode: {'WRITE' if WRITE else 'REPORT ONLY'}\n")

    rows_out = []
    with eng.connect() as c:
        rows = c.execute(text("""
            select id, tenant, plan, subscription_status, stripe_subscription_id
            from users order by id""")).all()
        for r in rows:
            sub = r.stripe_subscription_id
            if not sub:
                # ⭐ NO SUBSCRIPTION IS NOT "TEST". It is an account that never
                # subscribed, and that is a THIRD state.
                lm, ev = None, "no stripe_subscription_id — never subscribed"
            else:
                lm, ev = lookup(key, sub)
            rows_out.append((r.id, r.tenant, r.plan, r.subscription_status, lm, ev))
            print(f"  user {r.id:<3} {r.tenant:<22} plan={str(r.plan):<9} "
                  f"status={str(r.subscription_status):<9} -> "
                  f"livemode={'UNKNOWN' if lm is None else lm}   [{ev}]")

        if WRITE:
            with eng.begin() as w:
                n = 0
                for uid, _t, _p, _s, lm, ev in rows_out:
                    if lm is None:
                        continue          # ⭐ UNKNOWN STAYS NULL
                    w.execute(text("""update users
                                      set subscription_livemode=:lm,
                                          livemode_source='stripe_lookup'
                                      where id=:id"""), {"lm": lm, "id": uid})
                    n += 1
                print(f"\n  wrote {n} rows; "
                      f"{sum(1 for x in rows_out if x[4] is None)} left UNKNOWN")

    # ── the baseline count ────────────────────────────────────────────────
    live = [x for x in rows_out if x[4] is True]
    test = [x for x in rows_out if x[4] is False]
    # ⭐⭐ "NEVER SUBSCRIBED" IS NOT "UNKNOWN". Both are NULL in the column, and
    # collapsing them in the REPORT would overstate our ignorance: an account
    # with no subscription id has a KNOWN state — it never subscribed — while a
    # lookup that failed genuinely establishes nothing. A baseline that calls
    # seven free accounts "unknown" invites someone to go and resolve them.
    never = [x for x in rows_out if x[4] is None and "never subscribed" in x[5]]
    unk = [x for x in rows_out if x[4] is None and "never subscribed" not in x[5]]
    paying = [x for x in live if x[3] in ("active", "trialing")]
    print("\n=== BASELINE ===")
    print(f"  accounts total          {len(rows_out)}")
    print(f"  LIVE-MODE PAYING        {len(paying)}   <- the only real number")
    print(f"  live-mode, not paying   {len(live) - len(paying)}")
    print(f"  test-mode               {len(test)}")
    print(f"  never subscribed        {len(never)}   (known state, column stays NULL)")
    print(f"  UNKNOWN — unresolved    {len(unk)}   (lookup established nothing)")
    print("\n  ⭐ 'business/active' before this lane: "
          f"{sum(1 for x in rows_out if x[2] == 'business' and x[3] == 'active')}"
          "  <- what every prior count reported")


if __name__ == "__main__":
    main()
