from flask import render_template

from app import app, celery
from app.models.taskModel import Task

# Ruta para obtener todas las tareas
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    task_list = []
    
    for task in tasks:
        # Obtener el estado de la tarea Celery
        celery_task = celery.AsyncResult(task.celery_task_id)
        task_list.append({
            'id': str(task.id),
            'celery_id': str(celery_task.id),
            'nombre': task.nombre,
            'estado': celery_task.state,
        })
    
    return render_template('tasks.html', tasks=task_list)