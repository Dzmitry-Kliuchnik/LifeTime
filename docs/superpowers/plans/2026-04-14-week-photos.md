# Week Photos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-week photo attachments to the Lifetime Calendar — upload, display in a 2-column thumbnail grid, delete, and view full-size via lightbox.

**Architecture:** Files stored on disk at `backend/uploads/photos/{year}/{week_number}/{uuid}.{ext}`; metadata (filename, MIME type, size) in a new `week_photos` SQLite table. Three new API endpoints (GET/POST/DELETE) in a dedicated `photos.py` router. Static files served via FastAPI's `StaticFiles` mount at `/uploads`. All frontend changes live inside the existing `LifetimeCalendar.vue`.

**Tech Stack:** FastAPI + raw sqlite3, pytest + FastAPI TestClient (httpx), Vue 3 Composition API + axios, vitest.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/database.py` | Modify | Add `week_photos` table to `init_db()` |
| `backend/app/schemas.py` | Modify | Add `WeekPhoto` Pydantic model |
| `backend/app/routers/photos.py` | **Create** | GET / POST / DELETE photo endpoints |
| `backend/app/main.py` | Modify | Create uploads dir, mount `/uploads`, include photos router |
| `backend/tests/__init__.py` | **Create** | Empty — makes `tests/` a Python package |
| `backend/tests/test_photos.py` | **Create** | pytest tests for all photo endpoints |
| `frontend/src/utils/photoValidation.js` | **Create** | Pure `validatePhotoFile(file, currentCount)` helper |
| `frontend/src/utils/photoValidation.test.js` | **Create** | vitest tests for the validation helper |
| `frontend/src/components/LifetimeCalendar.vue` | Modify | Photo state, modal UI, upload/delete/lightbox |

---

### Task 1: Set up git worktree

**Files:** `.gitignore`

- [ ] **Step 1: Create feature branch in a new worktree**

Run from the project root `C:/DK/ITREX_OTHER/LifeTime2`:

```bash
git worktree add ../LifeTime2-photos feature/week-photos
cd ../LifeTime2-photos
```

All subsequent steps run from `../LifeTime2-photos` (the worktree).

- [ ] **Step 2: Add `backend/uploads/` to `.gitignore`**

Open `.gitignore` and add at the bottom:

```
# User-uploaded photos (runtime data, not source)
backend/uploads/
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore backend/uploads dir"
```

---

### Task 2: Database — `week_photos` table

**Files:**
- Modify: `backend/app/database.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_photos.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/__init__.py` as an empty file.

Create `backend/tests/test_photos.py`:

```python
import os
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Builds a minimal test app with the photos router, using isolated temp DB and uploads dir."""
    import app.database as db_module
    import app.routers.photos as photos_module

    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(photos_module, "PHOTOS_DIR", str(tmp_path / "photos"))

    from app.database import init_db
    init_db()

    from app.routers.photos import router
    test_app = FastAPI()
    test_app.include_router(router)

    return TestClient(test_app), tmp_path


def test_init_db_creates_week_photos_table(tmp_path, monkeypatch):
    import app.database as db_module

    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)

    from app.database import init_db
    init_db()

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='week_photos'"
    )
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result[0] == "week_photos"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend
source venv/Scripts/activate   # Windows (use venv/bin/activate on Linux/Mac)
pytest tests/test_photos.py::test_init_db_creates_week_photos_table -v
```

Expected: **FAIL** — `week_photos` table does not exist yet.

- [ ] **Step 3: Add `week_photos` table to `init_db()`**

In `backend/app/database.py`, inside `init_db()`, add after the existing `cursor.execute("""CREATE TABLE IF NOT EXISTS week_notes ...`)` block:

```python
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS week_photos (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                week_number   INTEGER NOT NULL,
                year          INTEGER NOT NULL,
                filename      TEXT NOT NULL,
                original_name TEXT NOT NULL,
                mime_type     TEXT NOT NULL,
                size_bytes    INTEGER NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_photos.py::test_init_db_creates_week_photos_table -v
```

Expected: **PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/database.py backend/tests/__init__.py backend/tests/test_photos.py
git commit -m "feat: add week_photos table to database schema"
```

---

### Task 3: `WeekPhoto` Pydantic schema

**Files:**
- Modify: `backend/app/schemas.py`

- [ ] **Step 1: Add `WeekPhoto` to `backend/app/schemas.py`**

At the end of the file, add:

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

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: add WeekPhoto schema"
```

---

### Task 4: Photos router — GET endpoint

**Files:**
- Create: `backend/app/routers/photos.py`
- Modify: `backend/tests/test_photos.py`

- [ ] **Step 1: Create a skeleton `backend/app/routers/photos.py`**

The test fixture imports this module, so it must exist before we run any test that uses `client`. Create it now with just the router and constants — no endpoints yet:

```python
import os
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.schemas import WeekPhoto

router = APIRouter(prefix="/api")

PHOTOS_DIR = os.path.join("uploads", "photos")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024   # 5 MB
MAX_PHOTOS_PER_WEEK = 5
```

- [ ] **Step 2: Write the failing test**

Add to `backend/tests/test_photos.py`:

```python
def test_get_photos_returns_empty_list_for_new_week(client):
    c, _ = client
    response = c.get("/api/week-photos/2024/3")
    assert response.status_code == 200
    assert response.json() == []
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_photos.py::test_get_photos_returns_empty_list_for_new_week -v
```

Expected: **FAIL** with 404 — GET route not registered yet.

- [ ] **Step 4: Add the GET endpoint to `backend/app/routers/photos.py`**

Append after the constants block:

```python
@router.get("/week-photos/{year}/{week_number}", response_model=list[WeekPhoto])
async def get_week_photos(year: int, week_number: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, week_number, year, filename, original_name, mime_type, size_bytes, created_at "
            "FROM week_photos WHERE year = ? AND week_number = ? ORDER BY created_at ASC",
            (year, week_number),
        )
        rows = cursor.fetchall()

    return [
        WeekPhoto(
            id=row[0],
            week_number=row[1],
            year=row[2],
            url=f"/uploads/photos/{row[2]}/{row[1]}/{row[3]}",
            original_name=row[4],
            size_bytes=row[6],
            created_at=row[7],
        )
        for row in rows
    ]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_photos.py::test_get_photos_returns_empty_list_for_new_week -v
```

Expected: **PASS**

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/photos.py backend/tests/test_photos.py
git commit -m "feat: add GET /api/week-photos/{year}/{week_number} endpoint"
```

---

### Task 5: Photos router — POST endpoint

**Files:**
- Modify: `backend/app/routers/photos.py`
- Modify: `backend/tests/test_photos.py`

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_photos.py`:

```python
def _upload(client, week_number="3", year="2024",
            content=b"fake-image-bytes", content_type="image/jpeg", filename="photo.jpg"):
    """Helper: POST a photo upload and return the response."""
    return client.post(
        "/api/week-photos",
        data={"week_number": week_number, "year": year},
        files={"file": (filename, content, content_type)},
    )


def test_upload_photo_creates_db_row_and_file(client):
    c, tmp_path = client
    response = _upload(c)

    assert response.status_code == 200
    body = response.json()
    assert body["original_name"] == "photo.jpg"
    assert body["week_number"] == 3
    assert body["year"] == 2024
    assert body["url"].startswith("/uploads/photos/2024/3/")
    assert body["size_bytes"] == len(b"fake-image-bytes")

    # File must exist on disk
    filename = body["url"].split("/")[-1]
    file_path = tmp_path / "photos" / "2024" / "3" / filename
    assert file_path.exists()


def test_get_photos_returns_uploaded_photo(client):
    c, _ = client
    _upload(c)
    response = c.get("/api/week-photos/2024/3")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["original_name"] == "photo.jpg"


def test_upload_enforces_count_limit(client):
    c, _ = client
    for i in range(5):
        r = _upload(c, filename=f"photo{i}.jpg")
        assert r.status_code == 200
    # 6th upload must be rejected
    response = _upload(c, filename="photo5.jpg")
    assert response.status_code == 400
    assert "limit" in response.json()["detail"].lower()


def test_upload_rejects_oversized_file(client):
    c, _ = client
    big_content = b"x" * (5 * 1024 * 1024 + 1)
    response = _upload(c, content=big_content)
    assert response.status_code == 400
    assert "size" in response.json()["detail"].lower()


def test_upload_rejects_unsupported_mime_type(client):
    c, _ = client
    response = _upload(c, content_type="application/pdf", filename="doc.pdf")
    assert response.status_code == 400
    assert "type" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run tests to verify they all fail**

```bash
pytest tests/test_photos.py::test_upload_photo_creates_db_row_and_file \
       tests/test_photos.py::test_get_photos_returns_uploaded_photo \
       tests/test_photos.py::test_upload_enforces_count_limit \
       tests/test_photos.py::test_upload_rejects_oversized_file \
       tests/test_photos.py::test_upload_rejects_unsupported_mime_type -v
```

Expected: all **FAIL** — POST route not implemented yet.

- [ ] **Step 3: Add the POST endpoint to `backend/app/routers/photos.py`**

Add after the `get_week_photos` function:

```python
@router.post("/week-photos", response_model=WeekPhoto)
async def upload_week_photo(
    week_number: int = Form(...),
    year: int = Form(...),
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: jpeg, png, gif, webp.",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(content)} bytes exceeds the 5 MB limit.",
        )

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM week_photos WHERE year = ? AND week_number = ?",
            (year, week_number),
        )
        count = cursor.fetchone()[0]

    if count >= MAX_PHOTOS_PER_WEEK:
        raise HTTPException(
            status_code=400,
            detail=f"Photo limit reached: max {MAX_PHOTOS_PER_WEEK} photos per week.",
        )

    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp"}
    filename = f"{uuid.uuid4()}.{ext_map[file.content_type]}"

    dest_dir = os.path.join(PHOTOS_DIR, str(year), str(week_number))
    os.makedirs(dest_dir, exist_ok=True)
    with open(os.path.join(dest_dir, filename), "wb") as f:
        f.write(content)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO week_photos (week_number, year, filename, original_name, mime_type, size_bytes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (week_number, year, filename, file.filename or filename, file.content_type, len(content)),
        )
        conn.commit()
        photo_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, week_number, year, filename, original_name, mime_type, size_bytes, created_at "
            "FROM week_photos WHERE id = ?",
            (photo_id,),
        )
        row = cursor.fetchone()

    return WeekPhoto(
        id=row[0],
        week_number=row[1],
        year=row[2],
        url=f"/uploads/photos/{row[2]}/{row[1]}/{row[3]}",
        original_name=row[4],
        size_bytes=row[6],
        created_at=row[7],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_photos.py::test_upload_photo_creates_db_row_and_file \
       tests/test_photos.py::test_get_photos_returns_uploaded_photo \
       tests/test_photos.py::test_upload_enforces_count_limit \
       tests/test_photos.py::test_upload_rejects_oversized_file \
       tests/test_photos.py::test_upload_rejects_unsupported_mime_type -v
```

Expected: all **PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/photos.py backend/tests/test_photos.py
git commit -m "feat: add POST /api/week-photos with size, type, and count validation"
```

---

### Task 6: Photos router — DELETE endpoint

**Files:**
- Modify: `backend/app/routers/photos.py`
- Modify: `backend/tests/test_photos.py`

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_photos.py`:

```python
def test_delete_photo_removes_db_row_and_file(client):
    c, tmp_path = client
    upload_resp = _upload(c)
    assert upload_resp.status_code == 200

    photo_id = upload_resp.json()["id"]
    filename = upload_resp.json()["url"].split("/")[-1]
    file_path = tmp_path / "photos" / "2024" / "3" / filename
    assert file_path.exists()

    delete_resp = c.delete(f"/api/week-photos/{photo_id}")
    assert delete_resp.status_code == 200

    # DB row gone
    list_resp = c.get("/api/week-photos/2024/3")
    assert list_resp.json() == []

    # File gone
    assert not file_path.exists()


def test_delete_nonexistent_photo_returns_404(client):
    c, _ = client
    response = c.delete("/api/week-photos/99999")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_photos.py::test_delete_photo_removes_db_row_and_file \
       tests/test_photos.py::test_delete_nonexistent_photo_returns_404 -v
```

Expected: both **FAIL** — DELETE route not implemented yet.

- [ ] **Step 3: Add the DELETE endpoint to `backend/app/routers/photos.py`**

Add after the `upload_week_photo` function:

```python
@router.delete("/week-photos/{photo_id}")
async def delete_week_photo(photo_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename, year, week_number FROM week_photos WHERE id = ?",
            (photo_id,),
        )
        row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Photo not found.")

    filename, year, week_number = row
    file_path = os.path.join(PHOTOS_DIR, str(year), str(week_number), filename)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM week_photos WHERE id = ?", (photo_id,))
        conn.commit()

    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": "Photo deleted successfully."}
```

- [ ] **Step 4: Run the full backend test suite**

```bash
pytest tests/test_photos.py -v
```

Expected: all **PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/photos.py backend/tests/test_photos.py
git commit -m "feat: add DELETE /api/week-photos/{photo_id} endpoint"
```

---

### Task 7: Wire up `main.py`

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Replace `backend/app/main.py` with the updated version**

```python
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import calendar, notes, user, photos

# Ensure uploads directory exists before StaticFiles mount
os.makedirs(os.path.join("uploads", "photos"), exist_ok=True)

app = FastAPI(title="Lifetime Calendar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(user.router)
app.include_router(calendar.router)
app.include_router(notes.router)
app.include_router(photos.router)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {"message": "Lifetime Calendar API"}
```

- [ ] **Step 2: Run all backend tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: all **PASS**

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: mount /uploads static files and register photos router in main"
```

---

### Task 8: Frontend validation utility

**Files:**
- Create: `frontend/src/utils/photoValidation.js`
- Create: `frontend/src/utils/photoValidation.test.js`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/utils/photoValidation.test.js`:

```js
import { describe, it, expect } from 'vitest'
import { validatePhotoFile } from './photoValidation.js'

const makeFile = (size, type, name = 'photo.jpg') =>
  new File([new Uint8Array(size)], name, { type })

describe('validatePhotoFile', () => {
  it('returns null for a valid file within all limits', () => {
    const file = makeFile(1024, 'image/jpeg')
    expect(validatePhotoFile(file, 0)).toBeNull()
  })

  it('accepts all supported MIME types', () => {
    for (const type of ['image/jpeg', 'image/png', 'image/gif', 'image/webp']) {
      expect(validatePhotoFile(makeFile(1024, type), 0)).toBeNull()
    }
  })

  it('returns an error string when count is already at max (5)', () => {
    const result = validatePhotoFile(makeFile(1024, 'image/jpeg'), 5)
    expect(result).not.toBeNull()
    expect(result.toLowerCase()).toContain('limit')
  })

  it('returns an error string when file exceeds 5 MB', () => {
    const result = validatePhotoFile(makeFile(5 * 1024 * 1024 + 1, 'image/jpeg'), 0)
    expect(result).not.toBeNull()
    expect(result.toLowerCase()).toContain('size')
  })

  it('returns an error string for unsupported MIME type', () => {
    const result = validatePhotoFile(makeFile(1024, 'application/pdf', 'doc.pdf'), 0)
    expect(result).not.toBeNull()
    expect(result.toLowerCase()).toContain('type')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend
npm run test
```

Expected: **FAIL** — `photoValidation.js` module not found.

- [ ] **Step 3: Create `frontend/src/utils/photoValidation.js`**

```js
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp'])
const MAX_SIZE = 5 * 1024 * 1024  // 5 MB
const MAX_COUNT = 5

/**
 * Validates a photo File before upload.
 * @param {File} file
 * @param {number} currentCount - photos already attached to this week
 * @returns {string|null} error message, or null if valid
 */
export function validatePhotoFile(file, currentCount) {
  if (currentCount >= MAX_COUNT) {
    return `Photo limit reached: max ${MAX_COUNT} photos per week.`
  }
  if (file.size > MAX_SIZE) {
    return `File size exceeds the 5 MB limit.`
  }
  if (!ALLOWED_TYPES.has(file.type)) {
    return `Unsupported file type: ${file.type}. Allowed: jpeg, png, gif, webp.`
  }
  return null
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
npm run test
```

Expected: all **PASS**

- [ ] **Step 5: Commit**

```bash
cd ..
git add frontend/src/utils/photoValidation.js frontend/src/utils/photoValidation.test.js
git commit -m "feat: add client-side photo validation utility"
```

---

### Task 9: Frontend — photo state, fetch, upload, delete

**Files:**
- Modify: `frontend/src/components/LifetimeCalendar.vue` (script section only)

All edits below are inside the `<script setup>` block.

- [ ] **Step 1: Add the import for `validatePhotoFile`**

At the top of `<script setup>`, after the existing imports, add:

```js
import { validatePhotoFile } from '@/utils/photoValidation.js'
```

- [ ] **Step 2: Add new reactive state**

After the voice recording state block (the block ending with `const recordingTimer = ref(null)`), add:

```js
// Photo state
const weekPhotos = ref([])
const isUploadingPhoto = ref(false)
const photoUploadError = ref('')
const lightboxPhoto = ref(null)
```

- [ ] **Step 3: Replace `openWeekModal` with an async version that fetches photos**

Replace the existing `openWeekModal` function:

```js
const openWeekModal = async (week) => {
  selectedWeek.value = week
  weekNote.value = week.note || ''
  weekPhotos.value = []
  photoUploadError.value = ''
  showWeekModal.value = true

  try {
    const response = await axios.get(
      `${API_BASE}/api/week-photos/${week.year}/${week.week_of_year}`
    )
    weekPhotos.value = response.data
  } catch (err) {
    console.error('Failed to load photos:', err)
  }
}
```

- [ ] **Step 4: Update `closeWeekModal` to reset photo state**

Inside the existing `closeWeekModal` function, after `weekNote.value = ''`, add:

```js
  weekPhotos.value = []
  photoUploadError.value = ''
  lightboxPhoto.value = null
```

- [ ] **Step 5: Add `uploadPhoto` and `deletePhoto` functions**

Add these two functions after `saveWeekNote`:

```js
const uploadPhoto = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const error = validatePhotoFile(file, weekPhotos.value.length)
  if (error) {
    photoUploadError.value = error
    event.target.value = ''
    return
  }

  photoUploadError.value = ''
  isUploadingPhoto.value = true

  try {
    const formData = new FormData()
    formData.append('week_number', selectedWeek.value.week_of_year)
    formData.append('year', selectedWeek.value.year)
    formData.append('file', file)

    const response = await axios.post(`${API_BASE}/api/week-photos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    weekPhotos.value.push(response.data)
  } catch (err) {
    photoUploadError.value =
      err.response?.data?.detail || 'Upload failed. Please try again.'
    console.error('Photo upload error:', err)
  } finally {
    isUploadingPhoto.value = false
    event.target.value = ''
  }
}

const deletePhoto = async (photoId) => {
  try {
    await axios.delete(`${API_BASE}/api/week-photos/${photoId}`)
    weekPhotos.value = weekPhotos.value.filter((p) => p.id !== photoId)
  } catch (err) {
    console.error('Failed to delete photo:', err)
  }
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/LifetimeCalendar.vue
git commit -m "feat: add photo state, fetch-on-open, upload, and delete to LifetimeCalendar"
```

---

### Task 10: Frontend — photos section template and lightbox

**Files:**
- Modify: `frontend/src/components/LifetimeCalendar.vue` (template + styles)

- [ ] **Step 1: Add the photos section inside the modal body**

In the `<template>`, find the closing `</div>` of the `.note-section` div (the one that ends just before `</div> <!-- end modal-body -->`). After it, insert:

```html
<!-- Photos Section -->
<div class="photos-section">
  <div class="photos-header">
    <span class="photos-label">PHOTOS ({{ weekPhotos.length }} / 5)</span>
    <label
      class="btn btn-photo-add"
      :class="{ disabled: weekPhotos.length >= 5 || isUploadingPhoto }"
    >
      <span v-if="isUploadingPhoto" class="btn-icon spinner">🔄</span>
      <span v-else class="btn-icon">📎</span>
      Add
      <input
        type="file"
        accept="image/jpeg,image/png,image/gif,image/webp"
        style="display: none"
        :disabled="weekPhotos.length >= 5 || isUploadingPhoto"
        @change="uploadPhoto"
      />
    </label>
  </div>

  <div v-if="photoUploadError" class="photo-upload-error">{{ photoUploadError }}</div>

  <div v-if="weekPhotos.length > 0" class="photos-grid">
    <div
      v-for="photo in weekPhotos"
      :key="photo.id"
      class="photo-thumb"
      @click="lightboxPhoto = photo"
    >
      <img :src="API_BASE + photo.url" :alt="photo.original_name" />
      <button
        class="photo-delete-btn"
        @click.stop="deletePhoto(photo.id)"
        aria-label="Delete photo"
      >✕</button>
    </div>
  </div>
  <p v-else class="photos-empty">No photos yet. Click Add to attach one.</p>
</div>
```

- [ ] **Step 2: Add the lightbox overlay**

Inside the `<Teleport to="body">` block, after the closing `</div>` of the existing modal container (the `@click.stop` div), add:

```html
<!-- Lightbox -->
<div v-if="lightboxPhoto" class="lightbox-backdrop" @click="lightboxPhoto = null">
  <div class="lightbox-container" @click.stop>
    <button class="lightbox-close" @click="lightboxPhoto = null" aria-label="Close lightbox">×</button>
    <img
      :src="API_BASE + lightboxPhoto.url"
      :alt="lightboxPhoto.original_name"
      class="lightbox-img"
    />
    <div class="lightbox-caption">{{ lightboxPhoto.original_name }}</div>
  </div>
</div>
```

- [ ] **Step 3: Add styles at the end of `<style scoped>`**

```css
/* ── Photos section ─────────────────────────────────────── */
.photos-section {
  margin-top: 16px;
}

.photos-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.photos-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.btn-photo-add {
  cursor: pointer;
  padding: 4px 10px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: opacity 0.2s;
}

.btn-photo-add.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.photo-upload-error {
  font-size: 12px;
  color: #e55;
  margin-bottom: 8px;
}

.photos-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.photo-thumb {
  position: relative;
  height: 72px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--color-border);
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.7);
  border: none;
  border-radius: 50%;
  color: #ccc;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

.photo-delete-btn:hover {
  background: rgba(200, 0, 0, 0.85);
  color: #fff;
}

.photos-empty {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ── Lightbox ────────────────────────────────────────────── */
.lightbox-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.88);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.lightbox-close {
  position: absolute;
  top: -40px;
  right: 0;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 32px;
  cursor: pointer;
  line-height: 1;
}

.lightbox-img {
  max-width: 100%;
  max-height: 80vh;
  border-radius: 8px;
  object-fit: contain;
}

.lightbox-caption {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/LifetimeCalendar.vue
git commit -m "feat: add photos section and lightbox overlay to week modal"
```

---

### Task 11: Final integration check

- [ ] **Step 1: Run all backend tests**

```bash
cd backend
source venv/Scripts/activate
pytest tests/ -v
```

Expected: all **PASS**

- [ ] **Step 2: Run all frontend tests**

```bash
cd frontend
npm run test
```

Expected: all **PASS**

- [ ] **Step 3: Manual smoke test**

Start both servers:

```bash
# Terminal 1 — backend (from worktree root)
cd backend && source venv/Scripts/activate && python main.py

# Terminal 2 — frontend (from worktree root)
cd frontend && npm run dev
```

Open http://localhost:5173 and verify:
- Open any week → Photos section appears below the note with "No photos yet" message
- Click Add → file picker opens; select a JPEG/PNG
- Photo appears as a 72px thumbnail in the 2-column grid
- Counter updates: `PHOTOS (1 / 5)`
- Click the thumbnail → lightbox opens with full-size image; click outside or × to close
- Click ✕ on thumbnail → photo removed from grid and disk
- Close modal, reopen same week → photos still appear (persistence check)
- Try uploading a `.pdf` → error message appears without upload
- Try uploading a file > 5 MB → error message appears without upload

- [ ] **Step 4: Final commit**

```bash
git add -A
git status   # verify only expected files
git commit -m "feat: week photos — complete implementation"
```
