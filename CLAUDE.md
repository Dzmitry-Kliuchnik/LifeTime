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

## Key Facts

- Voice transcription falls back to a mock string when `OPENAI_API_KEY` is not set
- Node.js requirement: `^20.19.0 || >=22.12.0` (see `frontend/package.json`)

## Project Skills

Detailed reference content has been extracted into project skills in `.claude/skills/`:

- **`lifetime-architecture`** — data flow, backend internals (DB, tables, calendar math), frontend file map, API base URL
- **`lifetime-week-conventions`** — week object fields, week identity key, procedure for modifying week structure, CSS conventions
- **`lifetime-best-practices`** — API design, security (CORS, SQL injection, secrets), error handling, frontend state consistency, env vars
