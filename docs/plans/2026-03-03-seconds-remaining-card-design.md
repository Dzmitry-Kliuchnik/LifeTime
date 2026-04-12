# Design: Seconds Remaining Stat Card

**Date:** 2026-03-03
**Status:** Approved

## Summary

Add a live-ticking "Seconds Remaining" stat card to the calendar stats grid in `LifetimeCalendar.vue`. The card shows time remaining until the user's life expectancy date, formatted as `Dd Hh Mm Ss`, decrementing every second.

## Requirements

- Live countdown — ticks every second in real time
- Formatted breakdown — displays days, hours, minutes, seconds
- Added as a 5th card alongside the existing 4 stat cards (not replacing "Weeks Remaining")
- No backend changes required

## Approach

Pure frontend. `LifetimeCalendar.vue` already receives `props.userData` (`{birthdate, life_expectancy}`) from `App.vue`. The end date is computed entirely on the frontend.

## Implementation Details

### New State

```js
const secondsRemaining = ref(0)
const countdownTimer = ref(null)
```

### Helper Function

```js
const computeSecondsRemaining = () => {
  const endDate = new Date(props.userData.birthdate)
  endDate.setFullYear(endDate.getFullYear() + props.userData.life_expectancy)
  secondsRemaining.value = Math.max(0, Math.floor((endDate - Date.now()) / 1000))
}
```

### Lifecycle

- `onMounted`: call `computeSecondsRemaining()` once, then start `setInterval` every 1000ms to call it again (keeps in sync with wall clock rather than pure decrement drift)
- `onUnmounted`: `clearInterval(countdownTimer.value)` — prevents memory leak

Add `onUnmounted` to the existing Vue import.

### Computed Display

```js
const formattedCountdown = computed(() => {
  const s = secondsRemaining.value
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${d.toLocaleString()}d ${h}h ${String(m).padStart(2,'0')}m ${String(sec).padStart(2,'0')}s`
})
```

Example output: `21,380d 14h 32m 07s`

### New Stat Card (template)

Appended after the "Total Years" card inside `.stats-grid`:

- **CSS class**: `seconds-card`
- **Icon**: hourglass SVG
- **`stat-value`**: `{{ formattedCountdown }}`
- **`stat-label`**: `Seconds Remaining`
- **Progress bar**: remaining fraction `(total_weeks - lived_weeks) / total_weeks` (reuses existing data, no new API fields)

### Layout Impact

The `.stats-grid` uses `repeat(auto-fit, minmax(280px, 1fr))`. The 5th card reflows naturally:

| Viewport | Layout |
|----------|--------|
| Wide (>1200px) | 5 columns |
| Medium (~768px) | 3+2 or 2+3 |
| `≤768px` breakpoint | `repeat(2, 1fr)` → 2+2+1 |
| `≤480px` breakpoint | `1fr` → 5 stacked |

No CSS changes needed.

## Files Changed

- `frontend/src/components/LifetimeCalendar.vue` — only file modified
  - Script: add `onUnmounted` import, two new refs, `computeSecondsRemaining`, `formattedCountdown` computed, update `onMounted`
  - Template: add 5th stat card
  - CSS: add `.seconds-card` icon color (matching existing pattern)
