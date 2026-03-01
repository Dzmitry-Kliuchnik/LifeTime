# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Frontend

```bash
cd frontend
npm install
npm run dev       # dev server at http://localhost:5173
npm run build     # production build → dist/
npm run preview   # serve dist/ locally
```

Node.js requirement: `^20.19.0 || >=22.12.0` (enforced in `package.json`).

## Source Structure

```
frontend/src/
├── main.js                        # App entry — mounts App.vue, imports main.css
├── App.vue                        # Shell: theme system + view routing
├── components/
│   ├── LifetimeCalendar.vue       # Main calendar grid + week modal
│   └── UserSettings.vue           # Settings modal (birthdate / life expectancy)
└── assets/
    ├── design-system.css          # CSS custom properties (design tokens)
    ├── base.css                   # CSS reset + base element styles
    └── main.css                   # App-level layout; imports base.css
```

`design-system.css` is imported by `base.css` which is imported by `main.css` which is imported by `main.js` — so all CSS variables are globally available.
The `@` alias resolves to `frontend/src/` (configured in `vite.config.js`).

## API Base URL

`const API_BASE = 'http://localhost:8000'` is **hardcoded in all three component files**:
- `src/App.vue:7`
- `src/components/UserSettings.vue:11`
- `src/components/LifetimeCalendar.vue:9`

If the backend port or host changes, update all three.

## App.vue — Shell and Theme System

**View routing** (no Vue Router — simple `v-if` logic):
- `isLoading` → skeleton loading state
- `showSettings` → renders `<UserSettings>` modal
- `userData` set and `!showSettings` → renders `<LifetimeCalendar>`

On mount: calls `GET /api/user`. If response is `null` or errors, sets `showSettings = true`.

**Theme system** (`darkMode` ref, `data-theme` attribute on `<html>`):
- On mount: reads `localStorage.getItem('lifetime-calendar-theme')`. If absent, reads `prefers-color-scheme` and saves the result.
- `toggleTheme()` flips `darkMode`, writes to localStorage, sets `document.documentElement.setAttribute('data-theme', 'dark'|'light')`.
- System theme changes (`matchMedia.addEventListener('change', ...)`) only apply when no manual preference is stored (i.e., localStorage value is absent or `'system'`).
- CSS picks up `[data-theme="dark"]` or `[data-theme="light"]` selectors defined in `design-system.css`.

**Events from children:**
- `UserSettings` emits `user-saved` with `{ birthdate, life_expectancy }` → `handleUserSaved()` stores in `userData` ref and hides settings.
- `UserSettings` emits `close` → `showSettings = false`.

## LifetimeCalendar.vue — Calendar Grid and Week Modal

### State

```js
calendarData   // { total_weeks, lived_weeks, current_week, weeks: [...] }
isLoading      // boolean
error          // string
selectedWeek   // week object currently open in modal
showWeekModal  // boolean
weekNote       // string — v-model of textarea in modal

// Voice recording
isRecording       // boolean
isTranscribing    // boolean
recordingError    // string
mediaRecorder     // MediaRecorder instance
audioChunks       // Blob[]
recordingDuration // seconds (updated by setInterval)
recordingTimer    // interval ID
```

### Calendar Data Loading

`loadCalendarData()` calls `GET /api/calendar` and stores the response in `calendarData`. Called on `onMounted`.

### Grid Rendering

The weeks grid is a CSS `grid-template-columns: repeat(52, 1fr)` — 52 columns, one per week, rows implicitly represent years of life.

Each `<div class="week-box">` gets classes from `getWeekClass(week)`:
- `lived` — `week.is_lived === true`
- `current` — `week.is_current === true`
- `has-note` — `week.note` is truthy
- `year-start` — `week.week_of_year === 1` (ISO week 1 = first week of a calendar year)

`--week-box-size` CSS custom property is set inline on `.calendar-grid` to `max(8px, min(1.2vw, 12px))`, scaling with viewport while clamped to readable sizes.

### Year Labels

`getYearLabels()` computes one label per row of 52 life-weeks. For each group of 52 sequential weeks it finds the **dominant calendar year** (most weeks belonging to that year) and returns `{ year, rowIndex }`. Labels are rendered in `.year-labels` as a flex column alongside the weeks grid.

### Week Modal

Opened by `openWeekModal(week)`: copies `week.note` into the `weekNote` ref.

`saveWeekNote()` sends `POST /api/week-note` with:
```js
{
  week_number: selectedWeek.week_of_year,  // ISO week-of-year (NOT sequential week_number)
  year: selectedWeek.year,
  note: weekNote,
  is_lived: selectedWeek.is_lived
}
```
After a successful save it also patches `calendarData.weeks[idx].note` in place so the grid re-renders without a full reload.

The modal is rendered via `<Teleport to="body">` to escape stacking context issues.

### Voice Recording Flow

State machine: idle → recording → transcribing → idle

1. **`startRecording()`**: calls `navigator.mediaDevices.getUserMedia({ audio: true })`, creates `MediaRecorder` with `mimeType: 'audio/webm'`, pushes chunks to `audioChunks` on `ondataavailable`. Starts a 1-second `setInterval` updating `recordingDuration`.
2. **`stopRecording()`**: calls `mediaRecorder.stop()`. The `onstop` handler fires, assembles `audioChunks` into a Blob, calls `transcribeAudio(blob)`, then stops all stream tracks.
3. **`transcribeAudio(audioBlob)`**: builds `FormData` and POSTs to `POST /api/week-note/voice`:
   ```
   week_number  = selectedWeek.week_of_year
   year         = selectedWeek.year
   is_lived     = selectedWeek.is_lived
   existing_note = weekNote (current textarea value)
   audio        = audioBlob  (filename: "recording.webm")
   ```
   On success, sets `weekNote` to `response.data.combined_note` (the backend-assembled text) and patches the week in `calendarData`.

Voice controls in the modal template use `v-if` to switch between three states: idle (`btn-voice`), recording (`btn-recording` with pulse animation), and transcribing (spinner indicator).

## UserSettings.vue — Settings Modal

Props: `userData` (Object, nullable — pre-fills form if editing).
Emits: `user-saved` (with `{ birthdate, life_expectancy }`), `close`.

Rendered via `<Teleport to="body">`.

Client-side validation before POST:
- `birthdate` must be non-empty
- `birthdate` must not be in the future

On successful `POST /api/user`, emits `user-saved` so `App.vue` updates its `userData` ref and hides the modal.

## Design System (`assets/design-system.css`)

All styling uses CSS custom properties (no Tailwind, no CSS-in-JS). Key categories:

| Variable group | Examples |
|---|---|
| `--color-primary-*` | 50–950 scale, sky-blue palette |
| `--color-success-*` | green — used for lived weeks |
| `--color-warning-*` | amber — used for current week |
| `--color-error-*` | red — used for errors |
| `--color-neutral-*` | gray scale |
| `--color-text-*` | `primary`, `secondary`, `tertiary`, `inverse` |
| `--color-background*` | `background`, `background-secondary`, `background-tertiary` |
| `--color-surface` | card/modal background |
| `--color-border` | borders |
| `--glass-bg/border/blur` | glassmorphism values |
| `--space-{1–32}` | spacing scale (0.25rem steps) |
| `--radius-{sm–full}` | border-radius scale |
| `--shadow-{sm–2xl}` | box-shadow scale |
| `--duration-{fast/normal/slow}` | 150ms / 250ms / 350ms |
| `--ease-{in/out/in-out}` | cubic-bezier curves |
| `--font-size-{xs–5xl}` | type scale |
| `--font-weight-{normal–bold}` | 400 / 500 / 600 / 700 |

**Theme switching**: `:root` defines light-mode defaults. `[data-theme="dark"]` and `[data-theme="light"]` override the semantic tokens (`--color-background`, `--color-surface`, `--color-text-*`, `--glass-*`, `--shadow-*`). The accent palette (`--color-primary-*`, `--color-success-*`, etc.) is theme-invariant.

**Reduced motion**: `@media (prefers-reduced-motion: reduce)` sets all duration variables to `0s`, effectively disabling transitions and animations globally.

## Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| `>768px` | default desktop layout |
| `≤768px` | 2-column stats grid, smaller week boxes (`--week-box-size: max(6px, min(1vw, 10px))`), modal footer stacks vertically |
| `≤480px` | 1-column stats grid, smallest week boxes (`max(4px, min(0.8vw, 6px))`) |

## Dependencies

| Package | Role |
|---|---|
| `vue@^3.5` | UI framework (Composition API, `<script setup>`) |
| `axios@^1.12` | HTTP client for all API calls |
| `vite@^7` | Build tool and dev server |
| `@vitejs/plugin-vue@^6` | Vue SFC transform |
| `vite-plugin-vue-devtools@^8` | Browser devtools panel (dev only) |

No Pinia, no Vue Router, no component library. All state is local `ref`/`reactive` within components.

## Best Practices

### Vue 3 Composition API

**Extract reusable logic into composables.**
Repeated patterns — API calls, loading/error state, the voice recording state machine — belong in `src/composables/` functions prefixed with `use`. This keeps components focused on rendering and makes logic independently testable:
```js
// src/composables/useCalendarData.js
export function useCalendarData() {
  const data = ref(null)
  const isLoading = ref(false)
  const error = ref('')
  const load = async () => { ... }
  return { data, isLoading, error, load }
}
```

**Use `computed()` for derived values, not methods.**
Values derived from reactive state — e.g., the progress percentage in the stats cards — should be `computed` refs. They cache and only recompute when dependencies change, unlike methods which recalculate on every render:
```js
// Prefer this:
const lifePercent = computed(() =>
  Math.round((calendarData.value.lived_weeks / calendarData.value.total_weeks) * 100)
)
// Over repeating the expression inline in the template
```

**Always clean up side effects in `onUnmounted`.**
`LifetimeCalendar.vue` uses `setInterval` for the recording timer and `App.vue` attaches a `matchMedia` listener. Both must be cleared when the component unmounts, otherwise they accumulate across hot-reloads and cause memory leaks:
```js
onUnmounted(() => {
  clearInterval(recordingTimer.value)
  mediaQuery.removeEventListener('change', handleSystemThemeChange)
})
```
The current `window.addEventListener('beforeunload', cleanup)` in `App.vue` is a workaround — `onUnmounted` is the correct Vue lifecycle hook for this.

**Declare `defineProps` and `defineEmits` with explicit types.**
Untyped props offer no IDE assistance and no runtime warnings. Use the type-literal syntax (no runtime import needed in `<script setup>`):
```js
const props = defineProps({
  userData: { type: Object, default: null }
})
const emit = defineEmits(['user-saved', 'close'])
```

**Prefer `shallowRef` for large external data objects.**
`calendarData` holds thousands of week objects. Using `ref()` makes Vue deeply reactive over the entire structure on every assignment. Use `shallowRef` so Vue only tracks the top-level reference, and trigger re-renders by replacing the value:
```js
const calendarData = shallowRef(null)
// Patch: replace the array reference instead of mutating
calendarData.value = {
  ...calendarData.value,
  weeks: calendarData.value.weeks.map((w, i) => i === weekIndex ? { ...w, note } : w)
}
```

**Use `v-memo` on the calendar grid for performance.**
With potentially 4000+ week boxes, each re-render is expensive. `v-memo` skips VDOM diffing for a list item when its tracked values haven't changed:
```html
<div
  v-for="week in calendarData.weeks"
  v-memo="[week.is_lived, week.is_current, week.note]"
  :key="week.week_number"
  ...
>
```

**Keep template expressions simple — move logic to `<script setup>`.**
Expressions like `Math.round((calendarData.lived_weeks / calendarData.total_weeks) * 100)` appear multiple times in the template. Define them once as named `computed` refs. Complex ternaries and method chains in templates are hard to read and can't be unit tested.

**`v-if` vs `v-show`**: use `v-if` for conditions that are rarely toggled (the three main view states in `App.vue`), and `v-show` for elements that toggle frequently (e.g., the voice recording controls in the modal) to avoid repeated mount/unmount costs.

### Axios

**Create a shared Axios instance instead of hardcoding `API_BASE` in every component.**
A single instance configured with `baseURL` and default headers centralises the API contract:
```js
// src/api/client.js
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? 'http://localhost:8000',
  timeout: 15_000,
})
```
Import `api` instead of `axios` in components. This is the only file that needs to change if the backend URL changes.

**Add a response interceptor for global error handling.**
Rather than a `catch` block in every component, intercept errors centrally:
```js
api.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.detail ?? error.message
    console.error('[API]', message)
    return Promise.reject(error)
  }
)
```
Components still need their own `catch` to update local `error` refs, but they no longer need to extract the error message.

**Cancel in-flight requests when the component unmounts.**
`loadCalendarData()` is called on mount. If the component unmounts before the request resolves (e.g., the user navigates away), the response callback tries to update an unmounted component's state. Use `AbortController`:
```js
let abortController = null

const loadCalendarData = async () => {
  abortController?.abort()
  abortController = new AbortController()
  try {
    const response = await api.get('/api/calendar', { signal: abortController.signal })
    calendarData.value = response.data
  } catch (err) {
    if (axios.isCancel(err)) return
    error.value = 'Failed to load calendar data.'
  }
}

onUnmounted(() => abortController?.abort())
```

### Vite and Environment Variables

**Use `import.meta.env.VITE_*` for all environment-specific values.**
Never hardcode URLs, API keys, or feature flags in source files. Create:
```
# .env (local defaults, not committed)
VITE_API_BASE=http://localhost:8000

# .env.example (committed, documents required variables)
VITE_API_BASE=http://localhost:8000
```
Only variables prefixed with `VITE_` are exposed to the browser bundle — this is a Vite security boundary.

**Use the `@` alias consistently for all local imports.**
`@` is already configured to resolve to `src/`. Prefer `@/composables/useCalendarData.js` over `../../composables/useCalendarData.js` for any import that crosses more than one directory level.

**Do not import from `node_modules` paths directly.**
Always use package names (`import axios from 'axios'`), not file paths into `node_modules`. Vite handles module resolution and tree-shaking; direct paths break both.

### CSS and Design System

**Always use design tokens, never raw values.**
Every color, spacing, shadow, and timing value in this codebase has a corresponding CSS custom property in `design-system.css`. Using raw values like `#22c55e` or `12px` directly in component styles bypasses the theme system and breaks dark mode:
```css
/* Correct */
color: var(--color-success-600);
padding: var(--space-3);

/* Wrong — not theme-aware, breaks dark mode */
color: #22c55e;
padding: 12px;
```

**Prefer semantic tokens over palette tokens in component styles.**
Use `--color-text-primary` rather than `--color-neutral-900`. Semantic tokens automatically resolve to the correct shade in both light and dark themes; palette tokens are fixed values:
```css
/* Correct — adapts to theme */
color: var(--color-text-secondary);

/* Avoid — always neutral-600, looks wrong in dark mode */
color: var(--color-neutral-600);
```

**Keep `<style scoped>` for component-specific styles.**
Do not override scoped styles from a parent using `:deep()`. If a child component needs different styling in different contexts, expose a prop or CSS custom property for it. Deep selectors break component encapsulation and make refactoring fragile.

**Do not add styles for dark mode inside components.**
Theme switching is handled entirely by `[data-theme="dark"]` selectors in `design-system.css` overriding semantic tokens. Component styles should reference tokens only — dark mode adaptation happens automatically. Adding `@media (prefers-color-scheme: dark)` or `[data-theme="dark"]` blocks inside SFC `<style>` sections duplicates and conflicts with that system.

### Accessibility

**All interactive elements must be keyboard-reachable.**
Week boxes already have `tabindex="0"` and `@keydown.enter`/`@keydown.space` handlers — maintain this for any new clickable non-button elements. Use `<button>` elements for actions whenever possible to get keyboard behavior for free.

**Modals must trap focus.**
The current `<Teleport to="body">` modals do not trap focus — pressing Tab can move focus behind the overlay. When adding new modals, implement a focus trap (move focus to the first focusable element on open; prevent Tab from leaving the modal; restore focus to the trigger on close).

**Provide meaningful `aria-label` for icon-only controls.**
The theme toggle and settings buttons already have `aria-label`. Maintain this for any new icon-only button. The label should describe the *action*, not the icon: `"Switch to dark mode"` not `"Moon icon"`.

**Use `role="status"` for loading and error states.**
Wrapping loading text and error messages in `<div role="status" aria-live="polite">` ensures screen readers announce state changes without requiring a focus change.
