# Usa uma imagem base oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# --- CORREÇÃO IMPORTANTE ---
# Instala a dependência do sistema que estava em falta (libgl1)
# antes de instalar as bibliotecas Python.
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Copia o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos do seu projeto (app, best.pt) para dentro do container
COPY . .

# Comando para iniciar a aplicação quando o container for executado
# Usa a forma "shell" que permite a substituição da variável de ambiente $PORT.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 backend_app:app
