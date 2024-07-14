import pandas as pd
import chardet
import hashlib
import io


def penalizacion_tipo_relu(num, fraccion_negativo=1000):
    # el sgundo parametro del return indica si sobrepasa la capacidad del aula o no
    return (num, True) if num > 0 else (abs(num//fraccion_negativo), False)


def abrir_archivo(archivo, sep=None):
    # Leer los bytes del archivo
    raw_data = archivo.read()
    
    # Detectar automáticamente la codificación del archivo
    resultado = chardet.detect(raw_data)
    codificacion = resultado['encoding']
    
    # Decodificar los bytes usando la codificación detectada
    decoded_data = raw_data.decode(codificacion)

    # Crear un objeto StringIO para cargar los datos en pandas
    io_string = io.StringIO(decoded_data)

    # Leer el CSV en un DataFrame de pandas
    df = pd.read_csv(io_string, sep=sep, na_values="")

    return df



def obtener_lineas_archivo(archivo):
    # Leer los bytes del archivo
    raw_data = archivo.read()
    
    # Detectar automáticamente la codificación del archivo
    resultado = chardet.detect(raw_data)
    codificacion = resultado['encoding']

    if codificacion is not None:
        # Decodificar los bytes usando la codificación detectada
        decoded_data = raw_data.decode(codificacion)

        # Dividir el contenido en líneas
        lineas = decoded_data.splitlines()

        return lineas
    else:
        return []

def hash_string(input_string):
    hasher = hashlib.md5()
    hasher.update(input_string.encode('utf-8'))
    hash = hasher.hexdigest()
    
    return hash