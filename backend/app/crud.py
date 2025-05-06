from sqlalchemy.orm import Session
from datetime import datetime
import random
from . import models, schemas
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import models

def delete_complaint(db: Session, complaint_id: int):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if complaint:
        db.delete(complaint)
        db.commit()
        return True
    return False

# Генерация кода обращения: FM-2025-XXXX
def generate_request_code():
    year = datetime.utcnow().year
    suffix = random.randint(1000, 9999)
    return f"FM-{year}-{suffix}"

# Создание задачи
def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(
        content=task.content,
        department=task.department,
        deadline=task.deadline,
        telegram_id=task.telegram_id,
        username=task.username,
        full_name=task.full_name,
        type=task.type,
        code=generate_request_code()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# Получение всех задач с обновлением просроченных
def get_tasks(db: Session):
    tasks = db.query(models.Task).all()
    # Обновляем просроченные статусы
    for task in tasks:
        if task.status != models.StatusEnum.done and task.deadline < datetime.utcnow():
            task.status = models.StatusEnum.overdue
    db.commit()
    return tasks

# Получение задачи по коду
def get_task_by_code(db: Session, code: str):
    return db.query(models.Task).filter(models.Task.code == code).first()

# Обновление статуса задачи
def update_task_status(db: Session, task_id: int, status: schemas.TaskUpdate):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    task.status = status.status
    db.commit()
    db.refresh(task)
    return task

# Сохранение ответа на задачу
def save_reply(db: Session, task_id: int, text: str, moderator_name: str = "Модератор"):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    reply = models.Response(
        request_id=task.id,
        text=text,
        sent_by=moderator_name,
        sent_at=datetime.utcnow()
    )
    task.reply = text  # для отображения в таблице
    db.add(reply)
    db.commit()
    return reply

# Получение статистики по всем задачам
def get_task_stats(db: Session):
    total = db.query(models.Task).count()
    done = db.query(models.Task).filter(models.Task.status == models.StatusEnum.done).count()
    in_progress = db.query(models.Task).filter(models.Task.status == models.StatusEnum.in_progress).count()
    overdue = db.query(models.Task).filter(models.Task.status == models.StatusEnum.overdue).count()

    return {
        "total": total,
        "done": done,
        "in_progress": in_progress,
        "overdue": overdue,
    }

# Получение детализированной статистики по каждому отделу
def get_detailed_stats(db: Session):
    departments = db.query(models.Task.department).distinct().all()  # Получаем уникальные отделы
    stats = {}

    for dept_obj in departments:
        dept = dept_obj[0]
        q = db.query(models.Task).filter(models.Task.department == dept)

        total = q.count()
        done = q.filter(models.Task.status == models.StatusEnum.done).count()
        in_progress = q.filter(models.Task.status == models.StatusEnum.in_progress).count()
        overdue = q.filter(models.Task.status == models.StatusEnum.overdue).count()

        # Вычисление средней продолжительности выполнения задач
        durations = []
        for task in q.filter(models.Task.status == models.StatusEnum.done):  # Только выполненные задачи
            if task.created_at and task.deadline:
                hours = (task.deadline - task.created_at).total_seconds() / 3600
                durations.append(hours)

        avg_hours = round(sum(durations) / len(durations), 1) if durations else 0

        stats[dept] = {
            "total": total,
            "done": done,
            "in_progress": in_progress,
            "overdue": overdue,
            "avg_hours": avg_hours
        }

    return stats
