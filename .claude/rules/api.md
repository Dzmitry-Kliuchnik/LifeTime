---
description: Backend API endpoints and their purpose
---

# API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/user` | Get stored birthdate + life expectancy |
| POST | `/api/user` | Save birthdate + life expectancy (replaces existing) |
| GET | `/api/calendar` | Get full week grid (requires user data saved first) |
| POST | `/api/week-note` | Upsert a note for a specific week |
| POST | `/api/transcribe-voice` | Transcribe audio via Whisper |
| POST | `/api/week-note/voice` | Transcribe audio and append to week note |
