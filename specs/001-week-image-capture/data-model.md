# Data Model: Camera Capture and Persistent Image Attachments

**Branch**: `001-week-image-capture`
**Date**: 2026-02-28

---

## New Database Table: `week_images`

```sql
CREATE TABLE IF NOT EXISTS week_images (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    year         INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    filename     TEXT    NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_week_images_week
    ON week_images (year, week_of_year);
```

### Column descriptions

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing primary key |
| `year` | INTEGER | Calendar year (e.g., 2026) |
| `week_of_year` | INTEGER | ISO week-of-year (1–53) |
| `filename` | TEXT | UUID-based filename with original extension (e.g., `a3f2c1d0.jpg`). Stored without path prefix; full URL is derived at query time as `/uploads/week-images/{filename}` |
| `created_at` | TIMESTAMP | Row creation timestamp (UTC, set by SQLite DEFAULT) |

### Relationship to existing tables

- `week_images.(year, week_of_year)` logically corresponds to
  `week_notes.(year, week_number)` where `week_notes.week_number` stores `week_of_year`.
- No foreign key constraint is declared (consistent with existing schema; SQLite FK
  enforcement is off by default in Python's `sqlite3`).
- A week can have zero or more images. Each image belongs to exactly one week.

---

## Updated Backend Python Models

### New Pydantic response models (in `backend/main.py`)

```python
class WeekImageResponse(BaseModel):
    id: int
    url: str           # e.g. "/uploads/week-images/a3f2c1d0.jpg"
    filename: str
    created_at: str

class WeekImagesListResponse(BaseModel):
    images: List[WeekImageResponse]
```

### New upload endpoint input (multipart form, no Pydantic model needed)

| Field | Type | Description |
|-------|------|-------------|
| `year` | Form[int] | Year of the target week |
| `week_of_year` | Form[int] | ISO week-of-year of the target week |
| `image` | UploadFile | Image file (content-type must start with `image/`) |

---

## New Filesystem Entity

```text
uploads/
└── week-images/
    ├── a3f2c1d0-1234-5678-abcd-ef0123456789.jpg
    ├── b7e9f2c1-aaaa-bbbb-cccc-ddddeeeeeeee.png
    └── ...
```

- Directory created at startup by `os.makedirs("uploads/week-images", exist_ok=True)`
  inside `init_db()` (or a new `init_uploads()` helper called at module import).
- Files are never deleted by the application in this iteration (out of scope per spec).
- Path is relative to the process working directory; canonical run location is the
  repository root.

---

## Frontend State Additions (`LifetimeCalendar.vue`)

New reactive refs added to the existing `<script setup>` block:

| Ref | Type | Initial value | Description |
|-----|------|---------------|-------------|
| `selectedWeekImages` | `Ref<Array>` | `[]` | Images for the currently open week modal. Each entry: `{id, url, filename, created_at}` |
| `isUploadingImage` | `Ref<boolean>` | `false` | True while multipart upload is in flight |
| `imageError` | `Ref<string>` | `''` | User-visible error message for image upload failures |
| `imageInputRef` | template ref | — | Reference to the hidden `<input type="file">` element |

### State lifecycle

1. `openWeekModal(week)` → calls `fetchWeekImages(week.year, week.week_of_year)` →
   populates `selectedWeekImages`.
2. `closeWeekModal()` → resets `selectedWeekImages = []`, `imageError = ''`,
   `isUploadingImage = false`.
3. `uploadImage(file)` → sets `isUploadingImage = true` → POST → on success:
   pushes new image object to `selectedWeekImages`; on failure: sets `imageError`.

---

## Schema Initialization

`init_db()` in `backend/main.py` is extended with:

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS week_images (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        year         INTEGER NOT NULL,
        week_of_year INTEGER NOT NULL,
        filename     TEXT    NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_week_images_week
        ON week_images (year, week_of_year)
""")
```

And a call to create the upload directory:

```python
os.makedirs("uploads/week-images", exist_ok=True)
```

Both additions are idempotent (`IF NOT EXISTS`, `exist_ok=True`) — safe on repeated
app restarts and on the first run after the feature is deployed.
