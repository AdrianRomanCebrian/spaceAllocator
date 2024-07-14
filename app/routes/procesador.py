
from app import app, db
from app.tasks.algoritmo_heuristico_task import procesar_datos

from flask import request, jsonify, redirect, url_for
from app import utils

from app.models.taskModel import Task

@app.route('/procesar', methods=['POST'])
def procesar_file():
    if request.method == 'POST':
        # Verificar que todos los archivos necesarios se han enviado
        if 'aulas' not in request.files or 'entradas' not in request.files or 'restricciones' not in request.files:
            return jsonify({'error': 'No se han enviado todos los archivos necesarios (aulas, entradas, restricciones)'}), 400
        
        if 'nombre' not in request.form:
            return jsonify({'error': 'No se ha enviado el nombre para identificar la tarea.'}), 400
        
        try:
            # Obtener los archivos
            archivo_aulas = request.files['aulas']
            archivo_entradas = request.files['entradas']
            archivo_restricciones = request.files['restricciones']
            nombre = request.form['nombre']

            # Verificar si los archivos tienen nombre
            if archivo_aulas.filename == '' or archivo_entradas.filename == '' or archivo_restricciones.filename == '':
                return jsonify({'error': 'Nombre de archivo no válido'}), 400
            
            if nombre == '':
                return jsonify({'error': 'Nombre de identificación no válido'}), 400
            
            task = Task.query.filter(Task.nombre == nombre).first()

            if task is not None:
                return jsonify({'error': 'Ya existe una tarea con el nombre indicado. Ingresa un nombre distinto.'}), 400

            # Llamar a la función abrir_archivo para procesar cada archivo
            df_aulas = utils.abrir_archivo(archivo_aulas, ";")
            df_entradas = utils.abrir_archivo(archivo_entradas, ";")
            lst_restricciones = utils.obtener_lineas_archivo(archivo_restricciones)
            celery_task = procesar_datos.delay(
                {str(k): int(v) for k, v in dict(df_aulas[["id", "capacity"]].values).items()}, 
                df_entradas.to_dict('records'), 
                lst_restricciones)
            
            # guardamos la tarea en db para tener la relacion
            db_task = Task()
            db_task.nombre = nombre
            db_task.celery_task_id = celery_task.id

            db.session.add(db_task)
            db.session.commit()

            return redirect(url_for('get_tasks'))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
