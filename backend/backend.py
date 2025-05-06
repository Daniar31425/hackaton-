### backend/app/database.py
import Cython
import dotenv
import fastapi
import psycopg2
import pydantic
from sqlalchemy import create_engine
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uvicorn

from backend.app.database import Base # type: ignore

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app import models, schemas, crud, keywords, utils
from backend.app.database import SessionLocal, engine, Base

# Создание таблиц в базе данных (если их ещё нет)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание задачи
@app.post("/tasks", response_model=schemas.TaskOut)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    department = task.department or keywords.match_department(task.content)
    task_data = schemas.TaskCreate(
        content=task.content,
        department=department,
        deadline=task.deadline
    )
    return crud.create_task(db, task_data)

# Получение всех задач
@app.get("/tasks", response_model=list[schemas.TaskOut])
def get_tasks(db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db)
    for task in tasks:
        task.status = utils.check_overdue(task)
    return tasks

# Обновление статуса задачи
@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, status: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = crud.update_task_status(db, task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Получение статистики
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return crud.get_task_stats(db)


DATABASE_URL = "postgresql://danik:9987@localhost:5432/futuremakers"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

### backend/app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.app.database import Base # type: ignore

class StatusEnum(str, enum.Enum):
    in_progress = "в процессе"
    done = "выполнена"
    overdue = "просрочена"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    department = Column(String, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.in_progress)
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime)

### backend/app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from backend.app.models import StatusEnum # type: ignore

class TaskCreate(BaseModel):
    content: str
    department: str
    deadline: datetime

class TaskOut(BaseModel):
    id: int
    content: str
    department: str
    status: StatusEnum
    created_at: datetime
    deadline: datetime

    class Config:
        orm_mode = True

class TaskUpdate(BaseModel):
    status: StatusEnum

### backend/app/crud.py
from sqlalchemy.orm import Session
from .. import models, schemas
from datetime import datetime

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_tasks(db: Session):
    return db.query(models.Task).all()

def update_task_status(db: Session, task_id: int, status: schemas.TaskUpdate):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task:
        task.status = status.status
        db.commit()
        db.refresh(task)
    return task

def get_task_stats(db: Session):
    return {
        "total": db.query(models.Task).count(),
        "done": db.query(models.Task).filter(models.Task.status == "выполнена").count(),
        "in_progress": db.query(models.Task).filter(models.Task.status == "в процессе").count(),
        "overdue": db.query(models.Task).filter(models.Task.status == "просрочена").count()
    }

### backend/app/keywords.py
KEYWORDS_DEPARTMENT = {
    "дорога": "Отдел транспорта",
    "мусор": "ЖКХ",
    "вода": "Коммунальные службы",
    "освещение": "Энергетика",
    "интернет": "Цифровизация",
    "экология": "Экология"
}

def match_department(text: str):
    for keyword, dept in KEYWORDS_DEPARTMENT.items():
        if keyword in text.lower():
            return dept
    return "Общие обращения"

### backend/app/utils.py
from datetime import datetime, timedelta
from backend.app.models import StatusEnum # type: ignore

def check_overdue(task):
    if task.status == StatusEnum.done:
        return task.status
    if task.deadline < datetime.utcnow():
        return StatusEnum.overdue
    return task.status

### backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .. import models, schemas, crud, database, keywords, utils
from backend.app.database import SessionLocal, engine # type: ignore

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
    if not task.department:
        task.department = keywords.match_department(task.content)
    return crud.create_task(db, task)

@app.get("/tasks", response_model=list[schemas.TaskOut])
def get_tasks(db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db)
    for task in tasks:
        task.status = utils.check_overdue(task)
    return tasks

@app.put("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, status: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = crud.update_task_status(db, task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return crud.get_task_stats(db)

### backend/requirements.txt
fastapi
uvicorn
sqlalchemy
psycopg2-psycopg2.Binary
pydantic
Cython-dotenv