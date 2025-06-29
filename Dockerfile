# Usa uma imagem base oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala as dependências do sistema que estavam em falta
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

# Copia o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instala as bibliotecas Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos do seu projeto para dentro do container
COPY . .

# Comando para iniciar a aplicação quando o container for executado
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 --log-level=debug backend_app:app
