# ADR-004: Lovable frontend in its own repository

Status: Accepted. Category: repository strategy (SPEC-008 §10.6, §18.5).

Context: SPEC-008 §18.3 places the frontend at apps/web inside the monorepo,
but Lovable's GitHub sync manages a whole repository, not a subdirectory.

Decision: the Lovable-generated frontend lives in its own repository
(axiom-web) under the same owner, synchronized by Lovable. The monorepo's
apps/web/README.md points to it. All §18.5 rules still apply: the frontend
holds no mathematics, no secrets, no business rules; prompts that generate it
are versioned in the monorepo at docs/lovable/ and are the reviewable artifact.

Trigger to revisit: Lovable subdirectory sync support, or frontend ejection
from Lovable — either returns the code to apps/web and supersedes this ADR.
