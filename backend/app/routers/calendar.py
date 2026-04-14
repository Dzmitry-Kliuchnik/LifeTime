from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.schemas import CalendarResponse

router = APIRouter(prefix="/api")


@router.get("/calendar")
async def get_calendar_data():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT birthdate, life_expectancy FROM user_data ORDER BY created_at DESC LIMIT 1"
            )
            user_row = cursor.fetchone()

        if not user_row:
            raise HTTPException(
                status_code=404,
                detail="User data not found. Please set your birthdate first.",
            )

        birthdate = datetime.fromisoformat(user_row[0])
        life_expectancy = user_row[1]
        total_weeks = life_expectancy * 52
        current_date = datetime.now()
        lived_weeks = int((current_date - birthdate).days / 7)
        current_week = lived_weeks + 1

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT week_number, year, note, is_lived FROM week_notes")
            notes_data = cursor.fetchall()

        notes_dict = {
            f"{row[1]}-{row[0]}": {"note": row[2], "is_lived": row[3]}
            for row in notes_data
        }

        weeks = []
        current_week_date = birthdate
        for week_num in range(1, total_weeks + 1):
            year = current_week_date.year
            week_of_year = current_week_date.isocalendar()[1]
            week_key = f"{year}-{week_of_year}"
            weeks.append({
                "week_number": week_num,
                "year": year,
                "week_of_year": week_of_year,
                "date": current_week_date.isoformat(),
                "is_lived": week_num <= lived_weeks,
                "is_current": week_num == current_week,
                "note": notes_dict.get(week_key, {}).get("note", ""),
            })
            current_week_date += timedelta(days=7)

        return CalendarResponse(
            total_weeks=total_weeks,
            lived_weeks=lived_weeks,
            current_week=current_week,
            weeks=weeks,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
