---
name: lifetime-backend-schema
description: Use when working with the database schema, Pydantic models, adding columns, writing queries, or understanding how user/week data is stored in the Lifetime Calendar backend.
---

# Lifetime Calendar — Backend Schema Reference

## SQLite Tables

Auto-created by `init_db()` at import time — no migration step.

```sql
CREATE TABLE IF NOT EXISTS user_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    birthdate TEXT NOT NULL,          -- ISO date string e.g. "1990-05-15"
    life_expectancy INTEGER DEFAULT 80,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS week_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number INTEGER NOT NULL,     -- ISO week-of-year (1–53), NOT sequential life week
    year INTEGER NOT NULL,
    note TEXT,
    is_lived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Critical:** `week_notes.week_number` stores the **ISO week-of-year** (`datetime.isocalendar()[1]`), not the sequential life-week number (1 to `life_expectancy * 52`). The lookup key everywhere is `f"{year}-{week_of_year}"`.

## Pydantic Models

```python
class UserData(BaseModel):
    birthdate: str           # ISO date string
    life_expectancy: int = 80

class WeekNote(BaseModel):
    week_number: int         # ISO week-of-year
    year: int
    note: Optional[str] = None
    is_lived: bool = False

class CalendarResponse(BaseModel):
    total_weeks: int
    lived_weeks: int
    current_week: int
    weeks: List[dict]        # list of week_data dicts (see lifetime-backend-api)

class VoiceTranscriptionResponse(BaseModel):
    transcription: str
    success: bool
    error: Optional[str] = None
```

## DB Path Gotcha

`DB_PATH = "lifetime_calendar.db"` is relative to CWD.
- `uvicorn backend.main:app` from repo root → DB created at root
- `python main.py` from inside `backend/` → DB created at `backend/lifetime_calendar.db`

Use one launch method consistently, or anchor with `pathlib`:
```python
DB_PATH = Path(__file__).parent / "lifetime_calendar.db"
```

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.104.1 | Web framework |
| uvicorn | 0.24.0 | ASGI server |
| python-dateutil | 2.8.2 | (available; calendar math uses stdlib `datetime`) |
| sqlalchemy | 2.0.23 | Listed but **not imported at runtime** |
| python-multipart | 0.0.6 | Required by FastAPI for `UploadFile` / `Form` |
| openai | 1.109.1 | Whisper transcription |
| pydub | 0.25.1 | Listed but **not called** in current code |
