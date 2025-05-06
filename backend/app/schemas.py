from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .models import StatusEnum, RequestType

class TaskCreate(BaseModel):
    content: str
    department: str
    deadline: datetime
    telegram_id: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    type: Optional[RequestType] = RequestType.complaint  # по умолчанию "жалоба"

class TaskUpdate(BaseModel):
    status: StatusEnum

class ResponseOut(BaseModel):
    id: int
    request_id: int
    text: str
    sent_by: Optional[str]
    sent_at: datetime

    class Config:
        from_attributes = True

class TaskOut(BaseModel):
    id: int
    code: Optional[str]
    content: str
    department: str
    status: StatusEnum
    type: RequestType
    created_at: datetime
    deadline: datetime
    telegram_id: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    reply: Optional[str] = None
    responses: Optional[List[ResponseOut]] = []

    class Config:
        from_attributes = True
