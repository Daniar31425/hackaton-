from datetime import datetime
from backend.app.models import StatusEnum

def check_overdue(task):
    if task.status == StatusEnum.done:
        return task.status
    if task.deadline < datetime.utcnow():
        return StatusEnum.overdue
    return task.status
