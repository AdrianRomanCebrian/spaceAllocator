from flask import render_template, jsonify, redirect, url_for
from celery.result import AsyncResult
import json

from app import app, celery

@app.route('/get_results_task/<task_id>/<task_name>')
def get_results_task(task_id, task_name):
    # Obtener el resultado de la tarea usando AsyncResult de Celery
    result = AsyncResult(task_id, app=celery)

    # Verificar si la tarea está lista
    if result.ready():
        # Obtener el resultado de la tarea
        task_result = result.result  # Aquí puedes ajustar según el resultado que devuelve tu tarea
        task_name_csv = f"{task_name.replace(' ', '_')}.csv"
        # Renderizar un template HTML con los resultados
        return render_template('task_results.html', task_result=task_result, task_name=task_name_csv)
        # return jsonify(task_result)
    else:
        # Si la tarea aún no está lista, mostrar un mensaje o redirigir a otra página
        return redirect(url_for('get_tasks'))