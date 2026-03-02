# CLAUDE.md — Backend

## Running the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Recommended (enables auto-reload):
uvicorn backend.main:app --reload --port 8000

# Alternative (no auto-reload):
python main.py
```

Interactive API docs: `http://localhost:8000/docs`

## File Structure

```
backend/
├── main.py           # Everything: app, models, DB, all endpoints
├── requirements.txt
└── venv/             # Local virtualenv (not committed)
```

The entire backend is a single file (`main.py`). No routers, no separate modules, no ORM — raw `sqlite3` calls only (SQLAlchemy is listed in requirements but unused at runtime).

## Project Skills

Detailed reference has been extracted into skills in `.claude/skills/`:

- **`lifetime-backend-schema`** — SQLite table definitions, Pydantic models, DB_PATH gotcha, dependencies
- **`lifetime-backend-api`** — All endpoint contracts, calendar data building, week note upsert, voice transcription flow
- **`lifetime-backend-best-practices`** — FastAPI patterns, SQLite connection handling, Pydantic validation, Python conventions
