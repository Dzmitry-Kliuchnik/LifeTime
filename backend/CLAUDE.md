# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

**DB_PATH gotcha**: `DB_PATH = "lifetime_calendar.db"` is relative to CWD. When running via `uvicorn backend.main:app` from the repo root, the DB file is created at the root as `lifetime_calendar.db`. When running `python main.py` from inside `backend/`, it's created at `backend/lifetime_calendar.db`. Use one launch method consistently.

## File Structure

```
backend/
├── main.py           # Everything: app, models, DB, all endpoints
├── requirements.txt
└── venv/             # Local virtualenv (not committed)
```

The entire backend is a single file (`main.py`). There are no routers, no separate modules, no ORM layer — raw `sqlite3` calls only (SQLAlchemy is listed in requirements but unused at runtime).

## Database

**Engine**: SQLite via the stdlib `sqlite3` module.
**Schema** (auto-created in `init_db()` at import time — no migration step):

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

**Critical**: `week_notes.week_number` stores the **ISO week-of-year** (`datetime.isocalendar()[1]`), not the sequential life-week number (1 to `life_expectancy * 52`). The lookup key used everywhere is `f"{year}-{week_of_year}"`.

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
    weeks: List[dict]        # list of week_data dicts (see below)

class VoiceTranscriptionResponse(BaseModel):
    transcription: str
    success: bool
    error: Optional[str] = None
```

## API Endpoints

### `GET /api/user`
Returns `{ birthdate, life_expectancy }` or `null` (not 404) if no user row exists.
Fetches the most recently created row via `ORDER BY created_at DESC LIMIT 1`.

### `POST /api/user`
Body: `UserData`.
**Deletes all rows** from `user_data` then inserts fresh — enforces single-user mode.

### `GET /api/calendar`
Calls `get_user_data()` internally (returns 404 if no user).
Builds the week list by iterating from `birthdate` in 7-day steps:

```python
# For each week:
week_data = {
    "week_number": week_num,          # sequential 1 to total_weeks
    "year": current_week_date.year,
    "week_of_year": current_week_date.isocalendar()[1],  # ISO week
    "date": current_week_date.isoformat(),
    "is_lived": week_num <= lived_weeks,
    "is_current": week_num == current_week,
    "note": notes_dict.get(week_key, {}).get("note", ""),
}
```

Notes lookup: `week_key = f"{year}-{week_of_year}"` — matches how notes are stored.

Calculated fields:
- `total_weeks = life_expectancy * 52`
- `lived_weeks = int((now - birthdate).days / 7)`
- `current_week = lived_weeks + 1`

### `POST /api/week-note`
Body: `WeekNote`.
Upsert: checks for existing row by `(week_number, year)` — where `week_number` is ISO week-of-year. Updates if exists, inserts if not.

### `POST /api/transcribe-voice`
Multipart form with `audio` file.
Saves file to a temp dir (`tempfile.mkdtemp()` at startup), calls `transcribe_audio_with_whisper()`, cleans up.
Returns `VoiceTranscriptionResponse`.

**Without `OPENAI_API_KEY`**: returns a `[Mock Transcription]` placeholder string instead of calling OpenAI. No exception raised.

### `POST /api/week-note/voice`
Multipart form fields: `week_number`, `year`, `is_lived`, `existing_note` (optional), `audio` file.
Flow:
1. Calls `transcribe_voice()` internally to get transcription
2. Appends transcription to `existing_note` as `\n\n[Voice Note]: {transcribed_text}`
3. Saves the combined note via `save_week_note()`
4. Returns `{ message, transcription, combined_note }`

## Voice Transcription

`transcribe_audio_with_whisper(audio_file_path)` in `main.py:86`:
- Requires `openai` package (already in `requirements.txt`)
- Reads `OPENAI_API_KEY` from environment
- Uses `openai.OpenAI(api_key=...).audio.transcriptions.create(model="whisper-1")`
- Falls back to mock string when `OPENAI_API_KEY` is absent — no exception propagated

To enable real transcription: `export OPENAI_API_KEY=sk-...` before starting the server.

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.104.1 | Web framework |
| uvicorn | 0.24.0 | ASGI server |
| python-dateutil | 2.8.2 | (available but calendar math uses stdlib `datetime`) |
| sqlalchemy | 2.0.23 | Listed but not imported at runtime |
| python-multipart | 0.0.6 | Required by FastAPI for `UploadFile` / `Form` |
| openai | 1.109.1 | Whisper transcription |
| pydub | 0.25.1 | Listed but not called in current code |

## CORS

Configured with `allow_origins=["*"]` — permissive for local dev. Tighten before any production deployment.

## Extending the Calendar Week Object

To add a field to the week data returned by `GET /api/calendar`, compute it inside the loop in `get_calendar_data()` (`main.py:224`) and add it to `week_data`. The frontend reads this dict directly in `LifetimeCalendar.vue`.

## Best Practices

### FastAPI

**Use `response_model` on every endpoint.**
Currently endpoints return raw dicts or `None`. Declaring `response_model=` gives you automatic output validation, strips unexpected fields, and makes the Swagger UI accurate:
```python
@app.get("/api/user", response_model=Optional[UserData])
@app.get("/api/calendar", response_model=CalendarResponse)
@app.post("/api/week-note", status_code=201)
```

**Use the lifespan context manager instead of module-level side effects.**
`init_db()` is currently called at import time. The FastAPI-idiomatic way is a lifespan handler, which makes startup/shutdown explicit and testable:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

**Run synchronous DB calls in a thread pool inside async endpoints.**
All endpoint functions are `async def`, but `sqlite3` is synchronous. Blocking the event loop on DB I/O is safe at this scale but will cause latency issues under concurrent load. Use `asyncio.to_thread()` (Python 3.9+) to offload blocking calls:
```python
result = await asyncio.to_thread(fetch_user_from_db)
```

**Use `APIRouter` when splitting endpoints across files.**
If `main.py` grows beyond one concern, group related routes in separate routers and include them in the app:
```python
router = APIRouter(prefix="/api", tags=["calendar"])
@router.get("/calendar")
...
app.include_router(router)
```

**Raise `HTTPException` with specific status codes, not 500 for everything.**
The current catch-all `except Exception as e: raise HTTPException(500, ...)` hides the real error type. Distinguish between:
- `404` — resource not found (already used for missing user)
- `422` — invalid input (Pydantic handles this automatically)
- `500` — unexpected server fault

**Avoid calling one endpoint handler from another.**
`get_calendar_data()` calls `await get_user_data()` and `save_week_note_with_voice()` calls `await transcribe_voice()` directly. This creates tight coupling and bypasses middleware, validation, and logging. Extract shared logic into plain `async def` helper functions instead.

### SQLite

**Use context managers for every connection.**
The current pattern opens a connection, commits manually, and closes in a `finally`-less block — a crash between `commit()` and `close()` leaks the connection. Use `with` instead:
```python
with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute(...)
    # conn.commit() is called automatically on __exit__ if no exception
```

**Enable WAL mode for better read concurrency.**
Add this once after opening the connection (or in `init_db()`):
```python
conn.execute("PRAGMA journal_mode=WAL")
```
WAL allows concurrent readers while a writer is active, which matters when the dev server hot-reloads and simultaneous requests hit the DB.

**Use `sqlite3.Row` as the row factory for dict-like access.**
Instead of accessing columns by index (`result[0]`, `result[1]`), set:
```python
conn.row_factory = sqlite3.Row
# then: result["birthdate"] instead of result[0]
```
This makes column access self-documenting and survives column reordering.

**Add a UNIQUE constraint on `week_notes(year, week_number)`.**
The upsert logic checks for existence then inserts/updates — a classic TOCTOU race. A `UNIQUE` constraint plus `INSERT OR REPLACE` (or `ON CONFLICT DO UPDATE`) is atomic:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_week_notes_key
    ON week_notes(year, week_number);
```

**Use `pathlib.Path` for `DB_PATH`.**
String paths break when the working directory changes. Anchor the DB path relative to `main.py`:
```python
from pathlib import Path
DB_PATH = Path(__file__).parent / "lifetime_calendar.db"
```
This makes `python main.py` and `uvicorn backend.main:app` both resolve to the same file regardless of CWD.

### Pydantic

**Add field-level constraints with `Field()`.**
Current models accept any string as `birthdate` and any integer as `life_expectancy`. Add validation at the model boundary:
```python
from pydantic import Field, field_validator

class UserData(BaseModel):
    birthdate: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    life_expectancy: int = Field(default=80, ge=1, le=130)

    @field_validator("birthdate")
    @classmethod
    def birthdate_not_future(cls, v):
        if datetime.fromisoformat(v).date() > datetime.now().date():
            raise ValueError("Birthdate cannot be in the future")
        return v
```

**Type `weeks` in `CalendarResponse` with a proper model.**
`weeks: List[dict]` disables output validation for the most important response field. Create a `WeekData` model so Pydantic can validate and document it:
```python
class WeekData(BaseModel):
    week_number: int
    year: int
    week_of_year: int
    date: str
    is_lived: bool
    is_current: bool
    note: str

class CalendarResponse(BaseModel):
    total_weeks: int
    lived_weeks: int
    current_week: int
    weeks: List[WeekData]
```

**Use `model_config` instead of class `Config` (Pydantic v2).**
The project uses Pydantic v2 (installed via FastAPI 0.104+). Use the v2 API:
```python
class UserData(BaseModel):
    model_config = {"str_strip_whitespace": True}
    birthdate: str
```

### Python

**Add type annotations to all functions.**
Currently none of the helper functions or endpoint handlers have return type annotations. This makes refactoring error-prone. At minimum annotate return types:
```python
def init_db() -> None: ...
async def get_user_data() -> dict | None: ...
def transcribe_audio_with_whisper(audio_file_path: str) -> str: ...
```

**Clean up the temp audio directory on shutdown.**
`AUDIO_UPLOAD_DIR = tempfile.mkdtemp()` creates a new directory on every process start and never removes it. Register cleanup with `atexit` or the lifespan handler:
```python
import atexit, shutil
atexit.register(shutil.rmtree, AUDIO_UPLOAD_DIR, ignore_errors=True)
```

**Use `logging` instead of `print()`.**
`print(f"Received request to save voice note for week...")` in `save_week_note_with_voice` bypasses log level filtering and structured log aggregation. Replace with:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Saving voice note for week %d, year %d", week_number, year)
```
