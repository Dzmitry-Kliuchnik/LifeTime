from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
import os
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)