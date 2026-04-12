# Seconds Remaining Stat Card — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a live-ticking "Seconds Remaining" stat card to the calendar stats grid, showing days/hours/minutes/seconds formatted countdown until the user's life expectancy date.

**Architecture:** Pure frontend change to `LifetimeCalendar.vue`. Compute end date from `props.userData.birthdate + props.userData.life_expectancy years`, drive a `secondsRemaining` ref with `setInterval` every 1000ms, display as `Dd Hh Mm Ss`. Clean up interval in `onUnmounted`.

**Tech Stack:** Vue 3 `<script setup>`, `computed`, `onMounted`, `onUnmounted`, CSS custom properties from `frontend/src/assets/design-system.css`

---

### Task 1: Add countdown state and lifecycle to the script

**File:**
- Modify: `frontend/src/components/LifetimeCalendar.vue:2` (imports line)
- Modify: `frontend/src/components/LifetimeCalendar.vue:273` (onMounted block)

**Step 1: Update the Vue import to add `onUnmounted` and `computed`**

Current line 2:
```js
import { ref, onMounted, defineProps } from 'vue'
```

Replace with:
```js
import { ref, computed, onMounted, onUnmounted, defineProps } from 'vue'
```

**Step 2: Add two new refs after the existing `error` ref (around line 14)**

After:
```js
const error = ref('')
```

Add:
```js
const secondsRemaining = ref(0)
const countdownTimer = ref(null)
```

**Step 3: Add the `computeSecondsRemaining` helper after the `loadCalendarData` function**

After the closing `}` of `loadCalendarData` (around line 41), add:
```js
const computeSecondsRemaining = () => {
  if (!props.userData?.birthdate || !props.userData?.life_expectancy) return
  const endDate = new Date(props.userData.birthdate)
  endDate.setFullYear(endDate.getFullYear() + props.userData.life_expectancy)
  secondsRemaining.value = Math.max(0, Math.floor((endDate - Date.now()) / 1000))
}
```

**Step 4: Add the `formattedCountdown` computed after `computeSecondsRemaining`**

```js
const formattedCountdown = computed(() => {
  const s = secondsRemaining.value
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${d.toLocaleString()}d ${h}h ${String(m).padStart(2, '0')}m ${String(sec).padStart(2, '0')}s`
})
```

**Step 5: Update `onMounted` to start the countdown**

Current `onMounted` block (around line 273):
```js
onMounted(() => {
  loadCalendarData()
})
```

Replace with:
```js
onMounted(() => {
  loadCalendarData()
  computeSecondsRemaining()
  countdownTimer.value = setInterval(computeSecondsRemaining, 1000)
})
```

**Step 6: Add `onUnmounted` cleanup directly after the `onMounted` block**

```js
onUnmounted(() => {
  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
  }
})
```

**Step 7: Verify the script changes manually**

Open the browser at `http://localhost:5173`. Open DevTools console. The page should load without errors. `secondsRemaining` is not yet visible in the UI — that's expected, the template change comes next.

---

### Task 2: Add the seconds stat card to the template

**File:**
- Modify: `frontend/src/components/LifetimeCalendar.vue` — template section, stats-grid

**Step 1: Locate the end of the stats grid**

Find the closing `</div>` of the `years-card` (around line 370) and the closing `</div>` of `.stats-grid` (line 371). It looks like:

```html
        <div class="stat-card glass-card years-card">
          <div class="stat-content">
            <div class="stat-icon years-icon">
              ...SVG...
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ Math.floor(calendarData.total_weeks / 52) }}</div>
              <div class="stat-label">Total Years</div>
            </div>
          </div>
        </div>
      </div>
```

**Step 2: Insert the new card between the `years-card` closing `</div>` and the `.stats-grid` closing `</div>`**

```html
        <div class="stat-card glass-card seconds-card">
          <div class="stat-content">
            <div class="stat-icon seconds-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
                <polyline points="12 7 12 12 15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value seconds-value">{{ formattedCountdown }}</div>
              <div class="stat-label">Seconds Remaining</div>
            </div>
          </div>
          <div class="stat-progress">
            <div class="progress-bar seconds-progress" :style="{ width: `${Math.round(((calendarData.total_weeks - calendarData.lived_weeks) / calendarData.total_weeks) * 100)}%` }"></div>
          </div>
        </div>
```

**Step 3: Verify in browser**

Reload `http://localhost:5173`. The stats grid should now show 5 cards. The 5th card displays the formatted countdown and it ticks every second. Confirm days / hours / minutes / seconds all update correctly by watching for the seconds digit to change.

---

### Task 3: Add CSS for the new card

**File:**
- Modify: `frontend/src/components/LifetimeCalendar.vue` — `<style>` section

**Step 1: Add icon background color after the `.years-icon` rule (around line 693)**

After:
```css
.years-icon {
  background: linear-gradient(135deg, var(--color-neutral-600), var(--color-neutral-700));
  color: white;
}
```

Add:
```css
.seconds-icon {
  background: linear-gradient(135deg, var(--color-error-500), var(--color-error-600));
  color: white;
}
```

**Step 2: Add font size override for the seconds value after the `.stat-value` rule (around line 706)**

After the `.stat-label` block (around line 714), add:
```css
.seconds-value {
  font-size: var(--font-size-xl);
}
```

This prevents the 20-character formatted string from overflowing the card on smaller viewports.

**Step 3: Add progress bar gradient for seconds after `.remaining-progress` (around line 732)**

After:
```css
.remaining-progress {
  background: linear-gradient(90deg, var(--color-warning-500), var(--color-warning-600));
}
```

Add:
```css
.seconds-progress {
  background: linear-gradient(90deg, var(--color-error-500), var(--color-error-600));
}
```

**Step 4: Add hover animation after the `.years-card:hover .years-icon` rule (around line 752)**

After:
```css
.years-card:hover .years-icon {
  transform: scale(1.1) rotate(-5deg);
}
```

Add:
```css
.seconds-card:hover .seconds-icon {
  transform: scale(1.1) rotate(5deg);
}
```

**Step 5: Final verification in browser**

1. Reload `http://localhost:5173`
2. Confirm the 5th card has a red icon, the countdown ticks every second
3. Open DevTools → check no console errors
4. Resize the browser window to confirm the grid reflows correctly at mobile widths (≤768px and ≤480px)
5. Leave the tab open for ~10 seconds and confirm the seconds digit visibly decrements
