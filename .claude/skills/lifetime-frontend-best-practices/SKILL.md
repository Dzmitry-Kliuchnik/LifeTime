---
name: lifetime-frontend-best-practices
description: Use when writing or reviewing Vue 3 components, Axios calls, Vite configuration, or CSS in the Lifetime Calendar frontend — composables, reactivity, request cancellation, env vars, and performance patterns.
---

# Lifetime Calendar — Frontend Best Practices

## Vue 3 Composition API

**Extract reusable logic into composables** (`src/composables/use*.js`):
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

**Use `computed()` for derived values** — caches and only recomputes when dependencies change:
```js
const lifePercent = computed(() =>
  Math.round((calendarData.value.lived_weeks / calendarData.value.total_weeks) * 100)
)
```

**Always clean up side effects in `onUnmounted`**:
```js
onUnmounted(() => {
  clearInterval(recordingTimer.value)
  mediaQuery.removeEventListener('change', handleSystemThemeChange)
})
```

**Declare `defineProps` and `defineEmits` with explicit types**:
```js
const props = defineProps({ userData: { type: Object, default: null } })
const emit = defineEmits(['user-saved', 'close'])
```

**Use `shallowRef` for large external data** (calendarData holds thousands of week objects):
```js
const calendarData = shallowRef(null)
// Patch by replacing the reference, not mutating:
calendarData.value = {
  ...calendarData.value,
  weeks: calendarData.value.weeks.map((w, i) => i === weekIndex ? { ...w, note } : w)
}
```

**Use `v-memo` on the calendar grid** to skip VDOM diffing for unchanged week boxes:
```html
<div
  v-for="week in calendarData.weeks"
  v-memo="[week.is_lived, week.is_current, week.note]"
  :key="week.week_number"
>
```

**`v-if` vs `v-show`**: `v-if` for rarely-toggled conditions (main view states); `v-show` for frequently-toggled elements (voice controls in modal).

**Keep template expressions simple** — move logic to named `computed` refs.

## Axios

**Create a shared Axios instance** instead of hardcoding `API_BASE` in every component:
```js
// src/api/client.js
import axios from 'axios'
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? 'http://localhost:8000',
  timeout: 15_000,
})
```

**Add a response interceptor** for global error extraction:
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

**Cancel in-flight requests on unmount** using `AbortController`:
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

## Vite and Environment Variables

**Use `import.meta.env.VITE_*` for all environment-specific values** — never hardcode URLs in source files:
```
# .env (local defaults, not committed)
VITE_API_BASE=http://localhost:8000

# .env.example (committed, documents required variables)
VITE_API_BASE=http://localhost:8000
```
Only `VITE_*` prefixed variables are exposed to the browser bundle (Vite security boundary).

**Use the `@` alias consistently** (`@` → `src/`) for any import crossing more than one directory level.

## CSS

See `lifetime-design-system` skill for token usage, theme rules, and responsive breakpoints.

Key rules:
- Always use CSS custom properties from `design-system.css`, never raw values
- Prefer semantic tokens (`--color-text-primary`) over palette tokens (`--color-neutral-900`)
- Component styles in `<style scoped>` only — no `:deep()` overrides
- Never add `[data-theme="dark"]` blocks inside SFC `<style>` sections
