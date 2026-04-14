import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.schemas import VoiceTranscriptionResponse, WeekNote
from app.services.voice import AUDIO_UPLOAD_DIR, cleanup_temp_file, transcribe_audio_with_whisper

router = APIRouter(prefix="/api")


@router.post("/week-note")
async def save_week_note(week_note: WeekNote):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM week_notes WHERE week_number = ? AND year = ?",
                (week_note.week_number, week_note.year),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE week_notes SET note = ?, is_lived = ? WHERE id = ?",
                    (week_note.note, week_note.is_lived, existing[0]),
                )
            else:
                cursor.execute(
                    "INSERT INTO week_notes (week_number, year, note, is_lived) VALUES (?, ?, ?, ?)",
                    (week_note.week_number, week_note.year, week_note.note, week_note.is_lived),
                )
            conn.commit()
        return {"message": "Week note saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-voice")
async def transcribe_voice(audio: UploadFile = File(...)):
    try:
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        file_id = str(uuid.uuid4())
        file_extension = audio.filename.split(".")[-1] if "." in audio.filename else "webm"
        temp_file_path = os.path.join(AUDIO_UPLOAD_DIR, f"{file_id}.{file_extension}")

        with open(temp_file_path, "wb") as buffer:
            buffer.write(await audio.read())

        try:
            transcription = transcribe_audio_with_whisper(temp_file_path)
            return VoiceTranscriptionResponse(transcription=transcription, success=True)
        except Exception as transcription_error:
            return VoiceTranscriptionResponse(
                transcription="",
                success=False,
                error=f"Transcription failed: {str(transcription_error)}",
            )
        finally:
            cleanup_temp_file(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.post("/week-note/voice")
async def save_week_note_with_voice(
    week_number: int = Form(...),
    year: int = Form(...),
    is_lived: bool = Form(...),
    existing_note: Optional[str] = Form(None),
    audio: UploadFile = File(...),
):
    try:
        print(f"Received request to save voice note for week {week_number}, year {year}")

        file_id = str(uuid.uuid4())
        file_extension = audio.filename.split(".")[-1] if "." in audio.filename else "webm"
        temp_file_path = os.path.join(AUDIO_UPLOAD_DIR, f"{file_id}.{file_extension}")

        with open(temp_file_path, "wb") as buffer:
            buffer.write(await audio.read())

        try:
            transcribed_text = transcribe_audio_with_whisper(temp_file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cleanup_temp_file(temp_file_path)

        if existing_note and existing_note.strip():
            combined_note = f"{existing_note.strip()}\n\n[Voice Note]: {transcribed_text}"
        else:
            combined_note = f"[Voice Note]: {transcribed_text}"

        week_note = WeekNote(
            week_number=week_number,
            year=year,
            note=combined_note,
            is_lived=is_lived,
        )
        await save_week_note(week_note)

        return {
            "message": "Voice note transcribed and saved successfully",
            "transcription": transcribed_text,
            "combined_note": combined_note,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
