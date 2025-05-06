import os
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from . import models, schemas, crud, database
from .database import SessionLocal, engine
from telegram import Bot
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tasks", response_model=schemas.TaskOut)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    created = crud.create_task(db, task)
    return created


@app.get("/tasks", response_model=list[schemas.TaskOut])
def get_tasks(db: Session = Depends(get_db)):
    return crud.get_tasks(db)


@app.get("/tasks/code/{code}", response_model=schemas.TaskOut)
def get_by_code(code: str, db: Session = Depends(get_db)):
    task = crud.get_task_by_code(db, code)
    if not task:
        raise HTTPException(status_code=404, detail="Код обращения не найден")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, status: schemas.TaskUpdate, db: Session = Depends(get_db)):
    updated = crud.update_task_status(db, task_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return updated


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Deleted"}


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return crud.get_task_stats(db)


@app.get("/stats/full")
def get_full_stats(db: Session = Depends(get_db)):
    return crud.get_detailed_stats(db)


@app.get("/stats/report")
def download_stats_report(db: Session = Depends(get_db)):
    stats = crud.get_detailed_stats(db)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="📄 Отчёт по обращениям", ln=True, align="C")
    pdf.ln(10)

    for dept, data in stats.items():
        pdf.set_font("Arial", "B", size=12)
        pdf.cell(0, 10, f"{dept}:", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"  Всего: {data['total']}", ln=True)
        pdf.cell(0, 8, f"  Выполнено: {data['done']}", ln=True)
        pdf.cell(0, 8, f"  В процессе: {data['in_progress']}", ln=True)
        pdf.cell(0, 8, f"  Просрочено: {data['overdue']}", ln=True)
        pdf.cell(0, 8, f"  Среднее время: {data['avg_hours']} ч", ln=True)
        pdf.ln(5)

    path = "report.pdf"
    pdf.output(path)
    return FileResponse(path, filename="report.pdf", media_type='application/pdf')


@app.post("/tasks/{task_id}/reply")
def reply_to_user(task_id: int, message: str = Body(...), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task or not task.telegram_id:
        raise HTTPException(status_code=404, detail="Task or Telegram ID not found")

    try:
        # Сохраняем ответ модератора и отправляем
        crud.save_reply(db, task_id, message, moderator_name="Модератор")
        bot.send_message(chat_id=task.telegram_id, text=f"📢 Ответ на ваше обращение:\n\n{message}")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки: {e}")
