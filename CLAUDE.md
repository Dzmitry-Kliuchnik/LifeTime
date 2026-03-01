# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Lifetime Calendar** — a full-stack app that visualizes a user's entire life as a grid of weeks. Built as a monorepo:

- `backend/` — FastAPI service, SQLite persistence (`backend/main.py` is the sole entrypoint)
- `frontend/` — Vue 3 + Vite SPA (`frontend/src/`)

## Development Commands

### Quick Start
```bash
./start.sh        # Linux/macOS — starts both servers
start.bat         # Windows — starts both servers
```

### Backend (manual)
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Frontend (manual)
```bash
cd frontend
npm install
npm run dev       # dev server on :5173
npm run build     # production build to dist/
npm run preview   # preview production build
```

**URLs:** Frontend `http://localhost:5173` | Backend `http://localhost:8000` | Swagger `http://localhost:8000/docs`

## Architecture

### Data Flow
1. `App.vue` calls `GET /api/user` on mount → shows `UserSettings` if no user, else `LifetimeCalendar`
2. `LifetimeCalendar.vue` calls `GET /api/calendar` → renders the week grid
3. Clicking a week opens a modal → `POST /api/week-note` saves notes
4. Optional voice notes → `POST /api/week-note/voice` (transcribes via OpenAI Whisper, requires `OPENAI_API_KEY`)

### Backend (`backend/main.py`)
- Single file — all endpoints, models, and DB logic live here
- **DB**: SQLite at `lifetime_calendar.db` (path relative to CWD, so run from `backend/` or use `uvicorn backend.main:app` from root)
- **Tables**: `user_data` (birthdate, life_expectancy), `week_notes` (week_number, year, note, is_lived)
- **Week identity**: keyed by `(year, week_of_year)` as `"year-week_of_year"` string — **not** the sequential week number
- **Single-user assumption**: `POST /api/user` deletes all rows and inserts fresh
- Calendar math: iterates forward from birthdate in 7-day steps; lived weeks = `(now - birthdate).days // 7`
- Schema auto-created by `init_db()` on import; no migrations

### Frontend (`frontend/src/`)
- **`App.vue`** — shell: theme management (dark/light via `data-theme` on `<html>`, persisted to localStorage), routing between views
- **`components/LifetimeCalendar.vue`** — main calendar grid; consumes `calendarData.weeks`; handles week modal with text + voice notes
- **`components/UserSettings.vue`** — birthdate and life expectancy form; emits `user-saved`
- **`assets/design-system.css`** — CSS custom properties for colors, spacing, typography, shadows; imported globally
- **`assets/base.css`** / **`assets/main.css`** — base resets and global styles
- `@` alias maps to `frontend/src/`

### API Base URL
Hardcoded as `const API_BASE = 'http://localhost:8000'` in **all three** Vue files (`App.vue`, `UserSettings.vue`, `LifetimeCalendar.vue`). Must be updated consistently in all three if the port changes.

## Key Conventions

- **Week fields**: each week object from the API has `week_number` (sequential 1–N), `year`, `week_of_year` (ISO), `date` (ISO string), `is_lived`, `is_current`, `note`. Notes lookup uses `week_of_year` not `week_number`.
- **CSS**: component-scoped styles with `<style scoped>`; shared design tokens in `design-system.css` (CSS variables)
- **Responsive breakpoints**: 768px (tablet), 480px (mobile)
- **Voice transcription**: falls back to a mock string when `OPENAI_API_KEY` is not set
- Node.js requirement: `^20.19.0 || >=22.12.0` (see `frontend/package.json`)

## When Modifying Week Structure

If you add/rename a field in the `/api/calendar` response:
1. Update the `week_data` dict in `get_calendar_data()` in `backend/main.py`
2. Update usage in `frontend/src/components/LifetimeCalendar.vue`

## Best Practices

### API Design
- Use consistent HTTP status codes: `200` for reads, `201` for resource creation, `204` for deletes, `422` for validation errors (FastAPI does this automatically for Pydantic failures).
- Keep request/response shapes stable — the frontend parses week objects by field name. Additive changes (new fields) are safe; renaming or removing fields requires updating both sides atomically.
- All API inputs are validated by Pydantic before reaching handler logic. Do not add redundant manual type checks inside endpoint functions.

### Security
- The backend's CORS policy (`allow_origins=["*"]`) is intentionally permissive for local development. Before exposing the app on a network, restrict `allow_origins` to the actual frontend origin.
- Never interpolate user input directly into SQL strings. All DB calls in this codebase correctly use parameterized queries (`?` placeholders) — maintain that pattern without exception.
- `OPENAI_API_KEY` must be supplied via environment variable, never committed to the repository.

### Error Handling
- Backend errors surface as `HTTPException` with a `detail` string. The frontend currently shows these via `console.error` or `alert`. For new features, match this pattern so errors are user-visible.
- Frontend Axios calls should always have a `catch` block that sets an error ref, never silently swallows exceptions.

### State Consistency
- After a successful `POST /api/week-note`, the frontend patches `calendarData.weeks[idx].note` in place rather than refetching the full calendar. Follow this pattern for any future mutations — patch local state optimistically, refetch only on full reloads.
- The single-user model means `POST /api/user` is destructive (deletes all rows). If multi-user support is ever needed, this endpoint and the DB schema both need coordinated changes.

### Environment Variables (Frontend)
- `API_BASE` is currently a hardcoded string literal. When adding any new environment-specific value, use Vite's `import.meta.env.VITE_*` mechanism instead of adding more hardcoded constants. Create a `.env` file with `VITE_API_BASE=http://localhost:8000` and a `.env.example` for documentation.
