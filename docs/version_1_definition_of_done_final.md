# EngineerAI — Version 1 Definition of Done (FINAL, approved by the Project Lead)

**Basis.** Mapped to `EngineerAI v0.1 — Architecture & Roadmap` (§3 folders, §4 Vault, §5 schema, §6 API, §7 roadmap, §8 future-proofing, §9 build now/later). Statuses are **proposals**; you decide what counts as v1. The decisions in §8 are yours as recorded in this review; this document was approved by the Project Lead on 2026-11-04. `vision.md` is committed as `bb43c9a` (13,611 bytes, SHA256 `a7619a78d49e6de8b0f6f20469685a1ee31031b4a7aac0605aa25d53dc8cd999`), and the copy in the project files matches it: the Lead Engineer checked that copy with `wc -c` and `sha256sum`, and read its line 54 and its four appended decisions-log entries.

**Evidence tags:** Sprint 3–9 closure reports (the Sprint 9 report is `sprint_9_closure_report.md`); **DB** = the Vault listing you pasted (20 entries as of 2026-10-30); **code** = read from your grep output (file and line given); **per memory** = stated in the project notes from code or output read in an earlier chat, not re-read from code in this one.

**Naming.** The architecture doc's four roadmap sprints are written **R1–R4** below so they do not collide with the project's real Sprint numbers.

## What changed from draft 6 (this is the final issue; earlier drafts are superseded)

1. **§9 additions (yours):** Y6 is met when 10 real design requests are marked trusted or not trusted, fewer than 2 are errors, and, if 3 or more are not trusted, the Project Lead has recorded what he decided after the discussion; and v1 closure does not establish that numeric answers are correct or reproducible, so Z1 stays outside v1.
2. **Basis:** "(your statement)" about `vision.md` is replaced by the Lead Engineer's own check of the project copy (13,611 bytes, SHA256 `a7619a78…d999`, matching the committed file).
3. **Y2 rider kept, with its scope stated:** keyword search is post-v1 unless real use shows entries hard to find, and that affects post-v1 timing only, not v1 closure.
4. **Status wording:** the title now reads FINAL, and the "Still open" item about approving the draft now records the approval.
5. **Re-issued with two wording fixes:** the Basis now says this document was approved by the Project Lead on 2026-11-04 (replacing "the document itself is not final until you approve it"), and §8's "Next" parenthesis now reads "(not started until the Project Lead approves its plan)".

**Carried corrections from draft 2:** (a) entries 13 and 14 are `engineering_knowledge` in the DB; (b) the architecture doc and `vision.md` say `design_knowledge`, the app offers `engineering_knowledge` and has no `failure` type; `design_pattern` is distinct from `design_knowledge`; (c) Sprint 3 Task 2 ran on `mistralai/mistral-small-2603` through xKiro, so it evidences that model only; (d) entries with no project are never retrieved (`retrieval.py`, Sprint 8 report).

## Decisions E1–E4 (yours, recorded in this review)

**E1: yes.** v1 does not require "learn from every completed project". **Note:** retrieval filters on `project_id` only (Sprint 8 report), so in v1 a preference works only inside the project where it was saved; entries with no project are never retrieved, so a global preference is not possible in v1. · **E2: yes, narrowed and extended:** "In v1, Design and Manufacturing are capabilities of the reasoning layer, not separate modules. CAD, Simulation and Reverse Engineering stay future modules; Research and Project Management are served in v1 by Vault entries and projects; Business Development is deferred; the departments/ placeholders stay." · **E3: yes.** Business Development is deferred, not dropped. · **E4: yes.** Vault delete is required for v1; edit is not. Recorded in `vision.md`'s decisions log (commit `bb43c9a`, entry dated 2026-11-02; its pointer reads "not yet final").

## 1. Roadmap deliverables (§7, items R1–R4)

| Deliverable | Proposed | Evidence |
|---|---|---|
| R1: scaffold, native; SQLite interim; core tables and migrations; Claude client; chat shell | **Done** | Sprints 4–9 run both apps; PostgreSQL + pgvector is the deferred target |
| R2: reasoning layer (prompts, schema, parsing); structured guidance; sections rendered; projects in the UI | **Done** | Sprint 8 eval 18/18; Sprint 9 V10 at medium 42/42, 0 misses |
| R2 success test ("5 kW at 300 rpm") | **Done** | Sprint 7: conversation 23, project 4 |
| R3: `knowledge_entries` table and API | **Done, differs** | Sprint 5; no `embedding` column |
| R3: embeddings and pgvector retrieval | **Deferred** | recency retrieval in its place (Sprint 8) |
| R3: auto-summarize a finished conversation | **Deferred** | manual capture only (Sprints 5, 7) |
| R3: preferences endpoint and injection into prompts | **Not built** (per memory) | no `user_preferences` table; `preference` exists only as an entry type; none saved (DB) |
| R3: retrieved knowledge injected into new conversations | **Done, different design** | Sprint 8: five most recent entries, same project only |
| R4: `engineering_analyses` persisted | **Not built** (per memory) | no table, no endpoint |
| R4: search and filter UI over the Vault | **Partial** | Sprint 6: `entry_type` filter; no keyword or tag search |
| R4: error handling, logging, single-user hardening | **Partial** | visible failure **done in forced failures** (Sprint 9 V2–V4); V5 run 1's natural 502 appears only in a screenshot sent during V5, not in the closure report; logging is a near-miss warning only; an unanswered user row and input clearing after a failed send remain on the backlog (accepted for v1; see Y4); no hardening work |
| R4: Docker Compose deployment | **Deferred** | the hardware reason no longer applies (per memory, 2026-10-27); no migration decision made |

## 2. Schema (§5) and API (§6)

| Item | Proposed | Evidence |
|---|---|---|
| `users`, `projects`, `conversations`, `messages` | **Done** | Sprint 4–8 reports |
| `knowledge_entries` | **Done, differs** | `entry_type`, `title`, `summary`, `content` (JSON), `tags` (JSON), provenance ids, `updated_at`; `entry_type` is not validated (entry 15 is "string", DB) |
| `engineering_analyses`, `user_preferences` | **Not built** | per memory: five tables in code |
| `POST/GET /api/projects`, `POST …/conversations`, `GET /api/conversations/{id}`, `GET/POST …/messages` | **Done** | Sprint 4 report, logs |
| `GET /api/projects/{id}` | **Missing** | gap carried since Sprint 4 |
| `POST/GET /api/knowledge`, `GET /api/knowledge/{id}` | **Done** | Sprint 5 |
| `/api/analyses` (2), `/api/preferences` (2) | **Not built** | per memory |
| `/api/health` | **Not evidenced** | not in any report |
| `GET /api/projects/{id}/conversations` | **Added, not in §6** | Sprint 4 |

## 3. Vault entry types (§4) and phases

| Type | Proposed | Evidence |
|---|---|---|
| `decision` | **Done** | ids 6, 9–12, 16, 17 (DB); id 20 is a stray test entry made from the `/knowledge` form during V6 |
| `lesson_learned` | **Partial** | offered in the UI (code: `KnowledgeList.tsx:9`, `SaveToVaultButton.tsx:8`); id 8 exists, test data only (DB) |
| `design_knowledge` | **Partial, name mismatch** | the app offers `engineering_knowledge` (code: `KnowledgeList.tsx:12`, `SaveToVaultButton.tsx:11`; ids 13, 14, DB); the vocabulary decision is recorded in `vision.md`'s decisions log (`bb43c9a`); Section 5's table and the architecture doc stay unchanged |
| `design_pattern` | **Done** | ids 1–5, 7, 18 (DB) |
| `failure` | **Not offered in the UI in v1** | code: the `ENTRY_TYPES` list in `SaveToVaultButton.tsx` has six types and no `failure` (your findstr); the column is a free string, so the API would accept it |
| `research_finding` | **Partial** | only id 19, test data (DB); the Sprint 6 report's "Research Note" entry is not in the Vault (unexplained) |
| `preference` | **Partial** | offered in the UI (code: `KnowledgeList.tsx:13`, `SaveToVaultButton.tsx:12`); none saved or used (DB); in v1 it works only inside the project where it was saved (E1 note) |
| Phase 2: semantic retrieval | **Deferred** | recency instead (Sprint 8) |
| Learn from every completed project | **Deferred (E1)** | needs cross-project retrieval and a "completed" status |

**Type vocabulary (decided):** the UI offers six entry types: `decision`, `lesson_learned`, `design_pattern`, `research_finding`, `engineering_knowledge`, `preference` (`SaveToVaultButton.tsx`, your findstr). `failure` is not offered in v1. The vocabulary decision is recorded in `vision.md`'s decisions log (`bb43c9a`); Section 5's table and the architecture doc stay unchanged (the architecture doc is not under `docs/`); no code change.

## 4. Departments (§3, §8), under E2 and E3

| Department | Proposed | Evidence |
|---|---|---|
| Design Engineering | **Partial** | capability through the guidance output (reasoning, calculations, materials); numeric outputs are not traceable (Z1) |
| Manufacturing Engineering | **Partial** | `manufacturing_suggestions` and `material_suggestions` exist; `vision.md` line 54 lists tolerances and cost estimates under Manufacturing Engineering (your findstr, repo copy) and the structured output contract has neither; numeric outputs are not traceable (Z1) |
| Project Management | **Partial** | projects and conversations; no status lifecycle; served in v1 by Vault entries and projects (E2) |
| Research | **Partial** | served in v1 by Vault entries (E2); `research_finding` has only test data (id 19, DB) |
| CAD, Reverse Engineering, Simulation | **Deferred** | future modules (E2); none built |
| Business Development | **Deferred (E3)** | none |

**`vision.md` note for E2 (recorded in the decisions log, commit `bb43c9a`):** "In v1, Design and Manufacturing are capabilities of the reasoning layer, not separate modules. CAD, Simulation and Reverse Engineering stay future modules; Research and Project Management are served in v1 by Vault entries and projects; Business Development is deferred; the departments/ placeholders stay."

## 5. Testable exit criteria (from the R3 and R4 success tests)

| ID | Test | Today |
|---|---|---|
| X1 | Decision in the same project: save a decision with a number, open a new conversation, ask a question that depends on it, compare before and after | **PASSED**: Sprint 8 P7 numeric 0/3 → 3/3; the UI conversation used 35 MPa (30.8 mm); Sprint 9 V10 at medium again 0/3 baseline, 3/3 retrieval |
| X2 | Preference in the same project: save a `preference` entry, new conversation, the answer reflects it, 3 runs before and after | **NOT RUN**: retrieval treats all types alike (Sprint 8 design), so it should work, unproven |
| X3 | Cross-project: record in project A, ask in project B | **NOT MET by design**; outside v1 under E1 |
| Y1 | Multi-day continuity: one real project, chats on 3 separate days with servers restarted between; earlier conversations reopen complete and the Vault still reaches the reasoning | **PARTIAL**: Sprint 4 reopened 24 conversations back to August; no single-project multi-day trial (plan below) |
| Y2 | Find an entry saved at least a week earlier within 30 seconds, by filter (relaxed for v1; keyword search is post-v1 unless real use shows entries hard to find, which affects post-v1 timing only) | **PARTIAL**: the `entry_type` filter works (Sprint 6); the timed find has not been run |
| Y3 | Save an analysis, retrieve it by id without the conversation | **NOT MET**: the table and endpoints do not exist (per memory) |
| Y4 | A failed AI call keeps your message and says so plainly | **MET on forced failures, with caveats** (Sprint 9 V3 and V4): V3 left the user message stored with no assistant row; V4 showed the message and a plain 502 message with no Claude bubble. V5 run 1's natural 502 (conversation 33): the screenshot you sent during V5, which is not in the closure report, shows the user message kept, no Claude bubble and the plain 502 message ("The model used its whole output budget (10,240 tokens, including its thinking)…"). Caveats: the error is plain text (a cosmetic backlog item); the typed input clears after a failed send and a manual retry duplicates the user row, and **these last two are accepted for v1** |
| Y5 | Delete a wrong entry (E4): it disappears from the list and from retrieval context | **NOT MET**: no delete endpoint; ids 15 and 20 are waiting to be deleted |
| Y6 *(proposed, new)* | The first 10 real design requests, in a project other than 1 or 7 (project 8 or a new project), each with a trusted or not trusted mark; fewer than 2 errors (a 502 or no answer); the not-trusted count reported (3 or more opens a discussion, a proposal you may change) | **NOT RUN**: this is the registered check of the provisional 10,240 cap and the medium effort setting |
| Z1 *(proposed, new)* | For a fixed set of engineering prompts, every safety-critical numeric result (for example a buckling FOS) states its inputs, method and material-property source so it can be reproduced independently | **NOT MET**: in Sprint 9 none reproduces from its stated inputs alone (two reproduce only with unstated textbook constants); the frozen item 1 line is a ready template |

**Y1 trial plan (yours):** use a **new** project (not 1, 7 or 8; project 8 stays your verified-empty control). Save only real decisions, since there is no delete yet. Three separate days, servers restarted between. The same period supplies the Y6 tally and part of Y4. A project that accumulates saved decisions runs with retrieval context, unlike project 8, so record which applies for each request.

## 6. What the code contains (per memory)

Five tables: `users`, `projects`, `conversations`, `messages`, `knowledge_entries`. `user_preferences` and `engineering_analyses` are not built. The database is `backend\engineerai.db`, gitignored; the Vault holds 20 entries (DB). Retrieval is project-scoped, five most recent entries, and skips JSON-shaped bodies (Sprint 8 report). The code was read in an earlier chat, not in this one.

## 7. §9 "Build now" list, the natural v1 anchor

Chat reasoning endpoint, projects, conversations: **Done**. Knowledge Vault v1 (storage and tag retrieval, then embeddings): **Partial** (no tag retrieval). User preferences: **Not built**. Single-user auth: **Done**. FastAPI + Next.js native on SQLite: **Done**.

## 8. Decisions recorded, and what is still open

**Decisions (yours):**
1. **E1–E4: yes** (above; E2 narrowed and extended).
2. **Preferences** stay as Vault entries, with no `user_preferences` table in v1; `engineering_analyses` and Y3 are post-v1.
3. **Type vocabulary:** the UI offers six types and `failure` is not offered in v1; the vocabulary decision is recorded in `vision.md`'s decisions log (`bb43c9a`); Section 5's table and the architecture doc stay unchanged (the architecture doc is not under `docs/`); no code change; `entry_type` validation is a future item.
4. **Vault delete and X2:** X2 runs after delete ships; delete ids 15 and 20, keep 16–18 (the eval scripts depend on them).
5. **Database:** v1 on SQLite; the PostgreSQL and Docker migration is post-v1, on a trigger (embeddings, deployment, or a second user). No decision to migrate has been made.
6. **Z1** is not a v1 criterion; revisit after the first-10 tally.
7. **Y1 and Y6:** the plan in §5; Y6 is the registered check of the provisional 10,240 cap and the medium setting.
8. **Where the document lives:** the project files, copied to `docs/` once approved.
9. **v1 polish:** a logo, last (§10).
10. **v1 closes when** the required criteria in §9 are met; Y2 is relaxed to filter-only; Y4's two caveats (the typed input clears after a failed send; a manual retry duplicates the user row) are accepted for v1.

**Next, after this document (not started until the Project Lead approves its plan):** the Vault delete sprint (Y5): hard delete with a confirm step, user-scoped, no edit; copy the SQLite file first; ids 15 and 20 first; keep 16–18 while the eval scripts exist.

**Still open:**
- This document is the Project Lead's approved final Definition of Done; it replaces the older drafts in the project files.
- Approve the Vault delete sprint plan (drafted after this document).

## 9. v1 closes when

v1 closes when every **required** criterion below is met. The roadmap tables (§1–§4) describe state; they do not decide closure.

| Criterion | Status in v1 | Today |
|---|---|---|
| X1 same-project decision | **Required** | **MET** (Sprint 8; Sprint 9 V10 at medium) |
| X2 preference in the same project | **Required** | NOT RUN; runs after Vault delete ships (§8) |
| Y1 multi-day continuity | **Required** | PARTIAL; trial plan in §5 |
| Y2 find an entry by filter (relaxed for v1) | **Required** | PARTIAL: the filter works (Sprint 6); the timed find has not been run |
| Y4 a failed AI call keeps your message and says so plainly | **Required** | **MET on forced failures**; the two caveats named in §5 are accepted for v1 |
| Y5 Vault delete | **Required** | NOT MET: no delete endpoint; the Vault delete sprint is next |
| Y6 first 10 real design requests | **Required** | NOT RUN |
| X3 cross-project | Not required | outside v1 under E1 |
| Y3 analyses survive the chat | Not required | post-v1 (`engineering_analyses` not built) |
| Z1 reproducible numeric answers | Not required | revisit after the first-10 tally |
| Logo | **Not an exit criterion** | polish, last (§10) |

Order implied by your decisions: Y5 before X2 (X2 runs after delete ships); the Y1 and Y6 evidence comes from the same period of real use.

**Y6 is met when** 10 real design requests are marked trusted or not trusted, fewer than 2 are errors, and, if 3 or more are not trusted, the Project Lead has recorded what he decided after the discussion.

**v1 closure does not establish that numeric answers are correct or reproducible; Z1 stays outside v1.**

## 10. v1 polish: logo, last; not an exit criterion for engineering correctness

**Decision (yours):** a logo is the last item of v1, as polish. It is **not** an exit criterion for engineering correctness.

**Scope:**
- One simple SVG mark, used as the favicon and in the page header, done in one session.
- Picked from at most three rough sketches.
- It must read at 16×16 and on light and dark backgrounds.

**Post-v1** (unless a second user or a commercial move appears): a wordmark, a colour system, and a name check.

**Sequencing:** no work starts until the other v1 items are done. If the logo has not happened when the others are done, v1 closes without it and the logo moves to the next version.
