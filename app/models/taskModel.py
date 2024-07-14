import uuid
from sqlalchemy.dialects.postgresql import UUID as pgUUID

from app import db

class Task(db.Model):
    id = db.Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    celery_task_id = db.Column(db.String(100), nullable=False)
