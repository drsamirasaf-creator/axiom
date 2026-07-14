# ADR-002: Identity deferred; demo-tenant header; open CORS

Status: Accepted for the Research and Educational edition (SPEC-008 §6.6).

Decision: v0 ships without user identity. All rows are scoped by the
X-AXIOM-Tenant header (default "demo"), giving tenant isolation semantics from
day one without an auth dependency. CORS is open so the Lovable frontend can
integrate immediately.

Trigger to revisit: any deployment beyond the educational edition, or the
first persistent multi-user workspace (expected Phase 5-6), at which point the
Identity and Access Service (SPEC-008 §19.4.9) is introduced and this ADR is
superseded.
