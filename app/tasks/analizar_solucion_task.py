from app.cmd.algotimo_heuristico import *
from app import celery

@celery.task
def procesar_solucion(aulas, entradas_records):
    try:
        # Procesar entradas directamente como diccionario de registros
        for entrada in entradas_records:
            entrada['restriccion'] = 0
            entrada['Superposiciones'] = 0
            entrada['Grupo_Hash'] = utils.hash_string(str(entrada['Codigo']).strip() +
                                                        str(entrada['Grupo']).strip() +
                                                        str(entrada['Curso']).strip() +
                                                        str(entrada['Titulacion']).strip())
            entrada['Grupo_Str'] = str(str(entrada['Titulacion']).strip() + " " +
                                                        str(entrada['Curso']).strip() + " " +
                                                        str(entrada['Asignatura']).strip() + " " +
                                                        str(entrada['Grupo']).strip())

        # Seleccionar solo las columnas necesarias
        columnas_necesarias_entradas = ['id', 'start_time', 'end_time', 'Codigo', 'Grupo', 'Curso',
                                        'Titulacion', 'Matriculados', 'Grupo_Hash', 'room_id',
                                        'restriccion', 'Superposiciones', 'Grupo_Str']
        entradas = [{col: entrada[col] for col in columnas_necesarias_entradas} for entrada in entradas_records]

        # calcular superoposiciones en las entradas
        entradas_con_superposicion_info, _ = calcular_superposicion_entradas(entradas)

        lst_entradas = []
        for entrada in entradas_con_superposicion_info:
            e = Entrada(entrada['id'], entrada['start_time'], entrada['end_time'], entrada['Matriculados'], str(entrada['room_id']), entrada['Grupo_Hash'], entrada['conflictos_horarios'], 0, entrada['Grupo_Str'])
            lst_entradas.append(e)

        # Crear individuo y calcular su fitness
        individuo = Individuo(lst_entradas)
        individuo.fitness, individuo.Conflictos = fitness(individuo, aulas)

        response = obtener_todos_los_resultados(individuo, aulas)
        return response
    except Exception as e:
        return {'error': str(e)}, 500