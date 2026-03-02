---
name: lifetime-best-practices
description: Use when adding API endpoints, writing SQL queries, handling errors, managing frontend state, or reviewing code for security issues in the Lifetime Calendar app.
---

# Lifetime Calendar — Best Practices

## API Design

- HTTP status codes: `200` reads, `201` resource creation, `204` deletes, `422` validation errors (FastAPI/Pydantic handles 422 automatically)
- Keep request/response shapes **stable** — additive changes (new fields) are safe; renaming/removing requires updating both backend and frontend atomically
- All API inputs validated by Pydantic before reaching handler logic — do **not** add redundant manual type checks inside endpoint functions

## Security

- CORS `allow_origins=["*"]` is intentionally permissive for local dev — restrict to actual frontend origin before exposing on a network
- **Never** interpolate user input directly into SQL strings — all DB calls use parameterized queries (`?` placeholders); maintain this without exception
- `OPENAI_API_KEY` must be supplied via environment variable, never committed to the repo

## Error Handling

- Backend errors surface as `HTTPException` with a `detail` string
- Frontend currently shows errors via `console.error` or `alert` — match this pattern for new features so errors are user-visible
- Frontend Axios calls must always have a `catch` block that sets an error ref — never silently swallow exceptions
- Re-raise `HTTPException` **before** any broad `except` clause (see commit history for this fix)

## Frontend State Consistency

- After a successful `POST /api/week-note`, patch `calendarData.weeks[idx].note` in place rather than refetching the full calendar
- Follow this pattern for any future mutations — patch local state optimistically, refetch only on full reloads
- The single-user model means `POST /api/user` is destructive (deletes all rows) — coordinate carefully if multi-user support is ever added

## Environment Variables

- `API_BASE` is currently a hardcoded string literal in three Vue files
- For any new environment-specific value, use Vite's `import.meta.env.VITE_*` mechanism
- Create a `.env` file with `VITE_API_BASE=http://localhost:8000` and a `.env.example` for documentation
