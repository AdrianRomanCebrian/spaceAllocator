from flask import render_template, jsonify, redirect, url_for, request

from app import utils
from app.models.taskModel import Task
from app import app, db

from app.tasks.analizar_solucion_task import procesar_solucion

@app.route('/analizar_solucion_form', methods=['GET'])
def analizar_solucion_form():
    return render_template('analizar_solucion.html')

@app.route('/analizar_solucion', methods=['POST'])
def analizar_solucion():
    if request.method == 'POST':
        
        # Verificar que todos los archivos necesarios se han enviado
        if 'solucion' not in request.files or 'aulas' not in request.files:
            return jsonify({'error': 'No se ha enviado doc'}), 400
        
        if 'nombre' not in request.form:
            return jsonify({'error': 'No se ha enviado el nombre para identificar la tarea.'}), 400
        
        try:
            # Obtener los archivos
            archivo_aulas = request.files['aulas']
            archivo_solucion = request.files['solucion']
            nombre = request.form['nombre']

            # Verificar si los archivos tienen nombre
            if archivo_aulas.filename == '' or archivo_solucion.filename == '':
                return jsonify({'error': 'Nombre de archivo no válido'}), 400
            
            if nombre == '':
                return jsonify({'error': 'Nombre de identificación no válido'}), 400
            
            task = Task.query.filter(Task.nombre == nombre).first()

            if task is not None:
                return jsonify({'error': 'Ya existe una tarea con el nombre indicado. Ingresa un nombre distinto.'}), 400
            
            # abrir archivos
            entradas_records = utils.abrir_archivo(archivo_solucion, ";").to_dict('records')

            df_aulas = utils.abrir_archivo(archivo_aulas, ";")
            aulas = {str(k): int(v) for k, v in dict(df_aulas[["id", "capacity"]].values).items()}

            # Verificar si los archivos tienen nombre
            if archivo_aulas.filename == '' or archivo_solucion.filename == '':
                return jsonify({'error': 'Nombre de archivo no válido'}), 400
            
            if nombre == '':
                return jsonify({'error': 'Nombre de identificación no válido'}), 400
            
            task = Task.query.filter(Task.nombre == nombre).first()

            if task is not None:
                return jsonify({'error': 'Ya existe una tarea con el nombre indicado. Ingresa un nombre distinto.'}), 400

            # Llamar a la función abrir_archivo para procesar cada archivo
            celery_task = procesar_solucion.delay(aulas, entradas_records)
            
            # guardamos la tarea en db para tener la relacion
            db_task = Task()
            db_task.nombre = nombre
            db_task.celery_task_id = celery_task.id

            db.session.add(db_task)
            db.session.commit()

            return redirect(url_for('get_tasks'))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return render_template('analizar_solucion.html')