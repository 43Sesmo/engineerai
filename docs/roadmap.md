# EngineerAI — Development Roadmap

The full sprint-by-sprint development roadmap is maintained here as each sprint is planned and completed.

**Status:** Sprint 1 (Foundation) is in progress. See the approved Sprint 1 Implementation Plan for full task-level detail.

This file will be filled in incrementally — each completed sprint should be summarized here (goals, what shipped, what was deferred) once it closes, so the roadmap reflects real progress rather than the original plan alone.

---

## Future Architectural Capabilities (Not Yet Scheduled)

Following an architecture review (2026-08-10, see `docs/vision.md` Section 7 and `docs/competitive-intelligence.md`), six cross-cutting capabilities were approved as future architectural concepts. **None are scheduled to a specific sprint yet** — they are placed here only to record roughly where they depend on other work, for future roadmap planning:

- **Engineering Verification & Validation** and **Iterative Engineering Loop** — earliest realistic value once at least one generative department (most likely CAD) exists; a natural pairing, likely scheduled together in a future phase.
- **Controlled Engineering Artifact Modification** — depends on generated artifacts existing to modify; realistically follows CAD generation, not before it.
- **Knowledge/Project Memory strengthening** — layers onto the Knowledge Vault's existing phased evolution (already documented in `docs/vision.md` Section 5); no new phase required, just additional depth within phases already planned.
- **CAD and Reverse Engineering strengthening** — enriches the scope of those two departments' eventual implementation; doesn't require a new phase, just a broader definition of "done" whenever those departments are eventually built.
- **Caching** — lowest near-term priority; realistically a later-stage infrastructure phase, once real performance pressure exists across multiple active departments.

Sprint 1 scope is unaffected by any of the above.
