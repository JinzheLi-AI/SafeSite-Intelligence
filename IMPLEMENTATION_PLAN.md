# Implementation plan

1. Establish a typed FastAPI/SQLAlchemy backend, validated AI contracts, deterministic risk policy, and transactional human-controlled lifecycle.
2. Seed a repeatable 18-case historical dataset and Tower A inspection; expose dashboard, analytics, evidence, knowledge and governance APIs.
3. Build a responsive Next.js command center, inspection review, incident lifecycle, and honest analyst/knowledge placeholders.
4. Test risk boundaries, persistence, invalid transitions, human decisions, reinspection and audit; run lint, typecheck, production build and browser workflow.
5. Document local setup, reset, mock boundaries and real-provider integration.

Design clarification: inspection findings are proposals. POST /inspections/{id}/confirm creates one confirmed incident per hazard. Incident confirmation/rejection endpoints also exist for subsequent human review. No unconfirmed AI incident is silently created.
