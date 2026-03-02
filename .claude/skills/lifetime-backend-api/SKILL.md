---
name: lifetime-backend-api
description: Use when implementing, modifying, or debugging API endpoints in the Lifetime Calendar backend — including calendar data building, week note upsert, voice transcription flow, or understanding what each endpoint accepts and returns.
---

# Lifetime Calendar — Backend API Reference

All endpoints live in `backend/main.py`. CORS is `allow_origins=["*"]` (permissive for local dev).

## `GET /api/user`

Returns `{ birthdate, life_expectancy }` or `null` (not 404) if no user row exists.
Fetches the most recently created row via `ORDER BY created_at DESC LIMIT 1`.

## `POST /api/user`

Body: `UserData`.
**Deletes all rows** from `user_data`, then inserts fresh — enforces single-user mode.

## `GET /api/calendar`

Calls `get_user_data()` internally (returns 404 if no user).
Builds the week list by iterating from `birthdate` in 7-day steps:

```python
# For each week:
week_data = {
    "week_number": week_num,          # sequential 1 to total_weeks
    "year": current_week_date.year,
    "week_of_year": current_week_date.isocalendar()[1],  # ISO week
    "date": current_week_date.isoformat(),
    "is_lived": week_num <= lived_weeks,
    "is_current": week_num == current_week,
    "note": notes_dict.get(week_key, {}).get("note", ""),
}
```

Notes lookup: `week_key = f"{year}-{week_of_year}"`.

Calculated fields:
- `total_weeks = life_expectancy * 52`
- `lived_weeks = int((now - birthdate).days / 7)`
- `current_week = lived_weeks + 1`

To add a field: edit the `week_data` dict inside `get_calendar_data()` (`main.py:224`) **and** update `LifetimeCalendar.vue`.

## `POST /api/week-note`

Body: `WeekNote`.
Upsert: checks for existing row by `(week_number, year)` — where `week_number` is ISO week-of-year. Updates if exists, inserts if not.

## `POST /api/transcribe-voice`

Multipart form with `audio` file.
Saves to temp dir (`tempfile.mkdtemp()` at startup), calls `transcribe_audio_with_whisper()`, cleans up.
Returns `VoiceTranscriptionResponse`.

Without `OPENAI_API_KEY`: returns `[Mock Transcription]` placeholder — no exception raised.

## `POST /api/week-note/voice`

Multipart form fields: `week_number`, `year`, `is_lived`, `existing_note` (optional), `audio` file.

Flow:
1. Calls `transcribe_voice()` internally → transcription string
2. Appends as `\n\n[Voice Note]: {transcribed_text}` to `existing_note`
3. Saves combined note via `save_week_note()`
4. Returns `{ message, transcription, combined_note }`

## Voice Transcription (`main.py:86`)

```python
transcribe_audio_with_whisper(audio_file_path)
```
- Requires `openai` package
- Reads `OPENAI_API_KEY` from environment
- Uses `openai.OpenAI(api_key=...).audio.transcriptions.create(model="whisper-1")`
- Falls back to mock string when key is absent — no exception propagated

To enable: `export OPENAI_API_KEY=sk-...` before starting the server.
