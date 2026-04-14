from typing import List, Optional

from pydantic import BaseModel


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
