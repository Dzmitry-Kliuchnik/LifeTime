# Feature Specification: Camera Capture and Persistent Image Attachments to Week Notes

**Feature Branch**: `001-week-image-capture`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "FE/BE: Add Camera Capture and Persistent Image Attachments to Week Notes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture and Attach a Photo to a Week Note (Priority: P1)

A user is editing a week note and wants to attach a visual memory — a photo taken in the
moment or selected from their device. They tap the Camera button in the note editor, the
device camera or file picker opens, they capture or select a photo, and the photo immediately
appears as a thumbnail inside the week note modal. The attachment is linked to that specific
week and persists across app restarts.

**Why this priority**: This is the core value proposition. Without the ability to attach and
persist a photo, no other story delivers value.

**Independent Test**: Can be fully tested by opening any week note, triggering the camera
action, completing the capture flow, and verifying a thumbnail appears and survives a page
reload — no other story needs to be implemented first.

**Acceptance Scenarios**:

1. **Given** a user has a week note modal open, **When** they activate the Camera action,
   **Then** a device camera or file picker interface is presented.
2. **Given** the camera/file picker is open, **When** the user captures or selects a valid
   image, **Then** the image is stored and a thumbnail appears in the week note modal
   without refreshing the full calendar.
3. **Given** a photo has been successfully attached, **When** the user closes and reopens the
   same week note, **Then** the thumbnail is still present and the image is accessible.
4. **Given** a photo has been attached to week 2025-W10, **When** the user opens a different
   week, **Then** the photo does not appear in that week's note.

---

### User Story 2 - View Previously Attached Images on Reopen (Priority: P2)

A user returns to a week they previously annotated with a photo. When they reopen that
week's note modal, they see all previously attached images displayed as thumbnails, giving
them instant visual context alongside any text or voice notes.

**Why this priority**: Without persistent retrieval, the capture story (P1) has no lasting
value. However, capture itself can be verified before implementing the full reopen view,
making this a distinct, independently testable deliverable.

**Independent Test**: Can be tested by attaching a photo (P1 complete), restarting the
application, reopening the same week, and confirming the thumbnails load.

**Acceptance Scenarios**:

1. **Given** a week has one or more images attached from a previous session, **When** the
   user opens that week's note modal, **Then** all previously attached thumbnails are
   displayed.
2. **Given** the app has been fully restarted since images were attached, **When** the user
   opens the relevant week note, **Then** the images are still visible and viewable.

---

### User Story 3 - Cancel Capture Without Side Effects (Priority: P3)

A user accidentally taps the Camera button or decides not to attach a photo after the
picker opens. They dismiss the camera or file picker. Nothing changes — no error appears,
no partial upload occurs, and any existing text or voice note content is unaffected.

**Why this priority**: This is a safety story. The core capture flow (P1) works without it,
but a clean cancel path is required for production readiness.

**Independent Test**: Can be tested by opening the Camera action and then dismissing the
picker; verify the modal state is identical to before the action was triggered.

**Acceptance Scenarios**:

1. **Given** a user has activated the Camera action, **When** they dismiss the picker
   without selecting a file, **Then** no error message is shown and the week note content
   is unchanged.
2. **Given** an existing text note is present in the modal, **When** the user cancels a
   camera capture, **Then** the text note content remains exactly as it was.

---

### User Story 4 - Graceful Error Handling on Upload Failure (Priority: P4)

If an image cannot be saved due to a storage or system error, the user receives a visible,
descriptive error message. Their existing text and voice note content is not lost or altered
as a result of the failure.

**Why this priority**: Error resilience depends on the upload path (P1) existing first, but
is required before the feature is considered complete.

**Independent Test**: Can be tested by simulating a failure condition and verifying that the
error message appears and no note data is lost.

**Acceptance Scenarios**:

1. **Given** an image upload fails, **When** the error is encountered, **Then** a
   user-visible error message is displayed describing the failure.
2. **Given** a text note already exists in the modal, **When** an image upload fails,
   **Then** the text note content is preserved unchanged.
3. **Given** a voice note already exists, **When** an image upload fails, **Then** the
   voice note is preserved unchanged.

---

### Edge Cases

- What happens when the user attaches multiple images to the same week note?
  Multiple thumbnails MUST all appear in the modal; each image is stored and linked
  independently.
- What happens if the stored image file is removed from disk outside the application?
  The thumbnail placeholder is shown or gracefully hidden; the app MUST NOT crash or
  display an unhandled error.
- What happens when a very large image is selected?
  The upload proceeds; no explicit application-level size restriction is imposed
  (the operating system and browser handle size constraints at selection time).
- What happens if the same week has a text note, a voice note, and images?
  All three content types MUST coexist and display correctly in the note modal without
  any content being overwritten or hidden.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The week note editing interface MUST include a Camera action button
  displayed alongside existing note action controls.
- **FR-002**: Users MUST be able to initiate a photo capture or file selection from the
  Camera action on both mobile and desktop browsers without requiring a separate app install.
- **FR-003**: Selected or captured images MUST be stored in persistent local storage linked
  to the application, not in temporary browser memory.
- **FR-004**: System MUST associate each stored image with the specific week it was
  attached to, using the week's year and ISO week number as the identifier.
- **FR-005**: System MUST display a thumbnail of the uploaded image inside the week note
  modal immediately after a successful upload, without a full calendar reload.
- **FR-006**: System MUST persist image metadata so that images survive application
  restarts and remain linked to the correct week.
- **FR-007**: System MUST display thumbnails of all previously attached images when a
  week note modal is opened.
- **FR-008**: System MUST make stored images accessible for display within the application.
- **FR-009**: System MUST show a user-visible error message when image storage fails.
- **FR-010**: System MUST preserve all existing text and voice note content if an image
  upload or storage operation fails.
- **FR-011**: Cancelling the camera or file picker selection MUST produce no error, no
  partial storage, and no change to existing note content.
- **FR-012**: All existing text note save and voice note transcription flows MUST continue
  to function correctly after this feature is introduced.

### Key Entities

- **Week Note**: The existing record for a specific week's annotations. Extended to
  support zero or more image attachments alongside existing text and voice content.
- **Week Image**: A single image attached to a specific week. Attributes: unique
  identifier, association with a week (year + ISO week number), a persistent reference
  to the stored file, and a creation timestamp. A week may have multiple images; each
  image belongs to exactly one week.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the full flow — open camera action, select or capture a
  photo, see the thumbnail — in under 30 seconds on both mobile and desktop browsers.
- **SC-002**: 100% of successfully uploaded images remain viewable after closing and
  reopening the application.
- **SC-003**: Thumbnail preview appears in the week note modal within 3 seconds of a
  successful upload under local network conditions.
- **SC-004**: Cancelling the camera or file picker leaves the week note modal state
  identical to its pre-action state in 100% of attempts.
- **SC-005**: Upload or storage failures produce a user-visible error message in 100% of
  failure cases, with zero loss of existing text or voice note content.
- **SC-006**: All images previously attached to a week display as thumbnails when that
  week note is reopened, in 100% of cases following successful prior uploads.
- **SC-007**: Existing text note save and voice note flows pass manual verification with
  zero regressions after this feature is deployed.

## Assumptions

- Image deletion is out of scope for this feature; users cannot remove attached images
  through the UI in this iteration.
- There is no per-week image count limit; all attached images are stored and displayed.
- The application remains local-first (frontend and backend on the same machine); no
  cloud storage or remote image hosting is required.
- Image format acceptance follows standard browser file input behavior covering all
  common image types; no additional format validation is applied by the application.
- If the application is later wrapped as a native mobile app, platform-level camera and
  filesystem permission handling is a separate, future concern outside this spec's scope.
