from flask import Flask
from celery import Celery
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'  # URL de Redis
app.config['result_backend'] = 'redis://redis:6379/0'  # URL de Redis
app.config['broker_connection_retry_on_startup'] = True  # If you wish to retain the existing behavior for retrying connections on startup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

db = SQLAlchemy(app)

# rutas
from app.tasks import *
from app.routes import *

# modelos
from app.models import *

# Crear la base de datos y las tablas
with app.app_context():
    db.create_all()