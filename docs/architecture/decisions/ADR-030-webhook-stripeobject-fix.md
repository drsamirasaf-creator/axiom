# ADR-030 — Webhook StripeObject coercion fix

Status: accepted · Phase 20.1 · Production hotfix

## Problem

The live webhook returned 500. Traceback: engine.process_event ->
event.get("type") -> AttributeError in stripe/_stripe_object.py. Cause:
stripe.Webhook.construct_event returns a StripeObject, not a plain dict.
StripeObject's attribute/`.get` semantics differ, so dict-style access
raised AttributeError. The unit tests passed because they fed plain dict
mocks — the mock did not match the real SDK return type.

## Decision

verify_and_parse now converts the verified event to a plain dict via
_to_plain_dict (to_dict_recursive() when available, else a JSON round-trip).
process_event additionally coerces the event and its nested data.object
defensively, so it is robust whether handed a dict or a StripeObject. A
regression test simulates a StripeObject-like object whose .get raises
AttributeError on missing keys, reproducing the production failure, and
asserts activation succeeds.

## Consequence

Battery at 283. Deploy this, then RESEND the failed event from the Stripe
dashboard (no re-payment needed) to activate the test subscription.

## Lesson

Mock fidelity: when mocking an SDK boundary, the mock's TYPE and access
semantics must match the real object, not just its data shape.
