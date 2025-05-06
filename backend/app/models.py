from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import enum

class StatusEnum(str, enum.Enum):
    in_progress = "в процессе"
    done = "выполнена"
    overdue = "просрочена"

class RequestType(str, enum.Enum):
    complaint = "жалоба"
    idea = "идея"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)  # 🔢 Код: FM-2025-0001
    content = Column(String, nullable=False)
    department = Column(String, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.in_progress)
    type = Column(Enum(RequestType), default=RequestType.complaint)  # 🆕 Тип запроса
    created_at = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime)
    
    telegram_id = Column(String, nullable=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)

    reply = Column(String, nullable=True)

    responses = relationship("Response", back_populates="task")  # связь

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("tasks.id"))
    text = Column(String, nullable=False)
    sent_by = Column(String, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="responses")
