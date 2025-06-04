# Usa una imagen base con Python
FROM python:3.11-slim


# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de la aplicación al contenedor
COPY . /app

# Instala las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Instala gunicorn
RUN pip install gunicorn

# Expón el puerto 8502 para el contenedor
EXPOSE 8502

# Comando para ejecutar la aplicación con gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8502", "script:app"]
