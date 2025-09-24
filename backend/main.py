from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
import os
import tempfile
import uuid
from typing import Optional, List

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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            birthdate TEXT NOT NULL,
            life_expectancy INTEGER DEFAULT 80,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS week_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            note TEXT,
            is_lived BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
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
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            # For development, return mock transcription if no API key
            return "[Mock Transcription] This is a placeholder transcription. Set OPENAI_API_KEY environment variable to use real Whisper."
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Read and transcribe the audio file
        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
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
            (user_data.birthdate, user_data.life_expectancy)
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
        cursor.execute("SELECT birthdate, life_expectancy FROM user_data ORDER BY created_at DESC LIMIT 1")
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
            raise HTTPException(status_code=404, detail="User data not found. Please set your birthdate first.")
        
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
        conn.close()
        
        # Create weeks data structure
        weeks = []
        notes_dict = {}
        
        # Convert notes to dictionary for quick lookup
        for note_data in notes_data:
            week_key = f"{note_data[1]}-{note_data[0]}"  # year-week_number
            notes_dict[week_key] = {
                "note": note_data[2],
                "is_lived": note_data[3]
            }
        
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
                "note": notes_dict.get(week_key, {}).get("note", "")
            }
            
            weeks.append(week_data)
            current_week_date += timedelta(days=7)
        
        return CalendarResponse(
            total_weeks=total_weeks,
            lived_weeks=lived_weeks,
            current_week=current_week,
            weeks=weeks
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
            (week_note.week_number, week_note.year)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing note
            cursor.execute(
                "UPDATE week_notes SET note = ?, is_lived = ? WHERE id = ?",
                (week_note.note, week_note.is_lived, existing[0])
            )
        else:
            # Insert new note
            cursor.execute(
                "INSERT INTO week_notes (week_number, year, note, is_lived) VALUES (?, ?, ?, ?)",
                (week_note.week_number, week_note.year, week_note.note, week_note.is_lived)
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
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = audio.filename.split('.')[-1] if '.' in audio.filename else 'webm'
        temp_file_path = os.path.join(AUDIO_UPLOAD_DIR, f"{file_id}.{file_extension}")
        
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        # Transcribe audio
        try:
            transcription = transcribe_audio_with_whisper(temp_file_path)
            
            return VoiceTranscriptionResponse(
                transcription=transcription,
                success=True
            )
            
        except Exception as transcription_error:
            return VoiceTranscriptionResponse(
                transcription="",
                success=False,
                error=f"Transcription failed: {str(transcription_error)}"
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
    week_number: int,
    year: int,
    is_lived: bool,
    existing_note: Optional[str] = None,
    audio: UploadFile = File(...)
):
    """
    Transcribe voice recording and append to existing week note.
    """
    try:
        # First transcribe the audio
        transcribe_response = await transcribe_voice(audio)
        
        if not transcribe_response.success:
            raise HTTPException(status_code=400, detail=transcribe_response.error)
        
        # Combine existing note with transcription
        transcribed_text = transcribe_response.transcription.strip()
        
        if existing_note and existing_note.strip():
            combined_note = f"{existing_note.strip()}\n\n[Voice Note]: {transcribed_text}"
        else:
            combined_note = f"[Voice Note]: {transcribed_text}"
        
        # Create WeekNote object and save
        week_note = WeekNote(
            week_number=week_number,
            year=year,
            note=combined_note,
            is_lived=is_lived
        )
        
        # Save using existing function
        await save_week_note(week_note)
        
        return {
            "message": "Voice note transcribed and saved successfully",
            "transcription": transcribed_text,
            "combined_note": combined_note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)