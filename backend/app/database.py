import sqlite3
from contextlib import contextmanager

DB_PATH = "lifetime_calendar.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
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
        conn.commit()
