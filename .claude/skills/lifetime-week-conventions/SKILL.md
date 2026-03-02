---
name: lifetime-week-conventions
description: Use when reading, writing, or modifying week data fields in the API response or frontend, adding fields to the calendar endpoint, or updating week note logic.
---

# Lifetime Calendar — Week Data Conventions

## Week Object Fields

Each week object from `GET /api/calendar` has:

| Field | Type | Description |
|-------|------|-------------|
| `week_number` | int | Sequential 1–N from birthdate |
| `year` | int | Calendar year |
| `week_of_year` | int | ISO week-of-year |
| `date` | string | ISO date string |
| `is_lived` | bool | Whether the week has passed |
| `is_current` | bool | Whether this is the current week |
| `note` | string | User's text note |

**Notes lookup uses `week_of_year`, not `week_number`.**

## Week Identity Key

Weeks are identified by `(year, week_of_year)` stored as the string `"year-week_of_year"`.
Example: week 3 of 2024 → `"2024-3"`.
The sequential `week_number` is **not** used as a key.

## When Modifying Week Structure

If you add or rename a field in the `/api/calendar` response, you must update **both** places atomically:

1. Update `week_data` dict inside `get_calendar_data()` in `backend/main.py`
2. Update usage in `frontend/src/components/LifetimeCalendar.vue`

**Additive changes** (new fields) are safe — the frontend won't break.
**Renaming or removing** fields requires updating both sides at the same time.

## CSS Conventions

- Component-scoped styles with `<style scoped>`
- Shared design tokens in `assets/design-system.css` (CSS custom properties)
- Responsive breakpoints: `768px` (tablet), `480px` (mobile)
