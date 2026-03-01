# Tasks: Camera Capture and Persistent Image Attachments to Week Notes

**Input**: Design documents from `/specs/001-week-image-capture/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/week-images-api.md ✓

**Tests**: No automated tests — manual verification only (per plan.md: "Manual verification (no automated test framework in project)"). Use `quickstart.md` for validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify and configure dependencies needed by all user stories before any implementation begins.

- [x] T001 Verify `python-multipart` is present in `backend/requirements.txt`; add `python-multipart` if absent (required for `UploadFile` + `Form` in FastAPI upload endpoint)
- [x] T002 Add `from fastapi.staticfiles import StaticFiles` import to `backend/main.py` (required by Phase 2 static mount task)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Extend `init_db()` in `backend/main.py` to `CREATE TABLE IF NOT EXISTS week_images (id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER NOT NULL, week_of_year INTEGER NOT NULL, filename TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)` with index `idx_week_images_week ON week_images (year, week_of_year)`
- [x] T004 Add `os.makedirs("uploads/week-images", exist_ok=True)` call inside `init_db()` (or a new `init_uploads()` called at module import) in `backend/main.py`
- [x] T005 Add `app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")` to `backend/main.py` to serve stored images at `GET /uploads/week-images/{filename}`
- [x] T006 Add `WeekImageResponse(BaseModel)` with fields `id: int`, `url: str`, `filename: str`, `created_at: str` and `WeekImagesListResponse(BaseModel)` with field `images: List[WeekImageResponse]` to `backend/main.py`

**Checkpoint**: Foundation ready — backend schema, upload directory, static mount, and response models are in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Capture and Attach a Photo (Priority: P1) 🎯 MVP

**Goal**: User opens the week note modal, taps the Camera button, device camera (mobile) or file picker (desktop) opens, user captures or selects a photo, image is uploaded and a thumbnail appears immediately inside the modal without a full calendar reload. Image persists to disk and SQLite.

**Independent Test**: Open any week modal → click Camera button → select/capture an image → verify thumbnail appears in modal → verify `uploads/week-images/<uuid>.<ext>` file exists on disk → verify row in `week_images` table. Matches quickstart.md §US1.

### Implementation for User Story 1

- [x] T007 [P] [US1] Implement `POST /api/week-images` endpoint in `backend/main.py`: accept `year: int = Form(...)`, `week_of_year: int = Form(...)`, `image: UploadFile = File(...)`, validate `image.content_type.startswith("image/")` (raise `HTTPException(400, "File must be an image")` on failure), generate `{uuid4()}.{original_extension}` filename, write file to `uploads/week-images/`, insert row into `week_images` table with parameterized query, return `WeekImageResponse` with status 201
- [x] T008 [P] [US1] Add reactive refs `selectedWeekImages = ref([])`, `isUploadingImage = ref(false)`, `imageError = ref('')` and template ref `imageInputRef = ref(null)` to `<script setup>` in `frontend/src/components/LifetimeCalendar.vue`
- [x] T009 [US1] Add hidden `<input type="file" accept="image/*" capture="environment" ref="imageInputRef" @change="handleImageSelected" style="display:none">` element to the week note modal template in `frontend/src/components/LifetimeCalendar.vue`
- [x] T010 [US1] Add Camera button to the week note modal action controls in `frontend/src/components/LifetimeCalendar.vue`: button calls `imageInputRef.click()`, disabled while `isUploadingImage` is true, visually consistent with existing voice note button
- [x] T011 [US1] Implement `async function uploadImage(file)` in `frontend/src/components/LifetimeCalendar.vue`: set `isUploadingImage = true`, build `FormData` with `year`, `week_of_year`, and `image` fields, POST to `${API_BASE}/api/week-images` with `Content-Type: multipart/form-data`, on success push response data to `selectedWeekImages`, always reset `isUploadingImage = false` in finally block
- [x] T012 [US1] Implement `function handleImageSelected(event)` in `frontend/src/components/LifetimeCalendar.vue`: read `event.target.files[0]`; if no file selected (cancel), return immediately (no-op); otherwise call `uploadImage(file)` and reset `event.target.value = ''` so the same file can be reselected
- [x] T013 [US1] Add thumbnail strip to week note modal template in `frontend/src/components/LifetimeCalendar.vue`: `<img v-for="img in selectedWeekImages" :key="img.id" :src="\`${API_BASE}${img.url}\`" alt="Week photo" class="week-image-thumb">` with scoped CSS `.week-image-thumb` sized to ~80×80px, `object-fit: cover`, `border-radius: 4px`

**Checkpoint**: US1 fully functional — user can capture/select a photo, thumbnail appears in modal, file persists on disk, DB row exists. Verify with quickstart.md §US1.

---

## Phase 4: User Story 2 — View Previously Attached Images on Reopen (Priority: P2)

**Goal**: When a user reopens a week note modal that had images attached in a previous session (including after app restart), all previously attached thumbnails are displayed.

**Independent Test**: Complete US1 (attach a photo) → close modal → restart the app → reopen the same week modal → verify thumbnails are still visible. Matches quickstart.md §US2.

### Implementation for User Story 2

- [x] T014 [P] [US2] Implement `GET /api/week-images/{year}/{week_of_year}` endpoint in `backend/main.py`: query `week_images` table with parameterized `SELECT id, filename, created_at FROM week_images WHERE year=? AND week_of_year=? ORDER BY id`, build `url = f"/uploads/week-images/{row['filename']}"` for each row, return `WeekImagesListResponse`; never return 404 — empty list is a valid response
- [x] T015 [P] [US2] Implement `async function fetchWeekImages(year, weekOfYear)` in `frontend/src/components/LifetimeCalendar.vue`: GET `${API_BASE}/api/week-images/${year}/${weekOfYear}`, assign `response.data.images` to `selectedWeekImages`, catch errors and set `imageError`
- [x] T016 [US2] Call `fetchWeekImages(week.year, week.week_of_year)` from `openWeekModal(week)` in `frontend/src/components/LifetimeCalendar.vue` (after setting `selectedWeek`)
- [x] T017 [US2] In `closeWeekModal()` in `frontend/src/components/LifetimeCalendar.vue`, reset `selectedWeekImages.value = []`, `imageError.value = ''`, and `isUploadingImage.value = false`

**Checkpoint**: US2 fully functional — images survive app restarts and reopen correctly. Verify with quickstart.md §US2.

---

## Phase 5: User Story 3 — Cancel Capture Without Side Effects (Priority: P3)

**Goal**: If the user opens the camera/file picker and then dismisses it without selecting a file, no error is shown, no upload occurs, and the modal state is identical to before the Camera button was clicked.

**Independent Test**: Open a week modal with existing text → click Camera button → dismiss picker without selecting → verify no error message, no new DB row, text note unchanged. Matches quickstart.md §US3.

### Implementation for User Story 3

- [x] T018 [US3] Verify `handleImageSelected` in `frontend/src/components/LifetimeCalendar.vue` guards `if (!event.target.files || event.target.files.length === 0) return` as the first statement, ensuring a cancel (empty selection) results in zero side effects; no upload, no error, no state change

**Checkpoint**: US3 functional — cancelling capture leaves modal state unchanged. Verify with quickstart.md §US3.

---

## Phase 6: User Story 4 — Graceful Error Handling on Upload Failure (Priority: P4)

**Goal**: If image storage fails (disk error, DB error), a visible error message is displayed in the modal. Existing text and voice note content is not lost.

**Independent Test**: Make `uploads/week-images/` read-only → open week modal with a text note → click Camera → select image → verify error message appears, text note is unchanged, app does not crash. Matches quickstart.md §US4.

### Implementation for User Story 4

- [x] T019 [US4] Wrap the file-write and DB-insert block in `POST /api/week-images` in `backend/main.py` with a `try/except Exception as e` that raises `HTTPException(500, f"Failed to save image: {e}")`, ensuring disk or DB failures return a structured error response
- [x] T020 [P] [US4] Add `imageError` display to week note modal template in `frontend/src/components/LifetimeCalendar.vue`: `<p v-if="imageError" class="image-error">{{ imageError }}</p>` with scoped CSS `.image-error { color: var(--color-error, #d32f2f); font-size: 0.875rem; margin-top: 0.5rem; }`
- [x] T021 [P] [US4] In the `catch` block of `uploadImage()` in `frontend/src/components/LifetimeCalendar.vue`, set `imageError.value = error.response?.data?.detail || 'Failed to upload image. Please try again.'` so the error detail from the backend is surfaced to the user

**Checkpoint**: US4 functional — upload failures show a user-visible error message, existing note content is preserved. Verify with quickstart.md §US4.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final non-regression verification.

- [x] T022 Add `@error="$event.target.style.display='none'"` (or a `v-show` flag) to the `<img>` thumbnail elements in `frontend/src/components/LifetimeCalendar.vue` so images deleted from disk outside the app are silently hidden rather than showing a broken-image icon
- [ ] T023 Verify `POST /api/week-note` (text save) and `POST /api/week-note/voice` (voice transcription) still function correctly after all changes by running the non-regression steps in `specs/001-week-image-capture/quickstart.md` §Non-Regression Verification

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - Can proceed sequentially in priority order: US1 → US2 → US3 → US4
  - Within each story, backend and frontend tasks marked [P] can run in parallel
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 2 — no dependency on other user stories
- **US2 (P2)**: Depends on Phase 2 — logically requires US1 to have produced images, but GET endpoint and fetchWeekImages can be implemented independently
- **US3 (P3)**: Depends on T012 (handleImageSelected from US1) — refine existing cancel guard
- **US4 (P4)**: Depends on T007 (POST endpoint from US1) and T011 (uploadImage from US1) — adds error handling wrappers

### Within Each User Story

- Backend endpoint tasks and frontend ref/UI tasks marked [P] can start simultaneously
- UI wiring (buttons, handlers) depends on refs being added first (T008 before T010, T011, T012)
- Thumbnail display (T013) depends on selectedWeekImages ref (T008)
- fetchWeekImages call from openWeekModal (T016) depends on fetchWeekImages being defined (T015)

### Parallel Opportunities

- T007 (backend POST endpoint) and T008 (frontend refs) can run in parallel — different files
- T014 (backend GET endpoint) and T015 (frontend fetchWeekImages) can run in parallel — different files
- T019 (backend error wrapping) and T020/T021 (frontend error display) can run in parallel — different files
- All Phase 1 tasks (T001, T002) can run in parallel — different files/concerns
- T003–T006 in Phase 2 are all in `backend/main.py` and must be done sequentially

---

## Parallel Example: User Story 1

```bash
# Backend and frontend can proceed simultaneously:
Task T007: "Implement POST /api/week-images endpoint in backend/main.py"
Task T008: "Add selectedWeekImages, isUploadingImage, imageError refs to LifetimeCalendar.vue"

# After T008 completes, these can run in parallel:
Task T009: "Add hidden file input element to modal template in LifetimeCalendar.vue"
Task T010: "Add Camera button to modal in LifetimeCalendar.vue"
Task T011: "Implement uploadImage() function in LifetimeCalendar.vue"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T006) — **CRITICAL, blocks all stories**
3. Complete Phase 3: User Story 1 (T007–T013)
4. **STOP and VALIDATE**: Run quickstart.md §US1 — camera opens, photo attaches, thumbnail appears, survives reload
5. Demo the core value proposition before proceeding

### Incremental Delivery

1. Setup + Foundational (Phase 1–2) → infrastructure ready
2. US1 (Phase 3) → user can capture and attach photos → **MVP demo**
3. US2 (Phase 4) → images persist across restarts → feature is production-viable
4. US3 (Phase 5) → cancel path is clean → UX polish
5. US4 (Phase 6) → error handling complete → feature is production-ready
6. Polish (Phase 7) → non-regression verified → ready to merge

### Camera vs. File Upload Note

All four user stories are served by a single `<input type="file" accept="image/*" capture="environment">` element (Decision 6 from research.md):
- **Mobile browsers**: `capture="environment"` opens the rear camera directly
- **Desktop browsers**: `capture="environment"` is ignored; standard file picker opens instead
- No additional camera library or `getUserMedia()` integration is needed — this is the browser-native approach and covers both capture and file upload in one element

---

## Notes

- [P] tasks = different files, no unmet dependencies — safe to implement simultaneously
- [Story] label maps each task to a specific user story for traceability
- All backend changes are additive to `backend/main.py` — no new Python files
- All frontend changes are additive to `frontend/src/components/LifetimeCalendar.vue` — no new Vue files
- All SQL uses `?` parameterized placeholders — never string interpolation (security requirement)
- `GET /api/calendar` is NOT modified — zero risk of calendar regression
- Commit after each phase or logical group; validate each story checkpoint before proceeding
