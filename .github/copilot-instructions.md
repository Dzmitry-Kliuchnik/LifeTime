# Copilot Instructions for Lifetime Calendar

Purpose: Enable AI coding agents to be productive immediately in this repo by capturing the architecture, workflows, conventions, and integration points used here.

## Architecture at a Glance
- Monorepo with two apps:
  - `backend/` — FastAPI service exposing JSON endpoints and persisting to SQLite.
  - `frontend/` — Vue 3 app (Vite) calling the backend via Axios.
- Data flow:
  1. Frontend calls `GET /api/user` to determine whether to show settings.
  2. Frontend calls `GET /api/calendar` to render the week grid.
  3. Week interactions call `POST /api/week-note` to save notes.
  4. User profile is saved via `POST /api/user`.
- Why this structure: keep backend stateless and simple; single SQLite file for persistence; Vue handles UI/UX with a compact, responsive week grid.

## Backend (FastAPI + SQLite)
- Main entrypoint: `backend/main.py` (also booted by `uvicorn backend.main:app`).
- DB: SQLite file `backend/lifetime_calendar.db` is created/read by `main.py` (note: `DB_PATH = "lifetime_calendar.db"` — the DB file sits under `backend/`).
- Models: lightweight Pydantic classes `UserData`, `WeekNote`, `CalendarResponse` in `main.py`.
- Endpoints:
  - `GET /api/user` → returns `{ birthdate, life_expectancy } | null`.
  - `POST /api/user` → replaces any existing row, assuming single-user mode.
  - `GET /api/calendar` → computes `weeks` client needs; each week has `week_number`, `year`, `week_of_year`, `date`, `is_lived`, `is_current`, `note`.
  - `POST /api/week-note` → upserts a note for `(year, week_number)`.
- Calendar math: iterates forward from `birthdate` in 7-day steps; ISO week via `datetime.isocalendar()[1]`. Lived week count is `(now - birthdate).days // 7`.
- CORS: permissive (`*`) to simplify local dev.

## Frontend (Vue 3 + Vite)
- App shell: `frontend/src/App.vue` toggles between `UserSettings` and `LifetimeCalendar` based on `GET /api/user`.
- Key component: `frontend/src/components/LifetimeCalendar.vue` renders the grid and week modal.
  - Expects `calendarData.weeks` from the backend.
  - Uses `week.week_of_year` to mark current and lived weeks; now also adds `year-start` on `week.week_of_year === 1`.
- Settings form: `frontend/src/components/UserSettings.vue` posts to `/api/user`.
- Build tooling: Vite with `@vitejs/plugin-vue` and `vite-plugin-vue-devtools`; see `frontend/vite.config.js`.

## Dev Workflows
- Quick start (Linux/macOS): `./start.sh` (starts both servers with auto-installs).
- Manual start:
  - Backend:
    - `cd backend`
    - `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
    - `pip install -r requirements.txt`
    - `uvicorn backend.main:app --reload --port 8000`
  - Frontend:
    - `cd frontend`
    - `npm install`
    - `npm run dev`
- URLs: Frontend `http://localhost:5173`, Backend `http://localhost:8000`, API docs `http://localhost:8000/docs`.

## Conventions & Patterns
- Single-user assumption: `/api/user` deletes and recreates `user_data` row on each save.
- Week identity: notes are keyed by `(year, week_number)` and looked up with `week_key = f"{year}-{week_of_year}"` when generating the calendar.
- Calendar weeks: 52 per year for totals, ISO week-of-year for labeling; lived/current computed on the fly.
- Styling: minimal CSS-in-component; responsive grid changes columns at 768px and 480px breakpoints.
- API base URL: hardcoded to `http://localhost:8000` in frontend (`App.vue`, `UserSettings.vue`, `LifetimeCalendar.vue`). Change in all three if port/host changes.

## Integration Points
- Axios calls in:
  - `frontend/src/App.vue` → `GET /api/user`
  - `frontend/src/components/UserSettings.vue` → `POST /api/user`
  - `frontend/src/components/LifetimeCalendar.vue` → `GET /api/calendar`, `POST /api/week-note`
- DB schema created in `init_db()` on import; no migrations.

## Gotchas & Tips
- Windows dev: prefer starting backend with `uvicorn backend.main:app --reload --port 8000` instead of `python main.py` for autoreload.
- If you change week structure fields, update both backend serialization and frontend component usage (`LifetimeCalendar.vue`).
- CORS is open for dev; tighten before production.

## Examples
- Add a new field to `weeks` (e.g., `quarter`):
  - Backend: compute in `/api/calendar` loop and include in `week_data` dict.
  - Frontend: render or style based on `week.quarter` in `LifetimeCalendar.vue`.
- Change API base: search for `API_BASE = 'http://localhost:8000'` in `frontend/src/*.vue` and update consistently.
