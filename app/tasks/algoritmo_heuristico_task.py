from app.cmd.algotimo_heuristico import *
from app import celery

@celery.task
def procesar_datos(aulas, entradas_records, restricciones_list):
    # try:
        # Procesar entradas directamente como diccionario de registros

        aulas, entradas_records, restricciones_list = verificar_tipos_de_datos(aulas, entradas_records, restricciones_list)
        
        for entrada in entradas_records:
            entrada['room_id'] = None
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
                                        'restriccion', 'Superposiciones', 'Grupo_Str', 'Asignatura']
        entradas = [{col: entrada[col] for col in columnas_necesarias_entradas} for entrada in entradas_records]

        # cargar restricciones
        for restriccion in restricciones_list:

            res_split = restriccion.split(";")
            if len(res_split) == 2:
                id, aula = res_split
                for e in entradas:
                    if e['id'] == str(id):
                        e['room_id'] = aula
                        e['restriccion'] = 1
                        break

            elif len(res_split) == 3:
                asignatura, grupo, aula = res_split        
                for e in entradas:
                    if (e['Asignatura'] == asignatura or e['Codigo'] == asignatura) and e['Grupo'] == grupo:
                        e['room_id'] = aula
                        e['restriccion'] = 1
            else:
                raise Exception("No se esperaba el tipo de restriccion que se ha puesto")

        # calcular superoposiciones en las entradas
        entradas_con_superposicion_info, grupos_conflicto_grupo = calcular_superposicion_entradas(entradas)

        individuo_optimo = generar_individuo_optimo(entradas_con_superposicion_info, aulas, grupos_conflicto_grupo)
 
        individuo_optimo_mejorado = vnd(individuo_optimo, aulas)

        aulas_dist= set()
        for e in individuo_optimo_mejorado.entradas:
            aulas_dist.add(e.Aula)

        response = obtener_todos_los_resultados(individuo_optimo_mejorado, aulas)
        
        return response
    # except Exception as e:
    #     return {'error': str(e)}, 500