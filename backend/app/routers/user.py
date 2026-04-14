from fastapi import APIRouter, HTTPException

from app.database import get_db
from app.schemas import UserData

router = APIRouter(prefix="/api")


@router.post("/user")
async def save_user_data(user_data: UserData):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_data")
            cursor.execute(
                "INSERT INTO user_data (birthdate, life_expectancy) VALUES (?, ?)",
                (user_data.birthdate, user_data.life_expectancy),
            )
            conn.commit()
        return {"message": "User data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user")
async def get_user_data():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT birthdate, life_expectancy FROM user_data ORDER BY created_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
        if result:
            return {"birthdate": result[0], "life_expectancy": result[1]}
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
