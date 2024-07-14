# Usa una imagen base oficial de Python
FROM python:3.11.0-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app - v2

# Copia el archivo de requerimientos y el archivo de la aplicación al contenedor
COPY . .

# Instala las dependencias
RUN pip install -r requirements.txt

# Expone el puerto en el que corre la aplicación
EXPOSE 5000

# Define el comando para correr la aplicación
CMD ["python", "run.py"]
