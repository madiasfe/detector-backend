# Dockerfile corrigido para Google Cloud Run
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para OpenCV e outras libs
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro para cache eficiente
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Expõe a porta que o Cloud Run usa
EXPOSE 8080

# Comando para executar a aplicação
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120 --preload backend_app:app
