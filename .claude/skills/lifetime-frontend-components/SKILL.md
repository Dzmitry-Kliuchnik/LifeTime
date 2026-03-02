---
name: lifetime-frontend-components
description: Use when working on Vue components in the Lifetime Calendar frontend — understanding App.vue theme/routing logic, LifetimeCalendar.vue grid rendering or voice recording state machine, or UserSettings.vue validation flow.
---

# Lifetime Calendar — Frontend Component Reference

## App.vue — Shell and Theme System

### View Routing (no Vue Router — `v-if` only)

| State | What renders |
|-------|-------------|
| `isLoading` | Skeleton loading state |
| `showSettings` | `<UserSettings>` modal |
| `userData` set and `!showSettings` | `<LifetimeCalendar>` |

On mount: calls `GET /api/user`. If response is `null` or errors, sets `showSettings = true`.

### Theme System (`darkMode` ref, `data-theme` on `<html>`)

- Mount: reads `localStorage.getItem('lifetime-calendar-theme')`. If absent, reads `prefers-color-scheme` and saves result.
- `toggleTheme()` flips `darkMode`, writes to localStorage, sets `document.documentElement.setAttribute('data-theme', 'dark'|'light')`.
- System theme changes only apply when no manual preference is stored (localStorage absent or `'system'`).
- CSS picks up `[data-theme="dark"]` / `[data-theme="light"]` selectors in `design-system.css`.

### Child Events

- `UserSettings` emits `user-saved` with `{ birthdate, life_expectancy }` → stores in `userData`, hides settings
- `UserSettings` emits `close` → `showSettings = false`

---

## LifetimeCalendar.vue — Calendar Grid and Week Modal

### State Refs

```js
calendarData   // { total_weeks, lived_weeks, current_week, weeks: [...] }
isLoading / error / selectedWeek / showWeekModal / weekNote

// Voice recording
isRecording / isTranscribing / recordingError
mediaRecorder / audioChunks / recordingDuration / recordingTimer
```

### Grid Rendering

- CSS `grid-template-columns: repeat(52, 1fr)` — 52 columns (weeks), rows = years of life
- `getWeekClass(week)` returns: `lived`, `current`, `has-note`, `year-start` (`week.week_of_year === 1`)
- `--week-box-size` set inline: `max(8px, min(1.2vw, 12px))`

### Year Labels

`getYearLabels()` computes one label per row of 52 life-weeks using the **dominant calendar year** (most weeks in that year). Returns `{ year, rowIndex }` array.

### Week Modal

- `openWeekModal(week)`: copies `week.note` → `weekNote` ref
- `saveWeekNote()` POSTs to `POST /api/week-note`:
  ```js
  {
    week_number: selectedWeek.week_of_year,  // ISO week-of-year, NOT sequential
    year: selectedWeek.year,
    note: weekNote,
    is_lived: selectedWeek.is_lived
  }
  ```
- On success: patches `calendarData.weeks[idx].note` in place (no full reload)
- Rendered via `<Teleport to="body">` to escape stacking context issues

### Voice Recording State Machine

`idle → recording → transcribing → idle`

1. **`startRecording()`**: `getUserMedia({ audio: true })`, creates `MediaRecorder` (`mimeType: 'audio/webm'`), pushes chunks to `audioChunks`. Starts 1s `setInterval` for `recordingDuration`.
2. **`stopRecording()`**: `mediaRecorder.stop()`. `onstop` assembles Blob → calls `transcribeAudio(blob)`, stops stream tracks.
3. **`transcribeAudio(audioBlob)`**: POSTs `FormData` to `POST /api/week-note/voice`:
   ```
   week_number   = selectedWeek.week_of_year
   year          = selectedWeek.year
   is_lived      = selectedWeek.is_lived
   existing_note = weekNote
   audio         = audioBlob  (filename: "recording.webm")
   ```
   On success: sets `weekNote` to `response.data.combined_note`, patches week in `calendarData`.

Voice controls use `v-if` to switch between: idle (`btn-voice`), recording (`btn-recording` + pulse), transcribing (spinner).

---

## UserSettings.vue — Settings Modal

- **Props**: `userData` (Object, nullable — pre-fills form if editing)
- **Emits**: `user-saved` (with `{ birthdate, life_expectancy }`), `close`
- Rendered via `<Teleport to="body">`

Client-side validation before POST:
- `birthdate` must be non-empty
- `birthdate` must not be in the future

On successful `POST /api/user`, emits `user-saved` → `App.vue` updates `userData` ref and hides modal.
