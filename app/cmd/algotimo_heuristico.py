from app import utils
from itertools import groupby, combinations
from collections import Counter
from datetime import datetime, timezone
import pytz

PENALIZACION_GRUPOS_AULAS_DIST = 50
RESTRICCION_CAPACIDAD_AULAS = 1
PENALIZACION_SUPERPOSICION = 1000

class Entrada:
    def __init__(self, id, start_time, end_time, Matriculados, Aula, Grupo_Hash, Conflictos_Horarios, Restriccion, grupo_str):
        self.id = id
        self.start_time = start_time
        self.end_time = end_time
        self.Matriculados = Matriculados
        self.Aula = Aula
        self.Grupo_Hash = Grupo_Hash
        self.Conflictos_Horarios = Conflictos_Horarios
        self.Restriccion = Restriccion
        self.Grupo_Str = grupo_str

    def __str__(self):
        return f"Entrada(id={self.id}, start_time={self.start_time}, end_time={self.end_time}, " \
               f"Matriculados={self.Matriculados}, Aula={self.Aula}, Grupo_Hash={self.Grupo_Hash})"
    
    def calcular_fitness_entrada(self, entradas, capacidad_aula):
        contador_superposicion = 0
        set_aulas_grupo = {}
        set_aulas_grupo[self.Aula] = 1
        
        for entrada in entradas:
            if entrada.id == self.id:
                continue
            
            if self.start_time < entrada.end_time and self.end_time > entrada.start_time and self.Aula == entrada.Aula:
                contador_superposicion += 1

            if entrada.Grupo_Hash == self.Grupo_Hash:
                cuenta = set_aulas_grupo.get(entrada.Aula, 0)
                set_aulas_grupo[entrada.Aula] = cuenta + 1

        contador_capacidad, _ = utils.penalizacion_tipo_relu(self.Matriculados - capacidad_aula)

        # Paso 1: Encontrar el valor más grande en el diccionario
        max_value = max(set_aulas_grupo.values())

        # Paso 2: Sumar todos los valores excepto el más grande
        suma_sin_max = sum(1 for key, value in set_aulas_grupo.items() if value != max_value and key == self.Aula)

        return suma_sin_max * PENALIZACION_GRUPOS_AULAS_DIST + contador_capacidad * RESTRICCION_CAPACIDAD_AULAS + contador_superposicion * PENALIZACION_SUPERPOSICION
            

class Individuo:
    def __init__(self, entradas):
        self.entradas = entradas
        self.fitness = None  # Inicialmente el fitness se puede dejar como None o asignar un valor inicial
        self.Conflictos = set()

    def contar_aulas_por_grupo(self):
        aulas_por_grupo = {}
        
        for entrada in self.entradas:
            grupo = entrada.Grupo_Hash
            aula = entrada.Aula
            
            if grupo not in aulas_por_grupo:
                aulas_por_grupo[grupo] = set()
            
            aulas_por_grupo[grupo].add(aula)
        
        # Convertir los sets en conteos
        aulas_por_grupo_conteo = {grupo: len(_aulas) for grupo, _aulas in aulas_por_grupo.items()}
        
        return aulas_por_grupo_conteo

def verificar_superposicion(entradas):
    total = 0
    # Ordenar las entradas por 'Aula' y luego por 'start_time'
    entradas_ordenadas = sorted(entradas, key=lambda x: (x.Aula, x.start_time))
    grupos_por_aula = groupby(entradas_ordenadas, lambda x: x.Aula)
    entradas_conflictivas = set()
    # Verificar superposiciones dentro de cada grupo de 'Aula'
    for aula, grupo in grupos_por_aula:
        grupo_ordenado = sorted(grupo, key=lambda x: x.start_time)
        for i in range(len(grupo_ordenado) - 1):
            if grupo_ordenado[i].end_time > grupo_ordenado[i + 1].start_time:
                total += 1
                entradas_conflictivas.add(grupo_ordenado[i].id)
                entradas_conflictivas.add(grupo_ordenado[i+1].id)
    return total, entradas_conflictivas

def verificar_capacidad_aulas_y_aulas_distintas(entradas, aulas_capacidad):
    total_capacidad = 0
    grupos = {}

    entradas_conflictivas = set()

    for entrada in entradas:
        # capacidad
        capacidad_aula = aulas_capacidad.get(entrada.Aula, 0)
        penalizacion_capacidad, sobrepasa_capacidad_bool = utils.penalizacion_tipo_relu(entrada.Matriculados - capacidad_aula)
        total_capacidad += penalizacion_capacidad

        if sobrepasa_capacidad_bool:
            entradas_conflictivas.add(entrada.id)

        # distintas aulas
        aulas_grupo = grupos.get(entrada.Grupo_Hash, {})
        num_aula_grupo, conflictos = aulas_grupo.get(entrada.Aula, (0, set()))
        num_aula_grupo += 1
        conflictos.add(entrada.id)
        aulas_grupo[entrada.Aula] = (num_aula_grupo, conflictos)
        grupos[entrada.Grupo_Hash] = aulas_grupo

    # calcular penalizaciones por aula distinta y conflictos
    penalizacion_aula_distinta = 0
    conflictos_totales = set()
    for _, valores in grupos.items():
         # Paso 1: Encontrar el valor más grande en el diccionario
        max_value = max([v[0] for v in valores.values()])

        for value in valores.values():
            

            # Sumar todos los valores excepto el más grande
            if value[0] != max_value:
                conflictos_totales = conflictos_totales.union(value[1])
                penalizacion_aula_distinta += value[0]
        
    return total_capacidad, penalizacion_aula_distinta, entradas_conflictivas, conflictos_totales


def fitness(individuo, aulas_capacidad, p=False):
    # Verificar superposición de tiempos
    penalizacion_superposicion, entradas_conflictivas_ids_superposicion = verificar_superposicion(individuo.entradas)

    # Verificar capacidad de las aulas
    restriccion_capacidad_aulas, penalizacion_grupos_aulas_dist, entradas_conflictivas_ids_capacidad, entradas_conflictivas_penalizacion_grupos_aulas_dist = verificar_capacidad_aulas_y_aulas_distintas(individuo.entradas, aulas_capacidad)

    # Calcular la aptitud (fitness)
    fitness_value = (penalizacion_grupos_aulas_dist * PENALIZACION_GRUPOS_AULAS_DIST +
                     restriccion_capacidad_aulas * RESTRICCION_CAPACIDAD_AULAS +
                     penalizacion_superposicion * PENALIZACION_SUPERPOSICION)
    
    conflictos = entradas_conflictivas_ids_superposicion.union(entradas_conflictivas_ids_capacidad).union(entradas_conflictivas_penalizacion_grupos_aulas_dist)
    if p:
        pass
        print(f"Aulas: {penalizacion_grupos_aulas_dist}. Capacidad: {restriccion_capacidad_aulas}. Superpos. :{penalizacion_superposicion}")
    return fitness_value, conflictos


def calcular_superposicion_entradas(entradas_dict):

    
    grupos_conflicto_grupo = {}

    for row in entradas_dict:
        set_grupos_conflicto_con_grupo_actual = grupos_conflicto_grupo.get(row['Grupo_Hash'], set())
        superposiciones = 0
        entradas_conflicto_grupo = {}
        row_id = row['id']
        start_time = row['start_time']
        end_time = row['end_time']
        for compartion_row in entradas_dict:
            if row_id == compartion_row['id']:
                continue  # saltar si es la misma entrada

            if start_time < compartion_row['end_time'] and end_time > compartion_row['start_time']:
                superposiciones += 1

                # vemos los grupos mas conflictivos
                grupo = compartion_row['Grupo_Hash']

                num_conflictos_grupos = entradas_conflicto_grupo.get(grupo, 0)
                num_conflictos_grupos += 1
                entradas_conflicto_grupo[grupo] = num_conflictos_grupos

                set_grupos_conflicto_con_grupo_actual.add(grupo)

        grupos_conflicto_grupo[row['Grupo_Hash']] = set_grupos_conflicto_con_grupo_actual

        row['Superposiciones'] = superposiciones

    # recorrer las filas de nuevo para anotar el numero de conflictos totales de cada grupo
    for row in entradas_dict:
        grupo = row['Grupo_Hash']
        num_conflictos_grupos = entradas_conflicto_grupo.get(row['Grupo_Hash'], 0)
        row['conflictos_horarios'] = num_conflictos_grupos

    return entradas_dict, grupos_conflicto_grupo

def generar_individuo_optimo(entradas, aulas, grupos_conflicto_grupo, indice=None):
    if indice is not None:
        pass
        print("GENERANDO: ", indice)

    # diccionario grupo_aula
    dict_grupo_aula = {}

    # Inicializar aulas disponibles con capacidad y horarios vacíos
    aulas_disponibles = {aula: {'capacidad': capacidad, 'horarios': [], 'grupos_asignados': set()} for aula, capacidad in aulas.items()}

    # Ordenar entradas por número de conflictos y superposiciones
    entradas_ordenadas = sorted(
        entradas, 
        key=lambda x: (-x['restriccion'], -x['conflictos_horarios'], -x['Superposiciones'])
    )
    
    lst_entradas = []

    for row in entradas_ordenadas:
        mejor_aula = None
        menor_penalizacion = float('inf')
        
        start_time = row['start_time']
        end_time = row['end_time']
        matriculados = row['Matriculados']

        # comprobar si el grupo tiene aulas asignadas
        grupo_hash = row['Grupo_Hash']

        conflictos_horarios = row['conflictos_horarios']

        aulas_asignadas_previamente = dict_grupo_aula.get(grupo_hash, [])

        if row['restriccion'] == 1:
            # se le va a asignar el aula restringida
            aula_restringida = row['room_id']
            # Asignar horario al aula seleccionada
            aulas_disponibles[aula_restringida]['horarios'].append((start_time, end_time))
            # anotar que este grupo tiene clase en esta aula
            aulas_disponibles[aula_restringida]['grupos_asignados'].add(grupo_hash)
            entrada = Entrada(row['id'], start_time, end_time, matriculados, row['room_id'], grupo_hash, conflictos_horarios, 1, row['Grupo_Str'])
            lst_entradas.append(entrada)

            # guardar la nueva mejor aula del grupo si no esta ya en la lista
            if aula_restringida not in aulas_asignadas_previamente:
                aulas_asignadas_previamente.append(aula_restringida)
                dict_grupo_aula[grupo_hash] = aulas_asignadas_previamente  # se actualiza la lista de aulas del grupo
            continue  # si tiene restriccion no se toca

        # si no tiene aulas asignadas se asigna la mejor aula
        if not aulas_asignadas_previamente:

            # Iterar sobre las aulas disponibles
            for aula, datos in aulas_disponibles.items():
                capacidad_aula = datos['capacidad']
                horarios_aula = datos['horarios']
                grupos_asignados = datos['grupos_asignados']
                penalizacion_superposicion = sum(1 for horario in horarios_aula if start_time < horario[1] and end_time > horario[0])
                penalizacion_grupos_asignados_conflicto = len(grupos_asignados.intersection(grupos_conflicto_grupo[grupo_hash]))

                # Calcular penalización de capacidad
                penalizacion_capacidad, _ = utils.penalizacion_tipo_relu(matriculados - capacidad_aula)
                penalizacion_total = penalizacion_grupos_asignados_conflicto * PENALIZACION_GRUPOS_AULAS_DIST + penalizacion_capacidad * RESTRICCION_CAPACIDAD_AULAS + penalizacion_superposicion * PENALIZACION_SUPERPOSICION

                # Seleccionar el aula con menor penalización
                if penalizacion_total < menor_penalizacion:
                    menor_penalizacion = penalizacion_total
                    mejor_aula = aula
        
        # si tiene asignadas comprobaremos si estan disponibles y se la asignamos. Sinó buscamos una nueva mejor aula.
        else:  
            # Iterar sobre las aulas disponibles
            for aula in aulas_asignadas_previamente:
                datos = aulas_disponibles.get(aula)
                capacidad_aula = datos['capacidad']
                horarios_aula = datos['horarios']
                penalizacion_superposicion = sum(1 for horario in horarios_aula if start_time < horario[1] and end_time > horario[0])
                
                # si hay superposiciones continuamos sino, cogemos el aula como la mejor
                if penalizacion_superposicion > 0:
                    continue
                else:
                    mejor_aula = aula
                    break

            if not mejor_aula:
                # Iterar sobre las aulas disponibles
                for aula, datos in aulas_disponibles.items():
                    capacidad_aula = datos['capacidad']
                    horarios_aula = datos['horarios']
                    grupos_asignados = datos['grupos_asignados']
                    penalizacion_superposicion = sum(1 for horario in horarios_aula if start_time < horario[1] and end_time > horario[0])
                    penalizacion_grupos_asignados_conflicto = len(grupos_asignados.intersection(grupos_conflicto_grupo[grupo_hash]))

                    # Calcular penalización de capacidad
                    penalizacion_capacidad, _ = utils.penalizacion_tipo_relu(matriculados - capacidad_aula)
                    penalizacion_total = penalizacion_grupos_asignados_conflicto * PENALIZACION_GRUPOS_AULAS_DIST + penalizacion_capacidad * RESTRICCION_CAPACIDAD_AULAS + penalizacion_superposicion * PENALIZACION_SUPERPOSICION

                    # Seleccionar el aula con menor penalización
                    if penalizacion_total < menor_penalizacion:
                        menor_penalizacion = penalizacion_total
                        mejor_aula = aula

        if mejor_aula:
            # Asignar horario al aula seleccionada
            aulas_disponibles[mejor_aula]['horarios'].append((start_time, end_time))
            # anotar que este grupo tiene clase en esta aula
            aulas_disponibles[mejor_aula]['grupos_asignados'].add(grupo_hash)
            entrada = Entrada(row['id'], start_time, end_time, matriculados, mejor_aula, grupo_hash, conflictos_horarios, 0, row['Grupo_Str'])
            lst_entradas.append(entrada)

            # guardar la nueva mejor aula del grupo si no esta ya en la lista
            if mejor_aula not in aulas_asignadas_previamente:
                aulas_asignadas_previamente.append(mejor_aula)
                dict_grupo_aula[grupo_hash] = aulas_asignadas_previamente  # se actualiza la lista de aulas del grupo

    # Crear individuo y calcular su fitness
    individuo = Individuo(lst_entradas)
    individuo.fitness, individuo.Conflictos = fitness(individuo, aulas, True)

    return individuo

def coinciden_fechas(fechas, entrada_start_time, entrada_end_time):
    f = False
    for m_s_e_start_time, m_s_e_end_time in fechas:
        if m_s_e_start_time < entrada_end_time and m_s_e_end_time > entrada_start_time:
            f = True
            break
    return f

def actualizar_soluciones_relacionadas(entradahash_fitness, fechas_mejores_soluciones, aulas_actualizar, mejor_solucion, aulas):
    # print("ACTUALIZANDO ENTRADAS")
    cont = 0
    for hash, (_, entrada) in entradahash_fitness.items():
        if entrada.Aula in aulas_actualizar or coinciden_fechas(fechas_mejores_soluciones, entrada.start_time, entrada.end_time):
            cont += 1
            # hay que recalcular la entrada:
            fitness_entrada_actual = entrada.calcular_fitness_entrada(mejor_solucion.entradas, aulas[entrada.Aula])
            entradahash_fitness[hash] = (fitness_entrada_actual, entrada)

    # print(f"{cont} entradas ACTUALIZADAS")

    return entradahash_fitness

def busqueda_local_intercambio(solucion_actual, aulas, entradahash_fitness):
    mejor_fitness = solucion_actual.fitness
    entradas = solucion_actual.entradas
    conflictivas = solucion_actual.Conflictos

    posibilidades_entorno = []

    dict_entradas = {e.id: e for e in entradas}

    for iter, id_entrada in enumerate(conflictivas):
        if iter % 100 == 0:
            print(iter)
        entrada1 = dict_entradas[id_entrada]
        for entrada2 in entradas:
            # Aplicar la restricción para descartar combinaciones no válidas
            if (entrada1.Restriccion == 1 or entrada2.Restriccion == 1 or
                entrada1.Aula == entrada2.Aula or 
                not (entrada1.start_time < entrada2.end_time and entrada1.end_time > entrada2.start_time)):
                continue

            # Intercambiar aulas
            entrada1_propuesta = Entrada(
                entrada1.id, entrada1.start_time, entrada1.end_time,
                entrada1.Matriculados, entrada2.Aula, entrada1.Grupo_Hash, 
                entrada1.Conflictos_Horarios, entrada1.Restriccion, entrada1.Grupo_Str
            )
            entrada2_propuesta = Entrada(
                entrada2.id, entrada2.start_time, entrada2.end_time,
                entrada2.Matriculados, entrada1.Aula, entrada2.Grupo_Hash, 
                entrada2.Conflictos_Horarios, entrada2.Restriccion, entrada2.Grupo_Str
            )

            hash_entrada1_propuesta = utils.hash_string(str(entrada1_propuesta))
            hash_entrada2_propuesta = utils.hash_string(str(entrada2_propuesta))
            
            fitness_entrada1_propuesta, _ = entradahash_fitness.get(hash_entrada1_propuesta, (None, None))
            fitness_entrada2_propuesta, _ = entradahash_fitness.get(hash_entrada2_propuesta, (None, None))
            
            if not fitness_entrada1_propuesta:
                fitness_entrada1_propuesta = entrada1_propuesta.calcular_fitness_entrada(entradas, aulas[entrada2.Aula])
                entradahash_fitness[hash_entrada1_propuesta] = (fitness_entrada1_propuesta, entrada1_propuesta)
            
            if not fitness_entrada2_propuesta:
                fitness_entrada2_propuesta = entrada2_propuesta.calcular_fitness_entrada(entradas, aulas[entrada1.Aula])
                entradahash_fitness[hash_entrada2_propuesta] = (fitness_entrada2_propuesta, entrada2_propuesta)

            fitness_entrada1_actual, _ = entradahash_fitness.get(utils.hash_string(str(entrada1)), (None, None))
            fitness_entrada2_actual, _ = entradahash_fitness.get(utils.hash_string(str(entrada2)), (None, None))
            
            if not fitness_entrada1_actual:
                fitness_entrada1_actual = entrada1.calcular_fitness_entrada(entradas, aulas[entrada1.Aula])
                entradahash_fitness[utils.hash_string(str(entrada1))] = (fitness_entrada1_actual, entrada1)
            
            if not fitness_entrada2_actual:
                fitness_entrada2_actual = entrada2.calcular_fitness_entrada(entradas, aulas[entrada2.Aula])
                entradahash_fitness[utils.hash_string(str(entrada2))] = (fitness_entrada2_actual, entrada2)

            diferencia = (fitness_entrada1_actual + fitness_entrada2_actual) - (fitness_entrada1_propuesta + fitness_entrada2_propuesta)
            posibilidades_entorno.append((diferencia, entrada1_propuesta, entrada2_propuesta))

    if len(posibilidades_entorno) == 0:
        return solucion_actual, entradahash_fitness
    else:
        mejora_mejor_solucion_entorno = max(posibilidades_entorno, key=lambda x: x[0])[0]

        mejores_soluciones = [(tupla[1], tupla[2]) for tupla in posibilidades_entorno if tupla[0] == mejora_mejor_solucion_entorno]
        
        aulas_actualizar = set()
        fechas_mejores_soluciones = set()
        mejor_fitness_iteracion = mejor_fitness

        dict_id_entrada = {e.id: e for e in solucion_actual.entradas}

        for mejor_solucion_entorno in mejores_soluciones:
            entrada1_propuesta, entrada2_propuesta = mejor_solucion_entorno

            aula_anterior1 = dict_id_entrada[entrada1_propuesta.id].Aula
            aula_anterior2 = dict_id_entrada[entrada2_propuesta.id].Aula

            dict_id_entrada[entrada1_propuesta.id] = entrada1_propuesta
            dict_id_entrada[entrada2_propuesta.id] = entrada2_propuesta

            nuevas_entradas = list(dict_id_entrada.values())
            solucion_propuesta = Individuo(nuevas_entradas)
            solucion_propuesta.fitness, solucion_propuesta.Conflictos = fitness(solucion_propuesta, aulas, True)

            if solucion_propuesta.fitness < mejor_fitness_iteracion and (mejor_fitness_iteracion - solucion_propuesta.fitness) >= mejora_mejor_solucion_entorno:
                solucion_actual = solucion_propuesta
                mejor_fitness_iteracion = solucion_actual.fitness

                aulas_actualizar.add(aula_anterior1)
                aulas_actualizar.add(aula_anterior2)

                fechas_mejores_soluciones.add((entrada1_propuesta.start_time, entrada1_propuesta.end_time))
                fechas_mejores_soluciones.add((entrada2_propuesta.start_time, entrada2_propuesta.end_time))
        
        

        entradahash_fitness = actualizar_soluciones_relacionadas(entradahash_fitness, fechas_mejores_soluciones, aulas_actualizar, solucion_actual, aulas)

    return solucion_actual, entradahash_fitness


def busqueda_local(solucion_actual, aulas, entradahash_fitness):
    mejor_fitness = solucion_actual.fitness
    conflictivas = solucion_actual.Conflictos

    posibilidades_entorno = []

    dict_entradas = {e.id: e for e in solucion_actual.entradas}

    for _, id_entrada in enumerate(conflictivas):
        entrada_actual = dict_entradas[id_entrada]

        if entrada_actual is None or entrada_actual.Restriccion == 1:  # si la entrada tiene una restriccion de asignacion no la modificamos en ningun caso
            continue
        
        hash_entrada_actual = utils.hash_string(str(entrada_actual))
        fitness_entrada_actual, _ = entradahash_fitness.get(hash_entrada_actual, (None, None))
        if not fitness_entrada_actual:
            fitness_entrada_actual = entrada_actual.calcular_fitness_entrada(solucion_actual.entradas, aulas[entrada_actual.Aula])
            entradahash_fitness[hash_entrada_actual] = (fitness_entrada_actual, entrada_actual)

        for aula, capacidad in aulas.items():
            if aula == entrada_actual.Aula:
                continue

            entrada_propuesta = Entrada(
                entrada_actual.id, entrada_actual.start_time, entrada_actual.end_time,
                entrada_actual.Matriculados, aula, entrada_actual.Grupo_Hash, 
                entrada_actual.Conflictos_Horarios, entrada_actual.Restriccion, entrada_actual.Grupo_Str
            )

            hash_entrada_propuesta = utils.hash_string(str(entrada_propuesta))
            fitness_entrada_propuesta, _ = entradahash_fitness.get(hash_entrada_propuesta, (None, None))
            if not fitness_entrada_propuesta:
                fitness_entrada_propuesta = entrada_propuesta.calcular_fitness_entrada(solucion_actual.entradas, capacidad)
                entradahash_fitness[hash_entrada_propuesta] = (fitness_entrada_propuesta, entrada_propuesta)
            

            diferencia = fitness_entrada_actual - fitness_entrada_propuesta

            posibilidades_entorno.append((diferencia, entrada_propuesta))

    # Paso 1: Encontrar el máximo valor en la posición 0
    if len(posibilidades_entorno) == 0:
        return solucion_actual, entradahash_fitness 
    else:
            
        mejora_mejor_solucion_entorno = max(posibilidades_entorno, key=lambda x: x[0])[0]

        # Paso 2: Filtrar las tuplas que tienen el máximo valor
        mejores_soluciones = [tupla[1] for tupla in posibilidades_entorno if tupla[0] == mejora_mejor_solucion_entorno]
        # print(f"MEJORES SOL: {len(mejores_soluciones)}")
        
        aulas_actualizar = set()
        fechas_mejores_soluciones = set()
        mejor_fitness_iteracion = mejor_fitness

        dict_id_entrada = {e.id: e for e in solucion_actual.entradas}

        for mejor_solucion_entorno in mejores_soluciones:

            aula_anterior = dict_id_entrada[mejor_solucion_entorno.id].Aula
            aula_actual = mejor_solucion_entorno.Aula

            dict_id_entrada[mejor_solucion_entorno.id] = mejor_solucion_entorno
            nuevas_entradas = list(dict_id_entrada.values())
        
            solucion_propuesta = Individuo(nuevas_entradas)
            solucion_propuesta.fitness, solucion_propuesta.Conflictos = fitness(solucion_propuesta, aulas, True)

            if solucion_propuesta.fitness < mejor_fitness_iteracion and (mejor_fitness_iteracion - solucion_propuesta.fitness) >= mejora_mejor_solucion_entorno:
                solucion_actual = solucion_propuesta
                mejor_fitness_iteracion = solucion_actual.fitness

                # aulas para actualizar  
                aulas_actualizar.add(aula_anterior)
                aulas_actualizar.add(aula_actual)

                # horarios actualizar
                fechas_mejores_soluciones.add((mejor_solucion_entorno.start_time, mejor_solucion_entorno.end_time))

        entradahash_fitness = actualizar_soluciones_relacionadas(entradahash_fitness, fechas_mejores_soluciones, aulas_actualizar, solucion_actual, aulas)

    return solucion_actual, entradahash_fitness


# FUNCION VND (Variable Neighborhood Descent) PARA OPTIMIZAR
def vnd(sol_optima, aulas, entorno = [busqueda_local, busqueda_local_intercambio]):
    """La funcion optimiza una solucion basandose en la oiptimizacion lcoal VND.
    
    * sol_optima: solucion generada por heuristico constructivo. posible solucion a mejorar
    * aulas: diccionario {aula_id: capacidad}
    * entorno: funciones de optimizacion por orden de prioridad"""

    # limite de posibilidades
    K = len(entorno)

    # empezamos por al primera opcion (posicion 0)
    i = 0
    
    # inicializo el diccionario de {entrada_hash: valor fitness}
    entradahash_fitness = {}
    iter = 1
    # lanzar bucle optimizacion
    while i < K:  # si quedan opciones en el entono continuar
        print("*****    ITER: ", iter, "    Entorno: ", i)
        iter += 1
        # obtener optimizador
        optimizador = entorno[i]  

        # lanzar optimizacion de la solucion
        sol_propuesta, entradahash_fitness = optimizador(sol_optima, aulas, entradahash_fitness)

        if sol_propuesta.fitness < sol_optima.fitness:
            # si es mejor -> actualizar sol_optima y volver a la primera opcion
            sol_optima = sol_propuesta
            i = 0
        
        else:
            # si la solucion propeusta no es mejor probamos con el siguiente optimizador en la lista
            i += 1

    # cuando hemos visitado todos los optimizadores sin encontrar mejoras terminamos
    return sol_optima

def convertir_tipos_entradas(entradas_records):
    for entrada in entradas_records:
        entrada['id'] = str(entrada.get('id', '')).replace('"', "").replace("'", "")
        entrada['start_time'] = int(entrada.get('start_time', 0))
        entrada['end_time'] = int(entrada.get('end_time', 0))
        entrada['Titulacion'] = str(entrada.get('Titulacion', '')).replace('"', "").replace("'", "")
        entrada['Curso'] = int(entrada.get('Curso', 0))
        entrada['Codigo'] = str(entrada.get('Codigo', '')).replace('"', "").replace("'", "")
        entrada['Asignatura'] = str(entrada.get('Asignatura', '')).replace('"', "").replace("'", "")
        entrada['Grupo'] = str(entrada.get('Grupo', '')).replace('"', "").replace("'", "")
        entrada['Matriculados'] = int(entrada.get('Matriculados', 0))
    return entradas_records

def convertir_restricciones(restricciones_list):
    restricciones_convertidas = []
    for restriccion in restricciones_list:
        partes = restriccion.split(';')
        partes_convertidas = [str(parte).replace('"', "").replace("'", "") for parte in partes]
        restriccion_convertida = ';'.join(partes_convertidas)
        restricciones_convertidas.append(restriccion_convertida)
    return restricciones_convertidas

def verificar_tipos_de_datos(aulas, entradas_records, restricciones_list):

    aulas_aux = {str(_id).replace('"', "").replace("'", ""): int(capacity) for _id, capacity in aulas.items()}
    # Ordenar las aulas por capacidad
    aulas_ordenadas = dict(sorted(aulas_aux.items(), key=lambda item: item[1]))

    entradas_records_aux = convertir_tipos_entradas(entradas_records)

    restricciones_list_aux = convertir_restricciones(restricciones_list)

    return aulas_ordenadas, entradas_records_aux, restricciones_list_aux


def obtener_hist_aulas_data(individuo):
    # Contar la frecuencia de cada valor en el diccionario
    data = individuo.contar_aulas_por_grupo()

    if not data:
        return [], []

    value_counts = Counter(data.values())
    
    # Preparar los datos para el histograma
    values = list(value_counts.keys())
    frequencies = [x/len(data) for x in list(value_counts.values())]
    
    return values, frequencies

def obtener_porcent_entrada_conflicto(individuo):
    if len(individuo.entradas) == 0:
        return 0
    
    entradas_conflicto = (len(individuo.Conflictos) / len(individuo.entradas)) * 100

    res = {
        "Entradas sin conflicto": 100 - entradas_conflicto,
        "Entradas con conflicto": entradas_conflicto,
    }
    return  res

def obtener_porcentaje_conflicto_tipo(individuo, aulas_capacidad):
    # Verificar superposición de tiempos

    _, entradas_conflictivas_ids_superposicion = verificar_superposicion(individuo.entradas)
    n_conflictos_superposicion = len(entradas_conflictivas_ids_superposicion)

    # Verificar capacidad de las aulas
    _, _, entradas_conflictivas_ids_capacidad, entradas_conflictivas_penalizacion_grupos_aulas_dist = verificar_capacidad_aulas_y_aulas_distintas(individuo.entradas, aulas_capacidad)
    n_conflictos_capacidad = len(entradas_conflictivas_ids_capacidad)
    n_conflictos_distintas_aulas_grupo = len(entradas_conflictivas_penalizacion_grupos_aulas_dist)

    conflictos_totales = n_conflictos_superposicion + n_conflictos_capacidad + n_conflictos_distintas_aulas_grupo
    res = {
        "Superposición": n_conflictos_superposicion,
        "Capacidad aulas": n_conflictos_capacidad,
        "Cambios de aula": n_conflictos_distintas_aulas_grupo,
    }

    # si todas son 0 metemos otra opcion para que aparezca el grafico
    if conflictos_totales == 0:
        res["No existen conflictos"] = 100

    # Devolver el porcentaje de cada uno para piechart
    return res

def obtener_media_alumnos_capacidad_sobrepasada(individuo, aulas_capacidad):
    if len(individuo.entradas) == 0:
        return 0
    porcentaje_exceso = [
        1 if (e.Matriculados - aulas_capacidad.get(e.Aula, 0)) > 0 else 0
        for e in individuo.entradas
    ]

    media_de_exceso = (sum(porcentaje_exceso) / len(porcentaje_exceso)) * 100

    return {
        "Porcentaje de clases capacidad no superada": 100 - media_de_exceso,
        "Porcentaje de clases capacidad superada": media_de_exceso
    }

def calcular_porcentaje_uso_por_aula(datos, capacidad_por_aula):
    """Esta funcion calcula el porcentaje promedio de ocupacion de cada aula"""
    ocupacion_por_aula = {}

    # Calcular la ocupación para cada aula
    for entrada in datos:
        aula_id = entrada.Aula
        capacidad = capacidad_por_aula[aula_id]
        ocupacion = entrada.Matriculados
        ocupacion_por_aula.setdefault(aula_id, []).append(ocupacion/capacidad)

    # Calcular el promedio de ocupación para cada aula
    promedio_ocupacion = {}
    for aula_id, ocupaciones in ocupacion_por_aula.items():
        promedio_ocupacion[aula_id] = sum(ocupaciones) / len(ocupaciones)

    return dict(sorted(promedio_ocupacion.items(), key=lambda item: item[1], reverse=True))

def obtener_dias_unicos(datos):
    # Obtener los días únicos
    dias_unicos = set()
    for entrada in datos:
        # Convertir start_time y end_time a objetos datetime en UTC
        start_datetime = datetime.fromtimestamp(entrada.start_time, tz=timezone.utc)
        end_datetime = datetime.fromtimestamp(entrada.end_time, tz=timezone.utc)
        
        # Extraer la fecha (sin la hora) en UTC para contar días únicos
        fecha_start = str(start_datetime.date())
        fecha_end = str(end_datetime.date())
        dias_unicos.add(fecha_start)
        dias_unicos.add(fecha_end)
    return dias_unicos

def obtener_numeroclases_por_dia(datos, dias_unicos):
    respuesta = {d: 0 for d in dias_unicos}

    for entrada in datos:
        start_date = str(datetime.fromtimestamp(entrada.start_time, tz=timezone.utc).date())

        cont = respuesta[start_date]
        respuesta[start_date] = cont + 1

    return respuesta

def obtener_linea_temporal_conflictos(individuo, dias_unicos):
    respuesta = {d: 0 for d in dias_unicos}

    for entrada in individuo.entradas:
        if entrada.id in individuo.Conflictos:
            start_date = str(datetime.fromtimestamp(entrada.start_time, tz=timezone.utc).date())

            cont = respuesta[start_date]
            respuesta[start_date] = cont + 1

    return respuesta

def calcular_ocupacion_promedio_en_personas_por_aula(datos):
    """Esta función calculará el promedio de ocupación de cada aula durante el período analizado."""
    ocupacion_por_aula = {}

    # Calcular la ocupación para cada aula
    for entrada in datos:
        aula_id = entrada.Aula
        ocupacion = entrada.Matriculados
        ocupacion_por_aula.setdefault(aula_id, []).append(ocupacion)

    # Calcular el promedio de ocupación para cada aula
    promedio_ocupacion = {}
    for aula_id, ocupaciones in ocupacion_por_aula.items():
        promedio_ocupacion[aula_id] = sum(ocupaciones) / len(ocupaciones)

    return dict(sorted(promedio_ocupacion.items(), key=lambda item: item[1], reverse=True))

def identificar_horarios_concurridos(datos, mas_concurridos=True, limit=5):
    """Esta función identificará los horarios concurridos basados en el número de entradas registradas para esos períodos de tiempo específicos."""
    horarios_concurridos = {}

    local_tz = pytz.timezone('Europe/Madrid')

    # Contar las entradas para cada horario
    for entrada in datos:
        inicio = datetime.fromtimestamp(entrada.start_time, tz=timezone.utc).astimezone(local_tz).time()
        fin = datetime.fromtimestamp(entrada.end_time, tz=timezone.utc).astimezone(local_tz).time()
        horario = (inicio, fin)
        horarios_concurridos[horario] = horarios_concurridos.get(horario, 0) + 1

    # Encontrar los horarios más o menos concurridos
    if mas_concurridos:
        horarios_ordenados = sorted(horarios_concurridos.items(), key=lambda x: x[1], reverse=True)
    else:
        horarios_ordenados = sorted(horarios_concurridos.items(), key=lambda x: x[1])

    # Convertir los tiempos a strings para serialización JSON
    horarios_ordenados_str = [((str(horario[0]), str(horario[1])), num) for horario, num in horarios_ordenados[:limit]]

    return horarios_ordenados_str

def calcular_porcentaje_aulas_utilizadas(datos, capacidad_por_aula):
    """Esta función calculará el promedio de la capacidad utilizada de las aulas durante el período analizado."""
    # numero total de aulas disponibles
    total_aulas = len(capacidad_por_aula)

    aulas_utilizadas = set()
    for entrada in datos:
        aulas_utilizadas.add(entrada.Aula)

    # porcentaje de aulas aulas_utilizadas
    porct_aulas_utilizadas = (len(aulas_utilizadas) / total_aulas) * 100

    return {
        "Porcentaje de aulas utilizadas": porct_aulas_utilizadas,
        "Porcentaje de aulas sin utilizar": 100 - porct_aulas_utilizadas,
    }


def calcular_duracion_promedio_entradas(datos):
    """Esta función calculará la duración promedio de las entradas en las aulas durante el período analizado."""
    duraciones = [entrada.end_time - entrada.start_time for entrada in datos]
    if duraciones:
        duracion_promedio_segundos = sum(duraciones) / len(duraciones)
    else:
        duracion_promedio_segundos = 0.0

    duracion_promedio_minutos = duracion_promedio_segundos / 60
    duracion_promedio_horas = duracion_promedio_minutos / 60

    return round(duracion_promedio_horas, 2)


def obtener_asignacion_optima(individuo):
    response_asignacion = {}
    for entrada in individuo.entradas:
        response_asignacion[entrada.id] = entrada.Aula

    return response_asignacion

def obtener_relacion_grupo_aula(datos):
    grupo_aula = {}

    for entrada in datos:
        grupo_aula.setdefault(entrada.Grupo_Str, set()).add(entrada.Aula)
    return {grupo: list(aulas) for grupo, aulas in grupo_aula.items()}

def obtener_todos_los_resultados(individuo_optimo_mejorado, aulas):
    """La funcion llama a todas las funciones de resultados y los reune todos"""
    resultados = {}

    # obtener la asignacion de las aulas
    resultados['datos_descargar_asignacion'] = obtener_asignacion_optima(individuo_optimo_mejorado)

    # Llamar a cada función y almacenar resultados en el diccionario
    resultados['histograma_aulas_data'] = obtener_hist_aulas_data(individuo_optimo_mejorado)
    resultados['piechart_porcentaje_entrada_conflicto'] = obtener_porcent_entrada_conflicto(individuo_optimo_mejorado)
    resultados['piechart_porcentaje_conflicto_tipo'] = obtener_porcentaje_conflicto_tipo(individuo_optimo_mejorado, aulas)
    resultados['numero_media_alumnos_capacidad_sobrepasada'] = obtener_media_alumnos_capacidad_sobrepasada(individuo_optimo_mejorado, aulas)

    # Calcular porcentaje de uso
    datos_entradas = individuo_optimo_mejorado.entradas  # Suponiendo que individuo_optimo_mejorado tiene un atributo 'entradas'
    resultados['porcentaje_uso_por_aula'] = calcular_porcentaje_uso_por_aula(datos_entradas, aulas)

    # Calcular ocupación promedio
    resultados['numero_ocupacion_promedio_en_personas_por_aula'] = calcular_ocupacion_promedio_en_personas_por_aula(datos_entradas)

    # Identificar horarios menos y más concurridos
    resultados['histograma_horarios_menos_concurridos'] = identificar_horarios_concurridos(datos_entradas, mas_concurridos=False)
    resultados['histograma_horarios_mas_concurridos'] = identificar_horarios_concurridos(datos_entradas, mas_concurridos=True)

    # Calcular capacidad promedio utilizada
    resultados['porcentaje_aulas_utilizadas'] = calcular_porcentaje_aulas_utilizadas(datos_entradas, aulas)

    # Calcular duración promedio de entradas
    resultados['horas_duracion_promedio_entradas'] = calcular_duracion_promedio_entradas(datos_entradas)

    # obtener dias unicos
    dias_unicos = obtener_dias_unicos(datos_entradas)

    resultados['linea_temporal_numero_clases'] = dict(sorted(obtener_numeroclases_por_dia(datos_entradas, dias_unicos).items(), key=lambda item: datetime.strptime(item[0], '%Y-%m-%d')))
    resultados['linea_temporal_numero_conflictos'] = dict(sorted(obtener_linea_temporal_conflictos(individuo_optimo_mejorado, dias_unicos).items(), key=lambda item: datetime.strptime(item[0], '%Y-%m-%d')))

    resultados['grupos_aulas_asignaciones'] = obtener_relacion_grupo_aula(datos_entradas)

    return resultados


