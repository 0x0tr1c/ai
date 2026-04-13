import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "surveys.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                client_journey TEXT NOT NULL,
                hint TEXT,
                generated_result TEXT NOT NULL,
                prompt_used TEXT,
                user_edited_result TEXT,
                model_name TEXT,
                updated_at TIMESTAMP
            )
            """)
        conn.commit()

def save_survey(journey: str, hint: str, result: dict, prompt: str = None, edited_result: dict = None, model_name: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO surveys (
                client_journey, hint, generated_result, prompt_used, user_edited_result, model_name
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            json.dumps(journey, ensure_ascii=False) if isinstance(journey, dict) else journey,
            hint,
            json.dumps(result, ensure_ascii=False),
            prompt,
            json.dumps(edited_result, ensure_ascii=False) if edited_result else None,
            model_name
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_surveys(limit: int = 50):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM surveys ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
def update_survey_edited_result(survey_id: int, edited_result: dict):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE surveys 
            SET user_edited_result = ?, 
                updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """, (
            json.dumps(edited_result, ensure_ascii=False),
            survey_id
        ))
        conn.commit()
        return cursor.rowcount > 0