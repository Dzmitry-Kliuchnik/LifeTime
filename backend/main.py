import os
import re
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Lifetime Calendar API")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "lifetime_calendar.db"

# Image upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birthdate TEXT NOT NULL,
            life_expectancy INTEGER DEFAULT 80,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS week_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            note TEXT,
            is_lived BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (week_number, year) REFERENCES week_notes(week_number, year)
        )
    """)
    conn.commit()
    conn.close()


# Initialize database on startup
init_db()


# Pydantic models
class UserData(BaseModel):
    birthdate: str
    life_expectancy: int = 80


class WeekNote(BaseModel):
    week_number: int
    year: int
    note: Optional[str] = None
    is_lived: bool = False


class CalendarResponse(BaseModel):
    total_weeks: int
    lived_weeks: int
    current_week: int
    weeks: List[dict]


class VoiceTranscriptionResponse(BaseModel):
    transcription: str
    success: bool
    error: Optional[str] = None


class NoteImage(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    created_at: str


# Temporary directories for audio files
AUDIO_UPLOAD_DIR = tempfile.mkdtemp()


def transcribe_audio_with_whisper(audio_file_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API.
    """
    try:
        import openai

        # Check if file exists and has content
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError("Audio file not found")

        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            return "Empty audio file detected."

        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # For development, return mock transcription if no API key
            return "[Mock Transcription] This is a placeholder transcription. Set OPENAI_API_KEY environment variable to use real Whisper."

        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)

        # Read and transcribe the audio file
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )

        # Return the transcribed text
        return transcript.strip() if transcript else "No speech detected in audio."

    except Exception as e:
        # If there's an error with the OpenAI API, fall back to mock
        if "api_key" in str(e).lower() or "openai" in str(e).lower():
            return "[Mock Transcription] OpenAI API not available. This is a placeholder transcription."
        else:
            raise Exception(f"Transcription failed: {str(e)}")


def cleanup_temp_file(file_path: str):
    """Clean up temporary audio file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not clean up temp file {file_path}: {e}")


@app.get("/")
async def root():
    return {"message": "Lifetime Calendar API"}


@app.post("/api/user")
async def save_user_data(user_data: UserData):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete existing user data (assuming single user for now)
        cursor.execute("DELETE FROM user_data")

        # Insert new user data
        cursor.execute(
            "INSERT INTO user_data (birthdate, life_expectancy) VALUES (?, ?)",
            (user_data.birthdate, user_data.life_expectancy),
        )
        conn.commit()
        conn.close()

        return {"message": "User data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user")
async def get_user_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT birthdate, life_expectancy FROM user_data ORDER BY created_at DESC LIMIT 1"
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            return {"birthdate": result[0], "life_expectancy": result[1]}
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar")
async def get_calendar_data():
    try:
        # Get user data first
        user_data = await get_user_data()
        if not user_data:
            raise HTTPException(
                status_code=404,
                detail="User data not found. Please set your birthdate first.",
            )

        birthdate = datetime.fromisoformat(user_data["birthdate"])
        life_expectancy = user_data["life_expectancy"]

        # Calculate weeks
        total_weeks = life_expectancy * 52
        current_date = datetime.now()

        # Calculate lived weeks
        lived_weeks = int((current_date - birthdate).days / 7)

        # Calculate current week of life
        current_week = lived_weeks + 1

        # Get week notes from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT week_number, year, note, is_lived FROM week_notes")
        notes_data = cursor.fetchall()
        
        # Get all images for notes
        cursor.execute("""
            SELECT week_number, year, id, filename, original_filename, 
                   file_size, mime_type, created_at 
            FROM note_images 
            ORDER BY created_at ASC
        """)
        images_data = cursor.fetchall()
        conn.close()

        # Create weeks data structure
        weeks = []
        notes_dict = {}
        images_dict = {}

        # Convert notes to dictionary for quick lookup
        for note_data in notes_data:
            week_key = f"{note_data[1]}-{note_data[0]}"  # year-week_number
            notes_dict[week_key] = {"note": note_data[2], "is_lived": note_data[3]}
        
        # Convert images to dictionary grouped by week
        for img_data in images_data:
            week_key = f"{img_data[1]}-{img_data[0]}"  # year-week_number
            if week_key not in images_dict:
                images_dict[week_key] = []
            images_dict[week_key].append({
                "id": img_data[2],
                "filename": img_data[3],
                "original_filename": img_data[4],
                "file_size": img_data[5],
                "mime_type": img_data[6],
                "created_at": img_data[7]
            })

        # Generate weeks data
        current_week_date = birthdate
        for week_num in range(1, total_weeks + 1):
            year = current_week_date.year
            week_of_year = current_week_date.isocalendar()[1]
            week_key = f"{year}-{week_of_year}"

            week_data = {
                "week_number": week_num,
                "year": year,
                "week_of_year": week_of_year,
                "date": current_week_date.isoformat(),
                "is_lived": week_num <= lived_weeks,
                "is_current": week_num == current_week,
                "note": notes_dict.get(week_key, {}).get("note", ""),
                "images": images_dict.get(week_key, [])
            }

            weeks.append(week_data)
            current_week_date += timedelta(days=7)

        return CalendarResponse(
            total_weeks=total_weeks,
            lived_weeks=lived_weeks,
            current_week=current_week,
            weeks=weeks,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/week-note")
async def save_week_note(week_note: WeekNote):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if note exists
        cursor.execute(
            "SELECT id FROM week_notes WHERE week_number = ? AND year = ?",
            (week_note.week_number, week_note.year),
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing note
            cursor.execute(
                "UPDATE week_notes SET note = ?, is_lived = ? WHERE id = ?",
                (week_note.note, week_note.is_lived, existing[0]),
            )
        else:
            # Insert new note
            cursor.execute(
                "INSERT INTO week_notes (week_number, year, note, is_lived) VALUES (?, ?, ?, ?)",
                (
                    week_note.week_number,
                    week_note.year,
                    week_note.note,
                    week_note.is_lived,
                ),
            )

        conn.commit()
        conn.close()

        return {"message": "Week note saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe-voice")
async def transcribe_voice(audio: UploadFile = File(...)):
    """
    Transcribe audio file using OpenAI Whisper and return the transcription text.
    """
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = (
            audio.filename.split(".")[-1] if "." in audio.filename else "webm"
        )
        temp_file_path = os.path.join(AUDIO_UPLOAD_DIR, f"{file_id}.{file_extension}")

        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)

        # Transcribe audio
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
            # Clean up temporary file
            cleanup_temp_file(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/api/week-note/voice")
async def save_week_note_with_voice(
    week_number: int = Form(...),
    year: int = Form(...),
    is_lived: bool = Form(...),
    existing_note: Optional[str] = Form(None),
    audio: UploadFile = File(...),
):
    """
    Transcribe voice recording and append to existing week note.
    """
    try:
        print(
            f"Received request to save voice note for week {week_number}, year {year}"
        )
        # First transcribe the audio
        transcribe_response = await transcribe_voice(audio)

        if not transcribe_response.success:
            raise HTTPException(status_code=400, detail=transcribe_response.error)

        # Combine existing note with transcription
        transcribed_text = transcribe_response.transcription.strip()

        if existing_note and existing_note.strip():
            combined_note = (
                f"{existing_note.strip()}\n\n[Voice Note]: {transcribed_text}"
            )
        else:
            combined_note = f"[Voice Note]: {transcribed_text}"

        # Create WeekNote object and save
        week_note = WeekNote(
            week_number=week_number, year=year, note=combined_note, is_lived=is_lived
        )

        # Save using existing function
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


@app.post("/api/week-note/image")
async def upload_image(
    week_number: int = Form(...),
    year: int = Form(...),
    image: UploadFile = File(...)
):
    """
    Upload an image for a specific week note.
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file extension
        file_ext = Path(image.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content to check size
        content = await image.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {MAX_IMAGE_SIZE / (1024 * 1024):.1f}MB"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Save metadata to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO note_images 
            (week_number, year, filename, original_filename, file_size, mime_type) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            week_number, 
            year, 
            filename, 
            image.filename, 
            len(content), 
            image.content_type
        ))
        image_id = cursor.lastrowid
        conn.commit()
        
        # Get the created timestamp
        cursor.execute("SELECT created_at FROM note_images WHERE id = ?", (image_id,))
        created_at = cursor.fetchone()[0]
        conn.close()
        
        return {
            "message": "Image uploaded successfully",
            "image": {
                "id": image_id,
                "filename": filename,
                "original_filename": image.filename,
                "file_size": len(content),
                "mime_type": image.content_type,
                "created_at": created_at
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/api/images/{filename}")
async def get_image(filename: str):
    """
    Serve an uploaded image file.
    """
    try:
        # Validate filename to prevent path traversal attacks
        # Only allow alphanumeric, dash, underscore and dot characters
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = UPLOAD_DIR / filename
        
        # Verify the resolved path is within UPLOAD_DIR
        try:
            file_path_resolved = file_path.resolve()
            upload_dir_resolved = UPLOAD_DIR.resolve()
            if not str(file_path_resolved).startswith(str(upload_dir_resolved)):
                raise HTTPException(status_code=403, detail="Access denied")
        except (OSError, RuntimeError):
            raise HTTPException(status_code=400, detail="Invalid path")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        return FileResponse(file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.delete("/api/images/{image_id}")
async def delete_image(image_id: int):
    """
    Delete an image by ID.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get image info
        cursor.execute("SELECT filename FROM note_images WHERE id = ?", (image_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail="Image not found")
        
        filename = result[0]
        
        # Validate filename before deletion (security check)
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid filename in database")
        
        if '..' in filename or '/' in filename or '\\' in filename:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid filename in database")
        
        # Delete from database
        cursor.execute("DELETE FROM note_images WHERE id = ?", (image_id,))
        conn.commit()
        conn.close()
        
        # Delete file from filesystem
        file_path = UPLOAD_DIR / filename
        
        # Verify the resolved path is within UPLOAD_DIR
        try:
            file_path_resolved = file_path.resolve()
            upload_dir_resolved = UPLOAD_DIR.resolve()
            if not str(file_path_resolved).startswith(str(upload_dir_resolved)):
                raise HTTPException(status_code=403, detail="Access denied")
        except (OSError, RuntimeError):
            raise HTTPException(status_code=400, detail="Invalid path")
        
        if file_path.exists():
            file_path.unlink()
        
        return {"message": "Image deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
