# EngineerAI — Sprint 1 Demo Walkthrough

*The authoritative, current record of how to bring EngineerAI up from nothing but a fresh clone. Written from what actually works, not from the original plan.*

---

## What Changed From the Original Plan

The original Sprint 1 plan assumed Docker Compose and PostgreSQL from the start. That changed during the hardware-adaptation review (`docs/vision.md` Major Decisions Log, 2026-08-09): the development machine's constraints made Docker impractical, so **SQLite is the current interim database**, with PostgreSQL + pgvector remaining the approved long-term target. Every step below reflects that — there is no Docker anywhere in this walkthrough.

Also: the original plan's Task 4 ("Database Connection Layer") doesn't appear as a separate step below — it was absorbed into Task 2's SQLite work and refined during Task 3, so there was never a separate implementation for it.

---

## Prerequisites

- **Python 3.11+**
- **Node.js LTS** and npm
- **Git**

**No Docker required.**

---

## 1. Clone

```powershell
git clone <your-repo-url> engineerai
cd engineerai
```

---

## 2. Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Apply migrations and seed the default user:

```powershell
alembic upgrade head
python -m app.db.seed
```

**Use `python -m app.db.seed`, not `python app\db\seed.py`.** The direct-path form fails with `ModuleNotFoundError: No module named 'app'` — this was found and documented during Task 6's real-machine verification, and it's the correct invocation from here on.

Start the server:

```powershell
uvicorn app.main:app --reload
```

Sanity check, from a second terminal:

```powershell
curl http://localhost:8000/api/health
```

Expect `{"status":"ok"}`.

---

## 3. Frontend Setup

From a new terminal, at the repo root:

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Visit `http://localhost:3000`.

---

## 4. The Full Walkthrough

1. The home page loads with the "EngineerAI" heading and a "View Projects" link.
2. Click it — you land on `/projects`.
3. Create a project (any title). It appears in the list immediately, no page reload.
4. Click into its chat. The URL becomes `/projects/{id}/chat`, and a conversation is created automatically — no separate "start conversation" step.
5. Type a message and send it.

**Expected today:** the send fails with a `502` — this is correct, not a bug. No Claude API key has been configured yet (see below). What matters here: **your message still appears in the transcript**, because Task 11 was deliberately built so the user's message is saved before the Claude call is attempted, not rolled back if that call fails. If you see your message on screen alongside a clear error for the missing reply, that's Sprint 1 working exactly as designed.

---

## 5. Known Outstanding Item

**No real Anthropic API key has been purchased or configured yet.** This is the one thing standing between "Sprint 1 code complete" and "Sprint 1 fully closed" — tracked since Task 7, and every downstream piece (Task 11's message round trip, Task 14's chat UI) has been built and verified right up to that exact point.

Once a key exists: set `CLAUDE_API_KEY` in `backend/.env`, restart the backend, and repeat Step 5 above. Expect a real Claude reply to appear in the transcript, completing the flow this document describes.

---

## 6. Additional Regression Checks

- `window.apiClient` should be accessible directly in the browser console (Task 13) — try `await apiClient.listProjects()`.
- `npm run build` (from `frontend/`) should complete with no errors.
- Direct backend checks still work independent of the browser: `Invoke-RestMethod http://localhost:8000/api/projects`, etc.
