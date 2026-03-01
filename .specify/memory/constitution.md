<!--
SYNC IMPACT REPORT
==================
Version change: (template) → 1.0.0
Modified principles: N/A (initial ratification from template)
Added sections:
  - Core Principles (5 principles defined)
  - Technology Stack
  - Development Workflow
  - Governance
Removed sections: N/A
Templates checked:
  - .specify/templates/plan-template.md          ✅ no changes required
  - .specify/templates/spec-template.md          ✅ no changes required
  - .specify/templates/tasks-template.md         ✅ no changes required
  - .specify/templates/agent-file-template.md    ✅ no changes required
  - .specify/templates/constitution-template.md  ✅ source template unchanged
Follow-up TODOs: none — all placeholders resolved.
-->

# Lifetime Calendar Constitution

## Core Principles

### I. API Contract Stability

The `/api/calendar` response shape is the public contract between backend and frontend.
Additive changes (new fields) are safe without coordination. Renaming or removing
fields MUST be applied atomically to both `backend/main.py` and
`frontend/src/components/LifetimeCalendar.vue` in the same commit.
All API inputs MUST be validated via Pydantic models; redundant manual type-checks
inside handler functions are prohibited.
HTTP status codes MUST follow the project convention: `200` reads, `201` creates,
`204` deletes, `422` Pydantic validation failures.

**Rationale**: A single-file backend and a tightly coupled SPA mean an inconsistency
between the two halves produces silent data corruption that is hard to diagnose.

### II. Secure-by-Default

Every SQL statement MUST use parameterized queries (`?` placeholders). Interpolating
user input directly into SQL strings is prohibited without exception.
Secrets (e.g., `OPENAI_API_KEY`) MUST be supplied exclusively via environment
variables and MUST NOT be committed to the repository.
The CORS policy (`allow_origins=["*"]`) is acceptable for localhost-only development
only. Before any network exposure the policy MUST be restricted to the actual
frontend origin.
New environment-specific values MUST use Vite's `import.meta.env.VITE_*` mechanism
with a matching `.env.example` entry; additional hardcoded constants are prohibited.

**Rationale**: The app stores personally meaningful life data. Injection vulnerabilities
and leaked credentials are unacceptable regardless of scope.

### III. Simplicity First (NON-NEGOTIABLE)

The backend MUST remain a single-file entrypoint (`backend/main.py`). All endpoints,
models, and DB logic live there unless a new file is explicitly justified.
No feature, abstraction, helper, or utility MUST be added for hypothetical future
requirements. Three similar lines of code are preferable to a premature abstraction.
Complexity additions MUST be recorded in the plan's Complexity Tracking table with a
rejected simpler alternative documented.

**Rationale**: The single-user, single-file architecture is a deliberate choice for
maintainability and auditability. Scope creep toward a multi-file service is a
constitution violation unless explicitly approved via amendment.

### IV. Transparent Error Handling

Backend errors MUST surface as `HTTPException` with a human-readable `detail` string.
Frontend Axios calls MUST have a `catch` block that sets an error ref or triggers a
user-visible alert; silent exception swallowing is prohibited.
Voice transcription failures MUST degrade gracefully (mock string fallback when
`OPENAI_API_KEY` is absent).

**Rationale**: The app is operated by a single user who needs to know when something
has gone wrong, not a silent failure that leaves state ambiguous.

### V. Optimistic State Consistency

After a successful `POST /api/week-note`, the frontend MUST patch
`calendarData.weeks[idx].note` in place rather than refetching the full calendar.
Full refetches are permitted only on page/component mount or explicit user-initiated
reload.
`POST /api/user` is a destructive operation (deletes all rows). Any UI flow that
triggers it MUST present an explicit confirmation before submission.
Multi-user support is out of scope; any change that introduces per-user row
discrimination requires a constitution amendment and coordinated schema migration.

**Rationale**: Unnecessary network round-trips degrade the perceived performance of
a grid that can represent hundreds of weeks. Predictable local state reduces bugs.

## Technology Stack

| Layer | Technology | Version constraint |
|-------|------------|--------------------|
| Backend language | Python | 3.11+ |
| Backend framework | FastAPI + Uvicorn | latest stable |
| Backend DB | SQLite (file: `lifetime_calendar.db`) | bundled with Python |
| Backend ORM | None — raw `sqlite3` with parameterized queries | — |
| Optional AI | OpenAI Whisper via `openai` SDK | latest stable |
| Frontend framework | Vue 3 (Composition API) | 3.x |
| Frontend build tool | Vite | 5.x |
| Frontend HTTP client | Axios | latest stable |
| Frontend styles | CSS custom properties in `design-system.css` | — |
| Node.js | `^20.19.0 \|\| >=22.12.0` | per `package.json` engines |

API base URL is currently a hardcoded string `http://localhost:8000` in three Vue
files (`App.vue`, `UserSettings.vue`, `LifetimeCalendar.vue`). New code MUST use
`import.meta.env.VITE_API_BASE` instead; the hardcoded constant is legacy and
SHOULD be migrated incrementally.

## Development Workflow

- Backend runs via `uvicorn backend.main:app --reload --port 8000` from the repo root.
  Running from `backend/` also works but changes the relative DB path.
- Frontend dev server runs via `npm run dev` from `frontend/` on port 5173.
- Quick-start scripts: `./start.sh` (Linux/macOS), `start.bat` (Windows).
- Week identity is keyed by `"year-week_of_year"` string (ISO week), NOT by the
  sequential `week_number`. Any new feature involving week lookup MUST use this key.
- `init_db()` runs on module import; there is no migration framework. Schema changes
  MUST be backward-compatible or include a manual migration note in the PR description.
- Responsive breakpoints: 768 px (tablet), 480 px (mobile). New UI components MUST
  handle both breakpoints.

## Governance

This constitution supersedes all informal conventions. When this document and a
comment in the source code conflict, the constitution takes precedence.

**Amendment procedure**:
1. Propose the change via a PR that edits this file and the `CLAUDE.md` if affected.
2. Update `CONSTITUTION_VERSION` per semantic versioning:
   - MAJOR — principle removed, renamed, or redefined in a backward-incompatible way.
   - MINOR — new principle or section added, or material guidance expanded.
   - PATCH — clarification, wording, or typo fix.
3. Update `LAST_AMENDED_DATE` to the merge date.
4. Run `speckit.constitution` after merging to propagate changes to dependent templates.

**Compliance review**: Every PR touching `backend/main.py` or any file in
`frontend/src/` MUST verify adherence to Principles I–V before merge.
The plan template's "Constitution Check" gate enforces this for planned features.

**Runtime guidance**: See `CLAUDE.md` at the repository root for development commands,
architecture notes, and coding conventions that complement this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-02-28 | **Last Amended**: 2026-02-28
