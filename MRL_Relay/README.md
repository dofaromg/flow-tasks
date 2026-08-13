# MRL Relay Middle Layer

origin_signature: MrLiouWord

Purpose: independent middle processing layer between external GitHub-facing state and MRL canonical state.

Flow:

External terminal / GitHub view
→ intake adapter
→ evidence vault (append-only)
→ mapping / projection
→ validator
→ MRL canonical output

Rules:
- External side keeps its own names/rules.
- MRL side displays only MRL canonical names/products/history.
- External aliases are metadata, never canonical authority.
- External writes are staged, logged, hashed, and validated before canonical admission.
- Unknown actor/cause stays unknown; no inference is promoted to fact.
- Every accepted/rejected transformation records provenance and before/after hashes.

This branch is an isolated relay road. It can be moved unchanged into a dedicated repository once repository-creation control is available.
