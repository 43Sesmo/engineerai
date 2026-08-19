# EngineerAI — Development Roadmap

The full sprint-by-sprint development roadmap is maintained here as each sprint is planned and completed.

This file will be filled in incrementally — each completed sprint should be summarized here (goals, what shipped, what was deferred) once it closes, so the roadmap reflects real progress rather than the original plan alone.

---

## Sprint 1 — Completed

**Delivered:**
- Repository scaffolding and `docs/vision.md` as the living source of truth.
- SQLite local development database — interim, per the hardware-adaptation review; PostgreSQL + pgvector remains the approved long-term target — fully migrated via Alembic, with foreign-key enforcement verified.
- FastAPI backend with centralized settings and a working API surface: health check, projects (create/list), conversations (create/get), and the full messages round trip (commit-before-Claude-call, preserving the user's message even when the AI call fails).
- Claude client wrapper — code-complete and logic-verified through every control-flow path.
- Next.js + TypeScript + Tailwind frontend: project list/create UI, chat UI with automatic conversation creation, console-verified API client.
- Competitive-intelligence review and six cross-cutting architectural capabilities documented (see below).
- A real GitHub repository, created and backed up.

**Deliberately deferred — scope boundaries, not gaps:**
- The Docker / PostgreSQL + pgvector migration — postponed for hardware reasons, tracked in `docs/vision.md`'s Major Decisions Log, to be picked back up when hardware allows.
- Structured engineering-guidance output (Sprint 2).
- Knowledge Vault implementation (Sprint 3).
- CAD generation, reverse engineering, simulation, manufacturing planning, and business opportunity discovery — every department beyond the reasoning layer itself.

**Outstanding blocker:** a real Anthropic API key has not yet been purchased or configured. Every part of the system that depends on it has been built and verified up to that exact point, not around it — this is the one item standing between "Sprint 1 code complete" and "Sprint 1 fully closed."

---

## Future Architectural Capabilities (Not Yet Scheduled)

Following an architecture review (2026-08-10, see `docs/vision.md` Section 7 and `docs/competitive-intelligence.md`), six cross-cutting capabilities were approved as future architectural concepts. **None are scheduled to a specific sprint yet** — they are placed here only to record roughly where they depend on other work, for future roadmap planning:

- **Engineering Verification & Validation** and **Iterative Engineering Loop** — earliest realistic value once at least one generative department (most likely CAD) exists; a natural pairing, likely scheduled together in a future phase.
- **Controlled Engineering Artifact Modification** — depends on generated artifacts existing to modify; realistically follows CAD generation, not before it.
- **Knowledge/Project Memory strengthening** — layers onto the Knowledge Vault's existing phased evolution (already documented in `docs/vision.md` Section 5); no new phase required, just additional depth within phases already planned.
- **CAD and Reverse Engineering strengthening** — enriches the scope of those two departments' eventual implementation; doesn't require a new phase, just a broader definition of "done" whenever those departments are eventually built.
- **Caching** — lowest near-term priority; realistically a later-stage infrastructure phase, once real performance pressure exists across multiple active departments.

Sprint 1 scope is unaffected by any of the above.
