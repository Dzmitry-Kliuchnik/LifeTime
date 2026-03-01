# Quickstart & Manual Verification: Camera Capture and Persistent Image Attachments

**Branch**: `001-week-image-capture`
**Date**: 2026-02-28

---

## Prerequisites

- App is running: `./start.sh` (Linux/macOS) or `start.bat` (Windows)
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- A user profile has been saved (birthdate set), so the calendar grid is visible.
- A test image is available on the device (photo or PNG/JPG file).

---

## User Story 1 — Capture and Attach a Photo (P1)

### Steps

1. Open `http://localhost:5173` in a browser (desktop or mobile).
2. Click any week cell on the calendar grid. The week note modal opens.
3. Locate the **Camera** button in the note modal (next to the voice/microphone button).
4. Click the Camera button.
   - **Desktop**: A file picker dialog opens. Select any image file.
   - **Mobile browser**: The system camera app opens. Take a photo (or pick from gallery).
5. After selecting/capturing, the upload starts automatically.
6. Within 3 seconds, a thumbnail of the uploaded image appears inside the modal.

### Expected outcomes

- [x] No error message appears.
- [x] Thumbnail is visible in the modal immediately.
- [x] A file named `<uuid>.<ext>` appears inside `uploads/week-images/` on disk.
- [x] The image row exists in `week_images` table:
  ```bash
  sqlite3 lifetime_calendar.db "SELECT * FROM week_images ORDER BY id DESC LIMIT 1;"
  ```

---

## User Story 2 — Reopen Week Shows Previously Attached Images (P2)

### Steps (continue from US1)

1. Close the modal (click Cancel or press Escape).
2. Restart the application (stop and restart `start.sh` / `start.bat`).
3. Re-open the same week by clicking the same cell.
4. Observe the week note modal.

### Expected outcomes

- [x] The thumbnail from US1 is visible in the modal on reopen.
- [x] The image file is still accessible at `http://localhost:8000/uploads/week-images/<filename>`.

---

## User Story 3 — Cancel Capture Without Side Effects (P3)

### Steps

1. Open any week note modal.
2. Click the Camera button.
3. Immediately dismiss the file picker (press Escape, click Cancel in the dialog, or
   navigate back on mobile) without selecting any file.

### Expected outcomes

- [x] No error message appears in the modal.
- [x] The modal state is identical to before the Camera button was clicked.
- [x] Any existing text in the note textarea is unchanged.
- [x] No new entry appears in `week_images` table.

---

## User Story 4 — Error Handling on Upload Failure (P4)

### Simulating a failure (development only)

Option A — Make the uploads directory read-only before testing:
```bash
chmod 000 uploads/week-images/   # Linux/macOS
# Restore after test:
chmod 755 uploads/week-images/
```

Option B — Temporarily rename the uploads directory to trigger a path error.

### Steps

1. Apply failure condition above.
2. Open a week note modal and click the Camera button.
3. Select an image file.

### Expected outcomes

- [x] A user-visible error message appears in the modal (e.g., "Failed to upload image...").
- [x] Any existing text note content in the modal is unchanged.
- [x] The app does not crash.
- [x] Restoring the directory and trying again succeeds.

---

## Non-Regression Verification

After all above steps, verify existing flows still work:

1. **Text note save**: Open any week, type a note, click Save Note → note persists on reopen.
2. **Voice note**: Open any week, click Start Voice Note, record a few seconds, stop →
   transcription appears in the note textarea.

---

## API Spot-Checks (optional, via curl or browser)

```bash
# List images for a specific week (replace 2026 and 10 with actual year/woy):
curl http://localhost:8000/api/week-images/2026/10

# Direct image access (replace filename with one from the DB):
curl -I http://localhost:8000/uploads/week-images/<filename>

# Swagger UI (full API exploration):
open http://localhost:8000/docs
```

---

## Cleanup After Testing

To reset image data without dropping other data:
```bash
sqlite3 lifetime_calendar.db "DELETE FROM week_images;"
rm -rf uploads/week-images/*
```
