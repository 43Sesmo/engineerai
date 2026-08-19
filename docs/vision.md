# EngineerAI — Vision

*This is the project's source of truth. It is maintained throughout development — every architecture review that changes mission scope, principles, or long-term capabilities should be reflected here.*

---

## 1. Mission Statement

EngineerAI is a **Personal AI Engineering Company** designed to act as a lifelong engineering partner. Its purpose is to transform ideas, sketches, photos, drawings, and engineering requirements into manufacturable engineering solutions — starting as a personal tool built for its founder, and designed to grow smarter with every project it touches through a dedicated Knowledge Vault.

---

## 2. Long-Term Vision

EngineerAI is intended to eventually be capable of:

- Understanding engineering ideas expressed in plain language
- Asking intelligent, targeted clarifying questions
- Generating design concepts
- Performing engineering calculations
- Creating CAD models
- Producing technical drawings
- Running simulations
- Suggesting manufacturing methods
- Estimating costs
- Reviewing designs for weaknesses or improvements
- Reverse engineering parts from photos and drawings
- Researching engineering solutions and precedents
- Managing engineering projects end to end
- Identifying engineering and business opportunities
- Continuously learning from every completed project through the Knowledge Vault

None of these capabilities beyond structured text-based engineering guidance exist yet. This section describes the destination the architecture is built toward, not the current state of the system.

---

## 3. Core Principles

- **Personal-first, commercial-later.** The system is architected for a single founder-user first. Commercial features — billing, multi-tenancy, marketplace, enterprise roles — are not built until a real second user exists.
- **Simplicity over premature scale.** Every technology and pattern chosen must be realistically buildable and maintainable by a solo founder.
- **Extensibility without overengineering.** Future departments and capabilities have a clear, pre-agreed place to plug in later, without speculative infrastructure being built ahead of actual need.
- **The Knowledge Vault is a first-class strategic asset**, not an afterthought — modeled correctly from day one because retrofitting it later would be far more costly than building it right the first time.
- **CAD generation is a primary long-term capability**, not a minor add-on — it represents the step-change from EngineerAI giving advice to EngineerAI producing manufacturable artifacts.
- Every architectural decision explicitly distinguishes **what is built now, what is deferred, and what should never be built until proven necessary.**

---

## 4. Department Descriptions

EngineerAI's long-term vision is to function as a complete engineering company serving a single user, composed of specialized departments. **None of these are implemented yet** — each has a reserved, empty placeholder in the codebase (`departments/`) so it can be added later without restructuring the system around it.

- **Design Engineering** — turns engineering requirements and raw ideas into concrete design concepts and specifications.
- **CAD Engineering** — generates CAD models and technical drawings from finalized design specifications. EngineerAI's primary long-term capability. Future scope includes parametric CAD generation, iterative refinement, geometry verification, controlled artifact modification and versioning, manufacturing-aware design, and handoff to simulation/manufacturing workflows — coordinated through the cross-cutting capabilities in Section 7.
- **Manufacturing Engineering** — suggests manufacturing methods, materials, tolerances, and cost estimates for a given design.
- **Simulation Engineering** — runs structural, thermal, or motion simulations against CAD models to validate a design before manufacture.
- **Research Engineering** — researches engineering solutions, standards, and precedents relevant to a project.
- **Reverse Engineering** — reconstructs a part from a photo through the pipeline: part identification → dimension estimation → CAD reconstruction → verification against evidence → revision/additional measurement if necessary → manufacturing drawing. The system is intended to eventually identify uncertainty and request additional evidence rather than presenting an uncertain measurement as exact.
- **Business Development** — mines the Knowledge Vault across projects to surface recurring problems, patterns, and potential business or product opportunities.
- **Project Management** — tracks and manages engineering projects, timelines, and decisions across their lifecycle.

---

## 5. Knowledge Vault Philosophy

The Knowledge Vault is EngineerAI's long-term moat — not a log of past conversations, but a structured, growing body of engineering memory meant to make the system measurably smarter with every project completed. Its architectural role is to eventually preserve not just individual entries but the *relationships* between them — engineering decisions, the assumptions and constraints behind them, project context, design revisions, verification results, generated artifacts, source/provenance information, and reusable design patterns — so future reasoning can draw on how and why past conclusions were reached, not just what was concluded.

It stores seven types of entries:

| Type | Purpose |
|---|---|
| `decision` | A specific engineering choice made, and why |
| `lesson_learned` | What went wrong or was underestimated, and why |
| `design_knowledge` | Reusable rules of thumb, formulas, standards references |
| `design_pattern` | Reusable, named engineering solution shapes — e.g. keyway design, bearing mounting, shaft-hub connections, flange couplings, bolt selection |
| `failure` | What was tried and didn't work |
| `preference` | Standing user preferences (units, preferred materials, tolerances) |
| `research_finding` | Notes from external research on a method or material |

The Vault is designed to evolve in phases, not all at once:

1. **Structured storage** — entries are created and tagged, retrievable by project and tag.
2. **Semantic retrieval** — embeddings allow relevant past knowledge to surface automatically during new engineering reasoning.
3. **Cross-project pattern extraction** — recurring lessons and patterns are periodically summarized into higher-level institutional knowledge.
4. **Business opportunity discovery** — accumulated project history is mined to surface product or business ideas that wouldn't be visible from any single project alone.

---

## 6. Future Roadmap

The high-level capability chain EngineerAI is being built toward, sprint by sprint:

```
Idea → Engineering Reasoning → CAD Generation → Simulation → Manufacturing Planning → Knowledge Vault Learning → Business Opportunity Discovery
```

The current foundation builds only the first link (Engineering Reasoning) and the beginning of Knowledge Vault Learning. Every other link — CAD Generation, Simulation, Manufacturing Planning, Business Opportunity Discovery, and Reverse Engineering as a path into CAD — is a deliberately reserved placeholder, waiting for a future, dedicated sprint rather than being bolted on ahead of need. The cross-cutting capabilities in Section 7 layer onto this same chain rather than replacing any part of it.

---

## 7. Cross-Cutting Architectural Capabilities

Distinct from Departments (Section 4), which are domain-specific engineering capabilities, cross-cutting capabilities are architectural patterns that operate *across* departments and the Engineering Reasoning Layer, rather than being owned by any one domain. **None of these are implemented yet.** They are documented here as approved future architectural concepts — added following a competitive-intelligence review (see `docs/competitive-intelligence.md`) — to be scheduled into the roadmap as dependencies allow, not pulled into current sprint work.

- **Reasoning** — the Engineering Reasoning Layer, already part of the core architecture, is the first cross-cutting capability; everything below builds on it.
- **Engineering Verification & Validation** — validates engineering calculations, generated artifacts, CAD geometry, and constraints; checks manufacturability; identifies assumptions and uncertainty; records verification results; and triggers revision when verification fails. Supports a `Generate → Verify → Revise → Verify → Approve` pattern, applicable across CAD, reverse engineering, calculations, simulation, and manufacturing planning.
- **Iterative Engineering Loop** — a reusable workflow shape: `Requirement → Engineering Reasoning → Design/Artifact Generation → Verification → Revision (if necessary) → Verification → Approval → Final Artifact`. A pattern departments and the reasoning layer follow, not a department itself.
- **Controlled Engineering Artifact Modification** — safely modifying important engineering artifacts: `Existing Artifact → Proposed Modification → Preview/Difference → User Approval → New Version`, with version history, rollback, traceability, and preservation of prior artifacts. Applies particularly to CAD and manufacturing artifacts.
- **Caching** — temporary, performance-oriented storage to reduce repeated work (repeated calculations, repeated AI/API requests, frequently accessed knowledge, expensive verification results, intermediate workflow results). Explicitly distinct from the Knowledge Vault: caching is disposable performance optimization, not persistent engineering memory.
- **Knowledge / Project Memory** — the strengthened Knowledge Vault role described in Section 5: preserving relationships between decisions, assumptions, constraints, revisions, verification results, artifacts, and provenance, not just isolated entries.

---

## 8. Major Decisions Log

- Personal-first architecture selected.
- FastAPI selected for backend.
- PostgreSQL + pgvector selected for data layer.
- Knowledge Vault designated as a first-class system.
- CAD Generation designated as a primary long-term capability.
- Reverse Engineering department approved.
- **2026-08-09** — SQLite adopted as the temporary local development database because the current development machine has 4 GB RAM and approximately 10 GB free storage. PostgreSQL + pgvector remains the approved long-term architecture. Docker Desktop and WSL2 are postponed until adequate hardware or another suitable development environment is available.
- **2026-08-10** — EngineerAI's architecture is being strengthened using lessons from existing engineering-AI systems (see `docs/competitive-intelligence.md`), with emphasis on verification, iterative engineering workflows, persistent engineering memory, controlled artifact modification, stronger CAD/reverse-engineering workflows, and caching. These are documented as architectural/future capabilities only — no Sprint 1 scope was changed, no departments were added, and no code, dependencies, or database migrations were introduced.
- **2026-08-19** — Sprint 1 completed. The personal-first architecture was validated end-to-end, from repository scaffolding through a working (if intentionally minimal) frontend. Key decisions validated in practice, not just on paper: SQLite proved to be a genuinely engine-agnostic interim database — zero domain model changes were needed to support it, confirming the JSON-not-JSONB and settings-centralization decisions made along the way; FastAPI + SQLModel + Alembic proved to be a workable, lightweight stack for solo-founder development, including surviving a real SQLite-specific Alembic configuration bug found and fixed during Task 6; Next.js's App Router required careful attention to Server/Client Component boundaries, learned directly from a real failure during Task 13. The full idea-to-Claude-to-storage round trip was implemented and verified in every respect except the final live-API-key step, which remains the one outstanding item before full closure. PostgreSQL + pgvector remains the approved long-term architecture, unchanged by any of the above.
