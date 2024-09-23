# Usar una imagen base de Python
FROM python:3.9-slim

# Actualizar e instalar dependencias necesarias para Selenium y ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    chromium-driver \
    chromium \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establecer variables de entorno para Chrome en modo "headless"
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Copiar los archivos necesarios al contenedor
COPY requirements.txt requirements.txt
COPY main.py main.py

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto (opcional, solo si necesitas interactuar con la web de alguna manera)
EXPOSE 8080

# Comando para ejecutar tu bot de Telegram
CMD ["python", "main.py"]
