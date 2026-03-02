---
name: lifetime-backend-best-practices
description: Use when writing or reviewing backend Python code in the Lifetime Calendar app — FastAPI patterns, SQLite connection handling, Pydantic validation, type annotations, and async practices.
---

# Lifetime Calendar — Backend Best Practices

## FastAPI

**Use `response_model` on every endpoint** — gives automatic output validation, strips unexpected fields, makes Swagger accurate:
```python
@app.get("/api/user", response_model=Optional[UserData])
@app.get("/api/calendar", response_model=CalendarResponse)
@app.post("/api/week-note", status_code=201)
```

**Use the lifespan context manager** instead of calling `init_db()` at module level:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

**Run synchronous DB calls in a thread pool** — `sqlite3` is blocking; endpoints are `async def`:
```python
result = await asyncio.to_thread(fetch_user_from_db)
```

**Raise `HTTPException` with specific status codes**, not 500 for everything. Distinguish `404` (not found), `422` (invalid input — Pydantic auto-handles), `500` (unexpected fault).

**Extract shared logic into plain helper functions** — avoid calling one endpoint handler from another (tight coupling, bypasses middleware and logging).

**Use `APIRouter`** when splitting endpoints across files:
```python
router = APIRouter(prefix="/api", tags=["calendar"])
app.include_router(router)
```

## SQLite

**Use context managers for every connection** — prevents leaked connections on crashes:
```python
with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute(...)
    # commit called automatically on __exit__
```

**Enable WAL mode** for better read concurrency (add once in `init_db()`):
```python
conn.execute("PRAGMA journal_mode=WAL")
```

**Use `sqlite3.Row` as the row factory** for dict-like column access:
```python
conn.row_factory = sqlite3.Row
# then: result["birthdate"] instead of result[0]
```

**Add a UNIQUE constraint** on `week_notes(year, week_number)` and use atomic upsert:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_week_notes_key
    ON week_notes(year, week_number);
```

**Anchor `DB_PATH` to `main.py`** using `pathlib` to avoid CWD-dependent behavior:
```python
DB_PATH = Path(__file__).parent / "lifetime_calendar.db"
```

## Pydantic

**Add field-level constraints with `Field()`**:
```python
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

**Type `weeks` in `CalendarResponse`** with a `WeekData` model instead of `List[dict]`:
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
    ...
    weeks: List[WeekData]
```

**Use `model_config` (Pydantic v2)** instead of inner `class Config`:
```python
class UserData(BaseModel):
    model_config = {"str_strip_whitespace": True}
```

## Python

**Add type annotations to all functions**:
```python
def init_db() -> None: ...
async def get_user_data() -> dict | None: ...
def transcribe_audio_with_whisper(audio_file_path: str) -> str: ...
```

**Clean up the temp audio directory on shutdown**:
```python
import atexit, shutil
atexit.register(shutil.rmtree, AUDIO_UPLOAD_DIR, ignore_errors=True)
```

**Use `logging` instead of `print()`**:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Saving voice note for week %d, year %d", week_number, year)
```
