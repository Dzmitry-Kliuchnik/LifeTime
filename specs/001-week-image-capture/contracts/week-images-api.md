# API Contract: Week Image Endpoints

**Branch**: `001-week-image-capture`
**Date**: 2026-02-28
**Base URL**: `http://localhost:8000` (hardcoded in frontend; migrate to `VITE_API_BASE` per constitution)

---

## 1. Upload Image

**Endpoint**: `POST /api/week-images`
**Content-Type**: `multipart/form-data`

### Request fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `year` | integer (Form) | Yes | Calendar year of the target week (e.g., `2026`) |
| `week_of_year` | integer (Form) | Yes | ISO week-of-year of the target week (1–53) |
| `image` | file (UploadFile) | Yes | Image file; content-type must start with `image/` |

### Success response — 201 Created

```json
{
  "id": 7,
  "url": "/uploads/week-images/a3f2c1d0-1234-5678-abcd-ef0123456789.jpg",
  "filename": "a3f2c1d0-1234-5678-abcd-ef0123456789.jpg",
  "created_at": "2026-02-28T14:32:01"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Database row ID of the new image record |
| `url` | string | Relative URL to serve the image (append to API_BASE for full URL) |
| `filename` | string | UUID-based filename with original extension |
| `created_at` | string | ISO 8601 timestamp of upload |

### Error responses

| HTTP status | `detail` value | When |
|-------------|---------------|------|
| 400 | `"File must be an image"` | Content-type does not start with `image/` |
| 500 | `"Failed to save image: {reason}"` | Disk write or DB insert error |

### Frontend usage

```javascript
const formData = new FormData()
formData.append('year', selectedWeek.value.year)
formData.append('week_of_year', selectedWeek.value.week_of_year)
formData.append('image', file)

const response = await axios.post(`${API_BASE}/api/week-images`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
// response.data → { id, url, filename, created_at }
// Patch local state:
selectedWeekImages.value.push(response.data)
```

---

## 2. List Images for a Week

**Endpoint**: `GET /api/week-images/{year}/{week_of_year}`
**Content-Type**: N/A (GET)

### Path parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | integer | Calendar year (e.g., `2026`) |
| `week_of_year` | integer | ISO week-of-year (1–53) |

### Success response — 200 OK

```json
{
  "images": [
    {
      "id": 7,
      "url": "/uploads/week-images/a3f2c1d0-1234-5678-abcd-ef0123456789.jpg",
      "filename": "a3f2c1d0-1234-5678-abcd-ef0123456789.jpg",
      "created_at": "2026-02-28T14:32:01"
    }
  ]
}
```

Returns an empty list `{ "images": [] }` when no images are attached to the week.
Never returns a 404 for this endpoint — no images is a valid state.

### Error responses

| HTTP status | `detail` value | When |
|-------------|---------------|------|
| 500 | `"Failed to fetch images: {reason}"` | DB query error |

### Frontend usage

```javascript
// Called from openWeekModal()
const response = await axios.get(
  `${API_BASE}/api/week-images/${week.year}/${week.week_of_year}`
)
selectedWeekImages.value = response.data.images
```

---

## 3. Serve Stored Image (Static Route)

**Endpoint**: `GET /uploads/week-images/{filename}`
**Handled by**: FastAPI `StaticFiles` mount (not a custom endpoint)

### Path parameter

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | string | Exact filename returned by the upload endpoint |

### Responses

| HTTP status | Description |
|-------------|-------------|
| 200 | Image binary with appropriate `Content-Type` header |
| 404 | File not found on disk (e.g., manually deleted) |

### Frontend usage

```html
<!-- In week modal thumbnail strip -->
<img
  v-for="img in selectedWeekImages"
  :key="img.id"
  :src="`${API_BASE}${img.url}`"
  alt="Week photo"
  class="week-image-thumb"
/>
```

---

## Contract Change Summary vs. Existing API

| Endpoint | Change type | Impact |
|----------|-------------|--------|
| `POST /api/week-images` | New | Additive |
| `GET /api/week-images/{year}/{woy}` | New | Additive |
| `GET /uploads/week-images/{filename}` | New static mount | Additive |
| `GET /api/calendar` | No change | None |
| `POST /api/week-note` | No change | None |
| `POST /api/week-note/voice` | No change | None |
| `GET /api/user` | No change | None |
| `POST /api/user` | No change | None |
