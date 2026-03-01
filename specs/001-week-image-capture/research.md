# Research: Camera Capture and Persistent Image Attachments

**Branch**: `001-week-image-capture`
**Date**: 2026-02-28
**Status**: Complete — all unknowns resolved

---

## Decision 1: Image Storage Location

**Decision**: Store images in `uploads/week-images/` relative to the process working
directory (i.e., the repository root when running `uvicorn backend.main:app` from root).

**Rationale**: The existing `DB_PATH = "lifetime_calendar.db"` uses a relative path from
CWD. The uploads directory follows the same convention for consistency. The directory is
created at startup via `os.makedirs(..., exist_ok=True)` alongside `init_db()`. This is
the simplest approach that matches the project's existing patterns.

**Alternatives considered**:
- Absolute path derived from `__file__`: More portable across CWD changes, but adds
  complexity inconsistent with how DB_PATH is currently handled.
- Temp directory: Rejected — images must survive restarts (spec requirement FR-006).
- Environment variable: Adds config surface without benefit for a local-first app.

---

## Decision 2: Unique Filename Strategy

**Decision**: `{uuid4()}.{original_extension}` — e.g., `a3f2c1d0-....jpg`.

**Rationale**: The existing voice transcription endpoint already uses `uuid4()` for
audio temp files (see `file_id = str(uuid.uuid4())` in `transcribe_voice()`). Reusing
the same pattern keeps the codebase consistent. UUIDs prevent filename collisions
across weeks and sessions.

**Alternatives considered**:
- `{year}-{week_of_year}-{uuid4}.{ext}`: More descriptive but adds no functional value
  since metadata is stored in SQLite; filename does not need to encode week identity.
- Incrementing integer filenames: Collision risk if parallel uploads ever occur.

---

## Decision 3: Static File Serving

**Decision**: Mount the `uploads/` directory via FastAPI's `StaticFiles`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```
Images are served at `GET /uploads/week-images/{filename}`.

**Rationale**: FastAPI's built-in `StaticFiles` requires zero additional dependencies
(`starlette` is already installed as a FastAPI dependency). One import and one
`app.mount()` call in `main.py` — minimal footprint, consistent with Simplicity First.

**Alternatives considered**:
- Separate endpoint that reads and streams the file: More code for no gain; StaticFiles
  handles range requests, ETag caching, and MIME type detection automatically.
- Serving images via a CDN or object storage: Out of scope for local-first app.

**Note on `python-multipart` dependency**: FastAPI requires `python-multipart` for
`UploadFile` / `Form` handling. Checking existing `requirements.txt`:

---

## Decision 4: Database Schema for Week Images

**Decision**: New table `week_images` with columns:
`id`, `year`, `week_of_year`, `filename`, `created_at`.
Add index `idx_week_images_week` on `(year, week_of_year)` for fast per-week lookup.

**Rationale**: Using explicit `year` + `week_of_year` column names (rather than the
confusingly-named `week_number` used in `week_notes`) aligns with the project's
documented week identity convention: `"year-week_of_year"` string. No foreign key is
needed — SQLite FK enforcement is disabled by default in Python's `sqlite3`, and the
existing `week_notes` table uses no FK constraints. `filename` (not full path) is stored
so the static serve path can be derived at query time.

**Alternatives considered**:
- Storing full file path: Breaks if the app is moved to a different directory.
- Re-using `week_notes` table with an images column: Would require a schema migration
  and storing JSON or pipe-delimited filenames — too fragile.

---

## Decision 5: Calendar API — Lazy vs. Eager Image Loading

**Decision**: Images are fetched lazily via a new `GET /api/week-images/{year}/{week_of_year}`
endpoint when the week modal opens. `GET /api/calendar` is NOT modified.

**Rationale**: `GET /api/calendar` currently returns up to 4160 week objects. Adding an
`images` array to every week would require a query per week or a bulk join on startup —
unnecessarily expensive. Most weeks will have no images. Lazy loading (modal open event)
keeps the calendar load fast and keeps the existing API contract stable (Constitution
Principle I, Principle V).

**Alternatives considered**:
- Embed `has_images: bool` flag in calendar response: Small addition, but adds complexity
  without a spec requirement for a grid-level visual indicator. Deferred to future if needed.
- Embed full image list in calendar response: Too expensive for the full grid.

---

## Decision 6: Frontend Camera/File Input Approach

**Decision**: Hidden `<input type="file" accept="image/*" capture="environment">` element,
triggered programmatically by a "Camera" button via a Vue template ref.

**Rationale**: This is the standard browser-native approach. On mobile browsers,
`capture="environment"` opens the rear camera directly. On desktop browsers,
`capture="environment"` is ignored and a normal file picker opens instead — which is the
correct degraded behavior per spec (FR-002). No JavaScript camera library needed.

**Alternatives considered**:
- `getUserMedia()` with a canvas screenshot: More complex, poorer UX on mobile,
  requires more code. The `<input capture>` approach is simpler and universally supported.
- Third-party camera library: Unnecessary dependency overhead.

---

## Decision 7: `python-multipart` Dependency

**Decision**: Verify `python-multipart` is already in `requirements.txt`; add it if absent.

**Rationale**: The existing `POST /api/week-note/voice` endpoint already uses `UploadFile`
and `Form`, so `python-multipart` is already a transitive requirement. The new image upload
endpoint uses the same multipart pattern. No new package installation is expected.

---

## Resolution Summary

All NEEDS CLARIFICATION items resolved. No ambiguities remain.

| # | Topic | Decision |
|---|-------|----------|
| 1 | Storage location | `uploads/week-images/` relative to repo root |
| 2 | Filename strategy | `{uuid4}.{ext}` — consistent with existing audio pattern |
| 3 | Static serving | FastAPI `StaticFiles` mount at `/uploads` |
| 4 | DB schema | New `week_images` table with `year`, `week_of_year`, `filename` |
| 5 | Calendar API | No change; images fetched lazily on modal open |
| 6 | Camera input | Hidden `<input type="file" accept="image/*" capture="environment">` |
| 7 | python-multipart | Already a project dependency (verify in requirements.txt) |
