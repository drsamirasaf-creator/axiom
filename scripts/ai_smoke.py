#!/usr/bin/env python3
"""Live AI smoke test (ADR-006 §1). Run MANUALLY with a real key:

    ANTHROPIC_API_KEY=sk-... python3 scripts/ai_smoke.py

The pytest suite never calls the live API (the seam is mocked); this
script is the one place a real call is exercised before deploy.
"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from services.api.modules.intelligence import ai_client, engines

DOC = ("Board strategy memo. We are targeting revenue growth of 6% (0.06) "
       "per year over the plan period, an EBIT margin of 13% (0.13) by "
       "year three, and capital expenditure of 8% of revenue (0.08). "
       "Long-run terminal growth of 2.5% (0.025) is assumed.")

try:
    reply = ai_client.complete(engines.ANALYSIS_SYSTEM_PROMPT,
                               engines.build_analysis_user_text(DOC, None))
except ai_client.AINotConfigured as e:
    sys.exit(f"NOT CONFIGURED: {e}")
print("--- raw model reply ---\n", reply[:2000])
try:
    raw = json.loads(reply.strip().removeprefix("```json")
                     .removeprefix("```").removesuffix("```"))
except json.JSONDecodeError:
    sys.exit("FAIL: model reply was not JSON")
gated = engines.gate_suggestions(raw, DOC)
print("\n--- after gates ---")
print(f"accepted: {len(gated['suggestions'])}  rejected: {len(gated['rejected'])}")
for s in gated["suggestions"]:
    print(f"  {s['field']} = {s['value']}  «{s['source_quote'][:60]}»")
for r in gated["rejected"]:
    print(f"  REJECTED: {r['reason'][:80]}")
ok = len(gated["suggestions"]) >= 2
print("\nSMOKE", "PASS" if ok else "WEAK (model proposed <2 gated suggestions)")
