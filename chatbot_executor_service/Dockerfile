# Usa una imagen más liviana basada en Python 3.10
FROM python:3.10

# Define el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo los archivos necesarios antes de instalar dependencias
COPY requirements.txt /app/

# Instala dependencias del sistema necesarias para Python (opcional, según tus paquetes)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Instalar cliente MySQL
RUN apt-get update && apt-get install -y default-mysql-client

# Copia el resto del código fuente al contenedor
COPY . /app
RUN chmod +x /app/entrypoint.sh

# Expone el puerto interno 5000
EXPOSE 5000

# Define el comando de ejecución con Gunicorn
# CMD ["gunicorn", "-k", "eventlet", "--log-level", "debug", "--timeout", "0", "--worker-connections", "1000", "-b", "0.0.0.0:5000", "app:app"]
CMD ["/app/entrypoint.sh"]