# Implementation Plan: Camera Capture and Persistent Image Attachments to Week Notes

**Branch**: `001-week-image-capture` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-week-image-capture/spec.md`

## Summary

Add a camera/file-capture button to the week note modal that lets the user attach photos
to any week. Each uploaded image is stored on local disk under `uploads/week-images/`,
metadata is persisted in a new `week_images` SQLite table, and the image is served back
via a FastAPI static mount. The frontend loads images lazily when a week modal opens and
patches local state after each upload — no full calendar reload.

## Technical Context

**Language/Version**: Python 3.11+ (backend), JavaScript ES2022 + Vue 3 (frontend)
**Primary Dependencies**: FastAPI + Uvicorn + python-multipart (backend), Vue 3 + Vite + Axios (frontend)
**Storage**: SQLite (`lifetime_calendar.db`) + local filesystem (`uploads/week-images/`)
**Testing**: Manual verification (no automated test framework in project)
**Target Platform**: Local web application (Chromium/Safari browser + localhost Python server)
**Project Type**: web-application (monorepo: backend/ + frontend/)
**Performance Goals**: Thumbnail renders within 3 seconds of successful upload on localhost
**Constraints**: Backend must remain single file (`backend/main.py`); local-first; single-user
**Scale/Scope**: 1 user, ~4160 weeks max (80-year life), unbounded images per week

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. API Contract Stability | New endpoints are additive; `GET /api/calendar` response shape unchanged; atomic backend+frontend changes on same branch | PASS | |
| II. Secure-by-Default | All `week_images` SQL uses `?` placeholders; no new secrets; CORS unchanged; image URL derived from API_BASE, no hardcoded constant | PASS | |
| III. Simplicity First | All new Python code stays in `backend/main.py`; `uploads/week-images/` is a runtime directory, not a new Python module; one `app.mount()` call added | PASS | |
| IV. Transparent Error Handling | Upload failures raise `HTTPException` with detail; frontend `catch` block sets `imageError` ref; user-visible error in modal | PASS | |
| V. Optimistic State Consistency | After upload, `selectedWeekImages` patched in-place; images fetched lazily on modal open; no full calendar refetch | PASS | |

**Post-Design Re-check**: All contracts are purely additive. `GET /api/calendar` endpoint
and its response shape are not modified. PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-week-image-capture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── week-images-api.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── main.py              # Extended: StaticFiles import+mount, week_images table init,
│                        #   POST /api/week-images, GET /api/week-images/{year}/{woy}
└── uploads/
    └── week-images/     # Runtime-created; persistent image storage on local disk

frontend/
└── src/
    └── components/
        └── LifetimeCalendar.vue  # Extended: hidden file input, camera button,
                                  #   fetchWeekImages(), uploadImage(), selectedWeekImages
                                  #   ref, thumbnail strip, imageError ref
```

**Structure Decision**: Web application layout. All backend changes are additive to the
single `backend/main.py` entrypoint. All frontend changes are additive to
`frontend/src/components/LifetimeCalendar.vue`. No new source files are created in either
`backend/` or `frontend/src/`.

## Complexity Tracking

> No constitution violations — table kept for reference only.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
