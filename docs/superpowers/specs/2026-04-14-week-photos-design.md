# Week Photos Feature — Design Spec

**Date:** 2026-04-14  
**Status:** Approved

## Overview

Add the ability to attach multiple photos to any week in the Lifetime Calendar. Photos are stored on the file system with metadata in SQLite, displayed as compact 2-column thumbnails in the week modal, and viewable full-size via a lightbox.

---

## Constraints

- Max **5 photos** per week
- Max **5 MB** per file
- Accepted MIME types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- No visual indicator on the calendar grid cells for weeks with photos

---

## Section 1 — Data & Storage

### Database

New table added to `backend/app/database.py` → `init_db()`:

```sql
CREATE TABLE IF NOT EXISTS week_photos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number   INTEGER NOT NULL,
    year          INTEGER NOT NULL,
    filename      TEXT NOT NULL,        -- stored name: {uuid}.{ext}
    original_name TEXT NOT NULL,        -- user's original filename
    mime_type     TEXT NOT NULL,
    size_bytes    INTEGER NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### File system

Files stored at: `backend/uploads/photos/{year}/{week_number}/{uuid}.{ext}`

The `uploads/` directory lives inside `backend/` alongside the SQLite DB. It is created at startup if it does not exist.

Images are served as static files via FastAPI's `StaticFiles` mount at `/uploads`.

---

## Section 2 — Backend

### New router: `backend/app/routers/photos.py`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/week-photos/{year}/{week_number}` | List all photos for a week |
| `POST` | `/api/week-photos` | Upload a photo (multipart: `week_number`, `year`, `file`) |
| `DELETE` | `/api/week-photos/{photo_id}` | Delete photo record from DB and file from disk |

### New Pydantic schema: `WeekPhoto`

Added to `backend/app/schemas.py`:

```python
class WeekPhoto(BaseModel):
    id: int
    week_number: int
    year: int
    url: str           # e.g. /uploads/photos/2024/3/uuid.jpg
    original_name: str
    size_bytes: int
    created_at: str
```

### Changes to `backend/app/main.py`

```python
from fastapi.staticfiles import StaticFiles
from app.routers import photos

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(photos.router)
```

The `uploads/photos` directory tree is created at startup.

### Validation (enforced in the API, not the DB)

- Reject if `size_bytes > 5 * 1024 * 1024`
- Reject if `mime_type not in {"image/jpeg", "image/png", "image/gif", "image/webp"}`
- Reject if existing photo count for that week ≥ 5

---

## Section 3 — Frontend

All changes are inside `frontend/src/components/LifetimeCalendar.vue` — no new component files.

### New reactive state

```js
const weekPhotos = ref([])        // photos for the currently open week
const isUploadingPhoto = ref(false)
const lightboxPhoto = ref(null)   // null = closed, object = shown full-size
```

### Modal changes

A **Photos section** is added below the Note section:

- Label row: `PHOTOS (n / 5)` + `📎 Add` button (hidden `<input type="file">`)
- 2-column grid of compact thumbnails (72px tall), each with a `✕` delete button in the top-right corner
- "Click a photo to view full size" hint
- Empty slots show remaining capacity

### Data flow

- `openWeekModal(week)` fetches photos via `GET /api/week-photos/{year}/{week_number}` alongside existing note data
- "Add Photo" triggers file validation client-side (type, size, and count), then `POST /api/week-photos`
- `✕` button calls `DELETE /api/week-photos/{photo_id}`, then removes from local `weekPhotos` array
- Clicking a thumbnail sets `lightboxPhoto` — a full-screen overlay renders the image

### Lightbox

Simple overlay: dark backdrop + centred `<img>` + close button. Click backdrop or close button to dismiss. No additional library needed.

---

## Section 4 — Testing

### Backend (`pytest`)

File: `backend/tests/test_photos.py`

- Upload a valid photo → verify DB row created, file exists on disk
- `GET` list → verify uploaded photo appears
- `DELETE` photo → verify DB row gone, file removed from disk
- Upload 6th photo → expect 400
- Upload file > 5 MB → expect 400
- Upload unsupported MIME type → expect 400
- `init_db()` creates `week_photos` table

### Frontend (`vitest`)

File: `frontend/src/utils/photoValidation.test.js`

Extract a pure helper `validatePhotoFile(file, currentCount)` into `frontend/src/utils/photoValidation.js`:

- Returns error string if count ≥ 5
- Returns error string if file size > 5 MB
- Returns error string if MIME type unsupported
- Returns `null` (valid) for a good file under the limit

---

## Implementation Notes

- Use a git worktree for this feature branch
- `uploads/` directory should be added to `.gitignore` (user data, not source)
- The feature follows the same raw `sqlite3` pattern as the rest of the backend — no ORM
