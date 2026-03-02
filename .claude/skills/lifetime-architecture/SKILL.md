---
name: lifetime-architecture
description: Use when working on backend endpoints, frontend components, database schema, API integration, or understanding how data flows through the Lifetime Calendar app.
---

# Lifetime Calendar — Architecture Reference

## Data Flow

1. `App.vue` → `GET /api/user` on mount → shows `UserSettings` if no user, else `LifetimeCalendar`
2. `LifetimeCalendar.vue` → `GET /api/calendar` → renders the week grid
3. Clicking a week → modal → `POST /api/week-note` saves notes
4. Optional voice notes → `POST /api/week-note/voice` (transcribes via OpenAI Whisper, requires `OPENAI_API_KEY`)

## Backend (`backend/main.py`)

- **Single file** — all endpoints, models, and DB logic live here
- **DB**: SQLite at `lifetime_calendar.db` (path relative to CWD — run from `backend/` or use `uvicorn backend.main:app` from root)
- **Tables**:
  - `user_data`: birthdate, life_expectancy
  - `week_notes`: week_number, year, note, is_lived
- **Week identity**: keyed by `(year, week_of_year)` as `"year-week_of_year"` string — **not** the sequential week number
- **Single-user**: `POST /api/user` deletes all rows and inserts fresh
- **Calendar math**: iterates forward from birthdate in 7-day steps; lived weeks = `(now - birthdate).days // 7`
- **Schema**: auto-created by `init_db()` on import; no migrations

## Frontend (`frontend/src/`)

| File | Purpose |
|------|---------|
| `App.vue` | Shell: theme (dark/light via `data-theme` on `<html>`, persisted to localStorage), routing between views |
| `components/LifetimeCalendar.vue` | Main calendar grid; consumes `calendarData.weeks`; handles week modal with text + voice notes |
| `components/UserSettings.vue` | Birthdate and life expectancy form; emits `user-saved` |
| `assets/design-system.css` | CSS custom properties for colors, spacing, typography, shadows; imported globally |
| `assets/base.css` / `assets/main.css` | Base resets and global styles |

`@` alias maps to `frontend/src/`

## API Base URL

Hardcoded as `const API_BASE = 'http://localhost:8000'` in **all three** Vue files:
- `App.vue`
- `UserSettings.vue`
- `LifetimeCalendar.vue`

Must be updated consistently in **all three** if the port changes. Future env-specific values should use `import.meta.env.VITE_*` (Vite env mechanism).

## URLs

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:5173` |
| Backend | `http://localhost:8000` |
| Swagger docs | `http://localhost:8000/docs` |
