from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
import sqlite3
import uvicorn
import json
from fastapi.responses import Response

from llm_client import generate_survey_from_journey 
from prompts import SYSTEM_PROMPT
import database as db

app = FastAPI(title="Bank Survey Generator MVP")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация БД при старте
@app.on_event("startup")
def startup_event():
    db.init_db()

class SurveyRequest(BaseModel):
    journey: Any
    hint: Optional[str] = None

class SurveyResponse(BaseModel):
    category: str
    relevance: float
    questions: List[str]

@app.post("/api/generate", response_model=SurveyResponse)
async def generate_survey(request: SurveyRequest):
    # Вызов модели
    result = generate_survey_from_journey(request.journey, request.hint)
    
    survey_id = db.save_survey(
        journey=request.journey,
        hint=request.hint,
        result=result,
        prompt=SYSTEM_PROMPT,
        model_name="meta-llama-3.1-8b-instruct"
    )
    
    # Возвращаем результат + ID
    return {**result, "survey_id": survey_id}

@app.get("/api/surveys")
async def list_surveys(limit: int = 50):
    """Получить список последних сгенерированных опросов."""
    return db.get_all_surveys(limit)

@app.get("/api/surveys/{survey_id}")
async def get_survey(survey_id: int):
    """Получить детали конкретного опроса."""
    with sqlite3.connect(db.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Survey not found")
        return dict(row)

@app.get("/api/surveys/export/csv")
async def export_surveys_csv():
    import csv, io
    surveys = db.get_all_surveys(limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "category", "relevance", "questions_count", "hint"])
    for s in surveys:
        try:
            res = json.loads(s["generated_result"])
            writer.writerow([
                s["id"], s["created_at"], 
                res.get("category", ""), 
                res.get("relevance", ""), 
                len(res.get("questions", [])),
                s["hint"] or ""
            ])
        except:
            continue
    
        return Response(output.getvalue(), media_type="text/csv", 
                   headers={"Content-Disposition": "attachment; filename=surveys.csv"})
    
class EditRequest(BaseModel):
    edited_result: dict

@app.put("/api/surveys/{survey_id}/edit")
async def save_survey_edit(survey_id: int, request: EditRequest):
    """Сохраняет отредактированный пользователем результат."""
    success = db.update_survey_edited_result(survey_id, request.edited_result)
    if not success:
        raise HTTPException(status_code=404, detail="Survey not found")
    return {"status": "ok", "message": "Edit saved"}

from fastapi.staticfiles import StaticFiles
from pathlib import Path

app.mount("/", StaticFiles(directory=str(Path(__file__).parent / "frontend"), html=True), name="frontend")

if __name__ == "__main__":
    # Запуск сервера на 8000 порте
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)