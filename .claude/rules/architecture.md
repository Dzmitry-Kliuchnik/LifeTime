---
description: Project architecture — backend, frontend, and how they connect
---

# Architecture

Two completely separate servers — no monorepo tooling or shared code:

- **Backend** (`backend/`): FastAPI + SQLite, runs on `http://127.0.0.1:8000`
- **Frontend** (`frontend/`): Vue 3 + Vite SPA, runs on `http://localhost:5173`

The frontend calls the backend via axios with `API_BASE = 'http://127.0.0.1:8000'` hardcoded in `frontend/src/App.vue`. The SQLite database file (`lifetime_calendar.db`) lives in `backend/` at runtime.

## Backend (`backend/main.py`)

Single-file FastAPI app. No ORM usage at runtime — all DB access is raw `sqlite3`. SQLAlchemy is listed in requirements but not actively used. Key models: `UserData` and `WeekNote`. The calendar computation (week grid generation) happens entirely in `GET /api/calendar`.

Optional voice-to-text: `POST /api/transcribe-voice` and `POST /api/week-note/voice` use OpenAI Whisper. Without `OPENAI_API_KEY` in the environment, they return a mock transcription.

## Frontend (`frontend/src/`)

- `App.vue` — root component; owns `userData` state, dark/light theme (via `data-theme` on `<html>`, stored in `localStorage`), and routing between settings and calendar views
- `components/LifetimeCalendar.vue` — main calendar grid; largest file (~40 KB), handles week click/modal/note saving/voice recording
- `components/UserSettings.vue` — birthdate and life expectancy form
- `utils/countdown.js` — pure helpers: `computeEndDate` and `formatCountdown`

Theme is CSS-variable based; toggled by setting `data-theme="dark"|"light"` on `document.documentElement`.
